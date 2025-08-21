# TkAnimationComponentData struct

from .Struct import Struct
from .TkAnimationData import TkAnimationData
from .List import List


class TkAnimationComponentData(Struct):
    def __init__(self, **kwargs):
        super(TkAnimationComponentData, self).__init__()

        """ Contents of the struct """
        self.data['Idle'] = kwargs.get('Idle', TkAnimationData())
        self.data['Anims'] = kwargs.get('Anims', List())
        # This will always just be empty for now...
        self.data['Trees'] = kwargs.get('Trees', List())
        self.data['NetSyncAnimation'] = kwargs.get('NetSyncAnimation', False)
        self.data['JointLODOverrides'] = kwargs.get('JointLODOverrides',
                                                    List())
        """ End of the struct contents"""
