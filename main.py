"""
    Main processing file that takes the data from blender and converts it
    to a form that is compatible with the exml files.
"""

from classes import *

class Create_Data():
    def __init__(self, name, path, object_names, index_stream, vertex_stream, uv_stream=None, n_stream=None, t_stream=None):

        self.name = name        # this is the name of the file
        self.path = path        # the path that the file is supposed to be located at
        self.object_names = object_names        # this is a list of names for each object. Each will be a child of the main model

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

        self.process_data()

        self.get_bounds()

        self.semantic_map = {0: 'vertex_stream',
                             1: 'uv_stream',
                             2: 'n_stream',
                             3: 't_stream'}

        self.check_streams()        #self.stream_list is created here

        self.create_vertex_layouts()        # this creates the VertexLayout and SmallVertexLayout properties

        self.mix_streams()

        """ Default values """
        # Geometry defaults
        self.GeometryData['Indices16Bit'] = 1
        self.GeometryData['self.JointBindings'] = None
        self.GeometryData['self.JointExtents'] = None
        self.GeometryData['self.JointMirrorPairs'] = None
        self.GeometryData['self.JointMirrorAxes'] = None
        self.GeometryData['self.SkinMatrixLayout'] = None
        self.GeometryData['self.MeshBaseSkinMat'] = None
        # Scene defaults
        self.SceneData['Name'] = self.path + self.name
        self.SceneData['Type'] = 'MODEL'
        self.SceneData['Transform'] = TkTransformData(TransX = 0, TransY = 0, TransZ = 0,
                                                      RotX = 0, RotY = 0, RotZ = 0,
                                                      ScaleX = 1, ScaleY = 1, ScaleZ = 1)
        self.SceneData['Attributes'] = List(TkSceneNodeAttributeData(Name = "GEOMETRY",
                                                                     AltID = "",
                                                                     Value = self.path + self.name + ".GEOMETRY.MBIN"))
        self.SceneData['Children'] = None

        self.process_nodes()
        
        self.TkGeometryData = TkGeometryData(**self.GeometryData)
        self.TkGeometryData.make_elements(main=True)
        self.TkSceneNodeData = TkSceneNodeData(**self.SceneData)
        self.TkSceneNodeData.make_elements(main=True)
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
                                                                     Value = 0))
            """,
                                            TkSceneNodeAttributeData(Name = 'MESHLINK',
                                                                     AltID = "",
                                                                     Value = name + 'Shape'))"""
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
                VertexStream += self.__dict__[self.semantic_map[sID]][i]
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
        for i in self.semantic_map:
            if self.__dict__[self.semantic_map[i]] is not None:
                self.stream_list.append(i)
        self.stream_list.sort()

    def write(self):
        self.TkGeometryData.tree.write("{}.GEOMETRY.exml".format(self.name))
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(self.name))

main = Create_Data('SQUARE', 'TEST\\', ['Square'],
                   index_stream = [[0,1,2], [2,3,0]],
                   vertex_stream = [[-1,1,0,1], [1,1,0,1], [1,-1,0,1], [-1,-1,0,1]],
                   uv_stream = [[0.3,0,0,1], [0,0.2,0,1], [0,0,0.1,1], [0.1,0.2,0,1]])

from lxml import etree

def prettyPrintXml(xmlFilePathToPrettyPrint):
    assert xmlFilePathToPrettyPrint is not None
    parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
    document = etree.parse(xmlFilePathToPrettyPrint, parser)
    document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

prettyPrintXml('SQUARE.GEOMETRY.exml')
prettyPrintXml('SQUARE.SCENE.exml')
