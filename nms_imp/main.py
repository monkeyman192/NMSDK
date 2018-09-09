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
from mbincompiler import mbinCompiler
from StreamCompiler import StreamData, TkMeshMetaData
from DataSerialise import TkVertexStream, TkIndexStream
from struct import pack
from hashlib import sha256

BASEPATH = 'CUSTOMMODELS'

def traverse(obj):
    # a custom generator to iterate over the tree of all the children on the scene (including the Model object)
    # this returns objects from the branches inwards (which *shouldn't* be a problem...)
    for child in obj.Children:
        for subvalue in traverse(child):
            yield subvalue
    else:
        yield obj

# simple function to take a list and move the entry at the ith index to the the index 'index' (in the new list with the value pop'd)
def movetoindex(lst, i, index):
    k = lst.pop(i)          # this will break if i > len(lst)...
    return lst[:index] + [k] + lst[index:]

def nmsHash(data):
    """
    Lazy hash function for mesh data
    This is simply the last 16 hexadecimal degits of a sha256 hash
    """
    if isinstance(data, list):
        d = array('f')
        for verts in data:
            d.extend(verts)
    else:
        d = data
    return int(sha256(d).hexdigest()[-16:], 16)

class Create_Data():
    def __init__(self, name, directory, model, anim_data = dict(), descriptor = None, **commands):

        """
        name - the name of the file we want to create. Most entities  within will have a name derived from this.
        directory - the full relative location of where the scene file will be located.
        model - The Model object that contains all the child nodes (of a number of different types)

        """

        self.name = name        # this is the name of the file
        self.directory = directory        # the path that the file is supposed to be located at
        self.Model = model                  # this is the main model file for the entire scene.
        self.anim_data = anim_data          # animation data (defaults to None)
        self.descriptor = descriptor

        self.fix_names()

        # assign each of the input streams to a variable
        self.mesh_metadata = dict()
        self.index_stream = []
        self.mesh_indexes = []
        self.vertex_stream = []
        self.uv_stream = []
        self.n_stream = []
        self.t_stream = []
        self.chvertex_stream = []
        self.mesh_bounds = dict()           # a disctionary of the bounds of just mesh objects. This will be used for the scene files
        self.materials = set()      # this will hopefully mean that there will be at most one copy of each unique TkMaterialData struct in the set
        self.hashes = dict()
        self.name_to_id = dict()

        #self.Entities = []          # a list of any extra properties to go in each entity

        # extract the streams from the mesh objects.
        index = 0
        for mesh in self.Model.ListOfMeshes:
            self.index_stream.append(mesh.Indexes)
            self.vertex_stream.append(mesh.Vertices)
            self.uv_stream.append(mesh.UVs)
            self.n_stream.append(mesh.Normals)
            self.t_stream.append(mesh.Tangents)
            self.chvertex_stream.append(mesh.CHVerts)
            self.mesh_metadata[mesh.Name] = {'hash': nmsHash(mesh.Vertices)}
            # also add in the material data to the list
            if mesh.Material is not None:
                self.materials.add(mesh.Material)
            mesh.ID = index             # assign the index location of the data to the Object so that it knows where its data is
            index += 1

        #for obj in self.Model.ListOfEntities:
        #    self.Entities.append(obj.EntityData)

        self.num_mesh_objs = index      # this is the total number of objects that have mesh data

        # an empty list of dicts that will ber populated then each entry will
        # be given back to the correct Mesh or Collision object
        self.mesh_data = [dict()]*self.num_mesh_objs

        # generate some variables relating to the paths
        self.path = os.path.join(BASEPATH, self.directory, self.name)         # the path location including the file name.
        self.texture_path = os.path.join(self.path, 'TEXTURES')
        self.anims_path = os.path.join(BASEPATH, self.directory, 'ANIMS')
        self.ent_path = os.path.join(self.path, 'ENTITIES')         # path location of the entity folder. Calling makedirs of this will ensure all the folders are made in one go

        self.create_paths()

        # This dictionary contains all the information for the geometry file 
        self.GeometryData = dict()

        self.geometry_stream = StreamData('{}.GEOMETRY.DATA.MBIN.PC'.format(self.path))

        # generate the geometry stream data now
        self.serialise_data()

        self.preprocess_streams()

        # This will just be some default entity with physics data
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
        if len(self.descriptor) != 0:
            self.descriptor = self.descriptor.to_exml()
            self.descriptor.make_elements(main = True)
        else:
            self.descriptor = None
        for material in self.materials:
            if type(material) != str:
                material.make_elements(main=True)

        for anim_name in list(self.anim_data.keys()):
            self.anim_data[anim_name].make_elements(main=True)

        # write all the files
        self.write()

        # convert all the created exml files to mbin files
        if not commands.get('dont_compile', False):
            self.convert_to_mbin()

    def create_paths(self):
        # check whether the require paths exist and make them
        if not os.path.exists(self.ent_path):
            os.makedirs(self.ent_path)
        if not os.path.exists(self.texture_path):
            os.makedirs(self.texture_path)
        if not os.path.exists(self.anims_path):
            os.makedirs(self.anims_path)


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

        self.element_count = len(self.stream_list)
        self.stride = 6*self.element_count        # this is 6* if normals and tangents are INT_2_10_10_10_REV, and 5* if just normals

        # secondly this will generate two lists containing the individual lengths of each stream

        self.i_stream_lens = list()
        self.v_stream_lens = list()
        self.ch_stream_lens = list()

        """
        # to fix 1.3x mesh collisions, we need to make all the mesh collisions have their indexes first
        # we require a mapping to know which is which though
        self.index_mapping = list(range(len(self.Model.ListOfMeshes)))        # the unchanged mapping
        insert_point = 0                                                        # an int to keep track of where to place the value (incremented by loop)
        for i in range(len(self.Model.ListOfMeshes)):
            mesh = self.Model.ListOfMeshes[i]
            if mesh._Type == 'COLLISION':
                if mesh.CType == 'Mesh':
                    self.index_mapping = movetoindex(self.index_mapping, i, insert_point)         # move the index it is now located at 'insert_point' so we can construct it correctly in the scene
                    insert_point += 1
        print(self.index_mapping, 'index_mapping')
        """

        # populate the lists containing the lengths of each individual stream
        for index in range(self.num_mesh_objs):
            self.i_stream_lens.append(len(self.index_stream[index]))
            self.v_stream_lens.append(len(self.vertex_stream[index]))
            self.ch_stream_lens.append(len(self.chvertex_stream[index]))

    def fix_names(self):
        # just make sure that the name and path is all in uppercase
        self.name = self.name.upper()
        self.directory = self.directory.upper()
    
    def serialise_data(self):
        """
        convert all the provided vertex and index data to bytes to be passed
        directly to the gstream and geometry file constructors
        """
        vertex_data = []
        index_data = []
        metadata = dict()
        for i, mesh_id in enumerate(self.mesh_metadata):
            vertex_data.append(TkVertexStream(verts = self.vertex_stream[i],
                                              uvs = self.uv_stream[i],
                                              normals = self.n_stream[i],
                                              tangents = self.t_stream[i]))
            new_indexes = []
            for tri in self.index_stream[i]:
                new_indexes.extend(tri)
            if max(new_indexes) > 2**16:
                indexes = array('I', new_indexes)
            else:
                indexes = array('H', new_indexes)
            index_data.append(TkIndexStream(indexes))
            metadata[mesh_id] = self.mesh_metadata[mesh_id]
        self.geometry_stream.create(metadata, vertex_data, index_data)
        self.geometry_stream.save()     # offset data populated here

        # while we are here we will generate the mesh metadata for the geometry
        # file.
        metadata_list = List()
        for i, m in enumerate(self.geometry_stream.metadata):
            metadata = {
                'ID': m.ID, 'hash': m.hash, 'vert_size': m.vertex_size,
                'vert_offset': self.geometry_stream.data_offsets[2*i],
                'index_size': m.index_size,
                'index_offset': self.geometry_stream.data_offsets[2*i + 1]}
            self.hashes[m.raw_ID] = m.hash
            geom_metadata = TkMeshMetaData()
            geom_metadata.create(**metadata)
            metadata_list.append(geom_metadata)
        self.GeometryData['StreamMetaDataArray'] = metadata_list

    def process_data(self):
        # This will do the main processing of the different streams.
        # indexes
        index_counts = list(3*x for x in self.i_stream_lens)    # the total number of index points in each object
        # now, re-order the indexes:
        #new_index_counts = list(index_counts[self.index_mapping[i]] for i in range(len(index_counts)))
        # and sort out the batches
        #self.batches = list((sum(new_index_counts[:i]), new_index_counts[i]) for i in range(self.num_mesh_objs))
        self.batches = list((sum(index_counts[:i]), index_counts[i])
                            for i in range(self.num_mesh_objs))
        print(self.batches, 'batches')
        # vertices
        self.vert_bounds = list((sum(self.v_stream_lens[:i]),
                                 sum(self.v_stream_lens[:i+1])-1)
                                for i in range(self.num_mesh_objs))
        # bounded hull data
        self.hull_bounds = list((sum(self.ch_stream_lens[:i]),
                                 sum(self.ch_stream_lens[:i+1]))
                                for i in range(self.num_mesh_objs))
        print(self.hull_bounds, 'bound hulls')

        # CollisionIndexCount
        # go over all the meshes and add all the batches. Not sure if this can be optimised to be obtained earier... Probably...
        ColIndexCount = 0
        for i in range(len(self.Model.ListOfMeshes)):
            mesh = self.Model.ListOfMeshes[i]
            if mesh._Type == 'COLLISION':
                if mesh.CType == 'Mesh':
                    #print(index_counts, sum(index_counts[:i]), index_counts[i])
                    ColIndexCount += index_counts[i]

        # we need to fix up the index stream as the numbering needs to be continuous across all the streams
        """ no longer true for the geometry stream in 1.5 """
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

        """
        #print(self.index_stream)
        #print('reshuffling indexes')
        # now we need to re-shuffle the index data
        new_index_data = list(range(self.num_mesh_objs))        # just fill with numbers for now, they will be overridden
        for i in range(self.num_mesh_objs):
            new_index_data[self.index_mapping.index(i)] = self.index_stream[i]
        self.index_stream = new_index_data
        #print(self.index_stream)
        """

        # First we need to find the length of each stream.
        self.GeometryData['IndexCount'] = 3*sum(self.i_stream_lens)
        self.GeometryData['VertexCount'] = sum(self.v_stream_lens)
        self.GeometryData['CollisionIndexCount'] = ColIndexCount
        self.GeometryData['MeshVertRStart'] = list(self.vert_bounds[i][0] for i in range(len(self.vert_bounds)))
        self.GeometryData['MeshVertREnd'] = list(self.vert_bounds[i][1] for i in range(len(self.vert_bounds)))
        self.GeometryData['BoundHullVertSt'] = list(self.hull_bounds[i][0] for i in range(len(self.hull_bounds)))
        self.GeometryData['BoundHullVertEd'] = list(self.hull_bounds[i][1] for i in range(len(self.hull_bounds)))
        if self.GeometryData['IndexCount'] > 2**16:
            self.GeometryData['Indices16Bit'] = 0
        else:
            self.GeometryData['Indices16Bit'] = 1

        # might as well also populate the hull data since we only need to union it all:
        hull_data = []
        for vert_list in self.chvertex_stream:
            hull_data += vert_list
        self.GeometryData['BoundHullVerts'] = hull_data

    def process_nodes(self):
        # this will iterate first over the list of mesh data and apply all the required information to the Mesh and Mesh-type Collisions objects.
        # We will then iterate over the entire tree of children to the Model and give them any required information

        # Go through every node
        for obj in traverse(self.Model):
            if obj.IsMesh:
                i = obj.ID      # this is the index associated with the Mesh-type object earlier to avoid having to iterate through everything twice effectively
                mesh_obj = self.Model.ListOfMeshes[i]
                name = mesh_obj.Name

                data = dict()

                #data['BATCHSTART'] = self.batches[self.index_mapping.index(i)][0]
                #data['BATCHCOUNT'] = self.batches[self.index_mapping.index(i)][1]
                data['BATCHSTART'] = self.batches[i][0]
                data['BATCHCOUNT'] = self.batches[i][1]
                data['VERTRSTART'] = self.vert_bounds[i][0]
                data['VERTREND'] = self.vert_bounds[i][1]
                data['BOUNDHULLST'] = self.hull_bounds[i][0]
                data['BOUNDHULLED'] = self.hull_bounds[i][1]
                if mesh_obj._Type == 'MESH':
                    # add the AABBMIN/MAX(XYZ) values:
                    data['AABBMINX'] = self.mesh_bounds[name]['x'][0]
                    data['AABBMINY'] = self.mesh_bounds[name]['y'][0]
                    data['AABBMINZ'] = self.mesh_bounds[name]['z'][0]
                    data['AABBMAXX'] = self.mesh_bounds[name]['x'][1]
                    data['AABBMAXY'] = self.mesh_bounds[name]['y'][1]
                    data['AABBMAXZ'] = self.mesh_bounds[name]['z'][1]
                    data['HASH'] = self.hashes[name]
                    # we only care about entity and material data for Mesh Objects
                    if type(mesh_obj.Material) != str:
                        if mesh_obj.Material is not None:
                            mat_name = str(mesh_obj.Material['Name'])
                            print('material name: {}'.format(mat_name))
                            
                            data['MATERIAL'] = os.path.join(self.path, mat_name.upper()) + '.MATERIAL.MBIN'
                        else:
                            data['MATERIAL'] = ''
                    else:
                        data['MATERIAL'] = mesh_obj.Material
                    if obj.HasAttachment:
                        if obj.EntityData is not None:
                            ent_path = os.path.join(self.ent_path, str(obj.EntityPath).upper())
                            data['ATTACHMENT'] = '{}.ENTITY.MBIN'.format(ent_path)
                            # also need to generate the entity data
                            AttachmentData = TkAttachmentData(Components = list(obj.EntityData.values())[0])        # this is the actual entity data
                            AttachmentData.make_elements(main=True)
                            # also write the entity file now too as we don't need to do anything else to it
                            AttachmentData.tree.write("{}.ENTITY.exml".format(ent_path))
                        else:
                            data['ATTACHMENT'] = obj.EntityPath
                    # enerate the mesh metadata for the geometry file:
                    self.mesh_metadata[obj.Name]['Hash'] = data['HASH']
                    self.mesh_metadata[obj.Name]['VertexDataSize'] = self.stride*(data['VERTREND'] - data['VERTRSTART'] + 1)
                    if self.GeometryData['Indices16Bit'] == 0:
                        m = 4
                    else:
                        m = 2
                    self.mesh_metadata[obj.Name]['IndexDataSize'] = m*data['BATCHCOUNT']
                    # also assign the 

            else:
                if obj._Type == 'LOCATOR':
                    if obj.HasAttachment:
                        if obj.EntityData is not None:
                            ent_path = os.path.join(self.ent_path, str(obj.EntityPath).upper())
                            data = {'ATTACHMENT': '{}.ENTITY.MBIN'.format(ent_path)}
                            # also need to generate the entity data
                            AttachmentData = TkAttachmentData(Components = list(obj.EntityData.values())[0])        # this is the actual entity data
                            AttachmentData.make_elements(main=True)
                            # also write the entity file now too as we don't need to do anything else to it
                            AttachmentData.tree.write("{}.ENTITY.exml".format(ent_path))
                        else:
                            data = {'ATTACHMENT': obj.EntityPath}
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
                    obj.Name = self.path
                    data = {'GEOMETRY': str(self.path) + ".GEOMETRY.MBIN"}
                elif obj._Type == 'REFERENCE':
                    data = None
                elif obj._Type == 'LIGHT':
                    data = None
            obj.create_attributes(data)
            

    def create_vertex_layouts(self):
        # sort out what streams are given and create appropriate vertex layouts
        VertexElements = List()
        SmallVertexElements = List()
        for sID in self.stream_list:
            # sID is the SemanticID
            if sID in [0,1]:
                Offset = 8*self.stream_list.index(sID)
                VertexElements.append(TkVertexElement(SemanticID = sID,
                                                      Size = 4,
                                                      Type = 5131,
                                                      Offset = Offset,
                                                      Normalise = 0,
                                                      Instancing = "PerVertex",
                                                      PlatformData = ""))
            #for the INT_2_10_10_10_REV stuff
            elif sID in [2,3]:
                Offset = 16 + (sID - 2)*4
                VertexElements.append(TkVertexElement(SemanticID = sID,
                                                      Size = 4,
                                                      Type = 36255,
                                                      Offset = Offset,
                                                      Normalise = 0,
                                                      Instancing = "PerVertex",
                                                      PlatformData = ""))
            
        for sID in [0,1]:
            Offset = 8*sID
            SmallVertexElements.append(TkVertexElement(SemanticID = sID,
                                                  Size = 4,
                                                  Type = 5131,
                                                  Offset = Offset,
                                                  Normalise = 0,
                                                  Instancing = "PerVertex",
                                                  PlatformData = ""))
        # fow now just make the small vert and vert layouts the same
        """ Vertex layout needs to be changed for the new normals/tangent format"""
        
        self.GeometryData['VertexLayout'] = TkVertexLayout(ElementCount = self.element_count,
                                                           Stride = self.stride,
                                                           PlatformData = "",
                                                           VertexElements = VertexElements)
        self.GeometryData['SmallVertexLayout'] = TkVertexLayout(ElementCount = 2,
                                                                Stride = 16,
                                                                PlatformData = "",
                                                                VertexElements = SmallVertexElements)
        
    def mix_streams(self):
        # this combines all the input streams into one single stream with the correct offset etc as specified by the VertexLayout
        # This also flattens each stream
        # Again, for now just make the SmallVertexStream the same. Later, change this.
        
        VertexStream = array('f')
        SmallVertexStream = array('f')
        for i in range(self.num_mesh_objs):
            for j in range(self.v_stream_lens[i]):
                for sID in self.stream_list:
                    # get the j^th 4Vector element of i^th object of the corresponding stream as specified by the stream list.
                    # As self.stream_list is ordered this will be mixed in the correct way wrt. the VertexLayouts
                    try:    
                        VertexStream.extend(self.Model.ListOfMeshes[i].__dict__[REV_SEMANTICS[sID]][j])
                        if sID in [0,1]:
                            SmallVertexStream.extend(self.Model.ListOfMeshes[i].__dict__[REV_SEMANTICS[sID]][j])
                    except:
                        # in the case this fails there is an index error caused by collisions. In this case just add a default value
                        VertexStream.extend((0,0,0,1))
        
        self.GeometryData['VertexStream'] = VertexStream
        self.GeometryData['SmallVertexStream'] = SmallVertexStream

        # finally we can also flatten the index stream:
        IndexBuffer = array('I')
        for obj in self.index_stream:
            for tri in obj:
                IndexBuffer.extend(tri)
        """
        # let's convert to the correct type of array data type here
        if not max(IndexBuffer) > 2**16:
            IndexBuffer = array('H', IndexBuffer)
        """
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
            if obj._Type == "MESH":
                # only add the meshes to the self.mesh_bounds dict:
                self.mesh_bounds[obj.Name] = {'x': x_bounds, 'y': y_bounds, 'z': z_bounds}

    def process_materials(self):
        # process the material data and gives the textures the correct paths
        for material in self.materials:
            if type(material) != str:
                # in this case we are given actual material data, not just a string path location
                samplers = material['Samplers']
                # this will have the order Diffuse, Masks, Normal and be a List
                if samplers is not None:
                    for sample in samplers.subElements:
                        # this will be a TkMaterialSampler object
                        t_path = str(sample['Map'])  # this should be the current absolute path to the image, we want to move it to the correct relative path
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
        #self.TkGeometryData.tree.write("{}.GEOMETRY.exml".format(self.path))
        mbinc = mbinCompiler(self.TkGeometryData, "{}.GEOMETRY.MBIN.PC".format(self.path))
        mbinc.serialise()
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(self.path))
        if self.descriptor is not None:
            self.descriptor.tree.write("{}.DESCRIPTOR.exml".format(self.path))
        for material in self.materials:
            if type(material) != str:
                material.tree.write("{0}.MATERIAL.exml".format(os.path.join(self.path, str(material['Name']).upper())))
        if len(self.anim_data) != 0:
            if len(self.anim_data) == 1:
                list(self.anim_data.values())[0].tree.write("{}.ANIM.exml".format(self.path))       # get the value and output it
            else:
                for name in list(self.anim_data.keys()):
                    self.anim_data[name].tree.write(os.path.join(self.anims_path, "{}.ANIM.exml".format(name.upper())))

    def convert_to_mbin(self):
        # passes all the files produced by
        print('Converting all .exml files to .mbin. Please wait while this finishes.')
        for directory, folders, files in os.walk(os.path.join(BASEPATH, self.directory)):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1] == '.exml':
                    retcode = subprocess.call(["MBINCompiler.exe", location])
                    if retcode == 0:
                        os.remove(location)

        
