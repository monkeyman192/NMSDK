import xml.etree.ElementTree as ET


def mxml_to_dict(fpath: str) -> dict:
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
            data[elem.get('name')] = lst
        elif '.xml' in elem.get('value'):
            # In this case we are loading a sub-struct.
            # Apply this function recursively.
            data[elem.get('name')] = element_to_dict(elem)
        else:
            # It's just a value.
            data[elem.get('name')] = elem.get('value')
    return data
