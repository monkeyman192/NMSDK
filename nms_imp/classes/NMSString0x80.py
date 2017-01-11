# Vector4f struct

from .Struct import Struct

STRUCTNAME = 'NMSString0x80'

class NMSString0x80(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Value = kwargs.get('Value', "")
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None

        self.STRUCTNAME = STRUCTNAME
