from typing import Annotated
from dataclasses import dataclass

from serialization.cereal_bin.structdata import datatype, Field
import serialization.cereal_bin.basic_types as bt

from serialization.NMS_Structures.NMS_types import Vector4f, NMS_list, astring


@dataclass
class TkMaterialFlags(datatype):
    MaterialFlag: Annotated[int, Field(bt.uint32)]


@dataclass
class TkMaterialUniform(datatype):
    Name: Annotated[str, Field(bt.string, 0x20)]
    Values: Annotated[tuple[float, float, float, float], Field(Vector4f)]
    ExtendedValues: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f])]


@dataclass
class TkMaterialSampler(datatype):
    Name: Annotated[str, Field(bt.string, 0x20)]
    Map: Annotated[str, Field(bt.string, 0x80)]
    IsCube: Annotated[bool, Field(bt.boolean)]
    UseCompression: Annotated[bool, Field(bt.boolean)]
    UseMipMaps: Annotated[bool, Field(bt.boolean)]
    IsSRGB: Annotated[bool, Field(bt.boolean)]
    MaterialAlternativeId: Annotated[str, Field(astring, 0x20)]
    TextureAddressMode: Annotated[int, Field(bt.uint32)]
    TextureFilterMode: Annotated[int, Field(bt.uint32)]
    Anisotropy: Annotated[int, Field(bt.int32)]


@dataclass
class TkMaterialData(datatype):
    Name: Annotated[str, Field(bt.string, 0x80)]
    Metamaterial: Annotated[str, Field(bt.string, 0x100)]
    Class: Annotated[str, Field(bt.string, 0x20)]
    TransparencyLayerID: Annotated[int, Field(bt.int32)]
    CastShadow: Annotated[bool, Field(bt.boolean)]
    DisableZTest: Annotated[bool, Field(bt.boolean)]
    CreateFur: Annotated[bool, Field(bt.boolean)]
    Link: Annotated[str, Field(bt.string, 0x80)]
    Shader: Annotated[str, Field(bt.string, 0x80)]
    Flags: Annotated[list[TkMaterialFlags], Field(datatype=NMS_list[TkMaterialFlags])]
    Uniforms: Annotated[list[TkMaterialUniform], Field(datatype=NMS_list[TkMaterialUniform])]
    Samplers: Annotated[list[TkMaterialSampler], Field(datatype=NMS_list[TkMaterialSampler])]
    ShaderMillDataHash: Annotated[int, Field(bt.int64)]


# Geometry structures


@dataclass
class TkVertexElement(datatype):
    SemanticID: Annotated[int, Field(bt.int32)]
    Size: Annotated[int, Field(bt.int32)]
    Type: Annotated[int, Field(bt.int32)]
    Offset: Annotated[int, Field(bt.int32)]
    Normalise: Annotated[int, Field(bt.int32)]
    Instancing: Annotated[int, Field(bt.uint32)]
    PlatformData: Annotated[int, Field(bt.int64)]


@dataclass
class TkVertexLayout(datatype):
    ElementCount: Annotated[int, Field(bt.int32)]
    Stride: Annotated[int, Field(bt.int32)]
    PlatformData: Annotated[int, Field(bt.int64)]
    VertexElements: Annotated[list[TkVertexElement], Field(NMS_list[TkVertexElement])]


@dataclass
class TkJointBindingData(datatype):
    InvBindMatrix: Annotated[list[float], Field(bt.single, length=0x10)]
    BindTranslate: Annotated[list[float], Field(bt.single, length=0x3)]
    BindRotate: Annotated[list[float], Field(bt.single, length=0x4)]
    BindScale: Annotated[list[float], Field(bt.single, length=0x3)]
