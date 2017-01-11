# TkVolumeTriggerType struct

from .Struct import Struct

STRUCTNAME = 'TkVolumeTriggerType'

class TkVolumeTriggerType(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.VolumeTriggerType = kwargs.get('VolumeTriggerType', "Open")
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
