# GcAlienPuzzleMissionOverride struct

from .Struct import Struct

STRUCTNAME = 'GcAlienPuzzleMissionOverride'

class GcAlienPuzzleMissionOverride(Struct):
    def __init__(self, **kwargs):
        super(GcAlienPuzzleMissionOverride, self).__init__()

        """ Contents of the struct """
        self.data['Mission'] = kwargs.get('Mission', '')
        self.data['Puzzle'] = kwargs.get('Puzzle', '')
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
