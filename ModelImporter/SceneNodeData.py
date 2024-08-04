import math

from mathutils import Matrix, Euler

from serialization.NMS_Structures import TkSceneNodeData

class SceneNodeData():
    """ Our own internal representation of the TkSceneNodeData class.
    This makes no attempt to map fields directly to the fields in that class,
    but will instead be a version-independent representation of it.
    """
    def __init__(self, info: TkSceneNodeData, parent: 'SceneNodeData' = None):
        self.info = info
        self.parent = parent
        self.verts = dict()
        self.idxs = list()
        self.faces = list()
        self.bounded_hull = list()
        # The metadata will be read from the geometry file later.
        self.metadata = None
        self.children: list[SceneNodeData] = []
        # Slightly wasteful but greatly simplifies things...
        for child in self.info.Children:
            self.children.append(SceneNodeData(child, self))
        self.attributes = {x.Name: x.Value for x in self.info.Attributes}

# region public methods

    def Attribute(self, name, astype=str):
        # Doesn't support AltID's
        if (attrib := self.attributes.get(name)) is not None:
            return astype(attrib)

    def iter(self):
        """ Returns an ordered iterable list of SceneNodeData objects. """
        objs = [self]
        for child in self.children:
            objs.extend(child.iter())
        return objs

    def get(self, ID):
        """ Return the SceneNodeData object with the specified ID. """
        for obj in self.iter():
            # Sanitize input ID for safety
            if isinstance(obj.Name, str):
                if obj.Name.upper() == ID.upper():
                    return obj

# region private methods

    def _generate_bounded_hull(self, bh_data):
        self.bounded_hull = bh_data[int(self.Attribute('BOUNDHULLST')):
                                    int(self.Attribute('BOUNDHULLED'))]

    def _generate_geometry(self, from_bh=False):
        """ Generate the faces and edge data.

        Parameters
        ----------
        from_bh : bool
            Whether the data is being generated from the hull data.
        """
        if len(self.idxs) == 0:
            if ((from_bh and len(self.bounded_hull) == 0)
                    or (not from_bh and len(self.verts.keys()) == 0)):
                raise ValueError('Something has gone wrong!!!')
        self.faces = list(zip(self.idxs[0::3],
                              self.idxs[1::3],
                              self.idxs[2::3]))

# region properties

    @property
    def Name(self) -> str:
        return self.info.Name

    @property
    def Transform(self) -> dict:
        trans = (
            self.info.Transform.TransX,
            self.info.Transform.TransY,
            self.info.Transform.TransZ,
        )
        rot = (
            math.radians(self.info.Transform.RotX),
            math.radians(self.info.Transform.RotY),
            math.radians(self.info.Transform.RotZ),
        )
        scale = (
            self.info.Transform.ScaleX,
            self.info.Transform.ScaleY,
            self.info.Transform.ScaleZ,
        )
        k = {'Trans': trans, 'Rot': rot, 'Scale': scale}
        return k

    @property
    def matrix_local(self) -> Matrix:
        t = self.Transform

        # Translation matrix
        mat_loc = Matrix.Translation((t['Trans'][0],
                                      t['Trans'][1],
                                      t['Trans'][2]))

        # Rotation matrix
        mat_rot = Euler((t['Rot'][0], t['Rot'][1], t['Rot'][2]), 'XYZ')
        mat_rot = mat_rot.to_matrix().to_4x4()
        """
        mat_rotx = Matrix.Rotation(t['Rot'][0], 4, 'X')
        mat_roty = Matrix.Rotation(t['Rot'][1], 4, 'Y')
        mat_rotz = Matrix.Rotation(t['Rot'][2], 4, 'Z')
        # Rotations are stored in the ZXY order
        mat_rot = mat_rotz @ mat_rotx @ mat_roty
        """

        # Scale Matrix
        mat_scax = Matrix.Scale(t['Scale'][0], 4, (1, 0, 0))
        mat_scay = Matrix.Scale(t['Scale'][1], 4, (0, 1, 0))
        mat_scaz = Matrix.Scale(t['Scale'][2], 4, (0, 0, 1))
        mat_sca = mat_scax @ mat_scay @ mat_scaz

        return mat_loc @ mat_rot @ mat_sca

    @property
    def Type(self):
        return self.info.Type
