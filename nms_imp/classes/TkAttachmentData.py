# TkAttachmentData struct

from .Struct import Struct
from .List import List
from .TkPhysicsComponentData import TkPhysicsComponentData

STRUCTNAME = 'TkAttachmentData'

class TkAttachmentData(Struct):
    def __init__(self, **kwargs):
        super(TkAttachmentData, self).__init__()

        """ Contents of the struct """
        self.data['Components'] = kwargs.get('Components', List(TkPhysicsComponentData()))
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
