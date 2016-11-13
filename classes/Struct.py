# Base struct class

from xml.etree.ElementTree import SubElement, Element, ElementTree
from numbers import Number

class Struct():
    def __init__(self, **kwargs):
        pass

    def _create_dict(self):
        # every object that is self.~ is copied into a different dictionary, self.data_dict
        data_dict = dict()
        for i in self.__dict__:
            data_dict[i] = self.__dict__[i]
        self.data_dict = data_dict
        
    def give_parent(self, parent):
        self.parent = parent

    def __getitem__(self, key):
        # returns the object in self.data_dict with key
        return self.data_dict[key]

    def __setitem__(self, key, value):
        # assigns the value 'value' to self.data_dict[key]
        # currently no checking so be careful! Incorrect use could lead to incorrect exml files!!!
        self.data_dict[key] = value

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
                # only other option is for it to be a class object. This will either be a class object itself,
                data.give_parent(self.element)
                data.make_elements(pname)
