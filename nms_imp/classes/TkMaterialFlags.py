# TkMaterialFlags struct

from .Struct import Struct

STRUCTNAME = 'TkMaterialFlags'

class TkMaterialFlags(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.MaterialFlag = kwargs.get('MaterialFlag', "_F01_DIFFUSEMAP")
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
