# TkPhysicsComponentData struct

from .Struct import Struct
from .Empty import Empty
from .TkPhysicsData import TkPhysicsData
from .TkVolumeTriggerType import TkVolumeTriggerType


class TkPhysicsComponentData(Struct):
    def __init__(self, **kwargs):
        super(TkPhysicsComponentData, self).__init__()

        """ Contents of the struct """
        self.data['Data'] = kwargs.get('Data', TkPhysicsData())
        self.data['RagdollData'] = kwargs.get('RagdollData', Empty(0x50))
        self.data['VolumeTriggerType'] = kwargs.get('VolumeTriggerType',
                                                    TkVolumeTriggerType())
        self.SurfaceProperties = ["None", "Glass"]  # Is this needed???
        self.data['SurfaceProperties'] = kwargs.get('SurfaceProperties',
                                                    "None")
        self.data['TriggerVolume'] = kwargs.get('TriggerVolume', False)
        self.data['Climbable'] = kwargs.get('Climbable', False)
        self.data['IgnoreModelOwner'] = kwargs.get('IgnoreModelOwner', False)
        self.data['NoVehicleCollide'] = kwargs.get('NoVehicleCollide', False)
        self.data['NoPlayerCollide'] = kwargs.get('NoPlayerCollide', False)
        self.data['CameraInvisible'] = kwargs.get('CameraInvisible', False)
        self.data['InvisibleForInteraction'] = kwargs.get(
            'InvisibleForInteraction', False)
        self.data['AllowTeleporter'] = kwargs.get('AllowTeleporter', False)
        self.data['BlockTeleporter'] = kwargs.get('BlockTeleporter', False)
        self.data['EndPadding'] = Empty(0x7)
        """ End of the struct contents"""
