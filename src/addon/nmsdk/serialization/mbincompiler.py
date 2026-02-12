__author__ = "monkeyman192"
__version__ = "0.5"

from .utils import serialize, pad


class mbinCompiler():
    def __init__(self, NMSstruct, out_name):
        # this is the struct containing all the data that needs to be
        # serialized
        self.struct = NMSstruct
        self.out_name = out_name
        self.output = open('{}'.format(out_name), 'wb')

    def header(self):
        data = bytearray()
        # return the header bytes (0x60 long)
        data.extend(b'\xDD\xDD\xDD\xDD')                                # magic
        data.extend(serialize(2500))                                  # version
        data.extend(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF')    # 0x8 bytes of 0xFF
        if hasattr(self.struct, 'GUID'):
            data.extend(serialize(self.struct.GUID, '<Q'))        # Actual GUID
        else:
            data.extend(b'CSTMGEOM')                        # custom name thing
        template_name = 'c' + '{}'.format(self.struct.name)
        data.extend(pad(template_name.encode('utf-8'), 0x40))     # struct name
        data.extend(b'\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE')
        return data

    def serialize(self):
        # this is the workhorse function.
        # we will keep track of the current location and also the current
        # expected final location
        # so that list data can be placed there
        with open(self.out_name, 'wb') as f:
            f.write(self.header())
            self.struct.serialize(f)


class ListWorker():
    def __init__(self, initial_state=(0x60, 0x60)):
        self.curr = initial_state[0]
        self.end = initial_state[1]
        # a list containing queued data that will be serialized once the main
        # struct is done
        self.dataQ = []

    def __call__(self):
        return (self.curr, self.end)

    def __setitem__(self, key, item):
        # only allow keys that are currently in the dict to be set
        if key in self.__dict__:
            self.__dict__[key] = item

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            raise KeyError


# TODO: redo as tests
if __name__ == "__main__":
    from NMS.classes import TkPhysicsComponentData

    pd = TkPhysicsComponentData()
    mbinc = mbinCompiler(pd, 'newmbin')
    mbinc.serialize()
