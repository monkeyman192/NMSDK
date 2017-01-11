# Primary Object class.
# Each object in blender will be passed into this class. Any children are added as child objects.

from xml.etree.ElementTree import SubElement, Element, ElementTree
from .TkSceneNodeData import TkSceneNodeData
from .TkSceneNodeAttributeData import TkSceneNodeAttributeData
from .List import List
from numbers import Number

class Object():
    def __init__(self, Type, Name, **kwargs):
        self.Type = Type        # This can be any of a number of things. The parent object will generally be a MESH type
        self.name = Name
        self.Vertices = kwargs.get('Vertices', [])
        self.Indexes = kwargs.get('Indexes', [])
        self.Transform = kwargs.get('Transform', None)

        self.Attributes = []

        self.Children = []

    def _create_dict(self):
        # every object that is self.~ is copied into a different dictionary, self.data_dict
        data_dict = dict()
        for i in self.__dict__:
            data_dict[i] = self.__dict__[i]
        self.data_dict = data_dict
        
    def give_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        self.Children.append(child)

    def __getitem__(self, key):
        # returns the object in self.data_dict with key
        return self.data_dict[key]

    def __setitem__(self, key, value):
        # assigns the value 'value' to self.data_dict[key]
        # currently no checking so be careful! Incorrect use could lead to incorrect exml files!!!
        self.data_dict[key] = value

    def process(self):
        # this is where the main processing of the child nodes occurs.
        pass

    def construct_data(self):
        # iterate through all the children and create a TkSceneNode for every child with the appropriate properties.
        
        # call each child's process function
        self.Child_Nodes = List()
        for node in self.Children:
            node.process()
            self.Child_Nodes.append(node.get_data)      # this will return the self.NodeData object in the child Object

        # next, create a TkSceneNodeData object and fill it with data
        # this won't get call until all the child nodes have already had their TkSceneNodeData objects created
        self.NodeData = TkSceneNodeData(Name = self.Name,
                                        Type = self.Type,
                                        Transform = self.Transform,
                                        Attributes = self.Attributes,
                                        Children = self.Child_Nodes)
        

    def make_elements(self, name=None, main=False):
        # creates a sub element tree that is to be returned or read by the parent class
        # the optional 'main' argument is a boolean value that is almost always False.
        # In the case of it being true, the SubElement is the primary one, and needs a 'Data' tag, not a 'Property' tag

        # if a name is given then the struct is a single sub element.
        # If no name is given then the sub element must be in a list and give it no name as the name is in the list
        if main == False:
            if name is not None:
                self.element = SubElement(self.parent, 'Property', {'name': name, 'value':self.STRUCTNAME + '.xml'})
            else:
                self.element = SubElement(self.parent, 'Property', {'value':self.STRUCTNAME + '.xml'})
        elif main == True:
            # in this case, we expect the name to be specified.
            # parent can be None in this case as it is is the main element
            self.element = Element('Data', {'template': self.STRUCTNAME})
            self.tree = ElementTree(self.element)

        # iterate through all the data and determine type and sort it out appropriately
        for pname in self.data_dict:
            data = self.data_dict[pname]
            if isinstance(data, Number):
                # in this case convert the int or foat to a string
                SubElement(self.element, 'Property', {'name': pname, 'value': str(data)})
            elif isinstance(data, str):
                # in this case we just add the string value as normal
                SubElement(self.element, 'Property', {'name': pname, 'value': data})
            elif isinstance(data, list):
                # in this case we need to add each element of the list as a sub property
                # first add the name as a SubElement
                SE = SubElement(self.element, 'Property', {'name': pname})
                for i in data:
                    SubElement(SE, 'Property', {'value': str(i)})
            elif data is None:
                SubElement(self.element, 'Property', {'name': pname})
            else:
                # only other option is for it to be a class object.
                data.give_parent(self.element)
                data.make_elements(pname)
