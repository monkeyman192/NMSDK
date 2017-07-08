# GcDestroyAction struct

from .Struct import Struct

STRUCTNAME = 'GcDestroyAction'

class GcDestroyAction(Struct):
    def __init__(self, **kwargs):
        super(GcDestroyAction, self).__init__()

        """ Contents of the struct """
        self.data['DestroyAll'] = bool(kwargs.get('DestroyAll', False))
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
