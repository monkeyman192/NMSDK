#Custom TkSceneNodeData struct for collisions

from .Struct import Struct
from .List import List
from .TkSceneNodeAttributeData import TkSceneNodeAttributeData

STRUCTNAME = 'TkSceneNodeData'

class Collision(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Type = 'COLLISION'
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        self.CType = kwargs.get('Type', None)
        self.Radius = kwargs.get('Radius', None)
        self.Width = kwargs.get('Width', None)
        self.Height = kwargs.get('Height', None)
        self.Depth = kwargs.get('Depth', None)

        # Parent needed so that it can be a SubElement of something
        self.parent = None

        self.STRUCTNAME = STRUCTNAME

    def process_collision(self):
        self.Attributes = List()
        self.Attributes.append(TkSceneNodeAttributeData(Name = "TYPE",
                                                        Value = self.Type))
        if self.Type == 'Box':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "WIDTH",
                                                            Value = self.Width))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "HEIGHT",
                                                            Value = self.Height))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "DEPTH",
                                                            Value = self.Depth))
        elif self.Type == 'Sphere':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "RADIUS",
                                                            Value = self.Radius))
        elif self.Type == 'Capsule':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "RADIUS",
                                                            Value = self.Radius))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "HEIGHT",
                                                            Value = self.Height))
        elif self.Type == 'Cylinder':
            self.Attributes.append(TkSceneNodeAttributeData(Name = "RADIUS",
                                                            Value = self.Radius))
            self.Attributes.append(TkSceneNodeAttributeData(Name = "HEIGHT",
                                                            Value = self.Height))
        elif self.Type == 'Mesh':
            # do a bunch of stuff
            pass
