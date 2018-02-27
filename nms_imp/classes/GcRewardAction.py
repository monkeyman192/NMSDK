# GcRewardAction struct

from .Struct import Struct

STRUCTNAME = 'GcRewardAction'

class GcRewardAction(Struct):
    def __init__(self, **kwargs):
        super(GcRewardAction, self).__init__()

        """ Contents of the struct """
        self.data['Reward'] = kwargs.get('Reward', "")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
