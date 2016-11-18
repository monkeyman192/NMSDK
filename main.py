"""
    Main processing file that takes the data from blender and converts it
    to a form that is compatible with the exml files.
"""

from classes import *
import os
import subprocess
from LOOKUPS import *
from shutil import copy2
from array import array

class Create_Data():
    def __init__(self, name, directory, object_names, index_stream, vertex_stream, uv_stream=None, n_stream=None, t_stream=None,
                 mat_indices = [], materials = [], collisions=[]):

        """
        name - the name of the file we want to create. Most entities  within will have a name derived from this.
        directory - the full relative location of where the scene file will be located.
        object_names - A list of the names of the children objects. This can be None, and if so the children will be given default names
        index_stream - A list containing lists of triangle indexes. Each sub list to the main list represents an entire 3d object.
        vertex_stream - A list containing lists of vertices. Each sublist to the main list represents an entire 3d object.

        """

        self.name = name        # this is the name of the file
        self.directory = directory        # the path that the file is supposed to be located at
        self.object_names = object_names        # this is a list of names for each object. Each will be a child of the main model

        self.fix_names()

        # assign each of the input streams to a variable
        self.index_stream = index_stream
        self.vertex_stream = vertex_stream
        self.uv_stream = uv_stream
        self.n_stream = n_stream
        self.t_stream = t_stream
        self.mat_indices = mat_indices  # this will be the same length as the list of objects, 
        self.mats = materials      # this will be a list of TkMaterialData objects
        self.collisions = collisions        # a list of Collision objects

        self.TkMaterialData_list = list()

        # process the stream and object_names inputs to make sure they are all fine:
        self.process_inputs()
        # The above function will define self.i_stream_lens and self.v_stream_lens and will ensure all inputs are the same length
        
        self.num_objects = len(self.object_names)        # only the number of objects, doesn't include collisions
        self.num_total = len(index_stream)                  # total number of objects including collision meshes

        self.path = os.path.join(self.directory, self.name)         # the path location including the file name.
        self.texture_path = os.path.join(self.path, 'TEXTURES')
        self.ent_path = os.path.join(self.path, 'ENTITIES')         # path location of the entity folder. Calling makedirs of this will ensure all the folders are made in one go

        self.create_paths()

        # This dictionary contains all the information for the geometry file 
        self.GeometryData = dict()
        # This dictionary contais all the data for the scene file
        self.SceneData = dict()
        # This dictionary contains all the data for the material file
        self.Materials = list()
        for i in range(self.num_objects):
            self.Materials.append(dict())

        # create the attachment data here as we will just write it when creating the related nodes in the scene file
        self.TkAttachmentData = TkAttachmentData()
        self.TkAttachmentData.make_elements(main=True)

        self.process_data()

        self.get_bounds()

        self.check_streams()        #self.stream_list is created here

        self.create_vertex_layouts()        # this creates the VertexLayout and SmallVertexLayout properties

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
        self.process_materials()

        self.process_nodes()

        self.mix_streams()      # make this last to make sure flattening each stream doesn't affect other data.

        # Assign each of the class objects that contain all of the data their data
        self.TkGeometryData = TkGeometryData(**self.GeometryData)
        self.TkGeometryData.make_elements(main=True)
        self.TkSceneNodeData = TkSceneNodeData(**self.SceneData)
        self.TkSceneNodeData.make_elements(main=True)
        for material in self.mats:
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

    def process_inputs(self):
        # Makes sure that the number of sublists in vertex_stream and index_stream are the same, and also the same as the number of object names
        # (if specified). If not, generate a number of default names for the object_names list.
        # The vertex and index lists will always come in a list, even if there is only one object (i. = [[(p1), (p2)]]
        
        len_streams = len(self.index_stream)
        self.i_stream_lens = list()
        self.v_stream_lens = list()

        self.child_collisions = [None]*len_streams

        # We have an added complication that the collision data *may* contain a mesh collision in which case we need to add the vertex and index streams.
        # these will be added first
        j = 0       # index to track which collision index and vertex element belongs to which object
        for i in range(len(self.collisions)):
            collision = self.collisions[i]
            if self.collisions[i] is not None:
                if collision.Type == 'Mesh':
                    self.child_collisions[i] = len_streams + j      # this is the index in the index and vertex streams and related objects of the collision data for each object
                    j += 1
                    self.index_stream.append(collision.Indexes)
                    self.vertex_stream.append(collision.Vertices)
                    if collision.uv_stream is not None:
                        self.uv_stream.append(collision.uv_stream)
                    if collision.Normals is not None:
                        self.n_stream.append(collision.Normals)
        # assign to the above two lists the lengths of each sub-stream
        for lst in self.index_stream:
            self.i_stream_lens.append(len(lst))
        for lst in self.vertex_stream:
            self.v_stream_lens.append(len(lst))
        # now check the object_names
        if self.object_names is not None and type(self.object_names) == list:
            len_names = len(self.object_names)
            if len_names != len_streams:        # this is the original length, not the modified length
                # we have a bit of a problem.
                # If there are less, add some default ones up to the right amount.
                # If there are more remove the trailing ones.
                # Either way, notify the user that something is wrong.
                if len_names < len_streams:
                    diff = len_streams - len_names
                    for i in range(diff):
                        self.object_names.append('{0}_{1}'.format(self.name, i))
                        error = 'less'
                elif len_names > len_streams:
                    self.object_names = self.object_names[:len_streams]
                    error = 'more'
                print("ERROR! The number of names supplied was {} than required. Please check your inputs.".format(error))
        else:
            # In this case no names have been provided, or they have been provided in the wrong format.
            # Notify the user and generate default names
            self.object_names = list()
            for i in range(len_streams):
                self.object_names.append('{0}_{1}'.format(self.name, i))
            print('No names for constituent objects specified. Objects given default names.')

    def fix_names(self):
        # just make sure that the name and path is all in uppercase
        self.name = self.name.upper()
        self.directory = self.directory.upper()

    def process_data(self):
        # This will do the main processing of the different streams.
        
        # indexes
        index_counts = list(3*x for x in self.i_stream_lens)    # the total number of index points in each object
        self.batches = list((sum(index_counts[:i]), index_counts[i]) for i in range(len(self.i_stream_lens)))
        # vertices
        self.vert_bounds = list((sum(self.v_stream_lens[:i]), sum(self.v_stream_lens[:i+1])-1) for i in range(len(self.v_stream_lens)))

        # we need to fix up the index stream as the numbering needs to be continuous across all the streams
        k = 0       # additive constant
        for i in range(len(self.index_stream)):
            # first add k to every element in every tuple
            curr_max = 0
            for j in range(len(self.index_stream[i])):
                self.index_stream[i][j] = tuple(k + index for index in self.index_stream[i][j])
                local_max = max(self.index_stream[i][j])
                if local_max > curr_max:
                    curr_max = local_max
            # now we set k to be the current max and this is added on to the next set.
            k = curr_max + 1
        #print(self.index_stream)
                

        # First we need to find the length of each stream.
        self.GeometryData['IndexCount'] = 3*sum(self.i_stream_lens)
        self.GeometryData['VertexCount'] = sum(self.v_stream_lens)
        self.GeometryData['MeshVertRStart'] = list(self.vert_bounds[i][0] for i in range(len(self.vert_bounds)))
        self.GeometryData['MeshVertREnd'] = list(self.vert_bounds[i][1] for i in range(len(self.vert_bounds)))

    def process_nodes(self):
        # this will look at the list in object_names and create child nodes for them
        # If the name is COLLISION the name becomes path + name, and the Type is COLLISION
        if len(self.object_names) != 0:
            self.SceneData['Children'] = List()
        if self.collisions == []:
            self.collisions = [None]*self.num_objects
        for i in range(self.num_objects):
            name = self.object_names[i]
            scene_data = dict()

            # get some info from the associated material file
            try:
                mat_name = self.mats[self.mat_indices[i]]['Name'].rstrip('_Mat')
            except:
                # in this case there aren't as many materials as there are things... Let's just give it  default value...
                mat_name = ''
            scene_data['Name'] = name
            scene_data['Type'] = 'MESH'
            scene_data['Transform'] = TkTransformData(TransX = 0, TransY = 0, TransZ = 0,
                                                      RotX = 0, RotY = 0, RotZ = 0,
                                                      ScaleX = 1, ScaleY = 1, ScaleZ = 1)
            scene_data['Attributes'] = List(TkSceneNodeAttributeData(Name = 'BATCHSTART',
                                                                     Value = self.batches[i][0]),
                                            TkSceneNodeAttributeData(Name = 'BATCHCOUNT',
                                                                     Value = self.batches[i][1]),
                                            TkSceneNodeAttributeData(Name = 'VERTRSTART',
                                                                     Value = self.vert_bounds[i][0]),
                                            TkSceneNodeAttributeData(Name = 'VERTREND',
                                                                     Value = self.vert_bounds[i][1]),
                                            TkSceneNodeAttributeData(Name = 'FIRSTSKINMAT',
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'LASTSKINMAT',
                                                                     Value = 0),
                                            TkSceneNodeAttributeData(Name = 'MATERIAL',
                                                                     Value = os.path.join(self.path, self.name)+ '_{}'.format(mat_name.upper()) + '.MATERIAL.MBIN'),
                                            TkSceneNodeAttributeData(Name = 'MESHLINK',
                                                                     Value = name + 'Shape'),
                                            TkSceneNodeAttributeData(Name = 'ATTACHMENT',
                                                                     Value = os.path.join(self.ent_path, name.upper()) + '.ENTITY.MBIN'))
            # also write the entity file now as it is pretty much empty anyway
            self.TkAttachmentData.tree.write("{}.ENTITY.exml".format(os.path.join(self.ent_path, name.upper())))
            
            if self.collisions[i] != None:
                collision_data = self.collisions[i]
                # in this case the object has some collision data. Create a child that is a TkCollision object (which is in fact just a renamed TkSceneNodeData object.
                collision_node = TkSceneNodeData(Name = self.path, Type='COLLISION')
                collision_node['Transform'] = collision_data.Transform
                if collision_data.col_type == 'Primitive':
                    # this case is simple, call the function and it will create the required List
                    collision_data.process_primitives()     # this will give the collision_data object an Attributes property that is a List of TkSceneNode AttributeData objects
                    collision_node['Attributes'] = collision_data.Attributes
                elif collision_data.col_type == 'Mesh':
                    # in this case, we need to get the correct batch start and count and vertr start and end
                    # self.child_collisions contains the required index to get the vert and index info.
                    collision_data.process_mesh(self.batches[self.child_collisions[i]][0],
                                                self.batches[self.child_collisions[i]][1],
                                                self.vert_bounds[self.child_collisions[i]][0],
                                                self.vert_bounds[self.child_collisions[i]][1])
                    collision_node['Attributes'] = collision_data.Attributes
                # set the collision data as a child
                scene_data['Children'] = List(collision_node)
            else:
                scene_data['Children'] = None
            # now add the child object the the list of children of the mian object
            self.SceneData['Children'].append(TkSceneNodeData(**scene_data))

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
        for i in range(self.num_total):
            for j in range(self.v_stream_lens[i]):
                for sID in self.stream_list:
                    # get the j^th 4Vector element of i^th object of the corresponding stream as specified by the stream list.
                    # As self.stream_list is ordered this will be mixed in the correct way wrt. the VertexLayouts
                    try:    
                        VertexStream.extend(self.__dict__[SEMANTICS[sID]][i][j])
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
        
        for i in range(len(self.vertex_stream)):
            obj = self.vertex_stream[i]
            x_verts = [i[0] for i in obj]
            y_verts = [i[1] for i in obj]
            z_verts = [i[2] for i in obj]
            x_bounds = (min(x_verts), max(x_verts))
            y_bounds = (min(y_verts), max(y_verts))
            z_bounds = (min(z_verts), max(z_verts))

            self.GeometryData['MeshAABBMin'].append(Vector4f(x=x_bounds[0], y=y_bounds[0], z=z_bounds[0], t=1))
            self.GeometryData['MeshAABBMax'].append(Vector4f(x=x_bounds[1], y=y_bounds[1], z=z_bounds[1], t=1))

    def check_streams(self):
        # checks what streams have been given. Vertex and index streams are always required.
        # self.stream list 
        self.stream_list = []
        for i in SEMANTICS:
            if self.__dict__[SEMANTICS[i]] is not None:
                self.stream_list.append(i)
        self.stream_list.sort()

    def process_materials(self):
        # process the material data and gives the textures the correct paths
        for material in self.mats:
            samplers = material['Samplers']
            # this will have the order Diffuse, Masks, Normal and be a List
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
        for material in self.mats:
            material.tree.write("{0}_{1}.MATERIAL.exml".format(os.path.join(self.path, self.name), material['Name'].rstrip('_Mat').upper()))

    def convert_to_mbin(self):
        # passes all the files produced by
        print('Converting all .exm files to .mbin. Please wait while this finishes.')
        for directory, folders, files in os.walk(self.directory):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1] == '.exml':
                    subprocess.call(["MBINCompiler.exe", location])

        
