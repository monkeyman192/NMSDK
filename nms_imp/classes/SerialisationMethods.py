from struct import pack, unpack
from binascii import hexlify, unhexlify

null = chr(0)

def fth(f):
    # converts a float value to hex
    return hex(unpack('<I', pack('<f', f))[0])

def to_chr(string):
    # this is a string of hex data
    out_string = ''
    for i in range(0, len(string)-1, 2):
        out_string += bytes((int(string[i: i+2], 16),)).decode("windows-1252")          # bit messy but seems to be needed to get all the characters..
    return out_string

def serialise(x):
    if type(x) == bytes:
        # in this case it is already sorted are ready to write
        return x
    elif type(x) == int:
        return pack('<i', x)
    elif type(x) == float:
        return pack('<f', x)
    else:
        # in this case just call bytes(~) on the object and hope we get something useful.
        # this should work because we can give custom classes a __bytes__ class method so that it returns the goods!
        return bytes(x)

def pad(input_data, length):
    data = bytearray()
    if isinstance(input_data, str):
        data.extend(pack('{}s'.format(length), string))
    elif isinstance(input_data, bytes):
        data.extend(input_data)
        data.extend(pack('{}s'.format(length - len(input_data)), b''))
    # pads the string to the required length with the null character
    return data

def list_header(offset, size, end):
    # returns the pointer information for the list
    # 0x10 bytes long
    data = bytearray()
    pointer_location = pad(serialise(offset), 0x8)
    data.extend(pointer_location)
    pointer_size = pack('<i', size)
    data.extend(pointer_size)
    data.extend(end)        # assume this is already a bytes object
    return data

def list_footer(foot):
    # some lists have different things at their ends... this can be used to generate them
    pass

#print(hexlify(pack('<f', 0.125)))
