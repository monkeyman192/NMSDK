# TkVolumeTriggerType struct

from .Struct import Struct

STRUCTNAME = 'TkVolumeTriggerType'

class TkVolumeTriggerType(Struct):
    def __init__(self, **kwargs):
        self.size = 0x4
        super(TkVolumeTriggerType, self).__init__()

        """ Contents of the struct """
        self.VolumeTriggerType = [
            "Open", "GenericInterior", "GenericGlassInterior", "Corridor",
            "SmallRoom", "LargeRoom", "OpenCovered", "HazardProtection",
            "FieldBoundary", "Custom_Biodome", "Portal", "VehicleBoost"]
        self.data['VolumeTriggerType'] = kwargs.get('VolumeTriggerType', "Open")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
