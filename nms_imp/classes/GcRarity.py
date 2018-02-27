# GcRarity struct

from .Struct import Struct

STRUCTNAME = 'GcRarity'

class GcRarity(Struct):
    def __init__(self, **kwargs):
        super(GcRarity, self).__init__()

        """ Contents of the struct """
        self.data['Rarity'] = kwargs.get('Rarity', "Common")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
