# TkMaterialUniform struct

from .Struct import Struct

STRUCTNAME = 'TkMaterialUniform'

class TkMaterialUniform(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.Values = kwargs.get('Values', None)
        self.ExtendedValues = kwargs.get('ExtendedValues', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
