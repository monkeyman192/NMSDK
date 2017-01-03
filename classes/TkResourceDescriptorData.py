# TkSceneNodeData struct

from .Struct import Struct
from .List import List

STRUCTNAME = 'TkResourceDescriptorData'

class TkResourceDescriptorData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Id = kwargs.get('Id', "_PROCOBJ_")
        self.Name = kwargs.get('Name', "_PROCOBJ_")
        self.ReferencePaths = kwargs.get("ReferencePaths", List())
        self.Chance = kwargs.get("Chance", 0)
        self.Children = kwargs.get("Children", None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
