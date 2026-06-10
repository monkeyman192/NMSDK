# TkTransformData struct

from .Struct import Struct

from ...utils.misc import truncate_float


class TkTransformData(Struct):
    def __init__(self, **kwargs):
        super(TkTransformData, self).__init__()

        """ Contents of the struct """
        self.data['TransX'] = truncate_float(kwargs.get('TransX', 0))
        self.data['TransY'] = truncate_float(kwargs.get('TransY', 0))
        self.data['TransZ'] = truncate_float(kwargs.get('TransZ', 0))
        self.data['RotX'] = truncate_float(kwargs.get('RotX', 0))
        self.data['RotY'] = truncate_float(kwargs.get('RotY', 0))
        self.data['RotZ'] = truncate_float(kwargs.get('RotZ', 0))
        self.data['ScaleX'] = truncate_float(kwargs.get('ScaleX', 1))
        self.data['ScaleY'] = truncate_float(kwargs.get('ScaleY', 1))
        self.data['ScaleZ'] = truncate_float(kwargs.get('ScaleZ', 1))
        """ End of the struct contents"""
