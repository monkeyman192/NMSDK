# TkGeometryData struct

from .Struct import Struct
from .List import List
from .TkVertexLayout import TkVertexLayout
from .SerialisationMethods import *
from .Empty import Empty
from half import binary16

from struct import pack

STRUCTNAME = 'TkGeometryData'

class TkGeometryData(Struct):
    def __init__(self, **kwargs):
        super(TkGeometryData, self).__init__()

        """ Contents of the struct """
        self.data['VertexCount'] = kwargs.get('VertexCount', 0)
        self.data['IndexCount'] = kwargs.get('IndexCount', 0)
        self.data['Indices16Bit'] = kwargs.get('Indices16Bit', 1)
        self.data['Padding00C'] = Empty(0x4)
        self.data['JointBindings'] = kwargs.get('JointBindings', List())
        self.data['JointExtents'] = kwargs.get('JointExtents', List())
        self.data['JointMirrorPairs'] = kwargs.get('JointMirrorPairs', List())
        self.data['JointMirrorAxes'] = kwargs.get('JointMirrorAxes', List())
        self.data['SkinMatrixLayout'] = kwargs.get('SkinMatrixLayout', List())        
        self.data['MeshVertRStart'] = kwargs.get('MeshVertRStart', List())
        self.data['MeshVertREnd'] = kwargs.get('MeshVertREnd', List())
        self.data['MeshBaseSkinMat'] = kwargs.get('MeshBaseSkinMat', List())
        self.data['MeshAABBMin'] = kwargs.get('MeshAABBMin', List())
        self.data['MeshAABBMax'] = kwargs.get('MeshAABBMax', List())
        self.data['VertexLayout'] = kwargs.get('VertexLayout', TkVertexLayout())
        self.data['SmallVertexLayout'] = kwargs.get('SmallVertexLayout', TkVertexLayout())
        self.data['IndexBuffer'] = kwargs.get('IndexBuffer', List())
        self.data['VertexStream'] = kwargs.get('VertexStream', List())
        self.data['SmallVertexStream'] = kwargs.get('SmallVertexStream', List())
        """ End of the struct contents"""

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME

    def serialise_list(self, data_name):
        # iterate over a list and serialise each value (assuming it is of a normal type...)
        data = bytearray()
        for val in self.data[data_name]:
            data.extend(serialise(val))
        return data

    def serialise(self, output):
        # list header ending
        lst_end = b'\x01\x00\x00\x00'

        bytes_in_list = 0
        curr_offset = 0xC0

        list_data = []

        if self.data['IndexCount'] %2 != 0:
            # in this case we have an odd number of verts. set the Indices16Bit value to be 0
            self.data['Indices16Bit'] = 0

        Indices16Bit = self.data['Indices16Bit']
        
        # this will be a specific serialisation method for this whole struct
        for pname in self.data:
            if pname in ['VertexCount', 'IndexCount', 'Indices16Bit']:
                output.write(pack('<i', self.data[pname]))
            elif pname in ['JointBindings', 'JointExtents', 'JointMirrorPairs', 'JointMirrorAxes', 'SkinMatrixLayout']:
                output.write(list_header(0, 0, lst_end))
            elif pname in ['MeshVertRStart', 'MeshVertREnd']:
                length = len(self.data[pname])
                output.write(list_header(curr_offset + bytes_in_list, length, lst_end))
                bytes_in_list += 4*length
                curr_offset -= 0x10
                list_data.append(self.serialise_list(pname))
            elif pname == 'MeshBaseSkinMat':
                output.write(list_header(0, 0, lst_end))
                curr_offset -= 0x10
            elif pname in ['MeshAABBMin', 'MeshAABBMax']:
                length = len(self.data[pname])
                output.write(list_header(curr_offset + bytes_in_list, length, lst_end))
                bytes_in_list += 0x10*length
                curr_offset -= 0x10
                list_data.append(self.serialise_list(pname))
            elif pname in ['VertexLayout', 'SmallVertexLayout']:
                # just pull the data directly
                output.write(pack('<i', self.data[pname].data['ElementCount']))
                output.write(pack('<i', self.data[pname].data['Stride']))
                output.write(bytes(self.data[pname].data['PlatformData']))
                curr_offset -= 0x10
                length = len(self.data[pname].data['VertexElements'])
                output.write(list_header(curr_offset + bytes_in_list, length, lst_end))
                bytes_in_list += 0x20*length
                curr_offset -= 0x10
                list_data.append(bytes(self.data[pname].data['VertexElements']))
            elif pname == 'IndexBuffer':
                if Indices16Bit == 0:
                    length = len(self.data[pname])
                else:
                    length = int(len(self.data[pname])/2)       # this should be an int anyway, but cast to an int so that we can pack it correctly
                output.write(list_header(curr_offset + bytes_in_list, length, lst_end))
                curr_offset -= 0x10
                bytes_in_list += 0x4*length
                data = bytearray()
                if Indices16Bit == 0:
                    for val in self.data['IndexBuffer']:
                        data.extend(pack('<i', val))
                else:
                    for val in self.data['IndexBuffer']:
                        data.extend(pack('<h', val))
                list_data.append(data)
            elif pname in ['VertexStream', 'SmallVertexStream']:
                length = 2*len(self.data[pname])
                output.write(list_header(curr_offset + bytes_in_list, length, lst_end))
                curr_offset -= 0x10
                bytes_in_list += length
                data = bytearray()
                for val in self.data[pname]:
                    data.extend(binary16(val))
                list_data.append(data)
            elif 'Padding' in pname:
                self.data[pname].serialise(output)
        for data in list_data:
            output.write(data)
            
        
