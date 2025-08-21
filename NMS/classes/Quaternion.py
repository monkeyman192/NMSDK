# Quaternion struct

from .Struct import Struct


class Quaternion(Struct):
    def __init__(self, **kwargs):
        super(Quaternion, self).__init__()

        """ Contents of the struct """
        self.data['x'] = kwargs.get('x', 0.0)
        self.data['y'] = kwargs.get('y', 0.0)
        self.data['z'] = kwargs.get('z', 0.0)
        self.data['w'] = kwargs.get('w', 0.0)
        """ End of the struct contents"""

    def __str__(self):
        return 'Quaternion({0}, {1}, {2}, {3})'.format(self.data['x'],
                                                       self.data['y'],
                                                       self.data['z'],
                                                       self.data['w'])

    def __repr__(self):
        return str(self)
