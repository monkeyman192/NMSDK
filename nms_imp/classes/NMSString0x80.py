# Vector4f struct

from .Struct import Struct
from .String import String

STRUCTNAME = 'NMSString0x80'

class NMSString0x80(Struct):
    def __init__(self, **kwargs):
        self.size = 0x80
        super(NMSString0x80, self).__init__()

        """ Contents of the struct """
        self.data['Value'] = String(kwargs.get('Value', ""), 0x80)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None

        self.STRUCTNAME = STRUCTNAME
