# List structure. This is a custom list that has a name and contains a number of a single structs

from xml.etree.ElementTree import SubElement

class List():
    def __init__(self, *args):
        self.subElements = [] # the list of the sub elements
        for e in args:
            self.subElements.append(e)

    def give_parent(self, parent):
        self.parent = parent

    def make_elements(self, name):
        # iterate through the elements in the list and call their make_elements function
        # all objects in this list class will be another class with a make_elements function defined as they should all be a subclass of Struct.
        self.element = SubElement(self.parent, 'Property', {'name': name})
        for element in self.subElements:
            element.give_parent(self.element)
            element.make_elements()

    def append(self, element):
        self.subElements.append(element)
