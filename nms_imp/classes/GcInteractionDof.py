# GcInteractionDof struct

from .Struct import Struct

STRUCTNAME = 'GcInteractionDof'

class GcInteractionDof(Struct):
    def __init__(self, **kwargs):
        super(GcInteractionDof, self).__init__()

        """ Contents of the struct """
        self.data['IsEnabled'] = kwargs.get('IsEnabled', True)
        self.data['UseGlobals'] = kwargs.get('UseGlobals', True)
        self.data['NearPlanetMin'] = kwargs.get('NearPlanetMin', 2)
        self.data['NearPlanetAdjust'] = kwargs.get('NearPlanetAdjust', 1)
        self.data['FarPlane'] = kwargs.get('FarPlane', 3)
        self.data['FarFadeDistance'] = kwargs.get('FarFadeDistance', 2)
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
