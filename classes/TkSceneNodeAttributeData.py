# TkSceneNodeAttributeData struct

from .Struct import Struct

STRUCTNAME = 'TkSceneNodeAttributeData'

class TkSceneNodeAttributeData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.AltID = kwargs.get('AltID', None)
        self.Value = kwargs.get('Value', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
