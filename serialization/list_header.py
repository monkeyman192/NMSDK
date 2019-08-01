import struct


class ListHeader():
    """ Context Manager to handle reading data located somewhere from a pointer
    """
    def __init__(self, fobj):
        self.fobj = fobj
        self.count = 0

    def __enter__(self):
        self.return_location = self.fobj.tell()
        offset, self.count = struct.unpack('<QI', self.fobj.read(0xC))
        self.fobj.seek(self.return_location)
        self.fobj.seek(offset, 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fobj.seek(self.return_location + 0x10)
