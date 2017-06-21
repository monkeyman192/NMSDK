import struct
from binascii import hexlify, unhexlify

null = chr(0)

def fth(f):
    # converts a float value to hex
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])

def hex_flip(h):
    # this takes some hex number that is 8 characters long, and re-arranges them from aa bb cc dd to dd cc bb aa (because NMS...)
    return h[8:] + h[6:8] + h[4:6] + h[2:4]

def to_chr(string):
    # this is a string of hex data
    out_string = ''
    for i in range(0, len(string)-1, 2):
        out_string += bytes((int(string[i: i+2], 16),)).decode("windows-1252")          # bit messy but seems to be needed to get all the characters..
    return out_string

def serialise(x):
    if type(x) == int:
        return to_chr(hexlify(struct.pack('<i', x)))
    elif type(x) == float:
        return to_chr(hexlify(struct.pack('<f', x)))

def pad(string, length):
    # pads the string to the required length with the null character
    return string.ljust(length, null)

def list_header(offset, size):
    # returns the pointer information for the list
    # 0x10 bytes long
    pointer_location = pad(serialise(offset), 0x8)
    pointer_size = to_chr(hexlify(struct.pack('<i', size)))
    end = to_chr('01FEFEFE')            # this will need to be specified potentially
    s = pointer_location + pointer_size + end
    return pointer_location + pointer_size + end

def list_footer(foot):
    # some lists have different things at their ends... this can be used to generate them
    pass
