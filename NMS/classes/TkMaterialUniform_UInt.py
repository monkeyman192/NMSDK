# TkMaterialUniform_UInt struct

from .Struct import Struct
from .String import String
from .Vector4i import Vector4i
from .List import List


class TkMaterialUniform_UInt(Struct):
    def __init__(self, **kwargs):
        super(TkMaterialUniform_UInt, self).__init__()

        """ Contents of the struct """
        self.data['Name'] = String(kwargs.get('Name', None), 0x20)
        self.data['Values'] = kwargs.get('Values', Vector4i())
        self.data['ExtendedValues'] = kwargs.get('ExtendedValues', List())
        """ End of the struct contents"""
