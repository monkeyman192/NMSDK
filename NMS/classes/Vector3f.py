# Vector3f struct

from .Struct import Struct
from struct import pack


class Vector3f(Struct):
    def __init__(self, **kwargs):
        super(Vector3f, self).__init__()

        """ Contents of the struct """
        self.data['x'] = kwargs.get('x', 0.0)
        self.data['y'] = kwargs.get('y', 0.0)
        self.data['z'] = kwargs.get('z', 0.0)
        """ End of the struct contents"""

    def __bytes__(self):
        # The empty 't' component will have a 1f placed in it anyway.
        return pack('<ffff', self.data['x'], self.data['y'], self.data['z'], 1)

    def __str__(self):
        return 'Vector3f({0}, {1}, {2})'.format(self.data['x'],
                                                self.data['y'],
                                                self.data['z'])

    def __repr__(self):
        return str(self)
