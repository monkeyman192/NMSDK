from collections import Counter
import math

from .mesh_utils import polygonalise

from mathutils import Matrix, Euler


class SceneNodeData():
    def __init__(self, info, parent: 'SceneNodeData' = None):
        self.info = info
        self.parent = parent
        self.verts = dict()
        self.idxs = list()
        self.bounded_hull = list()
        # The metadata will be read from the geometry file later.
        self.metadata = None
        self.children = list()
        children = self.info.pop('Children')
        for child in children:
            self.children.append(SceneNodeData(child, self))

# region public methods

    def Attribute(self, name, astype=str):
        # Doesn't support AltID's
        for attrib in self.info['Attributes']:
            if attrib['Name'] == name:
                return astype(attrib['Value'])

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
        self.idx_rep = Counter(self.idxs)
        print("GROUPING TRIS")
        self.new_faces = self._group_tris()

        """for face in self.faces:
            edges = [(face[0], face[1]),
                     (face[1], face[2]),
                     (face[2], face[0])]
            self.edges.extend(edges)"""

    def _group_tris(self):
        """ Take the list of indexes, and group by faces. """
        new_faces = []
        prev_idxs = set()
        curr_face_data = []
        # Iterate over the tris.
        # As far as I can tell, all tris which form a contigious n-gon are
        # consecutive.
        for tri in self.faces:
            idxs = set(tri)
            # & is the intersection operator for sets. This checks to see if
            # there are any overlapping indexes in the consecutive tris.
            if idxs & prev_idxs:
                # Add the current tri to the face being constructed.
                curr_face_data.append(tri)
            else:
                # If we have current face data, then it means that this tri is
                # part of a new n-gon and we want to write the curr_face_data
                # to the list of faces then reset it to be the current tri.
                if curr_face_data:
                    # If the face is indeed a single tri then we just add it,
                    # otherwise we need to generate the polygon.
                    if len(curr_face_data) == 1:
                        new_faces.append(curr_face_data[0])
                    else:
                        new_faces.append(polygonalise(curr_face_data))
                # Add the current tri to the curr_face_data
                curr_face_data = [tri]
            # Set the previous index as the current one.
            prev_idxs = set(tri)
        # Add the final face
        if len(curr_face_data) == 1:
            new_faces.append(curr_face_data[0])
        else:
            new_faces.append(polygonalise(curr_face_data))

        return new_faces

# region properties

    @property
    def Name(self) -> str:
        return self.info['Name']

    @property
    def Transform(self) -> dict:
        trans = (float(self.info['Transform']['TransX']),
                 float(self.info['Transform']['TransY']),
                 float(self.info['Transform']['TransZ']))
        rot = (math.radians(float(self.info['Transform']['RotX'])),
               math.radians(float(self.info['Transform']['RotY'])),
               math.radians(float(self.info['Transform']['RotZ'])))
        scale = (float(self.info['Transform']['ScaleX']),
                 float(self.info['Transform']['ScaleY']),
                 float(self.info['Transform']['ScaleZ']))
        return {'Trans': trans, 'Rot': rot, 'Scale': scale}

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
        return self.info['Type']
