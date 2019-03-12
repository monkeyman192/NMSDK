# stdlib imports
import os.path as op
import xml.etree.ElementTree as ET
import struct
from math import radians
from tempfile import TemporaryDirectory
import json
import os
import subprocess
import shutil

# Blender imports
import bpy  # pylint: disable=import-error
from mathutils import Matrix, Vector  # pylint: disable=import-error

# Internal imports
from serialization.formats import (bytes_to_half, bytes_to_int_2_10_10_10_rev,
                                   bytes_to_ubyte)
from serialization.utils import read_list_header
from NMS.LOOKUPS import VERTS, NORMS, UVS
from ModelImporter.readers import read_material, read_metadata, read_gstream
from ModelImporter.utils import element_to_dict
from ModelImporter.SceneNodeData import SceneNodeData

VERT_TYPE_MAP = {5121: {'size': 1, 'func': bytes_to_ubyte},
                 5131: {'size': 2, 'func': bytes_to_half},
                 36255: {'size': 1, 'func': bytes_to_int_2_10_10_10_rev}}
ROT_MATRIX = Matrix.Rotation(radians(90), 4, 'X')


class ImportScene():
    """ Load a scene into blender.

    Parameters
    ----------
    fpath : string
        filepath to the scene file to be loaded.
    """
    def __init__(self, fpath):
        self.local_directory = op.dirname(fpath)
        with open(op.join(os.getcwd(), 'config.json'), 'r') as config:
            self.mbincompiler_path = json.load(config)['mbincompiler_path']
        ext = op.splitext(fpath)[1]

        self.data = None
        self.vertex_elements = list()
        self.bh_data = list()
        self.materials = dict()
        self.scn = bpy.context.scene

        # change to render with cycles
        self.scn.render.engine = 'CYCLES'

        if ext.lower() == '.mbin':
            with TemporaryDirectory() as temp_dir:
                fpath_dst = op.join(temp_dir, op.basename(fpath))
                shutil.copy(fpath, fpath_dst)
                subprocess.call([self.mbincompiler_path, '-q', fpath_dst])
                fpath = fpath_dst.replace('.MBIN', '.EXML')
                self._load_scene(fpath)
        elif ext.lower() != '.exml':
            raise TypeError('Selected file is of the wrong format.')
        else:
            self._load_scene(fpath)

        if self.data is None:
            raise ValueError('Cannot load scene file...')
        self.scene_node_data = SceneNodeData(self.data)
        self.directory = op.dirname(self.scene_node_data.Name)
        # remove the name of the top level object
        self.scene_node_data.info['Name'] = None
        self.geometry_file = op.join(
            self.local_directory,
            op.relpath(
                self.scene_node_data.Attribute('GEOMETRY'),
                self.directory) + '.PC')
        self.geometry_stream_file = self.geometry_file.replace('GEOMETRY',
                                                               'GEOMETRY.DATA')

        # get the information about what data the geometry file contains
        with open(self.geometry_file, 'rb') as f:
            f.seek(0x140)
            self.count, self.stride = struct.unpack('<II', f.read(0x8))
            # skip platform data
            f.seek(0x8, 1)
            list_offset, list_count = read_list_header(f)
            f.seek(list_offset, 1)
            # jump to the actual TkVertexElement data
            for _ in range(list_count):
                data = dict()
                data['semID'], data['size'], data['type'], data['offset'] = \
                    struct.unpack('<IIII', f.read(0x10))
                f.seek(0x10, 1)
                self.vertex_elements.append(data)

        # load all the bounded hull data
        self._load_bounded_hulls()

        # load all the mesh metadata
        self.mesh_metadata = read_metadata(self.geometry_file)

        self._render_scene()

        self.state = 'FINISHED'

# region public methods

    def load_mesh(self, mesh_node):
        # TODO: rename?? / make private??
        """ Load the mesh.
        This will load the mesh data into memory then deserialize the actual
        vertex and index data from the gstream mbin.
        """
        self._load_mesh(mesh_node)
        self._deserialize_vertex_data(mesh_node)
        self._deserialize_index_data(mesh_node)
        mesh_node._generate_geometry()
        mesh_node._generate_bounded_hull(self.bh_data)

