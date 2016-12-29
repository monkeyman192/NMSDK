# TkMaterialData struct

from .Struct import Struct
from .List import List
from .TkMaterialFlags import TkMaterialFlags
from .TkMaterialUniform import TkMaterialUniform
from .Vector4f import Vector4f

STRUCTNAME = 'TkMaterialData'

class TkMaterialData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.Class = kwargs.get('Class', "Opaque")
        self.TransparencyLayerID = kwargs.get('TransparencyLayerID', 0)
        self.CastShadow = kwargs.get('CastShadow', "False")
        self.DisableZTest = kwargs.get('DisableZTest', "False")
        self.Link = kwargs.get('Link', "")
        self.Shader = kwargs.get('Shader', "SHADERS/UBERSHADER.SHADER.BIN")
        self.Flags = kwargs.get('Flags', List(TkMaterialFlags()))
        self.Uniforms = kwargs.get('Uniforms', List(TkMaterialUniform(Name="gMaterialColourVec4",
                                                                      Values=Vector4f(x=1.0, y=1.0, z=1.0, t=1.0)),
                                                    TkMaterialUniform(Name="gMaterialParamsVec4",
                                                                      Values=Vector4f(x=0.9, y=0.5, z=0.0, t=0.0)),
                                                    TkMaterialUniform(Name="gMaterialSFXVec4",
                                                                      Values=Vector4f()),
                                                    TkMaterialUniform(Name="gMaterialSFXColVec4",
                                                                      Values=Vector4f())))
        self.Samplers = kwargs.get('Samplers', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
