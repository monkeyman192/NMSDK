# TkVertexElement struct

from .Struct import Struct

STRUCTNAME = 'TkVertexElement'

class TkVertexElement(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.SemanticID = kwargs.get('SemanticID', None)
        self.Size = kwargs.get('Size', None)
        self.Type = kwargs.get('Type', None)
        self.Offset = kwargs.get('Offset', None)
        self.Normalise = kwargs.get('Normalise', None)
        self.Instancing = kwargs.get('Instancing', None)
        self.PlatformData = kwargs.get('PlatformData', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
