# GcDestructableComponentData struct

from .Struct import Struct
from .List import List
from .GcStatTrackType import GcStatTrackType
from .TkTextureResource import TkTextureResource
from .GcSubstanceAmount import GcSubstanceAmount

STRUCTNAME = 'GcDestructableComponentData'

class GcDestructableComponentData(Struct):
    def __init__(self, **kwargs):
        super(GcDestructableComponentData, self).__init__()

        """ Contents of the struct """
        self.data['Explosion'] = kwargs.get('Explosion', "")
        self.data['ExplosionScale'] = kwargs.get('ExplosionScale', 1)
        self.data['ExplosionScaleToBounds'] = kwargs.get('ExplosionScaleToBounds', False)
        self.data['VehicleDestroyEffect'] = kwargs.get('VehicleDestroyEffect', "")
        self.data['TriggerAction'] = kwargs.get('TriggerAction', "")
        self.data['IncreaseWanted'] = kwargs.get('IncreaseWanted', 1)
        self.data['LootReward'] = kwargs.get('LootReward', "")
        self.data['LootRewardAmountMin'] = kwargs.get('LootRewardAmountMin', 0)
        self.data['LootRewardAmountMax'] = kwargs.get('LootRewardAmountMax', 0)
        self.data['GivesSubstances'] = kwargs.get('GivesSubstances', List())
        self.data['StatsToTrack'] = kwargs.get('StatsToTrack', GcStatTrackType())
        self.data['GivesReward'] = kwargs.get('GivesReward', "")
        self.data['HardModeSubstanceMultiplier'] = kwargs.get('HardModeSubstanceMultiplier', 1)
        self.data['RemoveModel'] = kwargs.get('RemoveModel', True)
        self.data['DestroyedModel'] = kwargs.get('DestroyedModel', TkTextureResource())
        self.data['DestroyedModelUsesScale'] = kwargs.get('DestroyedModelUsesScale', False)
        self.data['DestroyForce'] = kwargs.get('DestroyForce', 10)
        self.data['DestroyForceRadius'] = kwargs.get('DestroyForceRadius', 5)
        self.data['DestroyEffect'] = kwargs.get('DestroyEffect', "")
        self.data['DestroyEffectPoint'] = kwargs.get('DestroyEffectPoint', "")
        self.data['DestroyEffectTime'] = kwargs.get('DestroyEffectTime', 2)
        self.data['ShowInteract'] = kwargs.get('ShowInteract', False)
        self.data['ShowInteractRange'] = kwargs.get('ShowInteractRange', 20)
        self.data['GrenadeSingleHit'] = kwargs.get('GrenadeSingleHit', True)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
