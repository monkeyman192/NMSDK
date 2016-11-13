# TkMaterialData struct

from .Struct import Struct

STRUCTNAME = 'TkMaterialData'

class TkMaterialData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.Class = kwargs.get('Class', "Opaque")
        self.TransparencyLayerID = kwargs.get('TransparencyLayerID', 0)
        self.CastShadow = kwargs.get('CastShadow', "False")
        self.DisableZTest = kwargs.get('DisableZTest', "False")
        self.Link = kwargs.get('Link', None)
        self.Shader = kwargs.get('Shader', "SHADERS/UBERSHADER.SHADER.BIN")
        self.Flags = kwargs.get('Flags', None)
        self.Uniforms = kwargs.get('Uniforms', None)
        self.Samplers = kwargs.get('Samplers', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
