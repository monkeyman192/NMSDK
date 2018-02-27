# GcProjectileImpactType struct

from .Struct import Struct

STRUCTNAME = 'GcProjectileImpactType'

class GcProjectileImpactType(Struct):
    def __init__(self, **kwargs):
        super(GcProjectileImpactType, self).__init__()

        """ Contents of the struct """
        self.data['Impact'] = kwargs.get('Impact', "Default")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