if __name__ == '__main__':

    main = Create_Data('SQUARE', 'TEST', ['Square1', 'Square2'],
                       index_stream = [[(0,1,2), (2,3,0)],
                                       [(0,1,2), (2,3,0)]],
                       vertex_stream = [[(-1,1,0,1), (1,1,0,1), (1,-1,0,1), (-1,-1,0,1)],
                                        [(2,1,0,1), (4,1,0,1), (4,-1,0,1), (2,-1,0,1)]],
                       uv_stream = [[(0.3,0,0,1), (0,0.2,0,1), (0,0.1,0,1), (0.1,0.2,0,1)],
                                    [(0.5,0,0,1), (0.2,0.2,0,1), (0,0.5,0,1), (0.1,0.2,0,1)]],
                       collisions = [Collision(Type='Mesh', Vertices=[(-4,4,0,1),(4,4,0,1), (4,-4,0,1), (-4,-4,0,1)],
                                               Indexes=[(0,1,2), (2,3,0)]),
                                     Collision(Type='Sphere', Radius=5)])


    from lxml import etree

    def prettyPrintXml(xmlFilePathToPrettyPrint):
        assert xmlFilePathToPrettyPrint is not None
        parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
        document = etree.parse(xmlFilePathToPrettyPrint, parser)
        document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

    prettyPrintXml('TEST\SQUARE.GEOMETRY.exml')
    prettyPrintXml('TEST\SQUARE.SCENE.exml')
    #prettyPrintXml('TEST\SQUARE\SQUARE_SQUARE.MATERIAL.exml')
