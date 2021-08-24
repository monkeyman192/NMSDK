#!/usr/bin/env python
"""Process the 3d model data and create required files for NMS.

This function will take all the data provided by the blender script and create
a number of .exml files that contain all the data required by the game to view
the 3d model created.
"""

__author__ = "monkeyman192"
__credits__ = ["monkeyman192", "gregkwaste"]

# Blender imports
import bpy

# stdlib imports
import os
import subprocess
from collections import OrderedDict as odict
from shutil import copy2
from array import array
# Internal imports
from ..NMS.classes import (TkAttachmentData, TkGeometryData, List,
                           TkVertexElement, TkVertexLayout, Vector4f)
from ..NMS.LOOKUPS import SEMANTICS, REV_SEMANTICS, STRIDES
from ..serialization.mbincompiler import mbinCompiler
from ..serialization.StreamCompiler import StreamData, TkMeshMetaData
from ..serialization.serializers import (serialize_index_stream,
                                         serialize_vertex_stream)
from .utils import nmsHash, traverse


class Export():
    """ Export the data provided by blender to .mbin files.

    Parameters
    ----------
    export_directory : str
        Absolute or relative path to where the data should be produced.
    scene_directory : str
        A path made up of two components; the sub-directory name relative to
        the PCBANKS folder, and the sub-folder relative to that (the "group
        name").
    scene_name : str
        The name of the scene file itself (and other files with automatically
        generated names)
    model : nmsdk.NMS.classes.Model
        Model containing all the scene information.
    anim_data : dict
        Animation data for the scene.
        The key corresponds to the name of the animation and the value being a
        TkAnimMetadata object.
    descriptior: Descriptor
        Descriptor information for the scene.
    settings : dict
        A dictionaty containing various export settings. These will generally
        be set by the blender export helper.
    """
    def __init__(self, export_directory, scene_directory, scene_name, model,
                 anim_data=dict(), descriptor=None, settings=dict()):
        self.export_directory = export_directory
        self.scene_directory = scene_directory.upper()
        self.scene_name = scene_name.upper()
        # this is the main model file for the entire scene.
        self.Model = model
        self.Model.check_vert_colours()
        # animation data (defaults to None)
        self.anim_data = anim_data
        self.descriptor = descriptor
        self.settings = settings

        # assign each of the input streams to a variable
        self.mesh_metadata = odict()
        self.index_stream = odict()
        self.mesh_indexes = odict()
        self.vertex_stream = odict()
        self.uv_stream = odict()
        self.n_stream = odict()
        self.t_stream = odict()
        self.c_stream = odict()
        self.chvertex_stream = odict()
        # mesh collision convex hull data
        self.ch_indexes = odict()
        self.ch_verts = odict()
        # a dictionary of the bounds of just mesh objects. This will be used
        # for the scene files
        self.mesh_bounds = odict()
        # this will hopefully mean that there will be at most one copy of each
        # unique TkMaterialData struct in the set
        self.materials = set()
        self.hashes = odict()
        self.mesh_names = list()

        # Make some settings values more easily accessible.
        self.preserve_node_info = self.settings.get('preserve_node_info',
                                                    False)
        self.export_original_geom_data = self.settings.get('reexport_geometry',
                                                           False)

        # a list of any extra properties to go in each entity
        # self.Entities = []

        # extract the streams from the mesh objects.
        for mesh in self.Model.Meshes.values():
            self.mesh_names.append(mesh.Name)
            self.index_stream[mesh.Name] = mesh.Indexes
            self.vertex_stream[mesh.Name] = mesh.Vertices
            self.uv_stream[mesh.Name] = mesh.UVs
            self.n_stream[mesh.Name] = mesh.Normals
            self.t_stream[mesh.Name] = mesh.Tangents
            if self.Model.has_vertex_colours:
                if mesh.Colours is None:
                    self.c_stream[mesh.Name] = (
                        [[0, 0, 0, 0]] * len(mesh.Vertices))
                else:
                    self.c_stream[mesh.Name] = mesh.Colours
            else:
                self.c_stream[mesh.Name] = None
            self.chvertex_stream[mesh.Name] = mesh.CHVerts
            self.mesh_metadata[mesh.Name] = {'hash': nmsHash(mesh.Vertices)}
            # also add in the material data to the list
            if mesh.Material is not None:
                self.materials.add(mesh.Material)

        # for obj in self.Model.ListOfEntities:
        #    self.Entities.append(obj.EntityData)

        self.num_mesh_objs = len(self.Model.Meshes)

        # generate some variables relating to the paths
        self.basepath = os.path.join(self.export_directory,
                                     self.scene_directory)
        self.texture_path = os.path.join(self.basepath, self.scene_name,
                                         'TEXTURES')
        self.anims_path = os.path.join(self.basepath, 'ANIMS')
        # path location of the entity folder. Calling makedirs of this will
        # ensure all the folders are made in one go
        self.ent_path = os.path.join(self.basepath, self.scene_name,
                                     'ENTITIES')
        # The name of the scene relative to the PCBANKS folder
        self.rel_named_path = os.path.join(self.scene_directory,
                                           self.scene_name)
        self.abs_name_path = os.path.join(self.basepath, self.scene_name)

        self.create_paths()

        # This dictionary contains all the information for the geometry file
        self.GeometryData = odict()

        if (not self.preserve_node_info
                or (self.preserve_node_info
                    and self.export_original_geom_data)):
            self.geometry_stream = StreamData(
                '{}.GEOMETRY.DATA.MBIN.PC'.format(
                    os.path.join(self.basepath, self.scene_name)))

            # generate the geometry stream data now
            self.serialize_data()

        self.preprocess_streams()

        # This will just be some default entity with physics data
        # This is created with the Physics Component Data by default
        self.TkAttachmentData = TkAttachmentData()
        self.TkAttachmentData.make_elements(main=True)

        self.process_data()

        self.get_bounds()

        # this creates the VertexLayout and SmallVertexLayout properties
        self.create_vertex_layouts()

        self.process_nodes()
        # make this last to make sure flattening each stream doesn't affect
        # other data.
        self.mix_streams()

        # Assign each of the class objects that contain all of the data their
        # data
        if (not self.preserve_node_info
                or (self.preserve_node_info
                    and self.export_original_geom_data)):
            self.TkGeometryData = TkGeometryData(**self.GeometryData)
            self.TkGeometryData.make_elements(main=True)
        self.Model.construct_data()
        self.TkSceneNodeData = self.Model.get_data()
        # get the model to create all the required data and this will continue
        # on down the tree
        self.TkSceneNodeData.make_elements(main=True)
        for material in self.materials:
            if not isinstance(material, str):
                material.make_elements(main=True)
        for anim_name in list(self.anim_data.keys()):
            self.anim_data[anim_name].make_elements(main=True)

        # write all the files
        self.write()

        self.convert_to_mbin()

    def create_paths(self):
        # check whether the require paths exist and make them
        if not os.path.exists(self.ent_path):
            os.makedirs(self.ent_path)
        if not os.path.exists(self.anims_path) and len(self.anim_data) > 1:
            os.makedirs(self.anims_path)

    def preprocess_streams(self):
        # this will iterate through the Mesh objects and check that each of
        # them has the same number of input streams. Any that don't will be
        # flagged and a message will be raised
        streams = set()
        for mesh in self.Model.Meshes.values():
            # first find all the streams over all the meshes that have been
            # provided
            streams = streams.union(mesh.provided_streams)
        for mesh in self.Model.Meshes.values():
            # next go back over the list and compare. If an entry isn't in the
            # list of provided streams print a messge (maybe make a new error
            # for this to be raised?)
            diff = streams.difference(mesh.provided_streams)
            if diff != set():
                print('ERROR! Object {0} is missing the streams: {1}'.format(
                    mesh.Name, diff))
                if 'Vertices' in diff or 'Indexes' in diff:
                    print('CRITICAL ERROR! No vertex and/or index data '
                          'provided for {} Object'.format(mesh.Name))

        self.stream_list = list(
            SEMANTICS[x] for x in streams.difference({'Indexes'}))
        self.stream_list.sort()

        self.element_count = len(self.stream_list)
        # Create a list to store the offset sizes for each data type
        offsets = list()
        for sid in self.stream_list:
            offsets.append(STRIDES[sid])
        # Now create an ordered dictionary. Each kvp is the sid and the actual
        # offset as calculated by the sum of all the entries before it.
        self.offsets = odict()
        for i, sid in enumerate(self.stream_list):
            self.offsets[sid] = sum(offsets[:i])
        self.stride = sum(offsets)

        # secondly this will generate two lists containing the individual
        # lengths of each stream
        self.i_stream_lens = odict()
        self.v_stream_lens = odict()
        self.ch_stream_lens = odict()

        # populate the lists containing the lengths of each individual stream
        for name in self.mesh_names:
            self.i_stream_lens[name] = len(self.index_stream[name])
            self.v_stream_lens[name] = len(self.vertex_stream[name])
            self.ch_stream_lens[name] = len(self.chvertex_stream[name])

    def serialize_data(self):
        """
        convert all the provided vertex and index data to bytes to be passed
        directly to the gstream and geometry file constructors
        """
        vertex_data = []
        index_data = []
        metadata = odict()
        for name in self.mesh_names:
            vertex_data.append(serialize_vertex_stream(
                verts=self.vertex_stream[name],
                uvs=self.uv_stream[name],
                normals=self.n_stream[name],
                tangents=self.t_stream[name],
                colours=self.c_stream[name]))
            new_indexes = self.index_stream[name]
            if max(new_indexes) > 2 ** 16:
                indexes = array('I', new_indexes)
            else:
                indexes = array('H', new_indexes)
            index_data.append(serialize_index_stream(indexes))
            metadata[name] = self.mesh_metadata[name]
        self.geometry_stream.create(metadata, vertex_data, index_data)
        self.geometry_stream.save()     # offset data populated here

        # while we are here we will generate the mesh metadata for the geometry
        # file.
        metadata_list = List()
        for i, m in enumerate(self.geometry_stream.metadata):
            metadata = {
                'ID': m.ID, 'hash': m.hash, 'vert_size': m.vertex_size,
                'vert_offset': self.geometry_stream.data_offsets[2 * i],
                'index_size': m.index_size,
                'index_offset': self.geometry_stream.data_offsets[2 * i + 1]}
            self.hashes[m.raw_ID] = m.hash
            geom_metadata = TkMeshMetaData()
            geom_metadata.create(**metadata)
            metadata_list.append(geom_metadata)
        self.GeometryData['StreamMetaDataArray'] = metadata_list

    def process_data(self):
        # This will do the main processing of the different streams.
        # indexes
        # the total number of index points in each object
        index_counts = list(self.i_stream_lens.values())
        # self.batches: the first value is the start, the second is the number
        self.batches = odict(zip(self.mesh_names,
                                 [(sum(index_counts[:i]), index_counts[i])
                                  for i in range(self.num_mesh_objs)]))
        # vertices
        v_stream_lens = list(self.v_stream_lens.values())
        self.vert_bounds = odict(zip(self.mesh_names,
                                     [(sum(v_stream_lens[:i]),
                                       sum(v_stream_lens[:i + 1]) - 1)
                                      for i in range(self.num_mesh_objs)]))
        # bounded hull data
        ch_stream_lens = list(self.ch_stream_lens.values())
        self.hull_bounds = odict(zip(self.mesh_names,
                                     [(sum(ch_stream_lens[:i]),
                                       sum(ch_stream_lens[:i + 1]))
                                      for i in range(self.num_mesh_objs)]))

        # we need to fix up the index stream as the numbering needs to be
        # continuous across all the streams
        mesh_index_end = 0       # additive constant
        for index_stream in self.index_stream.values():
            for j in range(len(index_stream)):
                index_stream[j] = index_stream[j] + mesh_index_end
            mesh_index_end = max(index_stream) + 1

        # get the convex hull index and vertex data
        for name, obj in self.Model.mesh_colls.items():
            self.ch_indexes[name] = obj.CHIndexes
            self.ch_verts[name] = obj.CHVerts

        # get the total lengths for the geometry data
        num_mesh_col_idxs = sum([len(x) for x in self.ch_indexes.values()])
        num_mesh_col_verts = sum([len(x) for x in self.ch_verts.values()])

        # First we need to find the length of each stream.
        self.GeometryData['IndexCount'] = sum(
            list(self.i_stream_lens.values())) + num_mesh_col_idxs
        self.GeometryData['VertexCount'] = sum(
            list(self.v_stream_lens.values())) + num_mesh_col_verts
        self.GeometryData['CollisionIndexCount'] = num_mesh_col_idxs
        self.GeometryData['MeshVertRStart'] = list(
            self.vert_bounds[name][0] for name in self.mesh_names)
        self.GeometryData['MeshVertREnd'] = list(
            self.vert_bounds[name][1] for name in self.mesh_names)
        self.GeometryData['BoundHullVertSt'] = list(
            self.hull_bounds[name][0] for name in self.mesh_names)
        self.GeometryData['BoundHullVertEd'] = list(
            self.hull_bounds[name][1] for name in self.mesh_names)
        # TODO: fix this!! (should be if max > 2**16, not count)
        if self.GeometryData['IndexCount'] > 2**16:
            self.GeometryData['Indices16Bit'] = 0
        else:
            self.GeometryData['Indices16Bit'] = 1

        # Sort out mesh collision convex hull data

        hull_batches = dict()
        hull_verts = dict()
        hull_indexes = dict()

        # create the list of mesh collision index data
        batch_offset = 0
        for name in self.ch_verts.keys():
            # For each mesh collision determine the start verts and indexes
            start_verts = self.GeometryData['MeshVertREnd'][-1] + 1
            start_idxs = batch_offset
            end_verts = start_verts + len(self.ch_verts[name]) - 1
            batch_offset = start_idxs + len(self.ch_indexes[name])
            self.GeometryData['MeshVertRStart'].append(start_verts)
            self.GeometryData['MeshVertREnd'].append(end_verts)
            hull_verts[name] = (start_verts, end_verts)
            hull_batches[name] = (start_idxs, len(self.ch_indexes[name]))
            # Add the mesh collision indexes
            self.index_stream[name] = [mesh_index_end + x for x in
                                       self.ch_indexes[name]]
            mesh_index_end = mesh_index_end + max(self.ch_indexes[name]) + 1
        # Fix up the index values for the actual mesh data
        for name, batch in self.batches.items():
            self.batches[name] = [batch[0] + batch_offset,
                                  batch[1]]

        # Also add the bounded hull vert start and ends
        for name, obj in self.Model.mesh_colls.items():
            length = len(obj.CHVerts)
            start = self.GeometryData['BoundHullVertEd'][-1]
            end = start + length
            self.GeometryData['BoundHullVertSt'].append(start)
            self.GeometryData['BoundHullVertEd'].append(end)
            hull_indexes[name] = (start, end)

        # might as well also populate the hull data since we only need to union
        # it all:
        hull_data = []
        self.GeometryData['BoundHullVerts'] = list()
        for name in self.mesh_names:
            hull_data += self.chvertex_stream[name]
        for verts in self.ch_verts.values():
            hull_data.extend(verts)
        for vert in hull_data:
            self.GeometryData['BoundHullVerts'].append(Vector4f(x=vert[0],
                                                                y=vert[1],
                                                                z=vert[2],
                                                                t=1.0))

        self.vert_bounds.update(hull_verts)
        self.hull_bounds.update(hull_indexes)
        self.batches.update(hull_batches)

    def process_nodes(self):
        # this will iterate first over the list of mesh data and apply all the
        # required information to the Mesh and Mesh-type Collisions objects.
        # We will then iterate over the entire tree of children to the Model
        # and give them any required information

        # Go through every node
        for obj in traverse(self.Model):
            if obj.IsMesh:
                name = obj.Name
                if obj._Type == 'MESH':
                    mesh_obj = self.Model.Meshes[name]
                elif obj._Type == 'COLLISION':
                    mesh_obj = self.Model.mesh_colls[name]
                name = mesh_obj.Name

                data = odict()

                data['BATCHSTART'] = self.batches[name][0]
                data['BATCHCOUNT'] = self.batches[name][1]
                data['VERTRSTART'] = self.vert_bounds[name][0]
                data['VERTREND'] = self.vert_bounds[name][1]
                data['BOUNDHULLST'] = self.hull_bounds[name][0]
                data['BOUNDHULLED'] = self.hull_bounds[name][1]
                if mesh_obj._Type == 'MESH':
                    # add the AABBMIN/MAX(XYZ) values:
                    data['AABBMINX'] = self.mesh_bounds[name]['x'][0]
                    data['AABBMINY'] = self.mesh_bounds[name]['y'][0]
                    data['AABBMINZ'] = self.mesh_bounds[name]['z'][0]
                    data['AABBMAXX'] = self.mesh_bounds[name]['x'][1]
                    data['AABBMAXY'] = self.mesh_bounds[name]['y'][1]
                    data['AABBMAXZ'] = self.mesh_bounds[name]['z'][1]
                    data['HASH'] = self.hashes.get(name, 0)
                    # we only care about entity and material data for Mesh
                    # Objects
                    if not isinstance(mesh_obj.Material, str):
                        if mesh_obj.Material is not None:
                            mat_name = str(mesh_obj.Material['Name'])
                            print('material name: {}'.format(mat_name))

                            data['MATERIAL'] = os.path.join(
                                self.rel_named_path,
                                mat_name.upper()) + '.MATERIAL.MBIN'
                        else:
                            data['MATERIAL'] = ''
                    else:
                        data['MATERIAL'] = mesh_obj.Material
                    if obj.HasAttachment:
                        if obj.EntityData is not None:
                            if not obj._entity_path_is_abs:
                                ent_path = os.path.join(self.rel_named_path,
                                                        'ENTITIES',
                                                        obj.EntityPath.upper())
                            else:
                                ent_path = obj.EntityPath.upper()
                            data['ATTACHMENT'] = '{}.ENTITY.MBIN'.format(
                                ent_path)
                            # also need to generate the entity data
                            AttachmentData = TkAttachmentData(
                                Components=list(obj.EntityData.values())[0])
                            AttachmentData.make_elements(main=True)
                            # also write the entity file now too as we don't
                            # need to do anything else to it
                            AttachmentData.tree.write(
                                "{}.ENTITY.exml".format(
                                    os.path.join(self.export_directory,
                                                 ent_path)))
                        else:
                            data['ATTACHMENT'] = obj.EntityPath
                    # enerate the mesh metadata for the geometry file:
                    self.mesh_metadata[name]['Hash'] = data['HASH']
                    self.mesh_metadata[name]['VertexDataSize'] = (
                        self.stride * (
                            data['VERTREND'] - data['VERTRSTART'] + 1))
                    if self.GeometryData['Indices16Bit'] == 0:
                        m = 4
                    else:
                        m = 2
                    self.mesh_metadata[name]['IndexDataSize'] = m * data[
                        'BATCHCOUNT']
                else:
                    # We need to rename the mesh collision objects
                    obj.Name = self.rel_named_path
            else:
                if obj._Type == 'LOCATOR':
                    if obj.HasAttachment:
                        if obj.EntityData is not None:
                            if not obj._entity_path_is_abs:
                                ent_path = os.path.join(self.rel_named_path,
                                                        'ENTITIES',
                                                        obj.EntityPath.upper())
                            else:
                                ent_path = obj.EntityPath.upper()
                            data = {'ATTACHMENT':
                                    '{}.ENTITY.MBIN'.format(ent_path)}
                            # also need to generate the entity data
                            AttachmentData = TkAttachmentData(
                                Components=list(obj.EntityData.values())[0])
                            AttachmentData.make_elements(main=True)
                            # also write the entity file now too as we don't
                            # need to do anything else to it
                            AttachmentData.tree.write(
                                "{}.ENTITY.exml".format(
                                    os.path.join(self.export_directory,
                                                 ent_path)))
                        else:
                            data = {'ATTACHMENT': obj.EntityPath}
                    else:
                        data = None
                elif obj._Type == 'COLLISION':
                    obj.Name = self.rel_named_path
                    if obj.CType == 'Box':
                        data = {'WIDTH': obj.Width, 'HEIGHT': obj.Height,
                                'DEPTH': obj.Depth}
                    elif obj.CType == 'Sphere':
                        data = {'RADIUS': 2 * obj.Radius}
                    elif obj.CType in ('Capsule', 'Cylinder'):
                        data = {'RADIUS': obj.Radius, 'HEIGHT': obj.Height}
                elif obj._Type == 'MODEL':
                    obj.Name = self.rel_named_path
                    data = {'GEOMETRY': self.rel_named_path + ".GEOMETRY.MBIN"}
                elif obj._Type in ['REFERENCE', 'LIGHT', 'JOINT']:
                    data = None
            obj.create_attributes(data, self.export_original_geom_data)

    def create_vertex_layouts(self):
        # sort out what streams are given and create appropriate vertex layouts
        VertexElements = List()
        SmallVertexElements = List()
        for sID in self.stream_list:
            # sID is the SemanticID
            if sID in [0, 1]:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=5131,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing="PerVertex",
                                                      PlatformData=""))
                # Also write the small vertex data
                Offset = 8 * sID
                SmallVertexElements.append(
                    TkVertexElement(SemanticID=sID,
                                    Size=4,
                                    Type=5131,
                                    Offset=Offset,
                                    Normalise=0,
                                    Instancing="PerVertex",
                                    PlatformData=""))
            # for the INT_2_10_10_10_REV stuff
            elif sID in [2, 3]:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=36255,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing="PerVertex",
                                                      PlatformData=""))
            elif sID == 4:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=5121,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing="PerVertex",
                                                      PlatformData=""))

        self.GeometryData['VertexLayout'] = TkVertexLayout(
            ElementCount=self.element_count,
            Stride=self.stride,
            PlatformData="",
            VertexElements=VertexElements)
        # TODO: do more generically
        self.GeometryData['SmallVertexLayout'] = TkVertexLayout(
            ElementCount=len(SmallVertexElements),
            Stride=0x8 * len(SmallVertexElements),
            PlatformData="",
            VertexElements=SmallVertexElements)

    def mix_streams(self):
        # this combines all the input streams into one single stream with the
        # correct offset etc as specified by the VertexLayout
        # This also flattens each stream so it needs to be called pretty much
        # last

        VertexStream = array('f')
        SmallVertexStream = array('f')
        for name, mesh_obj in self.Model.Meshes.items():
            for j in range(self.v_stream_lens[name]):
                for sID in self.stream_list:
                    # get the j^th 4Vector element of i^th object of the
                    # corresponding stream as specified by the stream list.
                    # As self.stream_list is ordered this will be mixed in the
                    # correct way wrt. the VertexLayouts
                    try:
                        VertexStream.extend(
                            mesh_obj.__dict__[REV_SEMANTICS[sID]][j])
                        if sID in [0, 1]:
                            SmallVertexStream.extend(
                                mesh_obj.__dict__[REV_SEMANTICS[sID]][j])
                    except IndexError:
                        # in the case this fails there is an index error caused
                        # by collisions. In this case just add a default value
                        VertexStream.extend((0, 0, 0, 1))
                    except TypeError:
                        print(f'{name} mesh has an error!')
                        raise

        self.GeometryData['VertexStream'] = VertexStream
        self.GeometryData['SmallVertexStream'] = SmallVertexStream

        # finally we can also flatten the index stream:
        IndexBuffer = array('I')
        # First write the mesh collision index buffer
        for name in self.Model.mesh_colls.keys():
            obj = self.index_stream[name]
            IndexBuffer.extend(obj)
        # Then write the normal mesh index buffer
        for name in self.mesh_names:
            obj = self.index_stream[name]
            IndexBuffer.extend(obj)
        # TODO: make this better (determine format correctly)
        """
        # let's convert to the correct type of array data type here
        if not max(IndexBuffer) > 2**16:
            IndexBuffer = array('H', IndexBuffer)
        """
        self.GeometryData['IndexBuffer'] = IndexBuffer

    def get_bounds(self):
        # this analyses the vertex stream and finds the smallest bounding box
        # corners.

        self.GeometryData['MeshAABBMin'] = List()
        self.GeometryData['MeshAABBMax'] = List()

        for obj in self.Model.Meshes.values():
            v_stream = obj.Vertices
            x_verts = [i[0] for i in v_stream]
            y_verts = [i[1] for i in v_stream]
            z_verts = [i[2] for i in v_stream]
            x_bounds = (min(x_verts), max(x_verts))
            y_bounds = (min(y_verts), max(y_verts))
            z_bounds = (min(z_verts), max(z_verts))

            self.GeometryData['MeshAABBMin'].append(
                Vector4f(x=x_bounds[0], y=y_bounds[0], z=z_bounds[0], t=1))
            self.GeometryData['MeshAABBMax'].append(
                Vector4f(x=x_bounds[1], y=y_bounds[1], z=z_bounds[1], t=1))
            if obj._Type == "MESH":
                # only add the meshes to the self.mesh_bounds dict:
                self.mesh_bounds[obj.Name] = {'x': x_bounds, 'y': y_bounds,
                                              'z': z_bounds}

    def write(self):
        """ Write all of the files required for the scene. """
        # We only need to write the geometry data if we aren't preserving
        # imported node data.
        if (not self.preserve_node_info
                or (self.preserve_node_info
                    and self.export_original_geom_data)):
            mbinc = mbinCompiler(
                self.TkGeometryData,
                "{}.GEOMETRY.MBIN.PC".format(self.abs_name_path))
            mbinc.serialize()
        print(f'Scene written to {self.abs_name_path}')
        self.TkSceneNodeData.tree.write("{}.SCENE.exml".format(
            self.abs_name_path))
        # Build all the descriptor exml data
        if self.descriptor is not None:
            descriptor = self.descriptor.to_exml()
            descriptor.make_elements(main=True)
            descriptor.tree.write(
                "{}.DESCRIPTOR.exml".format(self.abs_name_path))
        for material in self.materials:
            if not isinstance(material, str):
                material.tree.write(
                    "{0}.MATERIAL.exml".format(os.path.join(
                        self.abs_name_path, str(material['Name']).upper())))
        # Write the animation files
        idle_anim = bpy.context.scene.nmsdk_anim_data.idle_anim
        if len(self.anim_data) != 0:
            if len(self.anim_data) == 1:
                if idle_anim not in self.anim_data:
                    raise ValueError('Specified idle anim name is somehow not '
                                     'one of the animations that exists...')
                # get the value and output it
                self.anim_data[idle_anim].tree.write(
                    "{}.ANIM.exml".format(self.abs_name_path))
            else:
                for name in list(self.anim_data.keys()):
                    if name != idle_anim:
                        self.anim_data[name].tree.write(
                            os.path.join(self.anims_path,
                                         "{}.ANIM.exml".format(name.upper())))
                    else:
                        self.anim_data[idle_anim].tree.write(
                            "{}.ANIM.exml".format(self.abs_name_path))

    def convert_to_mbin(self):
        """ Convert all .exml file to .mbin files. """
        print('Converting .exml files to .mbin. Please wait.')
        for directory, _, files in os.walk(self.basepath):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1].lower() == '.exml':
                    # Force MBINCompiler to overwrite existing files and
                    # ignore errors.
                    mbincompiler_path = bpy.context.scene.nmsdk_default_settings.MBINCompiler_path  # noqa
                    retcode = subprocess.call(
                        [mbincompiler_path, "-y", "-f", "-Q", location])
                    if retcode == 0:
                        os.remove(location)
                    else:
                        print('MBINCompiler failed to run. Please ensure it '
                              'is registered on the path.')
