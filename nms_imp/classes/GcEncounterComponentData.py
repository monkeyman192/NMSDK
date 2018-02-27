# GcEncounterComponentData struct

from .Struct import Struct

STRUCTNAME = 'GcEncounterComponentData'

class GcEncounterComponentData(Struct):
    def __init__(self, **kwargs):
        super(GcEncounterComponentData, self).__init__()

        """ Contents of the struct """
        self.data['EncounterType'] = kwargs.get('EncounterType', "Guards")
        self.data['EncounterRobot'] = kwargs.get('EncounterRobot', "Drones")
        self.data['CountMin'] = kwargs.get('CountMin', 0)
        self.data['CountMax'] = kwargs.get('CountMax', 0)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
