# misc helper functions


def get_children(obj, curr_children, obj_types, condition=lambda x: True,
                 just_names=False):
    # return a flattened list of all the children of an object of a specified
    # type.
    # condition is a function applied to the child, and if it returns true,
    # then add the child to the list
    # if just_name is True, then only return the names, otherwise return the
    # actual objects themselves
    if type(obj_types) == str:
        obj_types = [obj_types]
    # otherwise we'll just assume that it is a list of strings
    for child in obj.children:
        if (child.NMSNode_props.node_types in obj_types and
                condition(child) is True):
            if just_names:
                curr_children.append(child.name)
            else:
                curr_children.append(child)
        curr_children += get_children(child, list(), obj_types, condition,
                                      just_names)
    return curr_children
