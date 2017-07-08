# GcActionTrigger struct

from .Struct import Struct
from .List import List

STRUCTNAME = 'GcActionTrigger'

class GcActionTrigger(Struct):
    def __init__(self, **kwargs):
        super(GcActionTrigger, self).__init__()

        """ Contents of the struct """
        self.data['Trigger'] = kwargs.get('Trigger', None)
        self.data['Action'] = kwargs.get('Action', List())
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
