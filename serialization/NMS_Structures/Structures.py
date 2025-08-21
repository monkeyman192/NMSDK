from typing import Annotated, Type
from io import BufferedWriter, BufferedReader
from dataclasses import dataclass
import struct

from serialization.cereal_bin.structdata import datatype, Field
import serialization.cereal_bin.basic_types as bt

from serialization.NMS_Structures.NMS_types import (
    Vector4f, NMS_list, astring, VariableSizeString, Quaternion_list, Vector4i
)


# Materials structures


@dataclass
class TkMaterialFlags(datatype):
    MaterialFlagEnum: Annotated[int, Field(bt.uint32)]


@dataclass
class TkMaterialFxFlags(datatype):
    MaterialFxFlagEnum: Annotated[int, Field(bt.uint32)]


@dataclass
class TkMaterialUniform_Float(datatype):
    Values: Annotated[tuple[float, float, float, float], Field(Vector4f)]
    ExtendedValues: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f])]
    Name: Annotated[str, Field(VariableSizeString)]


@dataclass
class TkMaterialUniform_UInt(datatype):
    Values: Annotated[tuple[int, int, int, int], Field(Vector4i)]
    ExtendedValues: Annotated[list[tuple[int, int, int, int]], Field(NMS_list[Vector4i])]
    Name: Annotated[str, Field(VariableSizeString)]


@dataclass
class TkMaterialSampler(datatype):
    MaterialAlternativeId: Annotated[str, Field(astring, 0x20)]
    Map: Annotated[str, Field(VariableSizeString)]
    Name: Annotated[str, Field(VariableSizeString)]
    Anisotropy: Annotated[int, Field(bt.int32)]
    TextureAddressMode: Annotated[int, Field(bt.uint32)]
    TextureFilterMode: Annotated[int, Field(bt.uint32)]
    IsCube: Annotated[bool, Field(bt.boolean)]
    IsSRGB: Annotated[bool, Field(bt.boolean)]
    UseCompression: Annotated[bool, Field(bt.boolean)]
    UseMipMaps: Annotated[bool, Field(bt.boolean)]


@dataclass
class TkMaterialData(datatype):
    Flags: Annotated[list[TkMaterialFlags], Field(datatype=NMS_list[TkMaterialFlags])]
    FxFlags: Annotated[list[TkMaterialFxFlags], Field(datatype=NMS_list[TkMaterialFxFlags])]
    Link: Annotated[str, Field(VariableSizeString)]
    Metamaterial: Annotated[str, Field(VariableSizeString)]
    Name: Annotated[str, Field(VariableSizeString)]
    Samplers: Annotated[list[TkMaterialSampler], Field(datatype=NMS_list[TkMaterialSampler])]
    Shader: Annotated[str, Field(VariableSizeString)]
    Uniforms_Float: Annotated[list[TkMaterialUniform_Float], Field(datatype=NMS_list[TkMaterialUniform_Float])]
    Uniforms_UInt: Annotated[list[TkMaterialUniform_UInt], Field(datatype=NMS_list[TkMaterialUniform_UInt])]
    ShaderMillDataHash: Annotated[int, Field(bt.int64)]
    TransparencyLayerID: Annotated[int, Field(bt.int32)]
    Class: Annotated[str, Field(bt.string, 0x20)]
    CastShadow: Annotated[bool, Field(bt.boolean)]
    CreateFur: Annotated[bool, Field(bt.boolean)]
    DisableZTest: Annotated[bool, Field(bt.boolean)]
    EnableLodFade: Annotated[bool, Field(bt.boolean)]


# Geometry structures


@dataclass
class TkVertexElement(datatype):
    Instancing: Annotated[int, Field(bt.uint32)]
    Type: Annotated[int, Field(bt.int32)]
    Normalise: Annotated[int, Field(bt.int8)]
    Offset: Annotated[int, Field(bt.int8)]
    SemanticID: Annotated[int, Field(bt.int8)]
    Size: Annotated[int, Field(bt.int8)]


