# TkAttachmentData struct

from .Struct import Struct
from .List import List
from .TkPhysicsComponentData import TkPhysicsComponentData

STRUCTNAME = 'TkAnimNodeData'

class TkAnimNodeData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Node = kwargs.get('Node', "")
        self.CanCompress = kwargs.get('CanCompress', "True")
        self.RotIndex = kwargs.get('RotIndex', 0)
        self.TransIndex = kwargs.get('TransIndex', 0)
        self.ScaleIndex = kwargs.get('ScaleIndex', 0)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
