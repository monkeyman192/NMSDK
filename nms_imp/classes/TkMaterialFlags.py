# TkMaterialFlags struct

from .Struct import Struct

STRUCTNAME = 'TkMaterialFlags'

class TkMaterialFlags(Struct):
    def __init__(self, **kwargs):
        self.size = 0x4         # since this is actually an int...
        super(TkMaterialFlags, self).__init__()

        """ Contents of the struct """
        self.data['MaterialFlag'] = kwargs.get('MaterialFlag', "_F01_DIFFUSEMAP")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
