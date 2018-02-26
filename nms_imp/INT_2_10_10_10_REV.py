# some functions to process the openGL data type INT_2_10_10_10_REV

import struct

def read(verts):
    # this is returns a list of the form [x, y, z, w]
    sel = 0b1111111111
    output = []
    for i in range(3):
        print((verts & (sel << i*10)) >> i*10, 10)
        output.append(twos_complement((verts & (sel << i*10)) >> i*10, 10))     # read the x, y, z components
    output.append((verts & (sel << 30)) >> 30)                                  # read the w component seperately (don't need sign)
    output[0], output[2] = output[2], output[0]                                 # swap x and z components of output
    norm = (output[0]**2 + output[1]**2 + output[2]**2)**0.5                    # calculate the norm of the x,y,z components of the array
    for i in range(3):
        output[i] = output[i]/norm                                              # then normalise
    return output

def twos_complement(input_value, num_bits):
    '''Calculates a two's complement integer from the given input value's bits'''
    mask = 2**(num_bits - 1)
    return -(input_value & mask) + (input_value & ~mask)

"""def bin_to_signed_int(b):
    # this will take a binary number and return the signed int of it
    sgn = b >> 9    # this the most significant bit
    if sgn == 1:"""
        

def write(verts):
    # writes the verts to a INT_2_10_10_10_REV
    # verts will come in as the format [x,y,z,w], so need to swap to [z,y,x,w]
    out = 0
    for i in range(3):
        a = int(verts[i]*511)        # maybe floor/ceil is needed??
        # implement a reverse twos compliment to get the signed binary representation
        if abs(a) == a:
            verts[i] = a
        else:
            verts[i] = (abs(a) ^ 0b1111111111) +1

    verts[0], verts[2] = verts[2], verts[0]                 # flip the x and z

    for i in range(4):
        out = out | (verts[i] << i*10)
    return struct.pack('<I', out)
    

if __name__ == "__main__":
    data = read(0x5EF00382)
    print(data)
    print(write(data))
