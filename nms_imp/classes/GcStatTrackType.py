# GcStatTrackType  struct

from .Struct import Struct

STRUCTNAME = 'GcStatTrackType '

class GcStatTrackType (Struct):
    def __init__(self, **kwargs):
        super(GcStatTrackType , self).__init__()

        """ Contents of the struct """
        self.data['StatTrackType'] = kwargs.get('StatTrackType', "SET")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
