#!/usr/bin/env python
"""Process the 3d model data and create required files for NMS.

This function will take all the data provided by the blender script and create
a number of .mxml files that contain all the data required by the game to view
the 3d model created.
"""

__author__ = "monkeyman192"
__credits__ = ["monkeyman192", "gregkwaste"]

# Blender imports
import bpy

import numpy as np

# stdlib imports
import os
import subprocess
from collections import OrderedDict as odict
from array import array
import struct
from itertools import accumulate
# Internal imports
from NMS.classes import TkAttachmentData
from NMS.LOOKUPS import SEMANTICS, REV_SEMANTICS, STRIDES, VERTS
from NMS.classes.Object import Model
from serialization.NMS_Structures import MBINHeader
from serialization.NMS_Structures.Structures import (
    TkMeshData, TkGeometryStreamData, TkVertexLayout, TkVertexElement, TkMeshMetaData
)
from serialization.NMS_Structures.Structures import (
    TkGeometryData as TkGeometryData_new,
)
from serialization.StreamCompiler import StreamData
from serialization.serializers import serialize_vertex_stream
from ModelExporter.utils import nmsHash, traverse


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
    def __init__(self, export_directory, scene_directory, scene_name, model: Model,
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
        self.mesh_coll_indexes = odict()
        self.mesh_coll_verts = odict()
        # a dictionary of the bounds of just mesh objects. This will be used
        # for the scene files
        self.mesh_bounds = odict()
        # this will hopefully mean that there will be at most one copy of each
        # unique TkMaterialData struct in the set
        self.materials = set()
        self.hashes = odict()
        self.mesh_names: list[str] = list()

        self.np_index_data = np.array([], dtype=np.uint32)

        # Make some settings values more easily accessible.
        self.preserve_node_info = self.settings.get('preserve_node_info',
                                                    False)
        self.export_original_geom_data = self.settings.get('reexport_geometry',
                                                           False)

        # a list of any extra properties to go in each entity
        # self.Entities = []

        self.np_indexes: list[np.ndarray] = []
        self.np_index_lenths = []
        self.np_index_maxs = []

        # extract the streams from the mesh objects.
        for i, mesh in enumerate(self.Model.Meshes.values()):
            self.mesh_names.append(mesh.Name)
            self.index_stream[mesh.Name] = mesh.Indexes
            self.vertex_stream[mesh.Name] = mesh.Vertices
            self.uv_stream[mesh.Name] = mesh.UVs
            self.n_stream[mesh.Name] = mesh.Normals
            self.t_stream[mesh.Name] = mesh.Tangents
            self.np_indexes.append(mesh.np_indexes)
            self.np_index_lenths.append(mesh.np_indexes.size)
            self.np_index_maxs.append(max(mesh.np_indexes) + 1)
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

        if sum(self.np_index_maxs) > 0xFFFF:
            self.Indices16Bit = 0
        else:
            self.Indices16Bit = 1

        # for obj in self.Model.ListOfEntities:
        #    self.Entities.append(obj.EntityData)

        self.num_mesh_objs = len(self.Model.Meshes)

        # generate some variables relating to the paths
        self.basepath = os.path.join(self.export_directory, self.scene_directory)
        self.texture_path = os.path.join(self.basepath, self.scene_name, 'TEXTURES')
        self.anims_path = os.path.join(self.basepath, 'ANIMS')
        # path location of the entity folder. Calling makedirs of this will
        # ensure all the folders are made in one go
        self.ent_path = os.path.join(self.basepath, self.scene_name, 'ENTITIES')
        # The name of the scene relative to the PCBANKS folder
        self.rel_named_path = os.path.join(self.scene_directory, self.scene_name)
        self.abs_name_path = os.path.join(self.basepath, self.scene_name)

        self.create_paths()

        # This dictionary contains all the information for the geometry file
        self.GeometryData = odict()

        self.preprocess_streams()

        self.gstream_fpath = f"{os.path.join(self.basepath, self.scene_name)}.GEOMETRY.DATA.MBIN.PC"

        if (not self.preserve_node_info
                or (self.preserve_node_info
                    and self.export_original_geom_data)):
            self.geometry_stream = StreamData(self.gstream_fpath)

            # generate the geometry stream data now
            self.serialize_data()

        # This will just be some default entity with physics data
        # This is created with the Physics Component Data by default
        self.TkAttachmentData = TkAttachmentData()
        self.TkAttachmentData.make_elements(main=True)

        self.process_data()

        self.get_bounds()

        # this creates the VertexLayout and PositionVertexLayout properties
        self.create_vertex_layouts()

        self.process_nodes()
        # make this last to make sure flattening each stream doesn't affect
        # other data.
        self.mix_streams()

        self.Model.construct_data()
        self.TkSceneNodeData = self.Model.get_data()
        for material in self.materials:
            if not isinstance(material, str):
                material.make_elements(main=True)
        for anim_name in list(self.anim_data.keys()):
            self.anim_data[anim_name].make_elements(main=True)

        # write all the files
        self.write()

        if not self.settings.get('no_convert', False):
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
            SEMANTICS[x] for x in streams.difference({'Indexes', 'Vertices'}))
        self.stream_list.sort()

        self.element_count = len(self.stream_list)
        # Create a list to store the offset sizes for each data type
        offsets = list()
        for sid in self.stream_list:
            if sid != VERTS:
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
        vertex_sizes = []
        vertex_pos_sizes = []
        index_sizes = []
        mesh_datas: list[TkMeshData] = []
        for i, name in enumerate(self.mesh_names):
            count = len(self.vertex_stream[name])
            v_data = serialize_vertex_stream(
                requires=self.stream_list,
                count=count,
                UVs=self.uv_stream[name],
                Normals=self.n_stream[name],
                Tangents=self.t_stream[name],
                Colours=self.c_stream[name]
            )
            v_pos_data = serialize_vertex_stream(
                requires={SEMANTICS["Vertices"]},
                count=count,
                Vertices=self.vertex_stream[name],
            )
            v_len = len(v_data)
            vertex_sizes.append(v_len)
            v_pos_len = len(v_pos_data)
            vertex_pos_sizes.append(v_pos_len)
            # new_indexes = self.index_stream[name]
            # # TODO: serialize the same way as they are in the actual data.
            # # This will also fail I think if there are indexes > 0xFFFF since it will serialize some as H and
            # # some as I
            # if max(new_indexes) > 2 ** 16:
            #     indexes = array('I', new_indexes)
            # else:
            #     indexes = array('H', new_indexes)
            # i_data = serialize_index_stream(indexes)
            i_data = self.np_indexes[i]
            if (max_idx := max(i_data)) > 0xFFFF:
                raise ValueError(
                    f"The mesh {name} has too many vertexes (max index found = {max_idx}). "
                    "Please simplify the model to export."
                )
            i_data = i_data.astype(np.uint16).tobytes()
            i_len = len(i_data)
            index_sizes.append(i_len)
            md = TkMeshData(
                name.upper(),
                v_data + i_data,
                v_pos_data,
                self.mesh_metadata[name]["hash"],
                i_len,
                v_len,
                v_pos_len,
            )
            mesh_datas.append(md)
        gstream_data = TkGeometryStreamData(mesh_datas)

        with open(self.gstream_fpath, "wb") as f:
            hdr = MBINHeader()
            hdr.header_namehash = 0x40025754
            hdr.header_guid = 0xCCB46895A8B36313
            hdr.write(f)
            gstream_data.write(f)

        # This is a list of 3-tuples with the structure (vert_offset, index_offset_vert_pos_offset)
        offsets = []

        # A bit of a hack, but we need the offsets of the index and vert data. We'll use this code to get it
        # since it works.
        with open(self.gstream_fpath, "rb") as f:
            # Read the number of TkMeshData's serialized.
            f.seek(0x28, 0)
            entries = struct.unpack("<I", f.read(4))[0]

            TkMeshData_size = 0x48

            # Then jump to the start of these.
            f.seek(0x30, 0)
            for i in range(entries):
                entry_start = f.tell()
                # First read the list header for MeshDataStream
                f.seek(entry_start + 0x10, 0)
                curr_pos = f.tell()
                offset = struct.unpack("<Q", f.read(8))[0]
                vert_data_pos = curr_pos + offset
                f.seek(entry_start + 0x20, 0)
                curr_pos = f.tell()
                offset = struct.unpack("<Q", f.read(8))[0]
                vert_pos_data_pos = curr_pos + offset
                # To get the index start, we just need to get the size of the vertex data and add it to the
                # start address of the vertex data since it's serialized in the same data.
                f.seek(entry_start + 0x3C, 0)
                vert_size = struct.unpack("<I", f.read(4))[0]
                offsets.append((vert_data_pos, vert_data_pos + vert_size, vert_pos_data_pos))
                f.seek(entry_start + TkMeshData_size, 0)

        # while we are here we will generate the mesh metadata for the geometry
        # file.
        # metadata_list = List()
        StreamMetaDataArray = []
        for i, md in enumerate(mesh_datas):
            StreamMetaDataArray.append(TkMeshMetaData(
                IdString=md.IdString.upper(),
                Hash=md.Hash,
                IndexDataOffset=offsets[i][1],
                IndexDataSize=index_sizes[i],
                VertexDataOffset=offsets[i][0],
                VertexDataSize=vertex_sizes[i],
                VertexPositionDataOffset=offsets[i][2],
                VertexPositionDataSize=vertex_pos_sizes[i],
                DoubleBufferGeometry=False,
            ))
            # metadata = {
            #     'ID': m.ID, 'hash': m.hash, 'vert_size': m.vertex_size,
            #     'vert_offset': self.geometry_stream.data_offsets[2 * i],
            #     'index_size': m.index_size,
            #     'index_offset': self.geometry_stream.data_offsets[2 * i + 1]}
            # self.hashes[m.raw_ID] = m.hash
            # geom_metadata = TkMeshMetaData()
            # geom_metadata.create(**metadata)
            # metadata_list.append(geom_metadata)
        self.GeometryData['StreamMetaDataArray'] = StreamMetaDataArray

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
            self.mesh_coll_indexes[name] = obj.Indexes
            self.mesh_coll_verts[name] = obj.Vertices
            self.np_indexes.append(obj.np_indexes)
            self.np_index_lenths.append(obj.np_indexes.size)
            self.np_index_maxs.append(max(obj.np_indexes) + 1)

        # get the total lengths for the geometry data
        num_mesh_col_idxs = sum(
            [len(x) for x in self.mesh_coll_indexes.values()]
        )
        num_mesh_col_verts = sum(
            [len(x) for x in self.mesh_coll_verts.values()]
        )

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

        # Sort out mesh collision convex hull data

        hull_batches = dict()
        hull_verts = dict()
        hull_indexes = dict()

        # create the list of mesh collision index data
        batch_offset = 0

        for name in self.mesh_coll_verts.keys():
            # For each mesh collision determine the start verts and indexes
            start_verts = self.GeometryData['MeshVertREnd'][-1] + 1
            start_idxs = batch_offset
            end_verts = start_verts + len(self.mesh_coll_verts[name]) - 1
            batch_offset = start_idxs + len(self.mesh_coll_indexes[name])
            self.GeometryData['MeshVertRStart'].append(start_verts)
            self.GeometryData['MeshVertREnd'].append(end_verts)
            hull_verts[name] = (start_verts, end_verts)
            hull_batches[name] = (
                start_idxs,
                len(self.mesh_coll_indexes[name])
            )
            # Add the mesh collision indexes
            self.index_stream[name] = [mesh_index_end + x for x in
                                       self.mesh_coll_indexes[name]]
            mesh_index_end = (
                mesh_index_end + max(self.mesh_coll_indexes[name]) + 1
            )

        self.GeometryData['Indices16Bit'] = self.Indices16Bit

        # Fix up the index values for the actual mesh data
        for name, batch in self.batches.items():
            self.batches[name] = [batch[0] + batch_offset,
                                  batch[1]]

        # Also add the bounded hull vert start and ends
        for name, obj in self.Model.mesh_colls.items():
            length = len(obj.Vertices)
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
        for verts in self.mesh_coll_verts.values():
            hull_data.extend(verts)
        for vert in hull_data:
            self.GeometryData['BoundHullVerts'].append((vert[0], vert[1], vert[2], 1.0))

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
                    data['AABBMINX'] = self.mesh_bounds[name]['X'][0]
                    data['AABBMINY'] = self.mesh_bounds[name]['Y'][0]
                    data['AABBMINZ'] = self.mesh_bounds[name]['Z'][0]
                    data['AABBMAXX'] = self.mesh_bounds[name]['X'][1]
                    data['AABBMAXY'] = self.mesh_bounds[name]['Y'][1]
                    data['AABBMAXZ'] = self.mesh_bounds[name]['Z'][1]
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
                                "{}.ENTITY.mxml".format(
                                    os.path.join(self.export_directory,
                                                 ent_path)))
                        else:
                            data['ATTACHMENT'] = obj.EntityPath
                    # TODO: Do we even need to add this mesh metadata?
                    # enerate the mesh metadata for the geometry file:
                    self.mesh_metadata[name]['Hash'] = data['HASH']
                    self.mesh_metadata[name]['VertexDataSize'] = self.stride * (
                        data['VERTREND'] - data['VERTRSTART'] + 1
                    )
                    self.mesh_metadata[name]['VertexPositionDataSize'] = STRIDES[VERTS] * (
                        data['VERTREND'] - data['VERTRSTART'] + 1
                    )
                    if self.GeometryData['Indices16Bit'] == 0:
                        m = 4
                    else:
                        m = 2
                    self.mesh_metadata[name]['IndexDataSize'] = m * data[
                        'BATCHCOUNT']
                else:
                    # We need to rename the mesh collision objects
                    obj.Name = self.rel_named_path + "|Collision"
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
                                "{}.ENTITY.mxml".format(
                                    os.path.join(self.export_directory,
                                                 ent_path)))
                        else:
                            data = {'ATTACHMENT': obj.EntityPath}
                    else:
                        data = None
                elif obj._Type == 'COLLISION':
                    obj.Name = self.rel_named_path + "|Collision"
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
        VertexElements = []
        PositionVertexElements = [
            TkVertexElement(
                SemanticID=VERTS,
                Size=4,
                Type=5131,
                Offset=0,
                Normalise=0,
                Instancing=0
            )
        ]
        for sID in self.stream_list:
            # sID is the SemanticID
            if sID == 1:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=5131,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing=0))

            # for the INT_2_10_10_10_REV stuff
            elif sID in [2, 3]:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=36255,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing=0))
            elif sID == 4:
                Offset = self.offsets[sID]
                VertexElements.append(TkVertexElement(SemanticID=sID,
                                                      Size=4,
                                                      Type=5121,
                                                      Offset=Offset,
                                                      Normalise=0,
                                                      Instancing=0))

        self.GeometryData['VertexLayout'] = TkVertexLayout(
            ElementCount=self.element_count,
            Stride=self.stride,
            PlatformData=0,
            VertexElements=VertexElements,
        )
        self.GeometryData['PositionVertexLayout'] = TkVertexLayout(
            ElementCount=len(PositionVertexElements),
            Stride=0x8 * len(PositionVertexElements),
            PlatformData=0,
            VertexElements=PositionVertexElements,
        )

    def mix_streams(self):
        # Handle the index streams.
        # First, we create a list which contains the cumulative count, and then we add this value to each
        # array.
        # We add 0 to the start to avoid adding anything to the first one.
        addt_values = [0] + list(accumulate(self.np_index_maxs))
        for i, addt in enumerate(addt_values[:-1]):
            self.np_indexes[i] += addt
        mesh_col_offset = len(self.mesh_names)

        if self.Indices16Bit == 0:
            dtype = np.uint32
        else:
            dtype = np.uint16

        index_array = np.concatenate(
            self.np_indexes[mesh_col_offset:] + self.np_indexes[:mesh_col_offset],
            dtype=dtype,
        )
        index_array_bytes = index_array.tobytes()
        if (dfct := (len(index_array_bytes) % 4)) != 0:
            index_array_bytes += b"\x00" * (4 - dfct)

        self.GeometryData['IndexBuffer'] = np.frombuffer(index_array_bytes, dtype=np.uint32)

    def get_bounds(self):
        # this analyses the vertex stream and finds the smallest bounding box
        # corners.

        self.GeometryData['MeshAABBMin'] = []
        self.GeometryData['MeshAABBMax'] = []

        # Combine the meshes
        objs = [*self.Model.Meshes.values(), *self.Model.mesh_colls.values()]

        for obj in objs:
            v_stream = obj.Vertices
            x_verts = [i[0] for i in v_stream]
            y_verts = [i[1] for i in v_stream]
            z_verts = [i[2] for i in v_stream]
            x_bounds = (min(x_verts), max(x_verts))
            y_bounds = (min(y_verts), max(y_verts))
            z_bounds = (min(z_verts), max(z_verts))

            self.GeometryData['MeshAABBMin'].append((x_bounds[0], y_bounds[0], z_bounds[0], 1))
            self.GeometryData['MeshAABBMax'].append((x_bounds[1], y_bounds[1], z_bounds[1], 1))
            if obj._Type == "MESH":
                # only add the meshes to the self.mesh_bounds dict:
                self.mesh_bounds[obj.Name] = {'X': x_bounds, 'Y': y_bounds,
                                              'Z': z_bounds}

    # TODO: Change this here too...
    def write(self):
        """ Write all of the files required for the scene. """
        # We only need to write the geometry data if we aren't preserving
        # imported node data.
        if (not self.preserve_node_info
                or (self.preserve_node_info
                    and self.export_original_geom_data)):
            # mbinc = mbinCompiler(
            #     self.TkGeometryData,
            #     "{}.GEOMETRY.MBIN.PC".format(self.abs_name_path))
            # mbinc.serialize()

            with open(f"{self.abs_name_path}.GEOMETRY.MBIN.PC", "wb") as f:
                hdr = MBINHeader(
                    header_magic = 0xDDDDDDDDDDDDDDDD,
                    header_namehash = 0x819C3220,
                    header_guid = 0xDA1F6CA99ADEF6A6,
                    header_timestamp = 0xFFFFFFFFFFFFFFFF,
                )
                hdr.write(f)
                gd = self.GeometryData
                thing = TkGeometryData_new(
                    PositionVertexLayout=gd["PositionVertexLayout"],
                    VertexLayout=gd["VertexLayout"],
                    BoundHullVertEd=gd["BoundHullVertEd"],
                    BoundHullVerts=gd["BoundHullVerts"],
                    BoundHullVertSt=gd["BoundHullVertSt"],
                    IndexBuffer=gd["IndexBuffer"],
                    JointBindings=[],
                    JointExtents=[],
                    JointMirrorAxes=[],
                    JointMirrorPairs=[],
                    MeshAABBMax=gd["MeshAABBMax"],
                    MeshAABBMin=gd["MeshAABBMin"],
                    MeshBaseSkinMat=[],
                    MeshVertREnd=gd["MeshVertREnd"],
                    MeshVertRStart=gd["MeshVertRStart"],
                    ProcGenNodeNames=[],
                    ProcGenParentId=[],
                    SkinMatrixLayout=[],
                    StreamMetaDataArray=gd["StreamMetaDataArray"],
                    CollisionIndexCount=gd["CollisionIndexCount"],
                    IndexCount=gd["IndexCount"],
                    Indices16Bit=self.Indices16Bit,
                    VertexCount=gd["VertexCount"],
                )
                thing.write(f)

        scene_path = f"{self.abs_name_path}.SCENE.MBIN"
        with open(scene_path, "wb") as f:
            hdr = MBINHeader()
            hdr.header_namehash = 0x3DB87E47
            hdr.header_guid = 0x42A57794F683F216
            hdr.write(f)
            self.TkSceneNodeData.write(f)
        print(f'Scene written to {scene_path}')
        # Build all the descriptor mxml data
        if self.descriptor is not None:
            descriptor = self.descriptor.to_mxml()
            descriptor.make_elements(main=True)
            descriptor.tree.write(
                "{}.DESCRIPTOR.mxml".format(self.abs_name_path))
        for material in self.materials:
            if not isinstance(material, str):
                material.tree.write(
                    "{0}.MATERIAL.mxml".format(os.path.join(
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
                    "{}.ANIM.mxml".format(self.abs_name_path))
            else:
                for name in list(self.anim_data.keys()):
                    if name != idle_anim:
                        self.anim_data[name].tree.write(
                            os.path.join(self.anims_path,
                                         "{}.ANIM.mxml".format(name.upper())))
                    else:
                        self.anim_data[idle_anim].tree.write(
                            "{}.ANIM.mxml".format(self.abs_name_path))

    def convert_to_mbin(self):
        """ Convert all .mxml file to .mbin files. """
        print('Converting .mxml files to .mbin. Please wait.')
        for directory, _, files in os.walk(self.basepath):
            for file in files:
                location = os.path.join(directory, file)
                if os.path.splitext(location)[1].lower() == '.mxml':
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
