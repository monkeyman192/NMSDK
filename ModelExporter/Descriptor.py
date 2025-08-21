# descriptor creater

# TODO: add docstrings

__author__ = "monkeyman192"

from utils.misc import get_obj_name
from NMS.classes import (List, TkModelDescriptorList, NMSString0x80,
                           TkResourceDescriptorList, TkResourceDescriptorData)
from ModelExporter.utils import get_children


# main external container. This is only slightly different to the Node_Data
# type, but we will keep it separate.
# this corresponds to the outmost TkModelDescriptorList object
class Descriptor():
    """ Main descriptor object. This is equivalent to the TkModelDescriptorList
    object. """
    def __init__(self):
        self.children = []
        self.path = ''

    def add_child(self, TypeId):
        self.children.append(Node_List(TypeId))
        return self.children[-1]

    def get_child(self, TypeId):
        for child in self.children:
            if child.TypeId == TypeId:
                return child

    def __str__(self):
        out = "Descriptor:\n"
        for child in self.children:
            out += str(child)
        return out

    def __len__(self):
        return len(self.children)

    def to_mxml(self):
        main_data = List()
        for child in self.children:
            main_data.append(child.to_mxml())
        return TkModelDescriptorList(List=main_data)


# this corresponds to the TkResourceDescriptorList object
class Node_List():
    def __init__(self, TypeId):
        self.TypeId = TypeId
        self.children = []

    def add_child(self, child):
        self.children.append(Node_Data(child))
        return self.children[-1]

    def __str__(self):
        out = ""
        for child in self.children:
            out += self.TypeId + '\n'
            out += str(child)
        return out

    def to_mxml(self):
        # converts this to a TkResourceDescriptorList object
        descriptors = List()
        for child in self.children:
            descriptors.append(child.to_mxml())
        return TkResourceDescriptorList(TypeId=self.TypeId,
                                        Descriptors=descriptors)


# this corresponds to the TkResourceDescriptorData object
class Node_Data():
    def __init__(self, obj):
        self.obj = obj
        self.children = []

    def add_child(self, TypeId):
        self.children.append(Node_List(TypeId))
        return self.children[-1]

    def get_child(self, TypeId):
        for child in self.children:
            if child.TypeId == TypeId:
                return child

    def __str__(self):
        try:
            # this will only work if called on a blender object
            out = "Node_Data " + self.obj.name + '\n'
        except AttributeError:
            out = "Node_Data" + "\n"
        for child in self.children:
            out += str(child)
        return out

    def to_mxml(self):
        # first, we need to do some processing on the name.
        # if the name starts with the prefix, then we need to sort it out so
        # that it is correct

        def not_proc(ob):
            # returns true if the object is not proc
            # nest the if statements this way as subsequent of statements
            # require the previous ones to be true
            if ob.NMSDescriptor_props.proc_prefix == "":        # ie. not proc
                if ob.NMSNode_props.node_types == "Reference":
                    if ob.NMSReference_props.reference_path != "":
                        return True
            return False

        name = get_obj_name(self.obj, None)

        # get the list off all children of self.obj that are ref nodes and
        # aren't proc
        non_proc_refs = get_children(self.obj, "Reference", not_proc)
        additional_ref_paths = set()

        for child in non_proc_refs:
            additional_ref_paths.add(child.NMSReference_props.reference_path)

        additional_refs = List()
        for path in additional_ref_paths:
            additional_refs.append(NMSString0x80(Value=path))

        if self.obj.NMSNode_props.node_types == 'Reference':
            refs = List(NMSString0x80(
                Value=self.obj.NMSReference_props.ref_path))
        else:
            refs = List()
        children = List()
        for child in self.children:
            children.append(child.to_mxml())
        # Check how many children there are so we aren't making empty
        # TkModelDescriptorList's for nothing.
        if len(children) == 0:
            _children = List()
        else:
            _children = List(TkModelDescriptorList(List=children))
        return TkResourceDescriptorData(Id=name.upper(),
                                        Name=name,
                                        ReferencePaths=refs + additional_refs,
                                        Chance=0,
                                        Children=_children)


if __name__ == "__main__":

    d = Descriptor()
    a = d.add_child('_TEST1_')
    a.add_child(int)        # just a dummy object
    a.add_child(float)
    a.add_child(str)
    b = d.add_child('_TEST2_')
    c = b.add_child(str)
    c.add_child('_SUBTEST_')
    c.add_child('_SUBTEST2_')

    print(d)
