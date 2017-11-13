# GcRarity struct

from .Struct import Struct

STRUCTNAME = 'GcRarity'

class GcRarity(Struct):
    def __init__(self, **kwargs):
        super(GcRarity, self).__init__()

        """ Contents of the struct """
<<<<<<< HEAD
        self.data['Rarity'] = kwargs.get('Rarity', "Common")
=======
        self.data['Rarity'] = kwargs.get('Rarity', 'None')
>>>>>>> refs/remotes/monkeyman192/Experimental
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
