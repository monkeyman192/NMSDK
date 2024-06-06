# File containing a number of lookup tables to keep it out of the main data

from collections import defaultdict

MATERIALFLAGS = ['_F01_DIFFUSEMAP', '_F02_SKINNED', '_F03_NORMALMAP', '_F04_',
                 '_F05_INVERT_ALPHA', '_F06_BRIGHT_EDGE', '_F07_UNLIT',
                 '_F08_REFLECTIVE', '_F09_TRANSPARENT', '_F10_NORECEIVESHADOW',
                 '_F11_ALPHACUTOUT', '_F12_BATCHED_BILLBOARD',
                 '_F13_UVANIMATION', '_F14_UVSCROLL', '_F15_WIND',
                 '_F16_DIFFUSE2MAP', '_F17_MULTIPLYDIFFUSE2MAP',
                 '_F18_UVTILES', '_F19_BILLBOARD', '_F20_PARALLAXMAP',
                 '_F21_VERTEXCOLOUR', '_F22_TRANSPARENT_SCALAR',
                 '_F23_TRANSLUCENT', '_F24_AOMAP', '_F25_ROUGHNESS_MASK',
                 '_F26_STRETCHY_PARTICLE', '_F27_VBTANGENT', '_F28_VBSKINNED',
                 '_F29_VBCOLOUR', '_F30_REFRACTION', '_F31_DISPLACEMENT',
                 '_F32_REFRACTION_MASK', '_F33_SHELLS', '_F34_GLOW',
                 '_F35_GLOW_MASK', '_F36_DOUBLESIDED', '_F37_',
                 '_F38_NO_DEFORM', '_F39_METALLIC_MASK',
                 '_F40_SUBSURFACE_MASK', '_F41_DETAIL_DIFFUSE',
                 '_F42_DETAIL_NORMAL', '_F43_NORMAL_TILING', '_F44_IMPOSTER',
                 '_F45_VERTEX_BLEND', '_F46_BILLBOARD_AT',
                 '_F47_REFLECTION_PROBE', '_F48_WARPED_DIFFUSE_LIGHTING',
                 '_F49_DISABLE_AMBIENT', '_F50_DISABLE_POSTPROCESS',
                 '_F51_DECAL_DIFFUSE', '_F52_DECAL_NORMAL',
                 '_F53_COLOURISABLE', '_F54_COLOURMASK', '_F55_MULTITEXTURE',
                 '_F56_MATCH_GROUND', '_F57_DETAIL_OVERLAY',
                 '_F58_USE_CENTRAL_NORMAL', '_F59_SCREENSPACE_FADE',
                 '_F60_ACUTE_ANGLE_FADE', '_F61_CLAMP_AMBIENT',
                 '_F62_DETAIL_ALPHACUTOUT', '_F63_DISSOLVE', '_F64_']

# Mesh vertex types
VERTS = 0
UVS = 1
NORMS = 2
TANGS = 3
COLOURS = 4
BLENDINDEX = 5
BLENDWEIGHT = 6

# Mesh vertex stride sizes
STRIDES = {VERTS: 8,
           UVS: 8,
           NORMS: 4,
           TANGS: 4,
           COLOURS: 4}

# Material types
DIFFUSE = 'gDiffuseMap'
DIFFUSE2 = 'gDiffuse2Map'
MASKS = 'gMasksMap'
NORMAL = 'gNormalMap'

SEMANTICS = {'Vertices': VERTS,
             'UVs': UVS,
             'Normals': NORMS,
             'Tangents': TANGS,
             'Colours': COLOURS,
             'BlendIndex': BLENDINDEX,
             'BlendWeight': BLENDWEIGHT}

REV_SEMANTICS = {VERTS: 'Vertices',
                 UVS: 'UVs',
                 NORMS: 'Normals',
                 TANGS: 'Tangents',
                 COLOURS: 'Colours',
                 BLENDINDEX: 'BlendIndex',
                 BLENDWEIGHT: 'BlendWeight'}

