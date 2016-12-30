# TkAttachmentData struct

from .Struct import Struct
from .List import List
from .TkPhysicsComponentData import TkPhysicsComponentData
from .TkAnimNodeFrameData import TkAnimNodeFrameData

STRUCTNAME = 'TkAnimMetaData'

class TkAnimMetaData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.FrameCount = kwargs.get('FrameCount', 0)
        self.NodeCount = kwargs.get('NodeCount', 0)
        self.NodeData = kwargs.get('NodeData', None)
        self.AnimFrameData = kwargs.get('AnimFrameData', None)
        self.StillFrameData = kwargs.get('StillFrameData', TkAnimNodeFrameData())
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
