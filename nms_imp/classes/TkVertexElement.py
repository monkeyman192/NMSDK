# TkVertexElement struct

from .Struct import Struct
from .String import String

STRUCTNAME = 'TkVertexElement'

class TkVertexElement(Struct):
    def __init__(self, **kwargs):
        super(TkVertexElement, self).__init__()

        """ Contents of the struct """
        self.data['SemanticID'] = kwargs.get('SemanticID', 0)
        self.data['Size'] = kwargs.get('Size', 0)
        self.data['Type'] = kwargs.get('Type', 0)
        self.data['Offset'] = kwargs.get('Offset', 0)
        self.data['Normalise'] = kwargs.get('Normalise', 0)
        self.data['Instancing'] = kwargs.get('Instancing', 0)
        self.data['PlatformData'] = String(kwargs.get('PlatformData', ""), 0x8)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