@dataclass
class TkVertexLayout(datatype):
    VertexElements: Annotated[list[TkVertexElement], Field(NMS_list[TkVertexElement, 1])]
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
    IdString: Annotated[str, Field(VariableSizeString)]
    Hash: Annotated[int, Field(bt.uint64)]
    IndexDataOffset: Annotated[int, Field(bt.int32)]
    IndexDataSize: Annotated[int, Field(bt.int32)]
    VertexDataOffset: Annotated[int, Field(bt.int32)]
    VertexDataSize: Annotated[int, Field(bt.int32)]
    VertexPositionDataOffset: Annotated[int, Field(bt.int32)]
    VertexPositionDataSize: Annotated[int, Field(bt.int32)]
    DoubleBufferGeometry: Annotated[bool, Field(bt.boolean)]



# TODO: Could make class generic which may be a little cleaner...

@dataclass
class TkGeometryData(datatype):
    PositionVertexLayout: Annotated[TkVertexLayout, Field(TkVertexLayout)]
    VertexLayout: Annotated[TkVertexLayout, Field(TkVertexLayout)]
    BoundHullVertEd: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    BoundHullVerts: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f, 1])]
    BoundHullVertSt: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    # TODO: See if it's possible to read directly with numpy.
    IndexBuffer: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    JointBindings: Annotated[list[TkJointBindingData], Field(NMS_list[TkJointBindingData, 1])]
    JointExtents: Annotated[list[TkJointExtentData], Field(NMS_list[TkJointExtentData, 1])]
    JointMirrorAxes: Annotated[list[TkJointMirrorAxis], Field(NMS_list[TkJointMirrorAxis, 1])]
    JointMirrorPairs: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    MeshAABBMax: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f, 1])]
    MeshAABBMin: Annotated[list[tuple[float, float, float, float]], Field(NMS_list[Vector4f, 1])]
    MeshBaseSkinMat: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    MeshVertREnd: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    MeshVertRStart: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    ProcGenNodeNames: Annotated[list[str], Field(NMS_list[VariableSizeString, 1])]
    ProcGenParentId: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    SkinMatrixLayout: Annotated[list[int], Field(NMS_list[bt.int32, 1])]
    StreamMetaDataArray: Annotated[list[TkMeshMetaData], Field(NMS_list[TkMeshMetaData, 1])]
    CollisionIndexCount: Annotated[int, Field(bt.int32)]
    IndexCount: Annotated[int, Field(bt.int32)]
    Indices16Bit: Annotated[int, Field(bt.int32)]
    VertexCount: Annotated[int, Field(bt.int32)]


@dataclass
class TkMeshData(datatype):
    IdString: Annotated[str, Field(VariableSizeString[0xFEFE0101, b"\xFE"])]
    MeshDataStream: Annotated[bytearray, Field(NMS_list[bt.uint8, 0xFEFE0101])]
    MeshPositionDataStream: Annotated[bytearray, Field(NMS_list[bt.uint8, 0xFEFE0101])]
    Hash: Annotated[int, Field(bt.uint64)]
    IndexDataSize: Annotated[int, Field(bt.int32)]
    VertexDataSize: Annotated[int, Field(bt.int32)]
    VertexPositionDataSize: Annotated[int, Field(bt.int32)]


@dataclass
class TkGeometryStreamData(datatype):
    StreamDataArray: Annotated[list[TkMeshData], Field(NMS_list[TkMeshData, 0x101])]


# Scene related


@dataclass
class TkSceneNodeAttributeData(datatype):
    Name: Annotated[str, Field(bt.string, length=0x10)]
    Value: Annotated[str, Field(VariableSizeString)]


@dataclass
class TkTransformData(datatype):
    RotX: Annotated[float, Field(bt.single)] = 0
    RotY: Annotated[float, Field(bt.single)] = 0
    RotZ: Annotated[float, Field(bt.single)] = 0
    ScaleX: Annotated[float, Field(bt.single)] = 1
    ScaleY: Annotated[float, Field(bt.single)] = 1
    ScaleZ: Annotated[float, Field(bt.single)] = 1
    TransX: Annotated[float, Field(bt.single)] = 0
    TransY: Annotated[float, Field(bt.single)] = 0
    TransZ: Annotated[float, Field(bt.single)] = 0


@dataclass
class TkSceneNodeData(datatype):
    Attributes: Annotated[list[TkSceneNodeAttributeData], Field(NMS_list[TkSceneNodeAttributeData])]
    Children: list["TkSceneNodeData"]
    Name: Annotated[str, Field(VariableSizeString)]
    Type: Annotated[str, Field(bt.string, length=0x10)]
    Transform: Annotated[TkTransformData, Field(TkTransformData)]
    NameHash: Annotated[int, Field(bt.uint32)]
    PlatformExclusion: Annotated[int, Field(bt.int8)] = 0


