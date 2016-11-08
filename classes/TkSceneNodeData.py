# TkSceneNodeData struct

from .Struct import Struct

STRUCTNAME = 'TkSceneNodeData'

class TkSceneNodeData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.Type = kwargs.get('Type', None)
        self.Transform = kwargs.get('Transform', None)
        self.Attributes = kwargs.get('Attributes', None)
        self.Children = kwargs.get('Children', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
