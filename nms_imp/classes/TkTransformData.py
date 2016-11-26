# TkTransformData struct

from .Struct import Struct

STRUCTNAME = 'TkTransformData'

class TkTransformData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.TransX = kwargs.get('TransX', None)
        self.TransY = kwargs.get('TransY', None)
        self.TransZ = kwargs.get('TransZ', None)
        self.RotX = kwargs.get('RotX', None)
        self.RotY = kwargs.get('RotY', None)
        self.RotZ = kwargs.get('RotZ', None)
        self.ScaleX = kwargs.get('ScaleX', None)
        self.ScaleY = kwargs.get('ScaleY', None)
        self.ScaleZ = kwargs.get('ScaleZ', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
