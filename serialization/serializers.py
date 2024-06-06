from typing import List

from NMS.LOOKUPS import SERIALIZE_FMT_MAP, REV_SEMANTICS
from serialization.formats import write_half, write_int_2_10_10_10_rev, ubytes_to_bytes


def serialize_vertex_stream(requires: List[str], **kwargs):
    """
    Return a serialized version of the vertex data

    Parameters
    ----------
    requires
        A list of required data streams. This will be pre-determined from the
        entire file so that we don't end up having the stream for one mesh not
        include something.
    """
    data = bytearray()
    count = len(kwargs.get('Vertices', list()))
    if count != 0:
        for i in range(count):
            for stream_type in requires:
                stream_name = REV_SEMANTICS[stream_type]
                if SERIALIZE_FMT_MAP[stream_type] == 0:
                    for val in kwargs[stream_name][i]:        # probably slow!!
                        data.extend(write_half(val))
                elif SERIALIZE_FMT_MAP[stream_type] == 1:
                    data.extend(write_int_2_10_10_10_rev(kwargs[stream_name][i]))
                elif SERIALIZE_FMT_MAP[stream_type] == 2:
                    data.extend(ubytes_to_bytes(kwargs[stream_name][i]))
        return data
    else:
        # return empty data
        return b''


def serialize_index_stream(indexes):
    """
    Return a serialized version of the index data
    """
    return indexes.tobytes()


if __name__ == "__main__":
    # TODO: move to tests
    from array import array
    d = array('I')
    d.extend([1, 2, 3, 4, 5, 735536])
    print(d.tobytes())
    a = serialize_index_stream(d)
    print(a)
