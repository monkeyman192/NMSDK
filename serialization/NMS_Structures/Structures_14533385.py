from typing import Annotated, Optional
from dataclasses import dataclass
from functools import cached_property

from serialization.cereal_bin.structdata import datatype, Field
import serialization.cereal_bin.basic_types as bt

from serialization.NMS_Structures.NMS_types import Vector4f, NMS_list, astring, VariableSizeString
import serialization.NMS_Structures.Structures_core as sc


# Materials structures


@dataclass
class TkMaterialFlags(datatype):
    MaterialFlag: Annotated[int, Field(bt.uint32)]


@dataclass
class TkMaterialUniform(datatype):
    Values: Annotated[tuple[float, float, float, float], Field(Vector4f)]
    ExtendedValues: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f])]
    Name: Annotated[str, Field(bt.string, 0x20)]


@dataclass
class TkMaterialSampler(datatype):
    MaterialAlternativeId: Annotated[str, Field(astring, 0x20)]
    Anisotropy: Annotated[int, Field(bt.int32)]
    TextureAddressMode: Annotated[int, Field(bt.uint32)]
    TextureFilterMode: Annotated[int, Field(bt.uint32)]
    Map: Annotated[str, Field(bt.string, 0x80)]
    Name: Annotated[str, Field(bt.string, 0x20)]
    IsCube: Annotated[bool, Field(bt.boolean)]
    IsSRGB: Annotated[bool, Field(bt.boolean)]
    UseCompression: Annotated[bool, Field(bt.boolean)]
    UseMipMaps: Annotated[bool, Field(bt.boolean)]


@dataclass
class TkMaterialData(datatype):
    Flags: Annotated[list[TkMaterialFlags], Field(datatype=NMS_list[TkMaterialFlags])]
    Link: Annotated[str, Field(VariableSizeString)]
    Metamaterial: Annotated[str, Field(VariableSizeString)]
    Name: Annotated[str, Field(VariableSizeString)]
    Samplers: Annotated[list[TkMaterialSampler], Field(datatype=NMS_list[TkMaterialSampler])]
    Shader: Annotated[str, Field(VariableSizeString)]
    Uniforms: Annotated[list[TkMaterialUniform], Field(datatype=NMS_list[TkMaterialUniform])]
    ShaderMillDataHash: Annotated[int, Field(bt.int64)]
    TransparencyLayerID: Annotated[int, Field(bt.int32)]
    Class: Annotated[str, Field(bt.string, 0x20)]
    CastShadow: Annotated[bool, Field(bt.boolean)]
    CreateFur: Annotated[bool, Field(bt.boolean)]
    DisableZTest: Annotated[bool, Field(bt.boolean)]


# Geometry structures


@dataclass
class TkVertexElement(datatype):
    PlatformData: Annotated[int, Field(bt.int64)]
    Instancing: Annotated[int, Field(bt.uint32)]
    Normalise: Annotated[int, Field(bt.int32)]
    Offset: Annotated[int, Field(bt.int32)]
    SemanticID: Annotated[int, Field(bt.int32)]
    Size: Annotated[int, Field(bt.int32)]
    Type: Annotated[int, Field(bt.int32)]


@dataclass
class TkVertexLayout(datatype):
    VertexElements: Annotated[list[TkVertexElement], Field(NMS_list[TkVertexElement])]
    PlatformData: Annotated[int, Field(bt.int64)]
    ElementCount: Annotated[int, Field(bt.int32)]
    Stride: Annotated[int, Field(bt.int32)]


@dataclass
class TkJointBindingData(datatype):
    InvBindMatrix: Annotated[list[float], Field(bt.single, length=0x10)]
    BindRotate: Annotated[list[float], Field(bt.single, length=0x4)]
    BindScale: Annotated[list[float], Field(bt.single, length=0x3)]
    BindTranslate: Annotated[list[float], Field(bt.single, length=0x3)]


@dataclass
class TkJointExtentData(datatype):
    JointExtentCenter: Annotated[list[float], Field(bt.single, length=0x3)]
    JointExtentMax: Annotated[list[float], Field(bt.single, length=0x3)]
    JointExtentMin: Annotated[list[float], Field(bt.single, length=0x3)]
    JointExtentStdDev: Annotated[list[float], Field(bt.single, length=0x3)]


@dataclass
class TkJointMirrorAxis(datatype):
    MirrorAxisMode: Annotated[int, Field(bt.int32)]
    RotAdjustW: Annotated[float, Field(bt.single)]
    RotAdjustX: Annotated[float, Field(bt.single)]
    RotAdjustY: Annotated[float, Field(bt.single)]
    RotAdjustZ: Annotated[float, Field(bt.single)]
    RotMirrorAxisX: Annotated[float, Field(bt.single)]
    RotMirrorAxisY: Annotated[float, Field(bt.single)]
    RotMirrorAxisZ: Annotated[float, Field(bt.single)]
    TransMirrorAxisX: Annotated[float, Field(bt.single)]
    TransMirrorAxisY: Annotated[float, Field(bt.single)]
    TransMirrorAxisZ: Annotated[float, Field(bt.single)]


