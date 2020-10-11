import xml.etree.ElementTree as ET


def scene_to_dict(fpath: str) -> dict:
    tree = ET.parse(fpath)
    root = tree.getroot()
    return element_to_dict(root)


def element_to_dict(node: ET.Element) -> dict:
    """ Converts an element object to a dictionary. """
    data = dict()
    for elem in list(node):
        # determine what the value is.
        # If there is no value then we have a list:
        if elem.get('value') is None:
            lst = list()
            for e in list(elem):
                lst.append(element_to_dict(e))
            # Sort the entries by name.
            #TODO: This is a temp fix to get around the issue of scene not
            # always having nodes in alphabetical order. A better solution is
            # to ensure they are exported in the same order as they were
            # imported.
            lst.sort(key=lambda x: x['Name'])
            data[elem.get('name')] = lst
        elif '.xml' in elem.get('value'):
            # In this case we are loading a sub-struct.
            # Apply this function recursively.
            data[elem.get('name')] = element_to_dict(elem)
        else:
            # It's just a value.
            data[elem.get('name')] = elem.get('value')
    return data
