# TkSceneNodeAttributeData struct

from .Struct import Struct
from .String import String


class TkSceneNodeAttributeData(Struct):
    """ A TkSceneNodeAttributeData object.
    Unlike many others, this has no kwargs since we require some defaults
    and some extra values to be passed in for better functionality.
    """
    def __init__(self, Name="", AltID="", Value="", fmt=None, orig=None):
        super(TkSceneNodeAttributeData, self).__init__()

        """ Contents of the struct """
        self.data['Name'] = String(Name, 0x10)
        if orig:
            # Set the values as specificed by the 'orig' argument
            self.data['AltID'] = String(orig[0], 0x10)
            self.data['Value'] = String(orig[1], 0x100)
        else:
            self.data['AltID'] = String(AltID, 0x10)
            self.data['Value'] = String(Value, 0x100, fmt=fmt)
        """ End of the struct contents"""
