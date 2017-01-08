#!/usr/bin/env python
"""Process the 3d model data and create required files for NMS.

This function will take all the data provided by the blender script and create a number of
.exml files that contain all the data required by the game to view the 3d model created.
"""

__author__ = "monkeyman192"
__credits__ = ["monkeyman192", "gregkwaste"]

from classes import *
import os
import subprocess
from LOOKUPS import *
from shutil import copy2
from array import array

BASEPATH = 'CUSTOMMODELS'

def traverse(obj):
    # a custom generator to iterate over the tree of all the children on the scene (including the Model object)
    # this returns objects from the branches inwards (which *shouldn't* be a problem...)
    for child in obj.Children:
        for subvalue in traverse(child):
            yield subvalue
    else:
        yield obj

class Create_Data():
    def __init__(self, name, directory, model):

        """
        name - the name of the file we want to create. Most entities  within will have a name derived from this.
        directory - the full relative location of where the scene file will be located.
        model - The Model object that contains all the child nodes (of a number of different types)

        """

        self.name = name        # this is the name of the file
        self.directory = directory        # the path that the file is supposed to be located at
        self.Model = model                  # this is the main model file for the entire scene.

        self.fix_names()

        # assign each of the input streams to a variable
        self.index_stream = []
        self.vertex_stream = []
        self.uv_stream = []
        self.n_stream = []
        self.t_stream = []
        self.materials = set()      # this will hopefully mean that there will be at most one copy of each unique TkMaterialData struct in the set

        # extract the streams from the mesh objects.
        index = 0
        for mesh in self.Model.ListOfMeshes:
            self.index_stream.append(mesh.Indexes)
            self.vertex_stream.append(mesh.Vertices)
            self.uv_stream.append(mesh.UVs)
            self.n_stream.append(mesh.Normals)
            self.t_stream.append(mesh.Tangents)
            # also add in the material data to the list
            if mesh.Material is not None:
                self.materials.add(mesh.Material)
            mesh.ID = index             # assign the index location of the data to the Object so that it knows where its data is
            index += 1

        self.num_mesh_objs = index      # this is the total number of objects that have mesh data

        self.mesh_data = [dict()]*self.num_mesh_objs    # an empty list of dicts that will ber populated then each entry will
                                                        # be given back to the correct Mesh or Collision object

        self.preprocess_streams()

        # generate some variables relating to the paths
        self.path = os.path.join(BASEPATH, self.directory, self.name)         # the path location including the file name.
        self.texture_path = os.path.join(self.path, 'TEXTURES')
        self.ent_path = os.path.join(self.path, 'ENTITIES')         # path location of the entity folder. Calling makedirs of this will ensure all the folders are made in one go

        self.create_paths()

        # This dictionary contains all the information for the geometry file 
        self.GeometryData = dict()

        # create the attachment data here as we will just write it when creating the related nodes in the scene file
        self.TkAttachmentData = TkAttachmentData()      # this is created with the Physics Component Data by default
        self.TkAttachmentData.make_elements(main=True)

        self.process_data()

        self.get_bounds()

        self.create_vertex_layouts()        # this creates the VertexLayout and SmallVertexLayout properties

        # Material defaults
        self.process_materials()

        self.process_nodes()

        self.mix_streams()      # make this last to make sure flattening each stream doesn't affect other data.

        # Assign each of the class objects that contain all of the data their data
        self.TkGeometryData = TkGeometryData(**self.GeometryData)
        self.TkGeometryData.make_elements(main=True)
        self.Model.construct_data()
        self.TkSceneNodeData = self.Model.get_data()
        self.TkSceneNodeData.make_elements(main=True)         # get the model to create all the required data and this will continue on down the tree
        for material in self.materials:
            material.make_elements(main=True)

        # write all the files
        self.write()

        # convert all the created exml files to mbin files
        self.convert_to_mbin()

    def create_paths(self):
        # check whether the require paths exist and make them
        if not os.path.exists(self.ent_path):
            os.makedirs(self.ent_path)
        if not os.path.exists(self.texture_path):
            os.makedirs(self.texture_path)


    def preprocess_streams(self):
        # this will iterate through the Mesh objects and check that each of them has the same number of input streams. Any that don't will be flagged and a message will be raised
        streams = set()
        for mesh in self.Model.ListOfMeshes:
            # first find all the streams over all the meshes that have been provided
            streams = streams.union(mesh.provided_streams)
        for mesh in self.Model.ListOfMeshes:
            # next go back over the list and compare. If an entry isn't in the list of provided streams print a messge (maybe make a new error for this to be raised?)
            diff = streams.difference(mesh.provided_streams)
            if diff != set():
                print('ERROR! Object {0} is missing the streams: {1}'.format(mesh.Name, diff))
                if 'Vertices' in diff or 'Indexes' in diff:
                    print('CRITICAL ERROR! No vertex and/or index data provided for {} Object'.format(mesh.Name))

        self.stream_list = list(SEMANTICS[x] for x in streams.difference({'Indexes'}))
        self.stream_list.sort()

        # secondly this will generate two lists containing the individual lengths of each stream

        self.i_stream_lens = list()
        self.v_stream_lens = list()

        # populate the lists containing the lengths of each individual stream
        for index in range(self.num_mesh_objs):
            self.i_stream_lens.append(len(self.index_stream[index]))
            self.v_stream_lens.append(len(self.vertex_stream[index]))

    def fix_names(self):
        # just make sure that the name and path is all in uppercase
        self.name = self.name.upper()
        self.directory = self.directory.upper()

    def process_data(self):
        # This will do the main processing of the different streams.
        # indexes
        index_counts = list(3*x for x in self.i_stream_lens)    # the total number of index points in each object
        self.batches = list((sum(index_counts[:i]), index_counts[i]) for i in range(self.num_mesh_objs))
        # vertices
        self.vert_bounds = list((sum(self.v_stream_lens[:i]), sum(self.v_stream_lens[:i+1])-1) for i in range(self.num_mesh_objs))

        # we need to fix up the index stream as the numbering needs to be continuous across all the streams
        k = 0       # additive constant
        for i in range(self.num_mesh_objs):
            # first add k to every element in every tuple
            curr_max = 0
            for j in range(self.i_stream_lens[i]):
                self.index_stream[i][j] = tuple(k + index for index in self.index_stream[i][j])
                local_max = max(self.index_stream[i][j])
                if local_max > curr_max:
                    curr_max = local_max
            # now we set k to be the current max and this is added on to the next set.
            k = curr_max + 1
                

        # First we need to find the length of each stream.
        self.GeometryData['IndexCount'] = 3*sum(self.i_stream_lens)
        self.GeometryData['VertexCount'] = sum(self.v_stream_lens)
        self.GeometryData['MeshVertRStart'] = list(self.vert_bounds[i][0] for i in range(len(self.vert_bounds)))
        self.GeometryData['MeshVertREnd'] = list(self.vert_bounds[i][1] for i in range(len(self.vert_bounds)))

    def process_nodes(self):
        # this will iterate first over the list of mesh data and apply all the required information to the Mesh and Mesh-type Collisions objects.
        # We will then iterate over the entire tree of children to the Model and give them any required information

        # Go through every node
        for obj in traverse(self.Model):
            if obj.IsMesh:
                i = obj.ID      # this is the index associated with the Mesh-type object earlier to avoid having to iterate through everything twice effectively
                mesh_obj = self.Model.ListOfMeshes[i]

                data = dict()

                data['BATCHSTART'] = self.batches[i][0]
                data['BATCHCOUNT'] = self.batches[i][1]
                data['VERTRSTART'] = self.vert_bounds[i][0]
                data['VERTREND'] = self.vert_bounds[i][1]
                if mesh_obj._Type == 'MESH':
                    # we only care about entity and material data for Mesh Objects
                    if mesh_obj.Material is not None:
                        mat_name = mesh_obj.Material['Name']
                        data['MATERIAL'] = os.path.join(self.path, self.name)+ '_{}'.format(mat_name.upper()) + '.MATERIAL.MBIN'
                    else:
                        data['MATERIAL'] = ''
                    data['ATTACHMENT'] = os.path.join(self.ent_path, mesh_obj.Name.upper()) + '.ENTITY.MBIN'
                    
                    # also write the entity file now as it is pretty much empty anyway
                    self.TkAttachmentData.tree.write("{}.ENTITY.exml".format(os.path.join(self.ent_path, mesh_obj.Name.upper())))
            else:
                if obj._Type == 'LOCATOR':
                    if obj.hasAttachment == True:
                        data['ATTACHMENT'] = os.path.join(self.ent_path, obj.Name.upper()) + '.ENTITY.MBIN'
                        self.TkAttachmentData.tree.write("{}.ENTITY.exml".format(os.path.join(self.ent_path, obj.Name.upper())))
                    else:
                        data = None
                elif obj._Type == 'COLLISION':
                    if obj.CType == 'Box':
                        data = {'WIDTH': obj.Width, 'HEIGHT': obj.Height, 'DEPTH': obj.Depth}
                    elif obj.CType == 'Sphere':
                        data = {'RADIUS': obj.Radius}
                    elif obj.CType == 'Capsule' or obj.CType == 'Cylinder':
                        data = {'RADIUS': obj.Radius, 'HEIGHT': obj.Height}
                elif obj._Type == 'MODEL':
                    data = {'GEOMETRY': str(self.path) + ".GEOMETRY.MBIN"}
                elif obj._Type == 'REFERENCE':
                    # TODO: Potentially get this information from blender? Or maybe just leave with a message in it for the user to add themselves?
                    data = {'SCENEGRAPH': 'Enter in the path of the SCENE.MBIN you want to reference here.'}
                elif obj._Type == 'LIGHT':
                    data = None
            obj.create_attributes(data)
            

    def create_vertex_layouts(self):
        # sort out what streams are given and create appropriate vertex layouts
        VertexElements = List()
        ElementCount = len(self.stream_list)
        for sID in self.stream_list:
            # sID is the SemanticID
            Offset = 8*self.stream_list.index(sID)
            VertexElements.append(TkVertexElement(SemanticID = sID,
                                                  Size = 4,
                                                  Type = 5131,
                                                  Offset = Offset,
                                                  Normalise = 0,
                                                  Instancing = "PerVertex",
                                                  PlatformData = ""))
        # fow now just make the small vert and vert layouts the same
        self.GeometryData['VertexLayout'] = TkVertexLayout(ElementCount = ElementCount,
                                                           Stride = 8*ElementCount,
                                                           PlatformData = "",
                                                           VertexElements = VertexElements)
        self.GeometryData['SmallVertexLayout'] = TkVertexLayout(ElementCount = ElementCount,
                                                                Stride = 8*ElementCount,
                                                                PlatformData = "",
                                                                VertexElements = VertexElements)
        
    def mix_streams(self):
        # this combines all the input streams into one single stream with the correct offset etc as specified by the VertexLayout
        # This also flattens each stream
        # Again, for now just make the SmallVertexStream the same. Later, change this.
        
        VertexStream = array('d')
        for i in range(self.num_mesh_objs):
            for j in range(self.v_stream_lens[i]):
                for sID in self.stream_list:
                    # get the j^th 4Vector element of i^th object of the corresponding stream as specified by the stream list.
                    # As self.stream_list is ordered this will be mixed in the correct way wrt. the VertexLayouts
                    try:    
                        VertexStream.extend(self.Model.ListOfMeshes[i].__dict__[REV_SEMANTICS[sID]][j])
                    except:
                        # in the case this fails there is an index error caused by collisions. In this case just add a default value
                        VertexStream.extend((0,0,0,1))
        
        self.GeometryData['VertexStream'] = VertexStream
        self.GeometryData['SmallVertexStream'] = VertexStream

        # finally we can also flatten the index stream:
        IndexBuffer = array('I')
        for obj in self.index_stream:
            for tri in obj:
                IndexBuffer.extend(tri)
        self.GeometryData['IndexBuffer'] = IndexBuffer

    def get_bounds(self):
        # this analyses the vertex stream and finds the smallest bounding box corners.

        self.GeometryData['MeshAABBMin'] = List()
        self.GeometryData['MeshAABBMax'] = List()
        
        for obj in self.Model.ListOfMeshes:
            v_stream = obj.Vertices
            x_verts = [i[0] for i in v_stream]
            y_verts = [i[1] for i in v_stream]
            z_verts = [i[2] for i in v_stream]
            x_bounds = (min(x_verts), max(x_verts))
            y_bounds = (min(y_verts), max(y_verts))
            z_bounds = (min(z_verts), max(z_verts))

            self.GeometryData['MeshAABBMin'].append(Vector4f(x=x_bounds[0], y=y_bounds[0], z=z_bounds[0], t=1))
            self.GeometryData['MeshAABBMax'].append(Vector4f(x=x_bounds[1], y=y_bounds[1], z=z_bounds[1], t=1))

    def process_materials(self):
        # process the material data and gives the textures the correct paths
        for material in self.materials:
            samplers = material['Samplers']
            # this will have the order Diffuse, Masks, Normal and be a List
            if samplers is not None:
                for sample in samplers.subElements:
                    # this will be a TkMaterialSampler object
                    t_path = sample['Map']  # this should be the current absolute path to the image, we want to move it to the correct relative path
                    new_path = os.path.join(self.texture_path, os.path.basename(t_path).upper())
                    try:
                        copy2(t_path, new_path)
                    except FileNotFoundError:
                        # in this case the path is probably broken, just set as empty if it wasn't before
                        new_path = ""
                    f_name, ext = os.path.splitext(new_path)
                    if ext != '.DDS' and ext != '':
                        # TODO: add code here to convert the image to dds format
                        # in this case the file is not in the correct format. Put the correct file extension in the material file
                        print('The file {} needs to be converted to .DDS format (file extention to be capitalised also!)'.format(new_path))
                        sample['Map'] = f_name + '.DDS'
                    else:
                        # all good in this case
                        sample['Map'] = new_path
                
    def write(self):
        # write each of the exml files.
        self.TkGeometryData.tree.write("{}.GEOMETRY.exml".format(self.path))
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(self.path))
        for material in self.materials:
            material.tree.write("{0}_{1}.MATERIAL.exml".format(os.path.join(self.path, self.name), material['Name'].rstrip('_Mat').upper()))

    def convert_to_mbin(self):
        # passes all the files produced by
        print('Converting all .exml files to .mbin. Please wait while this finishes.')
        for directory, folders, files in os.walk(os.path.join(BASEPATH, self.directory)):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1] == '.exml':
                    subprocess.call(["MBINCompiler.exe", location])
                    #if os.path.splitext(os.path.splitext(location)[0])[1] == ".SCENE":
                    os.remove(location)

        
