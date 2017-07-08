# GcSpawnAction struct

from .Struct import Struct

STRUCTNAME = 'GcSpawnAction'

class GcSpawnAction(Struct):
    def __init__(self, **kwargs):
        super(GcSpawnAction, self).__init__()

        """ Contents of the struct """
        self.data['Event'] = kwargs.get('Event', "")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
