from lxml import etree

from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from classes import *

import os
import subprocess

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
        self.data_view = ttk.Treeview(list_frame, columns = ['Object Name'], displaycolumns = ['Object Name'], selectmode='extended')
        self.data_view.heading("Object Name", text="Object Name")
        self.data_view["show"] = 'headings'
        ysb = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.data_view.yview)
        ysb.pack(side=RIGHT, fill=Y)
        self.data_view.configure(yscroll=ysb.set)
        self.data_view.pack()
        list_frame.pack()
        button_frame = Frame(self.master)
        add_button = Button(button_frame, text="ADD", command=self.add)
        add_button.pack(side=LEFT)
        run_button = Button(button_frame, text="RUN", command=self.run)
        run_button.pack(side=LEFT)
        quit_button = Button(button_frame, text="QUIT", command=self.quit)
        quit_button.pack(side=LEFT)
        button_frame.pack()

    def create_list(self):
        self.dir_list = os.listdir(self.path_name)
        # make sure the view is empty
        self.data_view.delete(*self.data_view.get_children())
        # now add stuff to it
        for _dir in self.dir_list:
            self.data_view.insert("", 'end', values=_dir)

    def run(self):
        self.selected_iids = self.data_view.selection()     # list of iids of selected elements
        self.selected_names = list(self.data_view.item(iid)['values'][0] for iid in self.selected_iids)
        print(self.selected_names)
        DataGenerator('PROCTEST', self.selected_names)

    def add(self):
        self.path_name = filedialog.askdirectory(title="Specify path containing custom models")
        self.create_list()

    def quit(self):
        self.master.destroy()

class DataGenerator():
    def __init__(self, name, obj_names):
        self.name = name
        self.obj_names = obj_names

        self.path = os.path.join('CUSTOMMODELS', self.name.upper())

        # run the jobs
        self.generate_descriptor()
        self.generate_scene()
        self.generate_geometry()

        self.write()
        self.convert_to_mbin()

    def generate_descriptor(self):
        data_list = List()
        for obj in self.obj_names:
            data = dict()
            data['Id'] = "_PROCOBJ_{}".format(self.obj_names.index(obj))
            data['Name'] = "_PROCOBJ_{}".format(self.obj_names.index(obj))
            data['ReferencePaths'] = List(NMSString0x80(Value = os.path.join('CUSTOMMODELS', obj.upper(), '{}.SCENE.MBIN'.format(obj.upper()))))
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
        for obj in self.obj_names:
            ref = Reference("_PROCOBJ_{}".format(self.obj_names.index(obj)), Scenegraph = os.path.join('CUSTOMMODELS', obj.upper(), '{}.SCENE.MBIN'.format(obj.upper())))
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
        

def prettyPrintXml(xmlFilePathToPrettyPrint):
    assert xmlFilePathToPrettyPrint is not None
    parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
    document = etree.parse(xmlFilePathToPrettyPrint, parser)
    document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

app = GUI(master=root)
app.mainloop()
