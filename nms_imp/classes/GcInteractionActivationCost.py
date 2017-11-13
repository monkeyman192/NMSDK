# GcInteractionActivationCost struct

from .Struct import Struct

STRUCTNAME = 'GcInteractionActivationCost'

class GcInteractionActivationCost(Struct):
    def __init__(self, **kwargs):
        super(GcInteractionActivationCost, self).__init__()

        """ Contents of the struct """
        self.data['SubstanceId'] = kwargs.get('SubstanceId', "")
        self.data['AltIds'] = kwargs.get('AltIds', List())
        self.data['Cost'] = kwargs.get('Cost', 0)
        self.data['Repeat'] = kwargs.get('Repeat', False)
        self.data['RequiredTech'] = kwargs.get('RequiredTech', "")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