TkSceneNodeData.__annotations__["Children"] = Annotated[list[TkSceneNodeData], Field(NMS_list[TkSceneNodeData])]


# Animation related

@dataclass
class TkAnimNodeFrameData(datatype):
    Rotations: Annotated[tuple[float, float, float, float], Field(Quaternion_list)]
    Scales: Annotated[list[Vector4f], Field(NMS_list[Vector4f])]
    Translations: Annotated[list[Vector4f], Field(NMS_list[Vector4f])]


@dataclass
class TkAnimNodeData(datatype):
    RotIndex: Annotated[int, Field(bt.int32)]
    ScaleIndex: Annotated[int, Field(bt.int32)]
    TransIndex: Annotated[int, Field(bt.int32)]
    Node: Annotated[str, Field(bt.string, length=0x40)]


@dataclass
class TkAnimMetadata(datatype):
    StillFrameData: Annotated[TkAnimNodeFrameData, Field(TkAnimNodeFrameData)]
    AnimFrameData: Annotated[list[TkAnimNodeFrameData], Field(NMS_list[TkAnimNodeFrameData])]
    NodeData: Annotated[list[TkAnimNodeData], Field(NMS_list[TkAnimNodeData])]
    FrameCount: Annotated[int, Field(bt.int32)]
    NodeCount: Annotated[int, Field(bt.int32)]
    Has30HzFrames: Annotated[bool, Field(bt.boolean)]


class NMSTemplate(datatype):
    _size = 0x10
    _alignment = 8
    _real_type: datatype
    _end_padding: int = 0xEEEEEE01

    @classmethod
    def deserialize(cls, buf: BufferedReader) -> datatype:
        start = buf.tell()
        offset, namehash, _ = struct.unpack("<QII", buf.read(0x10))
        ret = buf.tell()
        buf.seek(start + offset)
        if namehash in STRUCT_MAPPING:
            data = STRUCT_MAPPING[namehash].read(buf)
        else:
            raise ValueError(f"Unknown struct with name hash 0x{namehash:X}")
        buf.seek(ret)
        return data

    @classmethod
    def serialize(cls, buf: BufferedWriter, value):
        raise NotImplementedError()
        # ptr = buf.tell()
        # buf.write(struct.pack("<QII", 0, 0, cls._end_padding))
        # yield
        # cls._list_type._write_padding(buf)
        # offset = buf.tell()
        # size = len(value)
        # if size != 0:
        #     for v in value:
        #         cls._list_type._write(buf, v)
        #     buf.seek(ptr)
        #     buf.write(struct.pack("<QI", offset - ptr, size))


@dataclass
class TkResourceDescriptorData(datatype):
    Id: Annotated[str, Field(astring, 0x20)]
    Children: Annotated[list[NMSTemplate], Field(NMS_list[NMSTemplate])]
    ReferencePaths: Annotated[list[str], Field(NMS_list[VariableSizeString])]
    Chance: Annotated[float, Field(bt.single)]
    Name: Annotated[str, Field(bt.string, length=0x80)]


@dataclass
class TkResourceDescriptorList(datatype):
    Descriptors: Annotated[list[TkResourceDescriptorData], Field(NMS_list[TkResourceDescriptorData])]
    TypeId: Annotated[str, Field(bt.string, length=0x10)]


@dataclass
class TkModelDescriptorList(datatype):
    List: Annotated[list[TkResourceDescriptorList], Field(NMS_list[TkResourceDescriptorList])]


NAMEHASH_MAPPING = {
    "TkAnimMetadata": 0x8E7F1986,
    "TkSceneNodeData": 0x3DB87E47,
    "TkGeometryData": 0x819C3220,
    "TkGeometryStreamData": 0x40025754,
    "TkMaterialData": 0x4737D48A,
    "TkModelDescriptorList": 0x4026294F,
}

STRUCT_MAPPING: dict[int, Type[datatype]] = {
    0x8E7F1986: TkAnimMetadata,
    0x3DB87E47: TkSceneNodeData,
    0x819C3220: TkGeometryData,
    0x40025754: TkGeometryStreamData,
    0x4737D48A: TkMaterialData,
    0x4026294F: TkModelDescriptorList,
}
