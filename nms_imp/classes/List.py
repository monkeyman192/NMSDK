# List structure. This is a custom list that has a name and contains a number of a single structs

from xml.etree.ElementTree import SubElement
from .SerialisationMethods import list_header as header
from .SerialisationMethods import serialise

class List():
    def __init__(self, *args, **kwargs):
        self.size = 0x10        # this is how much space the list takes up in a struct
        self.subElements = [] # the list of the sub elements
        self._format = kwargs.get('_format', None)
        for e in args:
            self.subElements.append(e)

        self.curr_index = 0

    def give_parent(self, parent):
        self.parent = parent

    def make_elements(self, name):
        # iterate through the elements in the list and call their make_elements function
        # all objects in this list class will be another class with a make_elements function defined as they should all be a subclass of Struct.
        self.element = SubElement(self.parent, 'Property', {'name': name})
        try:
            for element in self.subElements:
                element.give_parent(self.element)
                element.make_elements()
        except:
            return

    def append(self, element):
        self.subElements.append(element)

    def __len__(self):
        self.length = len(self.subElements)
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr_index >= len(self):
            raise StopIteration
        else:
            self.curr_index += 1
            return self.subElements[self.curr_index - 1]

    def __bytes__(self):
        data = bytearray()
        for val in self.subElements:
            try:
                data.extend(bytes(val))
            except:
                data.extend(serialise(val))
        return bytes(data)

    def data_len(self):
        # returns the total length of the data when it would be serialised (TOTAL. ie. size of each element * length of list)
        try:
            return len(self.subElements[0])*len(self)
        except TypeError:
            return 4*len(self)
        except IndexError:
            return 0

    def serialise(self, output, list_worker, move_end = False, return_data = False):
        # this will return the actual block of serialised data the list contains
        if len(self) != 0:
            offset = list_worker['end'] - list_worker['curr']
        else:
            offset = 0
        size = len(self)
        h = header(offset, size)
        print(len(h), 'bloop')
        output.write(h)      # this serialises the list header.
        list_worker['curr'] += 0x10

        # now sort out the actual contents
        # this is going to be the actual data that gets put into the list
        data_out = ""
        for e in self.subElements:
            if hasattr(e, 'serialise'):
                data_out += e.serialise(output, list_worker, return_data = True)
            else:
                data_out += serialise(e)
        # let's just put in a check:
        #if len(data_out) != self.data_len():
        #    print(len(data_out), self.data_len())
        #    print("?!?! something has gone wrong???")
        list_worker.dataQ.append(data_out)
        list_worker['end'] += self.data_len()
