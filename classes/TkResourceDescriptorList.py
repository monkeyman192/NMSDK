# TkSceneNodeData struct

from .Struct import Struct
from .List import List

STRUCTNAME = 'TkResourceDescriptorList'

class TkResourceDescriptorList(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.TypeId = kwargs.get('TypeId', "_PROCOBJ_")
        self.Descriptors = kwargs.get('Descriptors', List())
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
