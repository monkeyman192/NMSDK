# Miscellaneous useful functions

# stdlib imports
from array import array
from hashlib import sha256
# blender imports
import bpy
from mathutils import Matrix, Vector
# Internal imports
from ..NMS.classes import Vector4f


ALL_TYPES = ['Reference', 'Mesh', 'Locator', 'Collision', 'Light', 'Joint']


# region Misc


def get_actions_with_name(anim_name):
    """ Get all the actions which are part of the same animation.

    Parameters
    ----------
    anim_name : str
        Base name of the action.

    Returns
    -------
    actions : list
        List of all the actions which have an action with the name provided.
    """
    actions = list()
    for action in bpy.data.actions:
        action_name = action.name.split('.', 1)[0]
        if action_name == anim_name:
            actions.append(action)
    return actions


def get_all_actions_in_scene(scene):
    """ Get a list of all action names in a scene.
    Actions of the form NAME.XYZ are considered just action NAME.

    Returns
    -------
    actions : set
        Set containing the names of all actions within the scene.
    """
    actions = set()
    for obj in scene.objects:
        obj_actions = get_all_actions(obj)
        if obj_actions:
            for action in obj_actions:
                # Add action name which is just the first component of the
                # unique action name blender uses
                actions.add(action[2].name.split('.')[0])
    return actions


def get_all_actions(obj):
    """Retrieve all actions given a blender object. Includes NLA-actions
       Full credit to this code goes to misnomer on blender.stackexchange
       (cf. https://blender.stackexchange.com/questions/14204/how-to-tell-which-object-uses-which-animation-action)  # noqa
    """
    # slightly modified to return the name of the object, and the action
    if obj.animation_data:
        if obj.animation_data.action:
            yield (obj.name, obj.NMSAnimation_props.anim_name,
                   obj.animation_data.action)
        for track in obj.animation_data.nla_tracks:
            for strip in track.strips:
                yield obj.name, obj.NMSAnimation_props.anim_name, strip.action


def get_children(obj, obj_types=ALL_TYPES, condition=lambda x: True,
                 just_names=False, flatten=True):
    """ Return all the children of an object of a specified type.

    Parameters
    ----------
    obj : bpy.types.Object
        The blender object to get the children of.
    obj_types : str or list or str's
        The object type(s) that we want children of. This can be a single type
        (eg. 'Mesh'), or a list (['Mesh', 'Locator']).
    condition : function
        A function which will be applied to the children. If it returns True
        then the child will be added to the list of children.
    just_names : bool
        If True, then just the name will be returned, otherwise it will return
        the objects themselves.
    """
    curr_children = list()
    if isinstance(obj_types, str):
        obj_types = [obj_types]
    # otherwise we'll just assume that it is a list of strings
    for child in obj.children:
        if (child.NMSNode_props.node_types in obj_types and
                condition(child) is True):
            if just_names:
                curr_children.append(child.name)
            else:
                curr_children.append(child)
        curr_children += get_children(child, obj_types, condition, just_names,
                                      flatten)
    return curr_children


# simple function to take a list and move the entry at the ith index to the the
# index 'index' (in the new list with the value pop'd)
def movetoindex(lst, i, index):
    k = lst.pop(i)          # this will break if i > len(lst)...
    return lst[:index] + [k] + lst[index:]


def nmsHash(data):
    """
    Lazy hash function for mesh data
    This is simply the last 16 hexadecimal digits of a sha256 hash
    """
    if isinstance(data, list):
        d = array('f')
        for verts in data:
            d.extend(verts)
    else:
        d = data
    return int(sha256(d).hexdigest()[-16:], 16)


def traverse(obj):
    # a custom generator to iterate over the tree of all the children on the
    # scene (including the Model object)
    # this returns objects from the branches inwards (which *shouldn't* be a
    # problem...)
    for child in obj.Children:
        for subvalue in traverse(child):
            yield subvalue
    else:
        yield obj


# region Transform Functions


def apply_local_transform(rotmat, data, normalize=True, use_norm_mat=False):
    """ Applys a local transform to the supplied data.

    Parameters
    ----------
    data : list of tuples
        The source data.
    normalize : bool
        Whether or not to normalize the resultant vector.
    use_norm_mat : bool
        Whether or not to use the normalized rotation matrix.
        This will be used for tangents and normals.

    This operation occurs in place
    """
    if use_norm_mat:
        norm_mat = rotmat.inverted().transposed()
    for i in range(len(data)):
        if use_norm_mat:
            _data = norm_mat @ Vector((data[i]))
        else:
            _data = rotmat @ Vector((data[i]))
        if normalize:
            _data.normalize()
        data[i] = (_data[0], _data[1], _data[2], 1.0)


