from collections import namedtuple
from functools import cached_property
from typing import Optional


gstream_info = namedtuple(
    'gstream_info',
    ['vert_size', 'vert_off', 'idx_size', 'idx_off']
)


# Useful regex: Annotated\[([^,]+).*


class TkSceneNodeAttributeData_T:
    Name: str
    Value: str


class TkTransformData_T:
    RotX: float
    RotY: float
    RotZ: float
    ScaleX: float
    ScaleY: float
    ScaleZ: float
    TransX: float
    TransY: float
    TransZ: float


class TkSceneNodeData_T:
    Attributes: list[TkSceneNodeAttributeData_T]
    Children: list["TkSceneNodeData_T"]
    Name: str
    Type: str
    Transform: TkTransformData_T
    NameHash: int

    @cached_property
    def attributes(self):
        return {attr.Name: attr.Value for attr in self.Attributes}

    def iter(self, filter_type: Optional[str] = None):
        # if filter_type is None or self.Type == filter_type:
        #     yield self
        for child in self.Children:
            if filter_type is None or self.Type == filter_type:
                yield child
            for subchild in child.iter(filter_type):
                yield subchild


class TkVertexElement_T:
    PlatformData: int
    Instancing: int
    Normalise: int
    Offset: int
    SemanticID: int
    Size: int
    Type: int


class TkVertexLayout_T:
    VertexElements: list[TkVertexElement_T]
    PlatformData: int
    ElementCount: int
    Stride: int


class TkJointBindingData_T:
    InvBindMatrix: list[float]
    BindRotate: list[float]
    BindScale: list[float]
    BindTranslate: list[float]


class TkJointExtentData_T:
    JointExtentCenter: list[float]
    JointExtentMax: list[float]
    JointExtentMin: list[float]
    JointExtentStdDev: list[float]


class TkJointMirrorAxis_T:
    MirrorAxisMode: int
    RotAdjustW: float
    RotAdjustX: float
    RotAdjustY: float
    RotAdjustZ: float
    RotMirrorAxisX: float
    RotMirrorAxisY: float
    RotMirrorAxisZ: float
    TransMirrorAxisX: float
    TransMirrorAxisY: float
    TransMirrorAxisZ: float


class TkMeshMetaData_T:
    Hash: int
    IndexDataOffset: int
    IndexDataSize: int
    VertexDataOffset: int
    VertexDataSize: int
    IdString: str
    DoubleBufferGeometry: bool


class TkGeometryData_T:
    SmallVertexLayout: TkVertexLayout_T
    VertexLayout: TkVertexLayout_T
    BoundHullVertEd: list[int]
    BoundHullVerts: list[tuple[float, float, float, float]]
    BoundHullVertSt: list[int]
    IndexBuffer: list[int]
    JointBindings: list[TkJointBindingData_T]
    JointExtents: list[TkJointExtentData_T]
    JointMirrorAxes: list[TkJointMirrorAxis_T]
    JointMirrorPairs: list[int]
    MeshAABBMax: list[tuple[float, float, float, float]]
    MeshAABBMin: list[tuple[float, float, float, float]]
    MeshBaseSkinMat: list[int]
    MeshVertREnd: list[int]
    MeshVertRStart: list[int]
    SkinMatrixLayout: list[int]
    StreamMetaDataArray: list[TkMeshMetaData_T]
    CollisionIndexCount: int
    IndexCount: int
    Indices16Bit: int
    VertexCount: int
