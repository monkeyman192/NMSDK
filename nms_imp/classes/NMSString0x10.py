# NMSString0x10 struct

from .Struct import Struct

STRUCTNAME = 'NMSString0x10'

class NMSString0x10(Struct):
    def __init__(self, **kwargs):
        super(NMSString0x10, self).__init__()

        """ Contents of the struct """
        self.data['Value'] = kwargs.get('Value', '')
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
