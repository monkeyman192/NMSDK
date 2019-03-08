# stdlib imports
import os.path as op
import xml.etree.ElementTree as ET
import struct
from collections import namedtuple
from math import radians

# Blender imports
import bpy, bmesh
from mathutils import Matrix

# Internal imports
from serialization.formats import bytes_to_half, bytes_to_int_2_10_10_10_rev
from serialization.utils import read_list_header
from NMS.LOOKUPS import VERTS

VERT_TYPE_MAP = {5131: {'size': 2, 'func': bytes_to_half},
                 36255: {'size': 1, 'func': bytes_to_int_2_10_10_10_rev}}


class ImportScene():
    """ Load a scene into blender.

    Parameters
    ----------
    fpath : string
        filepath to the scene file to be loaded.
    """
    def __init__(self, fpath):
        ext = op.splitext(fpath)[1]
        if ext.lower() == '.mbin':
            print('convert to exml...')
        elif ext.lower() != '.exml':
            raise TypeError('Selected file is of the wrong format.')
        self.data = None
        self.vertex_elements = list()
        self.bh_data = list()
        self.scn = bpy.context.scene
        # we now have the fpath as an exml...
        self._load_scene(fpath)
        if self.data is None:
            raise ValueError('Cannot load scene file...')
        self.scene_node_data = SceneNodeData(self.data)
        self.local_directory = op.dirname(fpath)
        self.directory = op.dirname(self.scene_node_data.Name)
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

        # get a dictionary look up of all the meshes
        self.meshes = recurse_scene_node(self.scene_node_data)
        # give them their metadata also
        metadata = read_metadata(self.geometry_file)
        for key, value in metadata.items():
            for mesh in self.meshes.values():
                if mesh.Name.upper() == key.upper():
                    mesh.metadata = value

        for key in self.meshes.keys():
            self.load_mesh(key)
        self._add_meshes_to_view()

        self.state = 'FINISHED'

# region public methods

    def load_mesh(self, ID):
        """ Load the mesh.
        This will load the mesh data into memory then deserialize the actual
        vertex and index data from the gstream mbin.
        """
        self._load_mesh(ID)
        self._deserialize_vertex_data(ID)
        self._deserialize_index_data(ID)
        self.meshes[ID]._generate_geometry()
        self.meshes[ID]._generate_bounded_hull(self.bh_data)

# region private methods

    def _add_meshes_to_view(self):
        """ Add all the attached meshes to the blender view. """
        for name, scene_node in self.meshes.items():
            # create main mesh object
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(scene_node.verts[VERTS],
                             scene_node.edges,
                             scene_node.faces)
            print(scene_node.verts[1])
            bm = bmesh.new()
            bm.from_mesh(mesh)
            mesh_obj = bpy.data.objects.new(name, mesh)
            rot_matrix = Matrix.Rotation(radians(90), 4, 'X')
            transform = scene_node.Transform['Trans']
            mesh_obj.location = transform
            rotation = scene_node.Transform['Rot']
            mesh_obj.rotation_euler = rotation
            scale = scene_node.Transform['Scale']
            mesh_obj.scale = scale
            mesh_obj.matrix_world = rot_matrix*mesh_obj.matrix_local
            self.scn.objects.link(mesh_obj)

            # create child object for bounded hull
            name = 'BH' + name
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydata(scene_node.bounded_hull, [], [])
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bh_obj = bpy.data.objects.new(name, mesh)
            bh_obj.parent = mesh_obj
            self.scn.objects.link(bh_obj)

    def _deserialize_index_data(self, ID):
        """ Take the raw vertex data and generate a list of actual vertex data.

        Parameters
        ----------
        ID : str
            id of the mesh to deserialize
        """
        mesh = self.meshes[ID]
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

    def _deserialize_vertex_data(self, ID):
        """ Take the raw vertex data and generate a list of actual vertex data.

        Parameters
        ----------
        ID : str
            id of the mesh to deserialize
        """
        mesh = self.meshes[ID]
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

    def _load_bounded_hulls(self):
        with open(self.geometry_file, 'rb') as f:
            f.seek(0x130)
            list_offset, list_count = read_list_header(f)
            f.seek(list_offset, 1)
            for _ in range(list_count):
                self.bh_data.append(struct.unpack('<fff', f.read(0xC)))
                # Skip 't' component.
                f.seek(0x4, 1)

    def _load_mesh(self, ID):
        """ Load the mesh data from the geometry stream file."""
        mesh = self.meshes[ID]
        mesh.raw_verts, mesh.raw_idxs = read_gstream(self.geometry_stream_file,
                                                     mesh.metadata)

    def _load_scene(self, fpath):
        tree = ET.parse(fpath)
        root = tree.getroot()
        self.data = element_to_dict(root)

    def _render_mesh(self, ID):
        """ Render the mesh in the blender view. """
        pass


