# GcSpaceshipClasses struct

from .Struct import Struct

STRUCTNAME = 'GcSpaceshipClasses'

class GcSpaceshipClasses(Struct):
    def __init__(self, **kwargs):
        super(GcSpaceshipClasses, self).__init__()

        """ Contents of the struct """
        self.data['ShipClass'] = kwargs.get('ShipClass', "Freighter")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