if __name__ == '__main__':

    main_obj = Model(name = 'Square')

    def_mat = TkMaterialData(name = 'Square1mat')

    Obj1 = Mesh(name = 'Square1',
                  Vertices = [(-1,1,0,1), (1,1,0,1), (1,-1,0,1), (-1,-1,0,1)],
                  Indexes = [(0,1,2), (2,3,0)],
                  UVs = [(0.3,0,0,1), (0,0.2,0,1), (0,0.1,0,1), (0.1,0.2,0,1)],
                Material = def_mat)
    main_obj.add_child(Obj1)
    Obj1_col = Collision(name = 'Square1_col', CollisionType = 'Mesh', Vertices = [(-4,4,0,1),(4,4,0,1), (4,-4,0,1), (-4,-4,0,1)],
                      Indexes = [(0,1,2), (2,3,0)])
    Obj1.add_child(Obj1_col)
    Obj2 = Mesh(name = 'Square2',
                  Vertices = [(2,1,0,1), (4,1,0,1), (4,-1,0,1), (2,-1,0,1)],
                  Indexes = [(0,1,2), (2,3,0)],
                  UVs = [(0.5,0,0,1), (0.2,0.2,0,1), (0,0.5,0,1), (0.1,0.2,0,1)])
    Obj1.add_child(Obj2)
    loc = Locator(name = 'testloc')
    Obj2.add_child(loc)
    ref = Reference(name = 'testref')
    loc.add_child(ref)
    ref2 = Reference(name = 'testref2')
    loc.add_child(ref2)
    light = Light(name = 'ls', Intensity = 200000, Colour = (0.4, 0.6, 0.2))
    Obj1.add_child(light)

    main = Create_Data('SQUARE', 'TEST', main_obj)


    from lxml import etree

    def prettyPrintXml(xmlFilePathToPrettyPrint):
        assert xmlFilePathToPrettyPrint is not None
        parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
        document = etree.parse(xmlFilePathToPrettyPrint, parser)
        document.write(xmlFilePathToPrettyPrint, xml_declaration='<?xml version="1.0" encoding="utf-8"?>', pretty_print=True, encoding='utf-8')

    #prettyPrintXml('TEST\SQUARE.GEOMETRY.exml')
    prettyPrintXml('TEST\SQUARE.SCENE.exml')
    #prettyPrintXml('TEST\SQUARE\SQUARE_SQUARE.MATERIAL.exml')
