from io import BufferedReader
from struct import pack, unpack
from math import sqrt


def float_to_hex(num):
    """ Convert a hex value to float. """
    return hex(unpack('<I', pack('<f', num))[0])


# TODO: Rename
def list_header(offset, size, end=b'\x01\x00\x00\x00'):
    """ Generate the list header.

    Parameters
    ----------
    offset : int
        Relative offset from the location the header will be placed.
    size : int
        Size in bytes of the block of information.
    end : bytes
        End 4 bytes of padding.

    Returns
    -------
    data : bytearray
        0x10 bytes of data representing the list header in memory.
    """
    data = bytearray()
    if size != 0:
        data.extend(pack('<Q', offset))
    else:
        data.extend(pack('Q', 0))
    data.extend(pack('<I', size))
    if isinstance(end, int):
        data.extend(pack('<I', end))
    else:
        data.extend(end)
    return data


def pad(input_data, length, pad_char=b'\x00', null_terminated=False):
    """ Pads a string to the required length with the null character.

    Parameters
    ----------
    input_data : string, bytes
        Input string.
    length : int
        Required length.
    pad_char : byte
        Byte used as the padding character.
    null_terminated : bool (optional)
        Whether or not to null-terminate the string
    Returns
    -------
    data : bytes
    """
    str_len = len(input_data)
    if not isinstance(input_data, bytes):
        input_data = bytes(input_data, 'utf-8')
    if null_terminated:
        return (input_data + b'\x00' + pad_char * (length - 2 - str_len) +
                b'\x00')
    else:

        return input_data + (length - str_len) * pad_char


def to_chr(string):
    # this is a string of hex data
    out_string = ''
    for i in range(0, len(string) - 1, 2):
        # bit messy but seems to be needed to get all the characters..
        out_string += bytes((int(string[i: i + 2], 16),)).decode(
            "windows-1252"
        )
    return out_string


# TODO: move the quaternion functions to a separate file as its own format
def quat_drop_component(arr):
    """ Determine which component of the quaternion to drop. """
    max_loc = 0
    doubled_elements = set()
    condensed_arr = set()
    for i in arr:
        if i in condensed_arr:
            doubled_elements.add(i)
        condensed_arr.add(i)

    if len(condensed_arr) == 4:
        max_loc = arr.index(max(condensed_arr))
    else:
        if 0x3FFF not in doubled_elements:
            max_loc = 0
        else:
            max_loc = arr.index(max(condensed_arr))
    return max_loc


def bytes_to_quat(data):
    """ Reads a byte array to a quaternion. """
    c_x, c_y, c_z = unpack('<HHH', data.read(0x6))
    # Get most significant bit
    i_x = c_x >> 0xF
    i_y = c_y >> 0xF
    # Determine which component was dropped
    dropcomponent = (i_x << 1 | i_y << 0)
    # Strip most significant bit
    c_x = c_x & 0x7FFF
    c_y = c_y & 0x7FFF
    c_z = c_z & 0x7FFF
    # generate quaternion components
    q_x = (c_x - 0x3FFF) * (1 / 0x3FFF) * (1 / sqrt(2))
    q_y = (c_y - 0x3FFF) * (1 / 0x3FFF) * (1 / sqrt(2))
    q_z = (c_z - 0x3FFF) * (1 / 0x3FFF) * (1 / sqrt(2))
    q_w = sqrt(max(0, 1 - q_x ** 2 - q_y ** 2 - q_z ** 2))
    # Return quaternion in the correct order depending on drop component
    if dropcomponent == 0:
        return (q_x, q_y, q_z, q_w)
    if dropcomponent == 1:
        return (q_x, q_y, q_w, q_z)
    if dropcomponent == 2:
        return (q_x, q_w, q_y, q_z)
    if dropcomponent == 3:
        return (q_w, q_x, q_y, q_z)
    # Default return case in case something goes wrong...
    return (0, 0, 0, 0)


def quat_to_hex(q):
    """ converts a quaternion to its hexadecimal representation """
    q = [int(0x3FFF * (sqrt(2) * i + 1)) for i in q]
    drop_index = quat_drop_component(q)
    del q[drop_index]
    drop_index = 3 - drop_index
    i_x = drop_index >> 1
    i_y = drop_index & 1

    q[0] = (i_x << 0xF) + q[0]
    q[1] = (i_y << 0xF) + q[1]

    return [hex(i) for i in q]


def read_list_data(data, element_size):
    return_data = []
    offset, count = read_list_header(data)
    init_loc = data.tell()
    data.seek(offset, 1)
    for _ in range(count):
        return_data.append(data.read(element_size))
    data.seek(init_loc, 0)
    return return_data


def read_list_header(data, return_to_start=True):
    """
    Takes the 0x10 byte header and returns the relative offset and
    number of entries

    Parameters
    ----------
    return_to_start : bool
        Whether to return the data objects' pointer back to the start of the
        list header or not.
    """
    offset, count = unpack('<QI', data.read(0xC))
    if return_to_start:
        data.seek(-0xC, 1)
    else:
        data.seek(0x4, 1)
    return offset, count


def returned_read(buff: BufferedReader, fmt: str, size: int, offset: int = 0):
    orig_pos = buff.tell()
    buff.seek(offset, 1)
    data = unpack(fmt, buff.read(size))
    buff.seek(orig_pos)
    return data


def read_string(data: BufferedReader, length: int, offset: int = 0,
                return_to_start: bool = False) -> str:
    """ Read a null terminated string. """
    orig_pos = data.tell()
    data.seek(offset, 1)
    fmt = str(length) + 's'
    string: bytes = unpack(fmt, data.read(length))[0].split(b'\x00')[0]
    ret = string.decode()
    if return_to_start:
        data.seek(orig_pos)
    return ret


def read_uint32(data: BufferedReader, offset: int = 0, return_to_start: bool = True):
    orig_pos = data.tell()
    data.seek(offset, 1)
    val = unpack("<I", data.read(4))[0]
    if return_to_start:
        data.seek(orig_pos)
    return val


def read_bool(data: BufferedReader, offset: int = 0, return_to_start: bool = False):
    """ Read a single boolean value. """
    orig_pos = data.tell()
    data.seek(offset, 1)
    val = unpack('?', data.read(1))[0]
    if return_to_start:
        data.seek(orig_pos)
    return val


def serialize(x, fmt=None):
    """ Generic serialization function. Attempts to return the bytes
    representation of the object. """
    if fmt is not None:
        # If a specific format string is passed in, use it.
        return pack(fmt, x)
    if isinstance(x, bytes):
        # in this case it is already sorted are ready to write
        return x
    elif isinstance(x, int):
        return pack('<i', x)
    elif isinstance(x, float):
        return pack('<f', x)
    else:
        # in this case just call bytes(~) on the object and hope we get
        # something useful.
        # this should work because we can give custom classes a __bytes__ class
        # method so that it returns the goods!
        return bytes(x)


if __name__ == "__main__":
    from io import BytesIO
    b = BytesIO(b'\xFF\x3F\xFF\x3F\xFF\x3F')
    print(bytes_to_quat(b))