@dataclass
class TkMeshMetaData(datatype):
    Hash: Annotated[int, Field(bt.uint64)]
    IndexDataOffset: Annotated[int, Field(bt.int32)]
    IndexDataSize: Annotated[int, Field(bt.int32)]
    VertexDataOffset: Annotated[int, Field(bt.int32)]
    VertexDataSize: Annotated[int, Field(bt.int32)]
    IdString: Annotated[str, Field(bt.string, 0x80)]
    DoubleBufferGeometry: Annotated[bool, Field(bt.boolean)]


@dataclass
class TkGeometryData(datatype):
    SmallVertexLayout: Annotated[TkVertexLayout, Field(TkVertexLayout)]
    VertexLayout: Annotated[TkVertexLayout, Field(TkVertexLayout)]
    BoundHullVertEd: Annotated[list[int], Field(NMS_list[int])]
    BoundHullVerts: Annotated[list[Vector4f], Field(NMS_list[Vector4f])]
    BoundHullVertSt: Annotated[list[int], Field(NMS_list[int])]
    IndexBuffer: Annotated[list[int], Field(NMS_list[int])]
    JointBindings: Annotated[list[TkJointBindingData], Field(NMS_list[TkJointBindingData])]
    JointExtents: Annotated[list[TkJointExtentData], Field(NMS_list[TkJointExtentData])]
    JointMirrorAxes: Annotated[list[TkJointMirrorAxis], Field(NMS_list[TkJointMirrorAxis])]
    JointMirrorPairs: Annotated[list[int], Field(NMS_list[int])]
    MeshAABBMax: Annotated[list[Vector4f], Field(NMS_list[Vector4f])]
    MeshAABBMin: Annotated[list[Vector4f], Field(NMS_list[Vector4f])]
    MeshBaseSkinMat: Annotated[list[int], Field(NMS_list[int])]
    MeshVertREnd: Annotated[list[int], Field(NMS_list[int])]
    MeshVertRStart: Annotated[list[int], Field(NMS_list[int])]
    SkinMatrixLayout: Annotated[list[int], Field(NMS_list[int])]
    StreamMetaDataArray: Annotated[list[TkMeshMetaData], Field(NMS_list[TkMeshMetaData])]
    CollisionIndexCount: Annotated[int, Field(bt.int32)]
    IndexCount: Annotated[int, Field(bt.int32)]
    Indices16Bit: Annotated[int, Field(bt.int32)]
    VertexCount: Annotated[int, Field(bt.int32)]


@dataclass
class TkMeshData(datatype):
    MeshDataStream: Annotated[list[bytes], Field(NMS_list[bytes])]
    Hash: Annotated[int, Field(bt.uint64)]
    IndexDataSize: Annotated[int, Field(bt.int32)]
    VertexDataSize: Annotated[int, Field(bt.int32)]
    IdString: Annotated[str, Field(bt.string, 0x80)]


@dataclass
class TkGeometryStreamData(datatype):
    StreamDataArray: Annotated[list[TkMeshData], Field(NMS_list[TkMeshData])]


# Scene related


@dataclass
class TkSceneNodeAttributeData(sc.TkSceneNodeAttributeData_T, datatype):
    Name: Annotated[str, Field(bt.string, length=0x10)]
    Value: Annotated[str, Field(VariableSizeString)]


@dataclass
class TkTransformData(sc.TkTransformData_T, datatype):
    RotX: Annotated[float, Field(bt.single)]
    RotY: Annotated[float, Field(bt.single)]
    RotZ: Annotated[float, Field(bt.single)]
    ScaleX: Annotated[float, Field(bt.single)]
    ScaleY: Annotated[float, Field(bt.single)]
    ScaleZ: Annotated[float, Field(bt.single)]
    TransX: Annotated[float, Field(bt.single)]
    TransY: Annotated[float, Field(bt.single)]
    TransZ: Annotated[float, Field(bt.single)]


@dataclass
class TkSceneNodeData(sc.TkSceneNodeData_T, datatype):
    Attributes: Annotated[list[TkSceneNodeAttributeData], Field(NMS_list[TkSceneNodeAttributeData])]
    Children: list["TkSceneNodeData"]
    Name: Annotated[str, Field(VariableSizeString)]
    Type: Annotated[str, Field(bt.string, length=0x10)]
    Transform: Annotated[TkTransformData, Field(TkTransformData)]
    NameHash: Annotated[int, Field(bt.uint32)]


TkSceneNodeData.__annotations__["Children"] = Annotated[list[TkSceneNodeData], Field(NMS_list[TkSceneNodeData])]
