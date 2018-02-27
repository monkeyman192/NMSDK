# GcWarpAction struct

from .Struct import Struct

STRUCTNAME = 'GcWarpAction'

class GcWarpAction(Struct):
    def __init__(self, **kwargs):
        super(GcWarpAction, self).__init__()

        """ Contents of the struct """
        self.data['WarpType'] = kwargs.get('WarpType', "BlackHole")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
