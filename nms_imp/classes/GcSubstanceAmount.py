# GcSubstanceAmount struct

from .Struct import Struct

STRUCTNAME = 'GcSubstanceAmount'

class GcSubstanceAmount(Struct):
    def __init__(self, **kwargs):
        super(GcSubstanceAmount, self).__init__()

        """ Contents of the struct """
        self.data['AmountMin'] = kwargs.get('AmountMin', 0)
        self.data['AmountMax'] = kwargs.get('AmountMax', 0)
        self.data['Specific'] = kwargs.get('Specific', "")
        self.data['SubstanceCategory'] = kwargs.get('SubstanceCategory', GcRealitySubstanceCategory())
        self.data['Rarity'] = kwargs.get('Rarity', GcRarity())
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
