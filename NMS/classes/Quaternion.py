# Quaternion struct

from .Struct import Struct
from ...serialization.formats import write_int_2_10_10_10_rev


class Quaternion(Struct):
    def __init__(self, **kwargs):
        super(Quaternion, self).__init__()

        """ Contents of the struct """
        self.data['x'] = kwargs.get('x', 0.0)
        self.data['y'] = kwargs.get('y', 0.0)
        self.data['z'] = kwargs.get('z', 0.0)
        self.data['w'] = kwargs.get('w', 0.0)
        """ End of the struct contents"""

    def __bytes__(self):
        return write_int_2_10_10_10_rev([self.data['x'],
                                         self.data['y'],
                                         self.data['z'],
                                         self.data['w']])
