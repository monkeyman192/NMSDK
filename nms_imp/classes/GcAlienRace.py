# GcAlienRace struct

from .Struct import Struct

STRUCTNAME = 'GcAlienRace'

class GcAlienRace(Struct):
    def __init__(self, **kwargs):
        super(GcAlienRace, self).__init__()

        """ Contents of the struct """
        self.data['AlienRace'] = kwargs.get('AlienRace', "Warriors")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