# region private methods

    def _add_empty_to_scene(self, scene_node):
        name = scene_node.Name

        # create a new empty instance
        empty_mesh = bpy.data.meshes.new(name)
        empty_obj = bpy.data.objects.new(name, empty_mesh)

        if scene_node.parent.Name is not None:
            empty_obj.parent = self.scn.objects[scene_node.parent.Name]

        # get transform and apply
        transform = scene_node.Transform['Trans']
        empty_obj.location = Vector(transform)
        # get rotation and apply
        rotation = scene_node.Transform['Rot']
        empty_obj.rotation_euler = rotation
        # get scale and apply
        scale = scene_node.Transform['Scale']
        empty_obj.scale = Vector(scale)
        # link the object then update the scene so that the above transforms
        # can be applied before we do the NMS -> blender scene rotation
        self.scn.objects.link(empty_obj)
        self.scn.update()

        if scene_node.parent.Name is None:
            empty_obj.matrix_world = ROT_MATRIX * empty_obj.matrix_world

    def _add_mesh_to_scene(self, scene_node):
        name = scene_node.Name
        mat_path = self._get_material_path(scene_node)
        material = self._create_material(mat_path)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(scene_node.verts[VERTS],
                         scene_node.edges,
                         scene_node.faces)
        # add normals
        for i, vert in enumerate(mesh.vertices):
            vert.normal = scene_node.verts[NORMS][i]

        mesh_obj = bpy.data.objects.new(name, mesh)

        # give object correct parent
        if scene_node.parent.Name is not None:
            mesh_obj.parent = self.scn.objects[scene_node.parent.Name]
        # get transform and apply
        transform = scene_node.Transform['Trans']
        mesh_obj.location = Vector(transform)
        # get rotation and apply
        rotation = scene_node.Transform['Rot']
        mesh_obj.rotation_euler = rotation
        # get scale and apply
        scale = scene_node.Transform['Scale']
        mesh_obj.scale = Vector(scale)
        # link the object then update the scene so that the above transforms
        # can be applied before we do the NMS -> blender scene rotation
        self.scn.objects.link(mesh_obj)
        self.scn.update()

        # ensure the newly created object is the active one in the scene
        self.scn.objects.active = mesh_obj
        mesh = mesh_obj.data
        # Add UV's
        bpy.ops.object.mode_set(mode='EDIT')
        if not mesh.uv_textures:
            mesh.uv_textures.new()
        # un-unwrap to generate a default mapping to overwrite
        bpy.ops.uv.unwrap()
        bpy.ops.object.mode_set(mode='OBJECT')

        uvs = scene_node.verts[UVS]
        uv_layers = mesh.uv_layers.active.data
        for idx, loop in enumerate(mesh.loops):
            uv = uvs[loop.vertex_index]
            uv_layers[idx].uv = (uv[0], 1 - uv[1])

        if scene_node.parent.Name is None:
            mesh_obj.matrix_world = ROT_MATRIX * mesh_obj.matrix_world
        if material is not None:
            mesh_obj.data.materials.append(material)

        # create child object for bounded hull
        name = 'BH' + name
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(scene_node.bounded_hull, [], [])
        bh_obj = bpy.data.objects.new(name, mesh)
        # Don't show the bounded hull
        bh_obj.hide = True
        bh_obj.parent = mesh_obj
        self.scn.objects.link(bh_obj)

    def _create_material(self, mat_path):
        # retrieve a cached copy if it exists
        if mat_path in self.materials:
            return self.materials[mat_path]
        # If not, first read the material file by converting the mbin path to
        # exml
        mat_data = None
        with TemporaryDirectory() as temp_dir:
            mat_path_dst = op.join(temp_dir, op.basename(mat_path))
            shutil.copy(mat_path, mat_path_dst)
            subprocess.call([self.mbincompiler_path, '-q', mat_path_dst])
            mat_path = mat_path_dst.replace('.MBIN', '.EXML')
            mat_data = read_material(mat_path)
        if mat_data is None or mat_data == dict():
            # no material data so just exit this function.
            return
        # create a new material
        mat_name = mat_data.pop('Name')
        mat = bpy.data.materials.new(name=mat_name)
        # for each texture make a new texture
        count = len(mat_data) - 1
        for tex_type, tex_path in mat_data.items():
            tex = bpy.data.textures.new('{0}_{1}'.format(mat_name, tex_type),
                                        'IMAGE')
            print(self._get_path(tex_path))
            img = bpy.data.images.load(self._get_path(tex_path))
            tex.image = img
            # place the materials in in reversed order
            tex_slot = mat.texture_slots.create(count - tex_type)
            tex_slot.texture = tex
        mat.use_shadeless = True
        self.materials[mat_path] = mat
        return mat

    def _deserialize_index_data(self, mesh):
        """ Take the raw index data and generate a list of actual index data.

        Parameters
        ----------
        mesh : SceneNodeData
            SceneNodeData of type MESH to get the vertex data of.
        """
        idx_count = int(mesh.Attribute('BATCHCOUNT'))
        size = mesh.metadata.idx_size // idx_count
        if size == 4:
            fmt = '<I'
        elif size == 2:
            fmt = '<H'
        else:
            raise ValueError('Something has gone wrong!!')
        with open(self.geometry_stream_file, 'rb') as f:
            f.seek(mesh.metadata.idx_off)
            for _ in range(idx_count):
                mesh.idxs.append(struct.unpack(fmt, f.read(size))[0])

    def _deserialize_vertex_data(self, mesh):
        """ Take the raw vertex data and generate a list of actual vertex data.

        Parameters
        ----------
        mesh : SceneNodeData
            SceneNodeData of type MESH to get the vertex data of.
        """
        semIDs = list()
        read_sizes = list()
        read_funcs = list()
        for ve in self.vertex_elements:
            mesh.verts[ve['semID']] = list()
            semIDs.append(ve['semID'])
            read_sizes.append(ve['size'] * VERT_TYPE_MAP[ve['type']]['size'])
            read_funcs.append(VERT_TYPE_MAP[ve['type']]['func'])
        num_verts = mesh.metadata.vert_size / self.stride
        if not num_verts % 1 == 0:
            raise ValueError('Something has gone wrong!!!')
        with open(self.geometry_stream_file, 'rb') as f:
            f.seek(mesh.metadata.vert_off)
            for _ in range(int(num_verts)):
                for i in range(self.count):
                    # Skip 't' component.
                    mesh.verts[semIDs[i]].append(
                        read_funcs[i](f.read(read_sizes[i]))[:-1])

    def _get_material_path(self, scene_node):
        real_path = None
        raw_path = scene_node.Attribute('MATERIAL')
        if raw_path is not None:
            real_path = self._get_path(raw_path)
        return real_path

    def _get_path(self, fpath):
        return op.normpath(
            op.join(self.local_directory, op.relpath(fpath, self.directory)))

    def _load_bounded_hulls(self):
        with open(self.geometry_file, 'rb') as f:
            f.seek(0x130)
            list_offset, list_count = read_list_header(f)
            f.seek(list_offset, 1)
            for _ in range(list_count):
                self.bh_data.append(struct.unpack('<fff', f.read(0xC)))
                # Skip 't' component.
                f.seek(0x4, 1)

    def _load_mesh(self, mesh):
        """ Load the mesh data from the geometry stream file."""
        mesh.raw_verts, mesh.raw_idxs = read_gstream(self.geometry_stream_file,
                                                     mesh.metadata)

    def _load_scene(self, fpath):
        tree = ET.parse(fpath)
        root = tree.getroot()
        self.data = element_to_dict(root)

    def _render_scene(self):
        """ Render the mesh in the blender view. """
        for obj in self.scene_node_data.iter():
            if obj.Type == 'MESH':
                obj.metadata = self.mesh_metadata.get(obj.Name.upper())
                self.load_mesh(obj)
                self._add_mesh_to_scene(obj)
            elif obj.Type == 'LOCATOR' or obj.Type == 'JOINT':
                self._add_empty_to_scene(obj)
