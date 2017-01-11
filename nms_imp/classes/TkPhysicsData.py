# TkPhysicsData struct

from .Struct import Struct

STRUCTNAME = 'TkPhysicsData'

class TkPhysicsData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Mass = kwargs.get('Mass', 0)
        self.Friction = kwargs.get('Friction', 0.5)
        self.RollingFriction = kwargs.get('RollingFriction', 0.2)
        self.AngularDamping = kwargs.get('AngularDamping', 0.2)
        self.LinearDamping = kwargs.get('LinearDamping', 0.1)
        self.Gravity = kwargs.get('Gravity', 20)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
