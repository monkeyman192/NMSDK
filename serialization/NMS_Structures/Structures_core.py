from collections import namedtuple
from functools import cached_property
from typing import Optional


gstream_info = namedtuple(
    'gstream_info',
    ['vert_size', 'vert_off', 'idx_size', 'idx_off']
)


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

    _metadata: gstream_info
    _verts: dict
    _faces: list
    _bounded_hull: list

    @property
    def verts(self):
        return self._verts
    
    @verts.setter
    def verts(self, value):
        self._verts = value

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
