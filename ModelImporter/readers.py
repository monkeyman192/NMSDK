from collections import namedtuple
from contextvars import ContextVar
import struct
from typing import Tuple

# TODO: move to the serialization folder?

from ..serialization.utils import (read_list_header, read_string, # noqa pylint: disable=relative-beyond-top-level
                                   bytes_to_quat, read_bool, read_uint32,
                                   returned_read)
from ..serialization.list_header import ListHeader  # noqa pylint: disable=relative-beyond-top-level
from ..NMS.LOOKUPS import VersionedOffsets
from ..utils.utils import exml_to_dict  # noqa pylint: disable=relative-beyond-top-level


# gstream_info = namedtuple(
#     'gstream_info',
#     ['vert_size', 'vert_off', 'idx_size', 'idx_off', 'dbl_buff']
# )
gstream_info = namedtuple(
    'gstream_info',
    ['vert_size', 'vert_off', 'idx_size', 'idx_off']
)


ctx_geom_guid: ContextVar[int] = ContextVar(
    "GeometryGUID",
    default=0x7E2C6C00A113D11F,
)


def read_anim(fname):  # TODO: FIX!
    """ Reads an anim file. """
    anim_data = dict()

    with open(fname, 'rb') as f:
        f.seek(0x60)
        # get the counts and offsets of all the info
        frame_count, node_count = struct.unpack('<II', f.read(0x8))
        anim_data['FrameCount'] = frame_count
        anim_data['NodeCount'] = node_count
        anim_data['NodeData'] = list()
        # NodeData
        with ListHeader(f) as node_data:
            for _ in range(node_data.count):
                node_name = read_string(f, 0x40)
                # Skip 'can_compress'
                f.seek(0x4, 1)
                rot_index, trans_index, scale_index = struct.unpack(
                    '<III', f.read(0xC))
                data = {'Node': node_name,
                        'RotIndex': rot_index,
                        'TransIndex': trans_index,
                        'ScaleIndex': scale_index}
                anim_data['NodeData'].append(data)
        # AnimFrameData
        anim_data['AnimFrameData'] = list()
        with ListHeader(f) as anim_frame_data:
            for _ in range(anim_frame_data.count):
                frame_data = dict()
                with ListHeader(f) as rot_data:
                    rot_data_lst = list()
                    for _ in range(int(rot_data.count // 3)):
                        rot_data_lst.append(bytes_to_quat(f))
                    frame_data['Rotation'] = rot_data_lst  # reads 0x6 bytes
                with ListHeader(f) as trans_data:
                    trans_data_lst = list()
                    for _ in range(trans_data.count):
                        trans_data_lst.append(
                            struct.unpack('<ffff', f.read(0x10)))
                    frame_data['Translation'] = trans_data_lst
                with ListHeader(f) as scale_data:
                    scale_data_lst = list()
                    for _ in range(scale_data.count):
                        scale_data_lst.append(
                            struct.unpack('<ffff', f.read(0x10)))
                    frame_data['Scale'] = scale_data_lst
                anim_data['AnimFrameData'].append(frame_data)
        # StillFrameData
        still_frame_data = dict()
        with ListHeader(f) as rot_data:
            rot_data_lst = list()
            for _ in range(int(rot_data.count // 3)):
                rot_data_lst.append(bytes_to_quat(f))  # reads 0x6 bytes
            still_frame_data['Rotation'] = rot_data_lst
        with ListHeader(f) as trans_data:
            trans_data_lst = list()
            for _ in range(trans_data.count):
                trans_data_lst.append(
                    struct.unpack('<ffff', f.read(0x10)))
            still_frame_data['Translation'] = trans_data_lst
        with ListHeader(f) as scale_data:
            scale_data_lst = list()
            for _ in range(scale_data.count):
                scale_data_lst.append(
                    struct.unpack('<ffff', f.read(0x10)))
            still_frame_data['Scale'] = scale_data_lst
        anim_data['StillFrameData'] = still_frame_data

        return anim_data


def read_entity_animation_data(fname: str) -> dict:  # TODO: Fix
    """ Read an entity file.

    This will currently only support reading the animation data from the
    entity file as it's all we care about right now...

    Returns
    -------
    anim_data
        List of dictionaries containing the path and name of the contained
        animation data.
    """

    anim_data = dict()
    with open(fname, 'rb') as f:
        f.seek(0x60)
        has_anims = False
        # Scan the list of components to see if we have a
        # TkAnimationComponentData struct present.
        with ListHeader(f) as components:
            for _ in range(components.count):
                return_offset = f.tell()
                offset = struct.unpack('<Q', f.read(0x8))[0]
                struct_name = read_string(f, 0x40)
                if struct_name == 'cTkAnimationComponentData':
                    has_anims = True
                    break
                # Read the nameHash but ignore it...
                f.read(0x8)
        # If no animation data is found, return.
        if not has_anims:
            return anim_data
        # Jump to the start of the struct
        f.seek(return_offset + offset)
        _anim_data = read_TkAnimationData(f)
        idle_anim_name = _anim_data.pop('Anim') or 'IDLE'
        anim_data[idle_anim_name] = _anim_data
        with ListHeader(f) as anims:
            for _ in range(anims.count):
                _anim_data = read_TkAnimationData(f)
                anim_data[_anim_data.pop('Anim')] = _anim_data
        return anim_data


def read_material(fname):
    """ Reads the textures and types from a material file.

    Returns
    -------
    data : dict
        Mapping between the texture type (one of DIFFUSE, MASKS, NORMAL) and
        the path to the texture
    """
    data = dict()

    # Read the data directly from the mbin
    with open(fname, 'rb') as f:
        f.seek(0x10)
        guid = struct.unpack("<Q", f.read(0x8))[0]
        ofs = VersionedOffsets.TkMaterialData[guid]
        sample_ofs = VersionedOffsets.TkMaterialSampler[guid]
        uniform_ofs = VersionedOffsets.TkMaterialUniform[guid]
        f.seek(0x60)
        # get name
        data["Name"] = read_string(f, 0x80, ofs["Name"], True)
        # get metamaterial, introduced in 2.61
        data["Metamaterial"] = read_string(f, 0x100, ofs["Metamaterial"], True)
        # get class
        data['Class'] = read_string(f, 0x20, ofs["Class"], True)
        # get whether it casts a shadow
        data['CastShadow'] = read_bool(f, ofs["CastShadow"], True)
        # save pointer for Flags Uniforms Samplers list headers
        # get material flags
        data['Flags'] = list()
        f.seek(0x60 + ofs["Flags"])
        list_offset, list_count = read_list_header(f)
        f.seek(list_offset, 1)
        for i in range(list_count):
            data['Flags'].append(struct.unpack('<I', f.read(0x4))[0])
        # get uniforms
        data['Uniforms'] = dict()
        f.seek(0x60 + ofs["Uniforms"])
        list_offset, list_count = read_list_header(f)
        f.seek(list_offset, 1)
        for _ in range(list_count):
            name = read_string(f, 0x20, uniform_ofs["Name"], True)
            value = returned_read(f, "<ffff", 0x10, uniform_ofs["Values"])
            data['Uniforms'][name] = value
            f.seek(uniform_ofs["_size"], 1)
        # get samplers (texture paths)
        data['Samplers'] = dict()
        f.seek(0x60 + ofs["Samplers"])
        list_offset, list_count = read_list_header(f)
        f.seek(list_offset, 1)
        for i in range(list_count):
            name = read_string(f, 0x20, sample_ofs["Name"], True)
            data['Samplers'][name] = read_string(f, 0x80, sample_ofs["Map"], True)
            if i != list_count - 1:
                f.seek(sample_ofs["_size"], 1)

    return data


def read_mesh_binding_data(fname):
    """ Read the data relating to mesh/joint bindings from the geometry file.

    Returns
    -------
    data : dict
        All the relevant data from the geometry file
    """
    geometry_offsets = VersionedOffsets.TkGeometryData[ctx_geom_guid.get()]
    data = dict()
    with open(fname, 'rb') as f:
        # First, check that there is data to read. If not, then return nothing
        f.seek(0x60 + geometry_offsets['JointBindings'] + 0x8)
        if struct.unpack('<I', f.read(0x4))[0] == 0:
            return
        # Read joint binding data
        f.seek(0x60 + geometry_offsets['JointBindings'])
        jo = VersionedOffsets.TkJointBindingData[ctx_geom_guid.get()]
        data['JointBindings'] = list()
        with ListHeader(f) as JointBindings:
            for _ in range(JointBindings.count):
                jb_data = dict()
                jb_data['InvBindMatrix'] = returned_read(f, '<' + 'f' * 0x10, 0x40, jo['InvBindMatrix'])
                jb_data['BindTranslate'] = returned_read(f, '<fff', 0xC, jo['BindTranslate'])
                jb_data['BindRotate'] = returned_read(f, '<ffff', 0x10, jo['BindRotate'])
                jb_data['BindScale'] = returned_read(f, '<fff', 0xC, jo['BindScale'])
                data['JointBindings'].append(jb_data)
                f.seek(jo['_size'])
        # skip to the skin matrix layout data
        f.seek(0x60 + geometry_offsets['SkinMatrixLayout'])
        with ListHeader(f) as SkinMatrixLayout:
            fmt = '<' + 'I' * SkinMatrixLayout.count
            data_size = 4 * SkinMatrixLayout.count
            data['SkinMatrixLayout'] = struct.unpack(fmt, f.read(data_size))

        # skip to the MeshBaseSkinMat data
        f.seek(0x60 + geometry_offsets['MeshBaseSkinMat'])
        with ListHeader(f) as MeshBaseSkinMat:
            fmt = '<' + 'I' * MeshBaseSkinMat.count
            data_size = 4 * MeshBaseSkinMat.count
            data['MeshBaseSkinMat'] = struct.unpack(fmt, f.read(data_size))

    return data


def read_metadata(fname):
    """ Reads all the metadata from the gstream file.

    Returns
    -------
    data : dict (str: namedtuple)
        Mapping between the names of the meshes and their metadata
    """
    data: dict[str, list[gstream_info]] = dict()
    with open(fname, 'rb') as f:
        # Let's get the GUID to see what version we are looking at.
        f.seek(0x10)
        guid = struct.unpack('<Q', f.read(0x8))[0]
        ctx_geom_guid.set(guid)
        # Let's check what it is. The current is 0x7E2C6C00A113D11F
        # Ones before this we will consider "old format".
        geometry_offsets = VersionedOffsets.TkGeometryData[ctx_geom_guid.get()]
        rel_offset = geometry_offsets["StreamMetaDataArray"]
        # move to the start of the StreamMetaDataArray header
        f.seek(0x60 + rel_offset)
        TkMeshMetaData_offsets = VersionedOffsets.TkMeshMetaData[ctx_geom_guid.get()]
        # find how far to jump
        list_offset, list_count = read_list_header(f)
        f.seek(list_offset, 1)
        for _ in range(list_count):
            # read the ID in and strip it to be just the string and no padding.
            string = read_string(
                f, 0x80, TkMeshMetaData_offsets["IdString"], True
            ).upper()
            # read in the actual data we want
            VertexDataSize = read_uint32(f, TkMeshMetaData_offsets["VertexDataSize"])
            VertexDataOffset = read_uint32(f, TkMeshMetaData_offsets["VertexDataOffset"])
            IndexDataSize = read_uint32(f, TkMeshMetaData_offsets["IndexDataSize"])
            IndexDataOffset = read_uint32(f, TkMeshMetaData_offsets["IndexDataOffset"])
            # DoubleBufferGeometry = read_bool(f, TkMeshMetaData_offsets["DoubleBufferGeometry"], True)
            gstream_info_ = gstream_info(VertexDataSize, VertexDataOffset, IndexDataSize, IndexDataOffset)
            if string not in data:
                data[string] = gstream_info_
            else:
                data[string] = [data[string]]
                data[string].append(gstream_info_)
            # Seek to the end of the chunk.
            f.seek(TkMeshMetaData_offsets["_size"], 1)
    return data


def read_gstream(fname: str, info: namedtuple) -> Tuple[bytes, bytes]:
    """ Read the requested info from the gstream file.

    Parameters
    ----------
    fname
        File path to the ~.GEOMETRY.DATA.MBIN.PC file.
    info
        namedtupled containing the vertex sizes and offset, and index sizes and
        offsets.

    Returns
    -------
    verts
        Raw vertex data.
    indexes
        Raw index data.
    """
    with open(fname, 'rb') as f:
        f.seek(info.vert_off)
        verts = f.read(info.vert_size)
        f.seek(info.idx_off)
        indexes = f.read(info.idx_size)
    return verts, indexes


def read_TkAnimationData(f) -> dict:
    """ Extract the animation name and path from the entity file. """
    data = dict()
    data['Anim'] = read_string(f, 0x10)
    data['Filename'] = read_string(f, 0x80)
    # Move the pointer to the end of the TkAnimationComponentData struct
    f.seek(0xA8, 1)
    return data


def read_TkModelDescriptorList(data: dict) -> dict:
    """ Take a dictionary of the model descriptor data and extract recursively
    just the useful info. """
    ret_data = dict()
    for d in data:
        desc_data = []
        for desc in d['Descriptors']:
            sub_desc_data = {
                'Id': desc['Id'],
                'Name': desc['Name'],
                'ReferencePaths': desc['ReferencePaths'],
                'Children': [read_TkModelDescriptorList(
                    x['List']) for x in desc['Children']]}
            desc_data.append(sub_desc_data)
        ret_data[d['TypeId']] = desc_data
    return ret_data


def read_descriptor(fname: str) -> dict:
    """ Take a file path to a descriptor and process it, returning a dict
    containing the necessary data.

    Parameters
    ----------
    fname
        Full path to the descriptor file to be parsed.

    Returns
    -------
    data
        A dictionary with the required data.
    """
    with open(fname) as f:
        # The top level is always a list, let's just extract it immediately.
        data = exml_to_dict(f)['List']
    data = read_TkModelDescriptorList(data)
    return data
