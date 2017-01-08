# TkAttachmentData struct

from .Struct import Struct
from .List import List
from .TkPhysicsComponentData import TkPhysicsComponentData

STRUCTNAME = 'TkAnimNodeFrameData'

class TkAnimNodeFrameData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Rotations = kwargs.get('Rotations', None)
        self.Translations = kwargs.get('Translations', None)
        self.Scales = kwargs.get('Scales', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
