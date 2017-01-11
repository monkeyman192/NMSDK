#Custom TkSceneNodeData struct for collisions

from .List import List
from .TkSceneNodeAttributeData import TkSceneNodeAttributeData
from .TkTransformData import TkTransformData

PRIMITIVES = ['Box', 'Sphere', 'Capsule', 'Cylinder']

class oldCollision():
    def __init__(self, **kwargs):

        self.Type = kwargs.get('Type', None)
        self.Radius = kwargs.get('Radius', None)
        self.Width = kwargs.get('Width', None)
        self.Height = kwargs.get('Height', None)
        self.Depth = kwargs.get('Depth', None)
        self.Indexes = kwargs.get('Indexes', None)
        self.Vertices = kwargs.get('Vertices', None)
        self.uv_stream = kwargs.get('uv_stream', None)
        self.Normals = kwargs.get('Normals', None)
        self.Transform = kwargs.get('Transform', TkTransformData(TransX = 0, TransY = 0, TransZ = 0,
                                                                 RotX = 0, RotY = 0, RotZ = 0,
                                                                 ScaleX = 1, ScaleY = 1, ScaleZ = 1))

        if self.Type in PRIMITIVES:
            self.col_type = 'Primitive'
        elif self.Type == 'Mesh':
            self.col_type = 'Mesh'
        else:
            # something has gone wrong if this happens!!
            self.col_type = None
        

    def process_primitives(self):
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

    def process_mesh(self, BatchStart, BatchCount, VertRStart, VertREnd):
        self.Attributes = List()
        self.Attributes.append(TkSceneNodeAttributeData(Name = "TYPE",
                                                        Value = self.Type))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'BATCHSTART',
                                                        Value = BatchStart))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'BATCHCOUNT',
                                                        Value = BatchCount))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'VERTRSTART',
                                                        Value = VertRStart))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'VERTREND',
                                                        Value = VertREnd))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'FIRSTSKINMAT',
                                                        Value = 0))
        self.Attributes.append(TkSceneNodeAttributeData(Name = 'LASTSKINMAT',
                                                        Value = 0))
