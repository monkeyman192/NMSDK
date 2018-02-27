# GcAISpaceshipTypes struct

from .Struct import Struct

STRUCTNAME = 'GcAISpaceshipTypes'

class GcAISpaceshipTypes(Struct):
    def __init__(self, **kwargs):
        super(GcAISpaceshipTypes, self).__init__()

        """ Contents of the struct """
        self.data['ShipType'] = kwargs.get('ShipType', "None")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
