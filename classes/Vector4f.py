# Vector4f struct

from .Struct import Struct

STRUCTNAME = 'Vector4f'

class Vector4f(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.x = kwargs.get('x', 0.0)
        self.y = kwargs.get('y', 0.0)
        self.z = kwargs.get('z', 0.0)
        self.t = kwargs.get('t', 0.0)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None

        self.STRUCTNAME = STRUCTNAME
