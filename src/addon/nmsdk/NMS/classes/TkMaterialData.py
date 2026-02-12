# TkMaterialData struct

from .Struct import Struct
from .List import List
from .TkMaterialFlags import TkMaterialFlags
from .TkMaterialUniform_Float import TkMaterialUniform_Float
from .TkMaterialUniform_UInt import TkMaterialUniform_UInt
from .TkMaterialSampler import TkMaterialSampler
from .Vector4f import Vector4f
from .Vector4i import Vector4i
from .String import String


class TkMaterialData(Struct):
    def __init__(self, **kwargs):
        super(TkMaterialData, self).__init__()

        """ Contents of the struct """
        self.data['Name'] = String(kwargs.get('Name', ""), 0x80)
        self.data['Metamaterial'] = String(kwargs.get('Metamaterial', ""), 0x80)
        self.data['Class'] = String(kwargs.get('Class', "Opaque"), 0x20)
        self.data['TransparencyLayerID'] = kwargs.get('TransparencyLayerID', 0)
        self.data['CastShadow'] = kwargs.get('CastShadow', "false")
        self.data['DisableZTest'] = kwargs.get('DisableZTest', "false")
        self.data['CreateFur'] = kwargs.get('CreateFur', "false")
        self.data['EnableLodFade'] = kwargs.get('EnableLodFade', "false")
        self.data['Link'] = String(kwargs.get('Link', ""), 0x80)
        self.data['Shader'] = String(
            kwargs.get('Shader', "SHADERS/UBERSHADER.SHADER.BIN"), 0x80)
        self.data['Flags'] = kwargs.get('Flags', List(TkMaterialFlags()))
        self.data['FxFlags'] = kwargs.get('FxFlags', None)
        self.data['Uniforms_Float'] = kwargs.get(
            'Uniforms_Float',
            List(
                TkMaterialUniform_Float(
                    Name="gMaterialColourVec4",
                    Values=Vector4f(X=1.000000, Y=1.000000, Z=1.000000, W=1.000000)),
                TkMaterialUniform_Float(
                    Name="gMaterialParamsVec4",
                    Values=Vector4f(X=0.900000, Y=0.500000, Z=0.000000, W=0.000000)),
                TkMaterialUniform_Float(
                    Name="gMaterialParams2Vec4",
                    Values=Vector4f(X=0.900000, Y=0.500000, Z=0.000000, W=0.000000)),
                TkMaterialUniform_Float(
                    Name="gMaterialSFXVec4",
                    Values=Vector4f()),
                TkMaterialUniform_Float(
                    Name="gMaterialSFXColVec4",
                    Values=Vector4f())))
        self.data['Uniforms_UInt'] = kwargs.get(
            'Uniforms_UInt',
            List(
                TkMaterialUniform_UInt(
                    Name="gDynamicFlags",
                    Values=Vector4i(X=3, Y=0, Z=0, W=0))))
        self.data['Samplers'] = kwargs.get('Samplers', TkMaterialSampler())
        self.data['ShaderMillDataHash'] = kwargs.get('Metamaterial', 0)
        """ End of the struct contents"""