# TODO: !REMOVE
def apply_local_transforms(rotmat, verts, norms, tangents, chverts):
    norm_mat = rotmat.inverted().transposed()

    for i in range(len(verts)):
        # Load Vertex
        vert = rotmat * Vector((verts[i]))
        # Store Transformed
        verts[i] = (vert[0], vert[1], vert[2], 1.0)
        # Load Normal
        norm = norm_mat * Vector((norms[i]))
        norm.normalize()
        # Store Transformed normal
        norms[i] = (norm[0], norm[1], norm[2], 1.0)
        # Load Tangent
        tang = norm_mat * Vector((tangents[i]))
        tang.normalize()
        # Store Transformed tangent
        tangents[i] = (tang[0], tang[1], tang[2], 1.0)
    for i in range(len(chverts)):
        chvert = rotmat * Vector((chverts[i]))
        # chvert = chverts[i]
        chverts[i] = Vector4f(x=chvert[0], y=chvert[1], z=chvert[2], t=1.0)


def calc_tangents(faces, verts, norms, uvs):
    """ Calculate the tangents.

    Parameters
    ----------
    faces : Unknown
    verts : Unknown
    norms : Unknown
    uvs : Unknown

    Returns
    -------
    tangents : Unknown
    """
    tangents = []
    # Init tangents
    for i in range(len(verts)):
        tangents.append(Vector((0, 0, 0, 0)))
    # We assume that verts length will be a multiple of 3 since
    # the mesh has been triangulated

    trisNum = len(faces)
    # Iterate in triangles
    for i in range(trisNum):
        tri = faces[i]
        vert_1 = tri[0]
        vert_2 = tri[1]
        vert_3 = tri[2]

        # Get Point Positions
        P0 = Vector((verts[vert_1]))
        P1 = Vector((verts[vert_2])) - P0
        P2 = Vector((verts[vert_3])) - P0

        P0_uv = Vector((uvs[vert_1]))
        P1_uv = Vector((uvs[vert_2])) - P0_uv
        P2_uv = Vector((uvs[vert_3])) - P0_uv
        # Keep only the 1st uvmap
        P1_uv = P1_uv.xy
        P2_uv = P2_uv.xy

        # Matrix determinant
        D = P1_uv[0] * P2_uv[1] - P2_uv[0] * P1_uv[1]
        D = 1.0 / max(D, 0.0001)  # Store the inverse right away

        # Apply equation
        tang = D * (P2_uv[1] * P1 - P1_uv[1] * P2)

        # Orthogonalize Gram-Shmidt
        n = Vector(norms[vert_1])
        tang = tang - n * tang.dot(n)
        # tang.normalize()

        # Add to existing
        # Vert_1
        tangents[vert_1] += tang
        # Vert_2
        tangents[vert_2] += tang
        # Vert_3
        # tang3 = Vector(tangents[vert_3]) + tang;
        # tang3.normalize()
        tangents[vert_3] += tang

    # Fix tangents
    for i in range(len(verts)):
        tang = tangents[i]
        tang.normalize()
        # (tangents[i].x, tangents[i].z, -tangents[i].y, 1.0)
        tangents[i] = (tangents[i].x, tangents[i].y, tangents[i].z, 1.0)

    return tangents


def transform_to_NMS_coords(ob):
    # this will return the local transform, rotation and scale of the object in
    # the NMS coordinate system

    M = Matrix()
    M[0] = Vector((1.0, 0.0, 0.0, 0.0))
    M[1] = Vector((0.0, 0.0, 1.0, 0.0))
    M[2] = Vector((0.0, -1.0, 0.0, 0.0))
    M[3] = Vector((0.0, 0.0, 0.0, 1.0))

    Minv = Matrix()
    Minv[0] = Vector((1.0, 0.0, 0.0, 0.0))
    Minv[1] = Vector((0.0, 0.0, -1.0, 0.0))
    Minv[2] = Vector((0.0, 1.0, 0.0, 0.0))
    Minv[3] = Vector((0.0, 0.0, 0.0, 1.0))

    return (M @ ob.matrix_local @ Minv).decompose()
