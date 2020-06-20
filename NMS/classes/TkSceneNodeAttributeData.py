# TkSceneNodeAttributeData struct

from .Struct import Struct
from .String import String


class TkSceneNodeAttributeData(Struct):
    def __init__(self, Name="", AltID="", Value="", fmt=None):
        super(TkSceneNodeAttributeData, self).__init__()

        """ Contents of the struct """
        self.data['Name'] = String(Name, 0x10)
        self.data['AltID'] = String(AltID, 0x10)
        self.data['Value'] = String(Value, 0x100, fmt=fmt)
        """ End of the struct contents"""
