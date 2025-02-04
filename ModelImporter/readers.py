from collections import namedtuple
import struct
from typing import Tuple
import os.path as op

# TODO: move to the serialization folder?

from serialization.utils import (read_list_header, read_string, # noqa pylint: disable=relative-beyond-top-level
                                   bytes_to_quat, read_bool, read_uint32,
                                   returned_read)
from serialization.list_header import ListHeader  # noqa pylint: disable=relative-beyond-top-level
from utils.utils import mxml_to_dict  # noqa pylint: disable=relative-beyond-top-level

from serialization.NMS_Structures import TkMaterialData, MBINHeader, NAMEHASH_MAPPING, TkAnimMetadata


gstream_info = namedtuple(
    'gstream_info',
    ['vert_size', 'vert_off', 'idx_size', 'idx_off']
)


def read_anim(fname):  # TODO: FIX!
    """ Reads an anim file. """
    anim_data = dict()

    with open(fname, "rb") as f:
        header = MBINHeader.read(f)
        assert header.header_namehash == NAMEHASH_MAPPING["TkAnimMetadata"]
        return TkAnimMetadata.read(f)

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
    if not op.exists(fname):
        return None
    with open(fname, "rb") as f:
        header = MBINHeader.read(f)
        return TkMaterialData.read(f)


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
        data = mxml_to_dict(f)['List']
    data = read_TkModelDescriptorList(data)
    return data
