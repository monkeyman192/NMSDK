__author__ = "monkeyman192"
__version__ = "0.5"


# local imports
from classes import *

# needed for misc functions
from struct import pack, unpack
from binascii import hexlify, unhexlify
#import xml.etree.ElementTree as ET

class mbinCompiler():
    def __init__(self, NMSstruct, out_name):
        self.struct = NMSstruct         # this is the struct containing all the data that needs to be serialised
        self.output = open('{}'.format(out_name), 'wb')#, encoding = "windows-1252")
        self.list_worker = ListWorker()
        

    def header(self):
        data = bytearray()
        # return the header bytes (0x60 long)
        data.extend(b'\xDD\xDD\xDD\xDD')        # magic
        data.extend(serialise(2500))               # version
        data.extend(pad(b'CUSTOMGEOMETRY', 0x10))      # custom name thing
        template_name = 'c' + '{}'.format(self.struct.STRUCTNAME)
        data.extend(pad(template_name.encode('utf-8'), 0x40))     # struct name
        data.extend(b'\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE')
        return data

    def serialise(self):
        # this is the workhorse function.
        # we will keep track of the current location and also the current expected final location
        # so that list data can be placed there
        #print(len(self.header()))
        self.output.write(self.header())
        self.list_worker['end'] = 0x60 + len(self.struct)      # add on the size of the struct to know where the current finish is
        self.struct.serialise(self.output)#, self.list_worker)
        #for data in self.list_worker.dataQ:
            #print(len(data), 'hi there')
        #    self.output.write(data)
        self.output.close()

        """
        if isinstance(data, List):
            self.dataQ.append(data.serialise())
            self.end_loc += data.dtype_len()*len(data)      # set the end point at the end of the list data
        data.serialise()
        self.curr_loc += len(data)
        """

class ListWorker():
    def __init__(self, initial_state = (0x60, 0x60)):
        self.curr = initial_state[0]
        self.end = initial_state[1]
        self.dataQ = []             # a list containing queued data that will be serialised once the main struct is done

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

if __name__ == "__main__":

    pd = TkPhysicsComponentData()
    mbinc = mbinCompiler(pd, 'newmbin')
    mbinc.serialise()
