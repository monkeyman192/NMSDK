# GcScannerIconTypes struct

from .Struct import Struct

STRUCTNAME = 'GcScannerIconTypes'

class GcScannerIconTypes(Struct):
    def __init__(self, **kwargs):
        super(GcScannerIconTypes, self).__init__()

        """ Contents of the struct """
        self.data['ScanIconType'] = kwargs.get('ScanIconType', 'None')
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
