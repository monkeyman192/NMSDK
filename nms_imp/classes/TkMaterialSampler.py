# TkMaterialSampler struct

from .Struct import Struct

STRUCTNAME = 'TkMaterialSampler'

class TkMaterialSampler(Struct):
    def __init__(self, **kwargs):

        """ Contents of the struct """
        self.Name = kwargs.get('Name', None)
        self.Map = kwargs.get('Map', None)
        self.IsCube = kwargs.get('IsCube', 'False')
        self.UseCompression = kwargs.get('UseCompression', "True")
        self.UseMipMaps = kwargs.get('UseMipMaps', "True")
        self.IsSRGB = kwargs.get('IsSRGB', None)        # True image, False for MASKS and NORMAL
        self.MaterialAlternativeId = kwargs.get('MaterialAlternativeId', "")
        self.TextureAddressMode = kwargs.get('TextureAddressMode', "Wrap")
        self.TextureFilterMode = kwargs.get('TextureFilterMode', "Trilinear")
        self.Anisotropy = kwargs.get('Anisotropy', 0)
        """ End of the struct contents"""

        """ Run code to convert struct contents into self.data_dict """
        self._create_dict()

        # Parent needed so that it can be a SubElement of something
        self.parent = None
        self.STRUCTNAME = STRUCTNAME
