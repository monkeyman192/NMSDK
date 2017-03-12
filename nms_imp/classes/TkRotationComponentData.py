# TkRotationComponentData struct

from .Struct import Struct
from .TkPhysicsData import TkPhysicsData
from .TkVolumeTriggerType import TkVolumeTriggerType
from .Vector4f import Vector4f

STRUCTNAME = 'TkRotationComponentData'

class TkRotationComponentData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Speed = kwargs.get('Speed', 1)
        self.Axis = kwargs.get('Axis', Vector4f(x = 0, y = 1, z = 0, t = 0))
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
