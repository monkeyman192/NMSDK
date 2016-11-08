# Vector4f struct

from .Struct import Struct

STRUCTNAME = 'Vector4f'

class Vector4f(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.x = kwargs.get('x', None)
        self.y = kwargs.get('y', None)
        self.z = kwargs.get('z', None)
        self.t = kwargs.get('t', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None

        self.STRUCTNAME = STRUCTNAME
