from .formats import write_half, write_int_2_10_10_10_rev, ubytes_to_bytes


def serialize_vertex_stream(**kwargs):
    """
    Return a serialized version of the vertex data
    """
    # Store the list of names of the data received
    data_streams = ['verts', 'uvs', 'normals', 'tangents', 'colours']
    fmt_map = {'verts': 0, 'uvs': 0, 'normals': 1, 'tangents': 1, 'colours': 2}
    data = bytearray()
    count = len(kwargs.get('verts', list()))
    if count != 0:
        # Remove any data that isn't actually provided
        for key, value in kwargs.items():
            if isinstance(value, list) and key in fmt_map.keys():
                if len(value) != count:
                    data_streams.remove(key)
            else:
                if key in data_streams:
                    data_streams.remove(key)

        for i in range(count):
            for d in data_streams:
                if fmt_map[d] == 0:
                    for val in kwargs[d][i]:        # probably slow!!
                        data.extend(write_half(val))
                elif fmt_map[d] == 1:
                    data.extend(write_int_2_10_10_10_rev(kwargs[d][i]))
                elif fmt_map[d] == 2:
                    data.extend(ubytes_to_bytes(kwargs[d][i]))
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