SERIALIZE_FMT_MAP = {VERTS: 0,
                     UVS: 0,
                     NORMS: 1,
                     TANGS: 1,
                     COLOURS: 2}


class VersionedOffsets:
    TkMeshMetaData = defaultdict(
        lambda: {
            "IdString": 0x00,
            "Hash": 0x80,
            "VertexDataSize": 0x88,
            "VertexDataOffset": 0x8C,
            "IndexDataSize": 0x90,
            "IndexDataOffset": 0x94,
            "DoubleBufferGeometry": 0x98,
            "_size": 0xA0,
        },
        {
            0x7E2C6C00A113D11F: {
                "Hash": 0x00,
                "IndexDataOffset": 0x08,
                "IndexDataSize": 0x0C,
                "VertexDataOffset": 0x10,
                "VertexDataSize": 0x14,
                "IdString": 0x18,
                "DoubleBufferGeometry": 0x98,
                "_size": 0xA0,
            }
        },
    )

    TkGeometryData = defaultdict(
        lambda: {
            "VertexCount": 0x000,
            "IndexCount": 0x004,
            "Indices16Bit": 0x008,
            "CollisionIndexCount": 0x00C,
            "JointBindings": 0x010,
            "JointExtents": 0x020,
            "JointMirrorPairs": 0x030,
            "JointMirrorAxes": 0x040,
            "SkinMatrixLayout": 0x050,
            "MeshVertRStart": 0x060,
            "MeshVertREnd": 0x070,
            "BoundHullVertSt": 0x080,
            "BoundHullVertEd": 0x090,
            "MeshBaseSkinMat": 0x0A0,
            "MeshAABBMin": 0x0B0,
            "MeshAABBMax": 0x0C0,
            "BoundHullVerts": 0x0D0,
            "VertexLayout": 0x0E0,
            "SmallVertexLayout": 0x100,
            "IndexBuffer": 0x120,
            "StreamMetaDataArray": 0x130,
            "_size": 0x140,
        },
        {
            0x7E2C6C00A113D11F: {
                "SmallVertexLayout": 0x000,
                "VertexLayout": 0x020,
                "BoundHullVertEd": 0x040,
                "BoundHullVerts": 0x050,
                "BoundHullVertSt": 0x060,
                "IndexBuffer": 0x070,
                "JointBindings": 0x080,
                "JointExtents": 0x090,
                "JointMirrorAxes": 0x0A0,
                "JointMirrorPairs": 0x0B0,
                "MeshAABBMax": 0x0C0,
                "MeshAABBMin": 0x0D0,
                "MeshBaseSkinMat": 0x0E0,
                "MeshVertREnd": 0x0F0,
                "MeshVertRStart": 0x100,
                "SkinMatrixLayout": 0x110,
                "StreamMetaDataArray": 0x120,
                "CollisionIndexCount": 0x130,
                "IndexCount": 0x134,
                "Indices16Bit": 0x138,
                "VertexCount": 0x13C,
                "_size": 0x140,
            }
        }
    )

    TkJointBindingData = defaultdict(
        lambda: {
            "InvBindMatrix": 0x00,
            "BindTranslate": 0x40,
            "BindRotate": 0x4C,
            "BindScale": 0x5C,
            "_size": 0x64,
        },
        {
            0x7E2C6C00A113D11F: {
                "InvBindMatrix": 0x00,
                "BindRotate": 0x40,
                "BindScale": 0x50,
                "BindTranslate": 0x5C,
                "_size": 0x64,
            },
        }
    )

    TkVertexLayout = defaultdict(
        lambda: {
            "ElementCount": 0x00,
            "Stride": 0x04,
            "PlatformData": 0x08,
            "VertexElements": 0x10,
            "_size": 0x20,
        },
        {
            0x7E2C6C00A113D11F: {
                "VertexElements": 0x00,
                "PlatformData": 0x10,
                "ElementCount": 0x18,
                "Stride": 0x1C,
                "_size": 0x20,
            }
        }
    )

    TkVertexElement = defaultdict(
        lambda: {
            "SemanticID": 0x00,
            "Size": 0x04,
            "Type": 0x08,
            "Offset": 0x0C,
            "Normalise": 0x10,
            "Instancing": 0x14,
            "PlatformData": 0x18,
            "_size": 0x20,
        },
        {
            0x7E2C6C00A113D11F: {
                "PlatformData": 0x00,
                "Instancing": 0x08,
                "Normalise": 0x0C,
                "Offset": 0x10,
                "SemanticID": 0x14,
                "Size": 0x18,
                "Type": 0x1C,
                "_size": 0x20,
            }
        }
    )

    TkMaterialData = defaultdict(
        lambda: {
            "Name": 0x000,
            "Metamaterial": 0x080,
            "Class": 0x180,
            "TransparencyLayerID": 0x1A0,
            "CastShadow": 0x1A4,
            "DisableZTest": 0x1A5,
            "CreateFur": 0x1A6,
            "Link": 0x1A7,
            "Shader": 0x227,
            "Flags": 0x2A8,
            "Uniforms": 0x2B8,
            "Samplers": 0x2C8,
            "ShaderMillDataHash": 0x2D8,
            "_size": 0x2E0,
        },
        {
            0xBE0E8A666B24ECE8: {
                "Flags": 0x000,
                "Samplers": 0x010,
                "Uniforms": 0x020,
                "ShaderMillDataHash": 0x030,
                "TransparencyLayerID": 0x038,
                "Metamaterial": 0x03C,
                "Link": 0x13C,
                "Name": 0x1BC,
                "Shader": 0x13C,
                "Class": 0x2BC,
                "CastShadow": 0x2DC,
                "CreateFur": 0x2DD,
                "DisableZTest": 0x2DE,
                "_size": 0x2E0,
            }
        }
    )

    TkSceneNodeData = defaultdict(
        lambda: {
            "Name": 0x00,
            "NameHash": 0x80,
            "Type": 0x88,
            "Transform": 0x98,
            "Attributes": 0xC0,
            "Children": 0xD0,
            "_size": 0xE0,
        },
        {
            0xF652C9123B23EEEF: {
                "Attributes": 0x00,
                "Children": 0x10,
                "Type": 0x20,
                "Transform": 0x30,
                "NameHash": 0x54,
                "Name": 0x58,
                "_size": 0xD8,
            }
        }
    )

    TkMaterialSampler = defaultdict(
        lambda: {
            "Name": 0x00,
            "Map": 0x20,
            "IsCube": 0xA0,
            "UseCompression": 0xA1,
            "UseMipMaps": 0xA2,
            "IsSRGB": 0xA3,
            "MaterialAlternativeId": 0xA8,
            "TextureAddressMode": 0xC8,
            "TextureFilterMode": 0xCC,
            "Anisotropy": 0xD0,
            "_size": 0xD8,
        },
        {
            0xBE0E8A666B24ECE8: {
                "MaterialAlternativeId": 0x00, 
                "Anisotropy": 0x20,
                "TextureAddressMode": 0x24,
                "TextureFilterMode": 0x28,
                "Map": 0x2C,
                "Name": 0xAC,
                "IsCube": 0xCC,
                "IsSRGB": 0xCD,
                "UseCompression": 0xCE,
                "UseMipMaps": 0xCF,
                "_size": 0xD0,
            }
        }
    )
    TkMaterialUniform = defaultdict(
        lambda: {
            "Name": 0x00,
            "Values": 0x20,
            "ExtendedValues": 0x30,
            "_size": 0x40
        },
        {
            0xBE0E8A666B24ECE8: {
                "Values": 0x00,
                "ExtendedValues": 0x10,
                "Name": 0x20,
                "_size": 0x40,
            }
        }
    )
