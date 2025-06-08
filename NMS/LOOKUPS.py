# File containing a number of lookup tables to keep it out of the main data

import numpy as np


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
STRIDES = {
    VERTS: 8,
    UVS: 8,
    NORMS: 4,
    TANGS: 4,
    COLOURS: 4,
}

# Material types
DIFFUSE = 'gDiffuseMap'
DIFFUSE2 = 'gDiffuse2Map'
MASKS = 'gMasksMap'
NORMAL = 'gNormalMap'

SEMANTICS = {
    'Vertices': VERTS,
    'UVs': UVS,
    'Normals': NORMS,
    'Tangents': TANGS,
    'Colours': COLOURS,
    'BlendIndex': BLENDINDEX,
    'BlendWeight': BLENDWEIGHT,
}

REV_SEMANTICS = {
    VERTS: 'Vertices',
    UVS: 'UVs',
    NORMS: 'Normals',
    TANGS: 'Tangents',
    COLOURS: 'Colours',
    BLENDINDEX: 'BlendIndex',
    BLENDWEIGHT: 'BlendWeight',
}

SERIALIZE_FMT_MAP = {
    VERTS: 0,
    UVS: 0,
    NORMS: 1,
    TANGS: 1,
    COLOURS: 2,
}

SERIALIZE_FMT_MAP_NEW = {
    VERTS: 5131,
    UVS: 5131,
    NORMS: 36255,
    TANGS: 36255,
    COLOURS: 5121,
}

VERT_TYPE_MAP = {
    5121: {'size': 1, 'np_fmt': "4B"},
    5131: {'size': 2, 'np_fmt': "4e"},       # half-precision floats
    36255: {'size': 1, 'np_fmt': np.int32}
}