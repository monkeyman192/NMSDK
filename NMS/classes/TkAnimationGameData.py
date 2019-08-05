# TkAnimationGameData struct

from .Struct import Struct


class TkAnimationGameData(Struct):
    def __init__(self, **kwargs):
        super(TkAnimationGameData, self).__init__()

        """ Contents of the struct """
        self.data['RootMotionEnabled'] = kwargs.get('RootMotionEnabled', False)
        self.data['BlockPlayerMovement'] = kwargs.get('BlockPlayerMovement',
                                                      False)
        self.data['BlockPlayerWeapon'] = kwargs.get('BlockPlayerWeapon',
                                                    'Unblocked')
