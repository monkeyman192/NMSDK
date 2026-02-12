# some functions to process the openGL data type INT_2_10_10_10_REV

import struct
import numpy as np

def bytes_to_int_2_10_10_10_rev(bytes_):
    return read_int_2_10_10_10_rev(struct.unpack('<I', bytes_)[0])


def read_int_2_10_10_10_rev(verts: int):
    # this is returns a list of the form [x, y, z, w]
    sel = 0b1111111111
    output = []
    for i in range(3):
        # read the x, y, z components
        output.append(twos_complement((verts & (sel << i*10)) >> i*10, 10))
    # read the w component seperately (don't need sign)
    output.append((verts & (sel << 30)) >> 30)
    # swap x and z components of output
    # output[0], output[2] = output[2], output[0]
    # calculate the norm of the x,y,z components of the array
    norm = (output[0]**2 + output[1]**2 + output[2]**2)**0.5
    # then normalise
    if not norm:
        return [0, 0, 0, 1]
    for i in range(3):
        output[i] = output[i]/norm
    return output


SEL_0 = 0b1111111111
SEL_10 = 0b1111111111 << 10
SEL_20 = 0b1111111111 << 20
MASK = 512


def np_read_int_2_10_10_10_rev(verts):
    """ Optimized version of the code to read the data type.
    The input array will be a row array and this will return a 2D array with 3 rows which will need to be
    flattened later."""
    a = fixed_twos_complement((verts & SEL_0) >> 0)
    b = fixed_twos_complement((verts & SEL_10) >> 10)
    c = fixed_twos_complement((verts & SEL_20) >> 20)
    d = np.vstack([a, b, c])
    # Divide each element by the norm of the values.
    norm = np.linalg.norm(d, axis=0)
    return d / norm[None, :]


def fixed_twos_complement(input_value):
    """Calculates a two's complement integer from the given input value"""
    return -(input_value & MASK) + (input_value & ~MASK)


def twos_complement(input_value, num_bits):
    """Calculates a two's complement integer from the given input value"""
    mask = 2**(num_bits - 1)
    return -(input_value & mask) + (input_value & ~mask)


def write_int_2_10_10_10_rev(verts):
    """
    writes the verts to a INT_2_10_10_10_REV
    verts will come in as the format [x,y,z,w], so need to swap to [z,y,x,w]
    """
    out = 0
    newverts = [0, 0, 0, 1]
    for i in range(3):
        a = int(verts[i]*511)        # maybe floor/ceil is needed??
        # implement a reverse twos compliment to get the signed binary
        # representation
        if abs(a) == a:
            newverts[i] = a
        else:
            newverts[i] = (abs(a) ^ 0b1111111111) + 1

    for i in range(4):
        out = out | (newverts[i] << i*10)
    return struct.pack('<I', out)
