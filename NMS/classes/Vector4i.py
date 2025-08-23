# Vector4i struct

from .Struct import Struct
from struct import pack


class Vector4i(Struct):
    def __init__(self, **kwargs):
        super(Vector4i, self).__init__()

        """ Contents of the struct """
        self.data['X'] = kwargs.get('X', 0)
        self.data['Y'] = kwargs.get('Y', 0)
        self.data['Z'] = kwargs.get('Z', 0)
        self.data['W'] = kwargs.get('W', 0)
        """ End of the struct contents"""

    def __bytes__(self):
        return pack('<iiii', self.data['X'], self.data['Y'], self.data['X'], self.data['W'])

    def __str__(self):
        return 'Vector4i({0}, {1}, {2}, {3})'.format(self.data['X'],
                                                     self.data['Y'],
                                                     self.data['Z'],
                                                     self.data['W'])

    def __repr__(self):
        return str(self)
