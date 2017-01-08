# TkTransformData struct

from .Struct import Struct

STRUCTNAME = 'TkTransformData'

class TkTransformData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.TransX = kwargs.get('TransX', 0)
        self.TransY = kwargs.get('TransY', 0)
        self.TransZ = kwargs.get('TransZ', 0)
        self.RotX = kwargs.get('RotX', 0)
        self.RotY = kwargs.get('RotY', 0)
        self.RotZ = kwargs.get('RotZ', 0)
        self.ScaleX = kwargs.get('ScaleX', 1)
        self.ScaleY = kwargs.get('ScaleY', 1)
        self.ScaleZ = kwargs.get('ScaleZ', 1)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
