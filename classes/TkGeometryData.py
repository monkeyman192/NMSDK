# TkGeometryData struct

from .Struct import Struct

STRUCTNAME = 'TkGeometryData'

class TkGeometryData(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.VertexCount = kwargs.get('VertexCount', None)
        self.IndexCount = kwargs.get('IndexCount', None)
        self.Indices16Bit = kwargs.get('Indices16Bit', None)
        self.JointBindings = kwargs.get('JointBindings', None)
        self.JointExtents = kwargs.get('JointExtents', None)
        self.JointMirrorPairs = kwargs.get('JointMirrorPairs', None)
        self.JointMirrorAxes = kwargs.get('JointMirrorAxes', None)
        self.SkinMatrixLayout = kwargs.get('SkinMatrixLayout', None)        
        self.MeshVertRStart = kwargs.get('MeshVertRStart', None)
        self.MeshVertREnd = kwargs.get('MeshVertREnd', None)
        self.MeshBaseSkinMat = kwargs.get('MeshBaseSkinMat', None)
        self.MeshAABBMin = kwargs.get('MeshAABBMin', None)
        self.MeshAABBMax = kwargs.get('MeshAABBMax', None)
        self.VertexLayout = kwargs.get('VertexLayout', None)
        self.SmallVertexLayout = kwargs.get('SmallVertexLayout', None)
        self.IndexBuffer = kwargs.get('IndexBuffer', None)
        self.VertexStream = kwargs.get('VertexStream', None)
        self.SmallVertexStream = kwargs.get('SmallVertexStream', None)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
