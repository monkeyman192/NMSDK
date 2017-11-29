# GcDiscoveryTypes struct

from .Struct import Struct

STRUCTNAME = 'GcDiscoveryTypes'

class GcDiscoveryTypes(Struct):
    def __init__(self, **kwargs):
        super(GcDiscoveryTypes, self).__init__()

        """ Contents of the struct """
        self.data['DiscoveryType'] = kwargs.get('DiscoveryType', "Unknown")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
