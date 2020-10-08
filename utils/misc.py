# Blender imports
import bpy


def clone_node(node, include_children=False, new_parent=None):
    """ Create a clone of the provided "node".

    Parameters
    ----------
    node : bpy_types.Object
        The node to clone.
    include_children : bool
        If True, then the children of `node` will also be cloned recursively.
    new_parent : bpy_types.Object
        The object that will be assigned as the parent of the newly copied node
    """
    # Copy the node then assign it its new parent.
    new_node = node.copy()
    # If there is no new_parent, then it will be the same as the parent of the
    # original node by default.
    if not new_parent:
        new_parent = node.parent
    new_node.parent = new_parent
    bpy.context.scene.collection.objects.link(new_node)
    if include_children:
        # Go over the children and clone them, assigning the parent as the
        # newly cloned node above.
        for child in node.children:
            clone_node(child, include_children, new_node)


def CompareMatrices(mat1, mat2, tol):
    """
    This will check whether the entires are pair-wise close enough (within tol)
    """
    # just going to assume they are the same size...
    for i in range(len(mat1)):
        for j in range(len(mat1)):
            if abs(mat1[i][j] - mat2[i][j]) > tol:
                return False
    return True


def ContinuousCompare(lst, tol):
    """
    Takes a list of tuples, and each element is compared to the next one.
    Any tuple that changes has the index of it returned.

    Parameters
    ----------
    lst : list of tuples
        A list of tuples which are animation data.
    tol : float
        The minimum difference between two consecutive values before they are
        considered different.

    Returns
    -------
    changing_indices : set
        The indexes that of the components of the tuple that change.
    """
    changing_indices = set()
    last_tup = None
    # iterate over all the tuples
    for i in range(len(lst)):
        # if it's the first entry, we just want to assign it and move onto the
        # next iteration
        if i == 0:
            last_tup = lst[i]
            continue
        else:
            tup = lst[i]
        # remove the indices already found to change so we don't keep testing
        # them
        indices_left_to_check = set(range(len(tup))) - changing_indices
        for j in indices_left_to_check:
            if (tup[j] - last_tup[j]).magnitude > tol:
                # if it changes, add it to the list
                changing_indices.add(j)
        last_tup = tup
    return changing_indices


def getParentRefScene(obj):
    """
    Returns the parent reference scene for the provided object.
    This is determined by whether the object has a parent at any point that is
    a reference node.
    """
    if obj.parent is None:
        return None
    if obj.parent.NMSNode_props.node_types == 'Reference':
        return obj.parent
    else:
        return getParentRefScene(obj.parent)


def get_root_node(obj):
    """ Returns the root node for the NMS scene. """
    if obj.parent is None and obj.NMSNode_props.node_types == 'Reference':
        return obj
    if obj.parent is not None:
        return get_root_node(obj.parent)


def get_obj_name(obj, export_name):
    if obj.NMSNode_props.override_name != '':
        return obj.NMSNode_props.override_name
    if obj.NMSNode_props.node_types == 'Reference':
        # Reference types can have their name come from a few different places
        if obj.NMSReference_props.scene_name != '':
            name = obj.NMSReference_props.scene_name.upper()
        elif obj.name.startswith('NMS_'):
            # This is the old format. Use the name of that it is being
            # saved as.
            if obj.name == 'NMS_SCENE':
                name = export_name
            else:
                name = obj.name[4:].upper()
        elif obj.name.endswith('.SCENE'):
            # Trim the `.SCENE` part.
            name = obj.name[:-6]
        else:
            # Just use the provided name.
            name = obj.name.upper()
    else:
        # Everything else we will just take the name it is given without the
        # NMS_ at the front if it has it.
        name = obj.name
        if name.startswith('NMS_'):
            name = name[4:].upper()
    return name


def truncate_float(val):
    """ Return the float value but truncated to at most 6 dp's. """
    new_val = float(f'{val:.6f}')
    if new_val == 0:
        return 0
    else:
        return new_val
