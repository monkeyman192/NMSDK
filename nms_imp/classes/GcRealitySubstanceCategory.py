# GcRealitySubstanceCategory struct

from .Struct import Struct

STRUCTNAME = 'GcRealitySubstanceCategory'

class GcRealitySubstanceCategory(Struct):
    def __init__(self, **kwargs):
        super(GcRealitySubstanceCategory, self).__init__()

        """ Contents of the struct """
<<<<<<< HEAD
        self.data['SubstanceCategory'] = kwargs.get('SubstanceCategory', "Commodity")
=======
        self.data['SubstanceCategory'] = kwargs.get('SubstanceCategory', 'None')
>>>>>>> refs/remotes/monkeyman192/Experimental
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
