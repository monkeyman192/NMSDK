# Quaternion struct

from .Struct import Struct


class Quaternion(Struct):
    def __init__(self, **kwargs):
        super(Quaternion, self).__init__()

        """ Contents of the struct """
        self.data['X'] = kwargs.get('X', 0.0)
        self.data['Y'] = kwargs.get('Y', 0.0)
        self.data['Z'] = kwargs.get('Z', 0.0)
        self.data['W'] = kwargs.get('W', 0.0)
        """ End of the struct contents"""

    def __str__(self):
        return 'Quaternion({0}, {1}, {2}, {3})'.format(self.data['X'],
                                                       self.data['Y'],
                                                       self.data['Z'],
                                                       self.data['W'])

    def __repr__(self):
        return str(self)
