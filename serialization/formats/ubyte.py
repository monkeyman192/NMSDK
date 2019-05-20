import struct


def bytes_to_ubyte(bytes_):
    """ Read an array of bytes into a list of unsigned bytes. """
    fmt = '<' + 'B' * len(bytes_)
    data = struct.unpack(fmt, bytes_)
    return [int(n) for n in data]


def ubytes_to_bytes(lst, target_length):
    """ Read a list of numbers in the range [0, 255] and generate a byte
    array

    Parameters
    ----------
    lst : list
        List of integers to convert
    target_length : int
        Target length of the byte array.
        If the length of the provided list is shorter than this then the
        resultant array is padded with \x00's up to this length.

    Returns
    -------
    arr : bytearray
    """
    if target_length < len(lst):
        raise ValueError('Target length must be equal to or greater than '
                         'input list length.')
    else:
        fmt = '<' + 'B' * target_length
        extra_zeros = target_length - len(lst)
    # Add any extra zeros
    lst.extend([0] * extra_zeros)
    return struct.pack(fmt, *lst)
