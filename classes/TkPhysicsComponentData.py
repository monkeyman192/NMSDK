# TkPhysicsComponentData struct

from .Struct import Struct
from .TkPhysicsData import TkPhysicsData
from .TkVolumeTriggerType import TkVolumeTriggerType

STRUCTNAME = 'TkPhysicsComponentData'

class TkPhysicsComponentData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Data = kwargs.get('Data', TkPhysicsData())
        self.TriggerVolume = kwargs.get('TriggerVolume', False)
        self.VolumeTriggerType = kwargs.get('VolumeTriggerType', TkVolumeTriggerType())
        self.Climbable = kwargs.get('Climbable', False)
        self.IgnoreModelOwner = kwargs.get('IgnoreModelOwner', False)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
