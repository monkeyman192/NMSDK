# TkGeometryData struct

from collections import OrderedDict
from io import BufferedWriter
from struct import pack

from .Struct import Struct
from .List import List
from .TkVertexLayout import TkVertexLayout
from ...serialization.utils import serialize, list_header


PADDING_BYTE = b'\xFE'


class TkGeometryData(Struct):
    def __init__(self, **kwargs):
        super(TkGeometryData, self).__init__()
        self.GUID = 0x71E36E603CED2E6E

        """ Contents of the struct """
        self.data['VertexCount'] = kwargs.get('VertexCount', 0)
        self.data['IndexCount'] = kwargs.get('IndexCount', 0)
        self.data['Indices16Bit'] = kwargs.get('Indices16Bit', 1)
        self.data['CollisionIndexCount'] = kwargs.get('CollisionIndexCount', 0)
        self.data['JointBindings'] = kwargs.get('JointBindings', List())
        self.data['JointExtents'] = kwargs.get('JointExtents', List())
        self.data['JointMirrorPairs'] = kwargs.get('JointMirrorPairs', List())
        self.data['JointMirrorAxes'] = kwargs.get('JointMirrorAxes', List())
        self.data['SkinMatrixLayout'] = kwargs.get('SkinMatrixLayout', List())
        self.data['MeshVertRStart'] = kwargs.get('MeshVertRStart', List())
        self.data['MeshVertREnd'] = kwargs.get('MeshVertREnd', List())
        self.data['BoundHullVertSt'] = kwargs.get('BoundHullVertSt', List())
        self.data['BoundHullVertEd'] = kwargs.get('BoundHullVertEd', List())
        self.data['MeshBaseSkinMat'] = kwargs.get('MeshBaseSkinMat', List())
        self.data['MeshAABBMin'] = kwargs.get('MeshAABBMin', List())
        self.data['MeshAABBMax'] = kwargs.get('MeshAABBMax', List())
        self.data['BoundHullVerts'] = kwargs.get('BoundHullVerts', List())
        self.data['VertexLayout'] = kwargs.get('VertexLayout',
                                               TkVertexLayout())
        self.data['SmallVertexLayout'] = kwargs.get('SmallVertexLayout',
                                                    TkVertexLayout())
        self.data['IndexBuffer'] = kwargs.get('IndexBuffer', List())
        self.data['StreamMetaDataArray'] = kwargs.get('StreamMetaDataArray',
                                                      List())
        """ End of the struct contents"""

    def serialize_list(self, data_name):
        # iterate over a list and serialize each value (assuming it is of a
        # normal type...)
        data = bytearray()
        for val in self.data[data_name]:
            data.extend(serialize(val))
        return data

    def serialize(self, output: BufferedWriter):
        # list header ending
        lst_end = b'\x01\x00\x00\x00'

        bytes_in_list = 0
        curr_offset = 0xE0

        list_data = OrderedDict()

        if self.data['IndexCount'] % 2 != 0 or self.data['IndexCount'] > 32767:
            # in this case we have an odd number of verts. set the Indices16Bit
            # value to be 0.
            # or we have too many verts to pack it using a half...
            self.data['Indices16Bit'] = 0

        Indices16Bit = self.data['Indices16Bit']
        empty_offsets = {}

        # Write all the data.
        # This will happen in the following way:
        # First we'll write all the constants, and some list headers.
        # As we write these list headers we'll keep track of the offsets to the
        # location we'll need to go back to to put the relative offset values.
        # Then we'll write the actual data in the list.
        for name in ('VertexCount', 'IndexCount', 'Indices16Bit',
                     'CollisionIndexCount'):
            output.write(pack('<i', self.data[name]))

        for name in ('JointBindings', 'JointExtents', 'JointMirrorPairs',
                     'JointMirrorAxes', 'SkinMatrixLayout', 'MeshVertRStart',
                     'MeshVertREnd', 'BoundHullVertSt', 'BoundHullVertEd',
                     'MeshBaseSkinMat', 'MeshAABBMin', 'MeshAABBMax',
                     'BoundHullVerts'):
            empty_offsets[name] = output.tell()
            output.write(list_header(0, len(self.data[name])))
        for name in ('VertexLayout', 'SmallVertexLayout'):
            output.write(pack('<I', self.data[name].data['ElementCount']))
            output.write(pack('<I', self.data[name].data['Stride']))
            output.write(bytes(self.data[name].data['PlatformData']))
            empty_offsets[name] = output.tell()
            output.write(
                list_header(0, len(self.data[name].data['VertexElements']))
            )
        # Write the IndexBuffer
        if Indices16Bit == 0:
            length = len(self.data['IndexBuffer'])
        else:
            # this should be an int anyway, but cast to an int so that
            # we can pack it correctly
            length = len(self.data['IndexBuffer']) // 2
        empty_offsets['IndexBuffer'] = output.tell()
        output.write(list_header(0, length))

        empty_offsets['StreamMetaDataArray'] = output.tell()
        output.write(list_header(0, len(self.data['StreamMetaDataArray'])))

        # Now that we have written all the normal stuff, we can write the
        # actual list data.
        for name in ('JointBindings', 'JointExtents', 'JointMirrorPairs',
                     'JointMirrorAxes', 'SkinMatrixLayout', 'MeshVertRStart',
                     'MeshVertREnd', 'MeshAABBMin', 'MeshAABBMax',
                     'MeshBaseSkinMat', 'BoundHullVertSt', 'BoundHullVertEd',
                     'BoundHullVerts'):
            # First, get the current location so that we can write it to the
            # start of the list header.
            curr_offset = output.tell()
            if name in ('MeshAABBMin', 'MeshAABBMax', 'BoundHullVerts'):
                if curr_offset % 0x10 != 0:
                    output.write(PADDING_BYTE * (0x10 - (curr_offset % 0x10)))
                curr_offset = output.tell()
            if name in ('JointBindings', 'JointExtents', 'JointMirrorPairs',
                        'JointMirrorAxes', 'SkinMatrixLayout'):
                # For now, we will have this as 0 always...
                # Instead of removing this from the outer list, I'll leave it in
                # case we want to change this or add this functionality later.
                pass
            else:
                output.write(self.serialize_list(name))
            if output.tell() != curr_offset:
                output.seek(empty_offsets[name], 0)
                output.write(pack('<Q', curr_offset - empty_offsets[name]))
                output.seek(0, 2)
        for name in ('VertexLayout', 'SmallVertexLayout'):
            curr_offset = output.tell()
            output.write(
                bytes(self.data[name].data['VertexElements'])
            )
            if output.tell() != curr_offset:
                output.seek(empty_offsets[name], 0)
                output.write(pack('<Q', curr_offset - empty_offsets[name]))
                output.seek(0, 2)

        curr_offset = output.tell()
        index_buffer_data = bytearray()
        # TODO: Optimise this??
        if Indices16Bit == 0:
            for val in self.data['IndexBuffer']:
                index_buffer_data.extend(pack('<I', val))
        else:
            for val in self.data['IndexBuffer']:
                index_buffer_data.extend(pack('<H', val))
        # If the data is not aligned to 0x8, then add some padding
        padding_bytes = (8 - (len(index_buffer_data) % 8)) % 8
        index_buffer_data.extend(padding_bytes * PADDING_BYTE)
        output.write(index_buffer_data)
        if output.tell() != curr_offset:
            output.seek(empty_offsets['IndexBuffer'], 0)
            output.write(pack('<Q', curr_offset - empty_offsets['IndexBuffer']))
            output.seek(0, 2)

        curr_offset = output.tell()
        output.write(bytes(self.data['StreamMetaDataArray']))
        if output.tell() != curr_offset:
            output.seek(empty_offsets['StreamMetaDataArray'], 0)
            output.write(pack(
                '<Q', curr_offset - empty_offsets['StreamMetaDataArray'])
            )
            output.seek(0, 2)
