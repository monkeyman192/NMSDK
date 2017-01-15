"""
A program to generate DESCRIPTOR, SCENE and GEOMETRY files to allow
for procedural generated spawning in NMS.
This works by the user selecting a list of folders directly containing
a SCENE file of a model.
These scenes are packaged together in a way that if the resultant SCENE
is referenced in the leveloneobjects file, one of the models will be
randomly chosen per planet, alleviating the need to add all the models
explicitly into the leveloneobjects file.
"""

__author__ = "monkeyman192"
__version__ = "0.5"

from tkinter import *
from tkinter import filedialog
from tkinter import ttk

# local imports
from .. import nms_imp
from wckToolTips import ToolTipManager
tt = ToolTipManager()

# needed for misc functions
import os
import subprocess
#import xml.etree.ElementTree as ET

root = Tk()

class GUI(Frame):
    def __init__(self, master):
        self.master = master
        Frame.__init__(self, self.master)

        self.selected_dirs = set()      # this will contain the indexes of the selected files

        self.createWidgets()

    def createWidgets(self):
        # frame with buttons
        list_frame = Frame(self.master)
        self.data_view = ttk.Treeview(list_frame, columns = ['Object Name', 'Path'], displaycolumns = '#all', selectmode='extended')
        self.data_view.heading("Object Name", text="Object Name")
        self.data_view.heading("Path", text="Path")
        self.data_view.column("Object Name", stretch=True)
        self.data_view.column("Path", stretch=True)
        self.data_view["show"] = 'headings'
        ysb = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.data_view.yview)
        ysb.pack(side=RIGHT, fill=Y)
        self.data_view.configure(yscroll=ysb.set)
        self.data_view.pack(fill=BOTH, expand=1)
        list_frame.pack(fill=BOTH, expand=1)
        button_frame = Frame(self.master)
        add_button = Button(button_frame, text="ADD", command=self.add)
        add_button.pack(side=LEFT)
        tt.register(add_button, "Opens a dialog to select a folder containing all the model folders")
        remove_button = Button(button_frame, text="REMOVE", command=self.remove)
        remove_button.pack(side=LEFT)
        tt.register(remove_button, "Removes selected models from list")
        run_button = Button(button_frame, text="RUN", command=self.run)
        run_button.pack(side=LEFT)
        tt.register(run_button, "Creates the proc-gen spawner for the selected models")
        runall_button = Button(button_frame, text="RUN ALL", command=lambda:self.run(_all=True))
        runall_button.pack(side=LEFT)
        tt.register(runall_button, "Creates the proc-gen spawner for all the models above")
        quit_button = Button(button_frame, text="QUIT", command=self.quit)
        quit_button.pack(side=LEFT)
        tt.register(quit_button, "Exits the program")
        button_frame.pack()

    def create_list(self):
        self.dir_list = os.listdir(self.path_name)
        # now add stuff to it
        # let's do a bit of precessing. We will have two options:
        # 1. The directory chosen contains a list of folders, each of which contains a scene file
        # 2. The directory just contains a scene file
        # either way we want to make sure that the folders contain a scene file
        contains_scene = False
        scene_names = []
        for file in self.dir_list:
            if "SCENE" in file and "EXML" not in file.upper():
                # in this case we have option 2.
                # add the name of the scene file to the list of files
                contains_scene = True
                path = self.get_scene_path(os.path.join(self.path_name, file))
                scene_names.append((file, path))
        if contains_scene == False:
            for folder in self.dir_list:
                # in this case we have option 1
                subfolders = os.listdir(os.path.join(self.path_name, folder))
                # if we make it to this line option 1. is what has happened. Search through
                for file in subfolders:
                    if "SCENE" in file and "EXML" not in file.upper():
                        contains_scene = True
                        path = self.get_scene_path(os.path.join(self.path_name, folder, file))
                        scene_names.append((file, path))
        for scene in scene_names:
            self.data_view.insert("", 'end', values=scene)

    def get_scene_path(self, file_path):
        # this will open the scene file and read the path name
        try:
            fd = os.open(file_path, os.O_RDONLY|os.O_BINARY)
            os.lseek(fd, 0x60, os.SEEK_SET)
            bin_data = os.read(fd, 0x80)
            data = bin_data.decode()
            clean_data = data.rstrip(chr(0))
            return clean_data
        finally:
            os.close(fd)

    def remove(self):
        self.data_view.delete(*self.data_view.selection())

    def run(self, _all=False):
        if _all == False:
            self.selected_iids = self.data_view.selection()     # list of iids of selected elements
        else:
            # in this case we just want everything in the list
            self.selected_iids = self.data_view.get_children()
        self.selected_objects = list(self.data_view.item(iid)['values'][1] for iid in self.selected_iids)
        DataGenerator('PROCTEST', self.selected_objects)

    def add(self):
        self.path_name = filedialog.askdirectory(title="Specify path containing custom models")
        self.create_list()

    def quit(self):
        self.master.destroy()

class DataGenerator():
    def __init__(self, name, objects):
        self.name = name
        self.objects = objects

        self.path = os.path.join('CUSTOMMODELS', self.name.upper())

        # run the jobs
        self.generate_descriptor()
        self.generate_scene()
        self.generate_geometry()

        self.write()
        self.convert_to_mbin()

    def generate_descriptor(self):
        data_list = List()
        for i in range(len(self.objects)):
            data = dict()
            data['Id'] = "_PROCOBJ_{}".format(i)
            data['Name'] = "_PROCOBJ_{}".format(i)
            data['ReferencePaths'] = List(NMSString0x80(Value = '{}.SCENE.MBIN'.format(self.objects[i])))
            data['Chance'] = 0
            data_list.append(TkResourceDescriptorData(**data))
        main_data = TkResourceDescriptorList(TypeId = "_PROCOBJ_",
                                             Descriptors = data_list)
        self.TkModelDescriptorList = TkModelDescriptorList(List = List(main_data))
        self.TkModelDescriptorList.make_elements(main=True)

    def generate_scene(self):
        # first generate the data
        self.SceneData = Model(os.path.join(self.path, self.name.upper()))
        self.SceneData.create_attributes({'GEOMETRY': os.path.join(self.path, '{}.GEOMETRY.MBIN'.format(self.name.upper()))})
        for i in range(len(self.objects)):
            ref = Reference("_PROCOBJ_{}".format(i), Scenegraph = '{}.SCENE.MBIN'.format(self.objects[i]))
            ref.create_attributes(None) # just pass None because it doesn't matter with how Reference is set up currently !!! THIS MIGHT CHANGE !!!
            self.SceneData.add_child(ref)
            
        self.SceneData.construct_data()
        
        self.TkSceneNodeData = self.SceneData.get_data()
        self.TkSceneNodeData.make_elements(main=True)

    def generate_geometry(self):
        # this is super easy as the default template is all we need. Yay!
        self.TkGeometryData = TkGeometryData()
        self.TkGeometryData.make_elements(main=True)

    def write(self):
        #make sure the directory exists:
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.TkModelDescriptorList.tree.write("{}.DESCRIPTOR.exml".format(os.path.join(self.path, self.name.upper())))
        self.TkGeometryData.tree.write("{}.GEOMETRY.exml".format(os.path.join(self.path, self.name.upper())))
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(os.path.join(self.path, self.name.upper())))

    def convert_to_mbin(self):
        # passes all the files produced by
        print('Converting all .exml files to .mbin. Please wait while this finishes.')
        for directory, folders, files in os.walk(self.path):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1] == '.exml':
                    subprocess.call(["MBINCompiler.exe", location])
                    os.remove(location)

app = GUI(master=root)
app.mainloop()
