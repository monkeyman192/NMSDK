# File containing a number of lookup tables to keep it out of the main data

import numpy as np


MATERIALFLAGS = ['_F01_DIFFUSEMAP', '_F02_SKINNED', '_F03_NORMALMAP', '_F04_FEATURESMAP',
                 '_F05_DEPTH_EFFECT', '_F06_', '_F07_UNLIT', '_F08_', '_F09_REFLECTIVE',
                 '_F10_', '_F11_ALPHACUTOUT', '_F12_BATCHED_BILLBOARD', '_F13_UV_EFFECT',
                 '_F14_', '_F15_WIND', '_F16_DIFFUSE2MAP', '_F17_', '_F18_',
                 '_F19_BILLBOARD', '_F20_PARALLAX', '_F21_VERTEXCUSTOM',
                 '_F22_OCCLUSION_MAP', '_F23_', '_F24_', '_F25_MASKS_MAP', '_F26_', '_F27_',
                 '_F28_', '_F29_', '_F30_REFRACTION', '_F31_DISPLACEMENT',
                 '_F32_REFRACTION_MASK', '_F33_SHELLS', '_F34_', '_F35_', '_F36_DOUBLESIDED',
                 '_F37_EXPLICIT_MOTION_VECTORS', '_F38_', '_F39_', '_F40_', '_F41_',
                 '_F42_DETAIL_NORMAL', '_F43_', '_F44_IMPOSTER', '_F45_', '_F46_',
                 '_F47_REFLECTION_PROBE', '_F48_', '_F49_', '_F50_DISABLE_POSTPROCESS',
                 '_F51_', '_F52_', '_F53_COLOURISABLE', '_F54_', '_F55_MULTITEXTURE',
                 '_F56_MATCH_GROUND', '_F57_', '_F58_USE_CENTRAL_NORMAL',
                 '_F59_BIASED_REACTIVITY', '_F60_', '_F61_', '_F62_', '_F63_DISSOLVE',
                 '_F64_RESERVED_FLAG_FOR_EARLY_Z_PATCHING_DO_NOT_USE']

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