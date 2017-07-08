# GcGoToStateAction struct

from .Struct import Struct

STRUCTNAME = 'GcGoToStateAction'

class GcGoToStateAction(Struct):
    def __init__(self, **kwargs):
        super(GcGoToStateAction, self).__init__()

        """ Contents of the struct """
        self.data['State'] = kwargs.get('State', "")
        self.data['Broadcast'] = bool(kwargs.get('Broadcast', False))
        self.data['BroadcastLevel'] = kwargs.get('BroadcastLevel', "Scene")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
