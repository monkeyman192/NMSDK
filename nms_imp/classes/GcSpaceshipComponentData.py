# GcSpaceshipComponentData struct

from .Struct import Struct
from .GcSpaceshipClasses import GcSpaceshipClasses

STRUCTNAME = 'GcSpaceshipComponentData'

class GcSpaceshipComponentData(Struct):
    def __init__(self, **kwargs):
        super(GcSpaceshipComponentData, self).__init__()

        """ Contents of the struct """
        self.data['ShipClass'] = kwargs.get('ShipClass', GcSpaceshipClasses())
        self.data['Cockpit'] = kwargs.get('Cockpit', '')
        self.data['MaxHeadTurn'] = kwargs.get('MaxHeadTurn', 0)
        self.data['MaxHeadPitchUp'] = kwargs.get('MaxHeadPitchUp', 0)
        self.data['MaxHeadPitchDown'] = kwargs.get('MaxHeadPitchDown', 0)
        self.data['BaseHealth'] = kwargs.get('BaseHealth', 0)
        self.data['FoVFixedDistance'] = kwargs.get('FoVFixedDistance', 0)
        self.data['WheelModel'] = kwargs.get('WheelModel', '')
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
