# GcPlayAnimAction struct

from .Struct import Struct

STRUCTNAME = 'GcPlayAnimAction'

class GcPlayAnimAction(Struct):
    def __init__(self, **kwargs):
        super(GcPlayAnimAction, self).__init__()

        """ Contents of the struct """
        self.data['Anim'] = kwargs.get('Anim', "")
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