class SceneNodeData():
    def __init__(self, info):
        self.info = info
        self.verts = dict()
        self.idxs = list()
        self.bounded_hull = None
        # The metadata will be read from the geometry file later.
        self.metadata = None
        self.children = list()
        children = self.info.pop('Children')
        for child in children:
            self.children.append(SceneNodeData(child))

    def _generate_bounded_hull(self, bh_data):
        self.bounded_hull = bh_data[int(self.Attribute('BOUNDHULLST')):
                                    int(self.Attribute('BOUNDHULLED'))]

    def _generate_geometry(self):
        """ Generate the faces and edge data. """
        if len(self.idxs) == 0 or len(self.verts.keys()) == 0:
            raise ValueError('Something has gone wrong!!!')
        self.faces = list(zip(self.idxs[0::3],
                              self.idxs[1::3],
                              self.idxs[2::3]))
        self.edges = list()
        for face in self.faces:
            edges = [(face[0], face[1]),
                     (face[1], face[2]),
                     (face[2], face[0])]
            self.edges.extend(edges)

    @property
    def Name(self):
        return self.info['Name']

    @property
    def Transform(self):
        trans = (float(self.info['Transform']['TransX']),
                 float(self.info['Transform']['TransY']),
                 float(self.info['Transform']['TransZ']))
        rot = (float(self.info['Transform']['RotX']),
               float(self.info['Transform']['RotY']),
               float(self.info['Transform']['RotZ']))
        scale = (float(self.info['Transform']['ScaleX']),
                 float(self.info['Transform']['ScaleY']),
                 float(self.info['Transform']['ScaleZ']))
        return {'Trans': trans, 'Rot': rot, 'Scale': scale}

    @property
    def Type(self):
        return self.info['Type']

    def Attribute(self, name):
        # Doesn't support AltID's
        for attrib in self.info['Attributes']:
            if attrib['Name'] == name:
                return attrib['Value']


def element_to_dict(node):
    """ Converts an element obect to a dictionary. """
    data = dict()
    for elem in list(node):
        # determine what the value is.
        # If there is no value then we have a list:
        if elem.get('value') is None:
            lst = list()
            for e in list(elem):
                lst.append(element_to_dict(e))
            data[elem.get('name')] = lst
        elif '.xml' in elem.get('value'):
            # In this case we are loading a sub-struct.
            # Apply this function recursively.
            data[elem.get('name')] = element_to_dict(elem)
        else:
            # It's just a value.
            data[elem.get('name')] = elem.get('value')
    return data


def read_metadata(fname):
    data = dict()
    with open(fname, 'rb') as f:
        # move to the start of the StreamMetaDataArray header
        f.seek(0x190)
        # find how far to jump
        list_offset, List_count = read_list_header(f)
        f.seek(list_offset, 1)
        for _ in range(List_count):
            # read the ID in and strip it to be just the string and no padding.
            string = struct.unpack('128s', f.read(0x80))[0].split(b'\x00')[0]
            string = string.decode()
            # skip the hash
            f.seek(0x8, 1)
            # read in the actual data we want
            vert_size, vert_off, idx_size, idx_off = struct.unpack(
                '<IIII',
                f.read(0x10))
            gstream_info = namedtuple('gstream_info',
                                      ['vert_size', 'vert_off',
                                       'idx_size', 'idx_off'])
            data[string] = gstream_info(vert_size, vert_off, idx_size, idx_off)
    return data


def read_gstream(fname, info):
    """ Read the requested info from the gstream file.

    Parameters
    ----------
    fname : string
        File path to the ~.GEOMETRY.DATA.MBIN.PC file.
    info : namedtuple
        namedtupled containing the vertex sizes and offset, and index sizes and
        offsets.

    Returns
    -------
    verts : bytes
        Raw vertex data.
    indexes : bytes
        Raw index data.
    """
    with open(fname, 'rb') as f:
        f.seek(info.vert_off)
        verts = f.read(info.vert_size)
        f.seek(info.idx_off)
        indexes = f.read(info.idx_size)
    return verts, indexes


def recurse_scene_node(node):
    # TODO: make more general if needed?
    mesh_nodes = dict()
    for child in node.children:
        if child.Type == 'MESH':
            mesh_nodes[child.Name] = child
        mesh_nodes.update(recurse_scene_node(child))
    return mesh_nodes