if __name__ == '__main__':

    main_obj = Model(Name = 'Square')

    #def_mat = TkMaterialData(Name = 'Square1mat')

    Obj1 = Mesh(Name = 'Square1',
                  Vertices = [(-1,1,0,1), (1,1,0,1), (1,-1,0,1), (-1,-1,0,1)],
                  Indexes = [(0,1,2), (2,3,0)],
                  UVs = [(0.3,0,0,1), (0,0.2,0,1), (0,0.1,0,1), (0.1,0.2,0,1)])
    main_obj.add_child(Obj1)
    Obj1_col = Collision(Name = 'Square1_col', CollisionType = 'Mesh', Vertices = [(-4,4,0,1),(4,4,0,1), (4,-4,0,1), (-4,-4,0,1)],
                      Indexes = [(0,1,2), (2,3,0)])
    Obj1.add_child(Obj1_col)
    Obj2 = Mesh(Name = 'Square2',
                  Vertices = [(2,1,0,1), (4,1,0,1), (4,-1,0,1), (2,-1,0,1)],
                  Indexes = [(0,1,2), (2,3,0)],
                  UVs = [(0.5,0,0,1), (0.2,0.2,0,1), (0,0.5,0,1), (0.1,0.2,0,1)])
    main_obj.add_child(Obj2)
    loc = Locator(Name = 'testloc')
    Obj2.add_child(loc)
    ref = Reference(Name = 'testref')
    loc.add_child(ref)
    ref2 = Reference(Name = 'testref2')
    loc.add_child(ref2)
    light = Light(Name = 'ls', Intensity = 200000, Colour = (0.4, 0.6, 0.2))
    Obj1.add_child(light)

    main = Create_Data('SQUARE', 'TEST', main_obj)


    from lxml import etree

    def prettyPrintXml(xmlFilePathToPrettyPrint):
        assert xmlFilePathToPrettyPrint is not None
        parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
        document = etree.parse(xmlFilePathToPrettyPrint, parser)
        document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

    #prettyPrintXml('TEST\SQUARE.GEOMETRY.exml')
    #prettyPrintXml('TEST\SQUARE.SCENE.exml')
    #prettyPrintXml('TEST\SQUARE\SQUARE_SQUARE.MATERIAL.exml')
