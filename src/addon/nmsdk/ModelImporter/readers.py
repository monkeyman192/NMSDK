import struct
from io import BufferedReader
from typing import NamedTuple

from ..serialization.list_header import ListHeader
from ..serialization.NMS_Structures import NAMEHASH_MAPPING, MBINHeader, TkAnimMetadata, TkMaterialData

# TODO: move to the serialization folder?
from ..serialization.utils import bytes_to_quat, read_string
from ..utils.utils import mxml_to_dict


class gstream_info(NamedTuple):
    vert_size: int
    vert_off: int
    idx_size: int
    idx_off: int
    vert_pos_size: int
    vert_pos_off: int


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
                    x.get('List', {})) for x in desc['Children']]}
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
