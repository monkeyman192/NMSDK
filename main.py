"""
    Main processing file that takes the data from blender and converts it
    to a form that is compatible with the exml files.
"""

from classes import *
import os
from LOOKUPS import *

class Create_Data():
    def __init__(self, name, directory, object_names, index_stream, vertex_stream, uv_stream=None, n_stream=None, t_stream=None):

        self.name = name        # this is the name of the file
        self.directory = directory        # the path that the file is supposed to be located at
        self.object_names = object_names        # this is a list of names for each object. Each will be a child of the main model
        self.num_objects = range(len(object_names))

        self.path = os.path.join(self.directory, self.name)         # the path location including the file name.
        self.ent_path = os.path.join(self.path, 'ENTITIES')         # path location of the entity folder. Calling makedirs of this will ensure all the folders are made in one go

        self.index_stream = index_stream
        self.vertex_stream = vertex_stream
        self.uv_stream = uv_stream
        self.n_stream = n_stream
        self.t_stream = t_stream

        self.vert_count = len(self.vertex_stream)       # total number, ignoring multiple objects

        # This dictionary contains all the information for the geometry file 
        self.GeometryData = dict()
        # This dictionary contais all the data for the scene file
        self.SceneData = dict()
        # This dictionary contains all the data for the material file
        self.Materials = list()
        for i in self.num_objects:
            self.Materials.append(dict())

        self.process_data()

        self.get_bounds()

        self.check_streams()        #self.stream_list is created here

        self.create_vertex_layouts()        # this creates the VertexLayout and SmallVertexLayout properties

        self.mix_streams()

        """ Basic values """
        # Scene defaults
        self.SceneData['Name'] = self.path
        self.SceneData['Transform'] = TkTransformData(TransX = 0, TransY = 0, TransZ = 0,
                                                      RotX = 0, RotY = 0, RotZ = 0,
                                                      ScaleX = 1, ScaleY = 1, ScaleZ = 1)
        self.SceneData['Attributes'] = List(TkSceneNodeAttributeData(Name = "GEOMETRY",
                                                                     AltID = "",
                                                                     Value = str(self.path) + ".GEOMETRY.MBIN"))
        self.SceneData['Children'] = None
        # Material defaults
        for i in self.num_objects:
            self.Materials[i]['Name'] = "{0}_{1}".format(self.object_names[i], 'Mat')
            self.Materials[i]['Class'] = "Opaque"
            self.Materials[i]['Flags'] = List(TkMaterialFlags(MaterialFlag = MATERIALFLAGS[1+1]))
            self.Materials[i]['Uniforms'] = List(TkMaterialUniform(Name = 'gMaterialColourVec4',
                                                                   Values = Vector4f(x = 1,
                                                                                    y = 1,
                                                                                    z = 1,
                                                                                    t = 1)),
                                                 TkMaterialUniform(Name = 'gMaterialParamsVec4',
                                                                   Values = Vector4f(x = 0.9,
                                                                                     y = 0.5,
                                                                                     z = 0,
                                                                                     t = 0)),
                                                 TkMaterialUniform(Name = 'gMaterialSFXVec4',
                                                                   Values = Vector4f(x = 0,
                                                                                     y = 0,
                                                                                     z = 0,
                                                                                     t = 0)),
                                                 TkMaterialUniform(Name = 'gMaterialSFXColVec4',
                                                                   Values = Vector4f(x = 0,
                                                                                     y = 0,
                                                                                     z = 0,
                                                                                     t = 0)))

        self.process_nodes()
        
        self.TkGeometryData = TkGeometryData(**self.GeometryData)
        self.TkGeometryData.make_elements(main=True)
        self.TkSceneNodeData = TkSceneNodeData(**self.SceneData)
        self.TkSceneNodeData.make_elements(main=True)
        self.TkMaterialData_list = list()
        for i in self.num_objects:
            self.TkMaterialData_list.append(TkMaterialData(**self.Materials[i]))
            # this will not work if there are multiple names that are the same in the object_names list.
        for i in self.num_objects:
            self.TkMaterialData_list[i].make_elements(main=True)
        self.write()

    def fix_names(self):
        # just make sure that the name and path is all in uppercase
        self.name = self.name.upper()
        self.path = self.path.upper()

    def process_nodes(self):
        # this will look at the list in object_names and create child nodes for them
        # If the name is COLLISION the name becomes path + name, and the Type is COLLISION
        if len(self.object_names) != 0:
            self.SceneData['Children'] = List()
        for name in self.object_names:
            scene_data = dict()
            scene_data['Name'] = name
            scene_data['Type'] = 'MESH'
            scene_data['Transform'] = TkTransformData(TransX = 0, TransY = 0, TransZ = 0,
                                                      RotX = 0, RotY = 0, RotZ = 0,
                                                      ScaleX = 1, ScaleY = 1, ScaleZ = 1)
            scene_data['Attributes'] = List(TkSceneNodeAttributeData(Name = 'BATCHSTART',
                                                                     AltID = "",
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'BATCHCOUNT',
                                                                     AltID = "",
                                                                     Value = len(self.index_stream)*3),
                                            TkSceneNodeAttributeData(Name = 'VERTRSTART',
                                                                     AltID = "",
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'VERTREND',
                                                                     AltID = "",
                                                                     Value = self.vert_count -1),
                                            TkSceneNodeAttributeData(Name = 'FIRSTSKINMAT',
                                                                     AltID = "",
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'LASTSKINMAT',
                                                                     AltID = "",
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'MATERIAL',
                                                                     AltID = "",
                                                                     Value = os.path.join(self.path, self.name)+ '_{}'.format(name.upper()) + '.MATERIAL.MBIN'),
                                            TkSceneNodeAttributeData(Name = 'MESHLINK',
                                                                     AltID = "",
                                                                     Value = name + 'Shape'))
            scene_data['Children'] = None
            # now add the child object the the list of children of the mian object
            self.SceneData['Children'].append(TkSceneNodeData(**scene_data))
            
    def process_data(self):
        # This will do the main processing of the different streams.

        # First we need to find the length of each stream.
        self.GeometryData['IndexCount'] = 3*len(self.index_stream)
        self.GeometryData['VertexCount'] = self.vert_count      ## TODO: fix this to work for the case of multiple objects
        self.GeometryData['MeshVertRStart'] = [0]
        self.GeometryData['MeshVertREnd'] = [self.GeometryData['VertexCount'] - 1]

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
        # Again, for now just make the SmallVertexStream the same. Later, change this.
        VertexStream = list()
        for i in range(0, self.vert_count):
            for sID in self.stream_list:
                # get the i^th 4Vector element of the corresponding stream as specified by the stream list.
                # As self.stream_list is ordered this will be mixed in the correct way wrt. the VertexLayouts
                VertexStream += self.__dict__[SEMANTICS[sID]][i]
        self.GeometryData['VertexStream'] = VertexStream
        self.GeometryData['SmallVertexStream'] = VertexStream

        # finally we can also flatten the index stream:
        IndexBuffer = list()
        for tri in self.index_stream:
            IndexBuffer += tri
        self.GeometryData['IndexBuffer'] = IndexBuffer

    def get_bounds(self):
        # this analyses the vertex stream and finds the smallest bounding box corners.
        x_verts = [i[0] for i in self.vertex_stream]
        y_verts = [i[1] for i in self.vertex_stream]
        z_verts = [i[2] for i in self.vertex_stream]
        x_bounds = (min(x_verts), max(x_verts))
        y_bounds = (min(y_verts), max(y_verts))
        z_bounds = (min(z_verts), max(z_verts))

        self.GeometryData['MeshAABBMin'] = List(Vector4f(x=x_bounds[0], y=y_bounds[0], z=z_bounds[0], t=1))
        self.GeometryData['MeshAABBMax'] = List(Vector4f(x=x_bounds[1], y=y_bounds[1], z=z_bounds[1], t=1))

    def check_streams(self):
        # checks what streams have been given. Vertex and index streams are always required.
        # self.stream list 
        self.stream_list = []
        for i in SEMANTICS:
            if self.__dict__[SEMANTICS[i]] is not None:
                self.stream_list.append(i)
        self.stream_list.sort()

    def create_material_data(self):
        # generates some material data. Not sure the best way to specify some of this...
        pass

    def write(self):
        if not os.path.exists(self.ent_path):
            os.makedirs(self.ent_path)
        self.TkGeometryData.tree.write("{}.GEOMETRY.exml".format(self.path))
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(self.path))
        for i in self.num_objects:
            self.TkMaterialData_list[i].tree.write("{0}_{1}.MATERIAL.exml".format(os.path.join(self.path, self.name), self.object_names[i].upper()))

main = Create_Data('SQUARE', 'TEST', ['Square'],
                   index_stream = [[0,1,2], [2,3,0]],
                   vertex_stream = [[-1,1,0,1], [1,1,0,1], [1,-1,0,1], [-1,-1,0,1]],
                   uv_stream = [[0.3,0,0,1], [0,0.2,0,1], [0,0,0.1,1], [0.1,0.2,0,1]])

from lxml import etree

def prettyPrintXml(xmlFilePathToPrettyPrint):
    assert xmlFilePathToPrettyPrint is not None
    parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
    document = etree.parse(xmlFilePathToPrettyPrint, parser)
    document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

prettyPrintXml('TEST\SQUARE.GEOMETRY.exml')
prettyPrintXml('TEST\SQUARE.SCENE.exml')
prettyPrintXml('TEST\SQUARE\SQUARE_SQUARE.MATERIAL.exml')
