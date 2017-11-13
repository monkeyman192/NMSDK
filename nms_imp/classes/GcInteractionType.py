# GcInteractionType struct

from .Struct import Struct

STRUCTNAME = 'GcInteractionType'

class GcInteractionType(Struct):
    def __init__(self, **kwargs):
        super(GcInteractionType, self).__init__()

        """ Contents of the struct """
        self.data['InteractionType'] = kwargs.get('InteractionType', "NPC")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
