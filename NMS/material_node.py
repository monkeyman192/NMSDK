import bpy
from mathutils import Vector

import os.path as op

from .LOOKUPS import DIFFUSE, MASKS, NORMAL, DIFFUSE2  # noqa pylint: disable=relative-beyond-top-level
from ..ModelImporter.readers import read_material  # noqa pylint: disable=relative-beyond-top-level
from ..utils.io import realize_path  # noqa pylint: disable=relative-beyond-top-level


def create_material_node(mat_path, material_cache):
    # retrieve a cached copy if it exists
    if mat_path in material_cache:
        return material_cache[mat_path]
    # Read the material data directly from the material MBIN
    mat_data = read_material(mat_path)
    if mat_data is None or mat_data == dict():
        # no texture data so just exit this function.
        return
    # create a new material
    mat_name = mat_data.pop('Name')
    mat = bpy.data.materials.new(name=mat_name)

    uniforms = mat_data['Uniforms']

    # Since we are using cycles we want to have node-based materials
    mat.use_nodes = True

    # Add some material settings:
    CastShadow = mat_data['CastShadow']
    if CastShadow:
        mat.shadow_method = 'OPAQUE'

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # clear any existing nodes just to be safe.
    nodes.clear()
    # Now add all the nodes we need.
    output_material = nodes.new(type='ShaderNodeOutputMaterial')
    output_material.location = (500, 0)
    principled_BSDF = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_BSDF.location = (200, 150)
    principled_BSDF.inputs['Roughness'].default_value = 1.0
    FRAGMENT_COLOUR0 = principled_BSDF.outputs['BSDF']

    # Set up some constants
    if 61 in mat_data['Flags']:
        kfAlphaThreshold = 0.1
        kfAlphaThresholdMax = 0.5
    elif 10 in mat_data['Flags']:
        kfAlphaThreshold = 0.45
        kfAlphaThresholdMax = 0.8
    else:
        kfAlphaThreshold = 0.0001

    if 0 not in mat_data['Flags']:
        rgb_input = nodes.new(type='ShaderNodeRGB')
        rgb_input.outputs[0].default_value[0] = uniforms['gMaterialColourVec4'][0]  # noqa
        rgb_input.outputs[0].default_value[1] = uniforms['gMaterialColourVec4'][1]  # noqa
        rgb_input.outputs[0].default_value[2] = uniforms['gMaterialColourVec4'][2]  # noqa
        rgb_input.outputs[0].default_value[3] = uniforms['gMaterialColourVec4'][3]  # noqa
        lColourVec4 = rgb_input.outputs['Color']

    # TODO: restructure all this to be as similar to the actual shaders as
    # possible

    # create the diffuse, mask and normal nodes and give them their images
    for tex_type, tex_path in mat_data['Samplers'].items():
        img = None
        if tex_type == DIFFUSE:
            # texture
            _path = realize_path(tex_path)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
            diffuse_texture = nodes.new(type='ShaderNodeTexImage')
            diffuse_texture.name = diffuse_texture.label = 'Texture Image - Diffuse'  # noqa
            diffuse_texture.image = img
            diffuse_texture.location = (-600, 300)
            lColourVec4 = diffuse_texture.outputs['Color']
            if 15 in mat_data['Flags']:
                # #ifdef _F16_DIFFUSE2MAP
                if 16 not in mat_data['Flags']:
                    # #ifndef _F17_MULTIPLYDIFFUSE2MAP
                    diffuse2_path = realize_path(
                        mat_data['Samplers'][DIFFUSE2])
                    if op.exists(diffuse2_path):
                        img = bpy.data.images.load(diffuse2_path)
                    diffuse2_texture = nodes.new(type='ShaderNodeTexImage')
                    diffuse2_texture.name = diffuse_texture.label = 'Texture Image - Diffuse2'  # noqa
                    diffuse2_texture.image = img
                    diffuse2_texture.location = (-400, 300)
                    mix_diffuse = nodes.new(type='ShaderNodeMixRGB')
                    mix_diffuse.location = (-200, 300)
                    links.new(mix_diffuse.inputs['Color1'],
                              lColourVec4)
                    links.new(mix_diffuse.inputs['Color2'],
                              diffuse2_texture.outputs['Color'])
                    links.new(mix_diffuse.inputs['Fac'],
                              diffuse2_texture.outputs['Alpha'])
                    lColourVec4 = mix_diffuse.outputs['Color']
                else:
                    print('Note: Please post on discord the model you are'
                          ' importing so I can fix this!!!')
            # #ifndef _F44_IMPOSTER
            if 43 not in mat_data['Flags']:
                # #ifdef _F39_METALLIC_MASK
                if 38 in mat_data['Flags']:
                    links.new(principled_BSDF.inputs['Metallic'],
                              diffuse_texture.outputs['Alpha'])
                else:
                    # use the default value from the file
                    if 'gMaterialParamsVec4' in uniforms:
                        principled_BSDF.inputs['Metallic'].default_value = uniforms['gMaterialParamsVec4'][2]  # noqa
        elif tex_type == MASKS:
            # texture
            _path = realize_path(tex_path)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
                img.colorspace_settings.name = 'XYZ'
            mask_texture = nodes.new(type='ShaderNodeTexImage')
            mask_texture.name = mask_texture.label = 'Texture Image - Mask'
            mask_texture.image = img
            mask_texture.location = (-700, 0)
            lfRoughness = None
            # RGB separation node
            separate_rgb = nodes.new(type='ShaderNodeSeparateRGB')
            separate_rgb.location = (-400, 0)
            links.new(separate_rgb.inputs['Image'],
                      mask_texture.outputs['Color'])
            if 43 not in mat_data['Flags']:
                # #ifndef _F44_IMPOSTER
                if 24 in mat_data['Flags']:
                    # #ifdef _F25_ROUGHNESS_MASK
                    # lfRoughness = 1 - lMasks.g
                    # subtract the green channel from 1:
                    sub_1 = nodes.new(type="ShaderNodeMath")
                    sub_1.operation = 'SUBTRACT'
                    sub_1.location = (-200, 0)
                    sub_1.inputs[0].default_value = 1.0
                    lfRoughness = sub_1.outputs['Value']
                    # link them up
                    links.new(sub_1.inputs[1], separate_rgb.outputs['G'])
                else:
                    roughness_value = nodes.new(type='ShaderNodeValue')
                    roughness_value.outputs[0].default_value = 1.0
                    lfRoughness = roughness_value.outputs['Value']
                # lfRoughness *= lUniforms.mpCustomPerMaterial->gMaterialParamsVec4.x;  # noqa
                mult_param_x = nodes.new(type="ShaderNodeMath")
                mult_param_x.operation = 'MULTIPLY'
                mult_param_x.inputs[1].default_value = uniforms[
                    'gMaterialParamsVec4'][0]
                links.new(mult_param_x.inputs[0], lfRoughness)
                lfRoughness = mult_param_x.outputs['Value']
            if lfRoughness is not None:
                links.new(principled_BSDF.inputs['Roughness'],
                          lfRoughness)
            # If the roughness wasn't ever defined then the default value is 1
            # which is what blender has as the default anyway

            # gMaterialParamsVec4.x
            # #ifdef _F40_SUBSURFACE_MASK
            if 39 in mat_data['Flags']:
                links.new(principled_BSDF.inputs['Subsurface'],
                          separate_rgb.outputs['R'])
            if 43 in mat_data['Flags']:
                # lfMetallic = lMasks.b;
                links.new(principled_BSDF.inputs['Metallic'],
                          separate_rgb.outputs['B'])

        elif tex_type == NORMAL:
            # texture
            _path = realize_path(tex_path)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
                img.colorspace_settings.name = 'XYZ'
            normal_texture = nodes.new(type='ShaderNodeTexImage')
            normal_texture.name = normal_texture.label = 'Texture Image - Normal'  # noqa
            normal_texture.image = img
            normal_texture.location = (-700, -300)
            # separate xyz then recombine
            normal_sep_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
            normal_sep_xyz.location = (-400, -300)
            normal_com_xyz = nodes.new(type='ShaderNodeCombineXYZ')
            normal_com_xyz.location = (-200, -300)
            # swap X and Y channels
            links.new(normal_com_xyz.inputs['X'],
                      normal_sep_xyz.outputs['Y'])
            links.new(normal_com_xyz.inputs['Y'],
                      normal_sep_xyz.outputs['X'])
            links.new(normal_com_xyz.inputs['Z'],
                      normal_sep_xyz.outputs['Z'])

            # normal map
            normal_map = nodes.new(type='ShaderNodeNormalMap')
            normal_map.location = (0, -300)
            # link them up
            links.new(normal_sep_xyz.inputs['Vector'],
                      normal_texture.outputs['Color'])
            links.new(normal_map.inputs['Color'],
                      normal_com_xyz.outputs['Vector'])
            links.new(principled_BSDF.inputs['Normal'],
                      normal_map.outputs['Normal'])

            if 42 in mat_data['Flags']:
                # lTexCoordsVec4.xy *= lUniforms.mpCustomPerMesh->gCustomParams01Vec4.z;  # noqa
                normal_scale = nodes.new(type='ShaderNodeMapping')
                normal_scale.location = (-1000, -300)
                scale = uniforms['gCustomParams01Vec4'][2]
                normal_scale.inputs['Scale'].default_value = Vector((scale, scale, scale))  # noqa
                tex_coord = nodes.new(type='ShaderNodeTexCoord')
                tex_coord.location = (-1200, -300)
                tex_coord.object = bpy.context.active_object
                links.new(normal_scale.inputs['Vector'],
                          tex_coord.outputs['Generated'])
                links.new(normal_texture.inputs['Vector'],
                          normal_scale.outputs['Vector'])

    # Apply some final transforms to the data before connecting it to the
    # Material output node

    if 20 in mat_data['Flags'] or 28 in mat_data['Flags']:
        # #ifdef _F21_VERTEXCOLOUR
        # lColourVec4 *= IN( mColourVec4 );
        col_attribute = nodes.new(type='ShaderNodeAttribute')
        col_attribute.attribute_name = 'Col'
        mix_colour = nodes.new(type='ShaderNodeMixRGB')
        links.new(mix_colour.inputs['Color1'],
                  lColourVec4)
        links.new(mix_colour.inputs['Color2'],
                  col_attribute.outputs['Color'])
        links.new(principled_BSDF.inputs['Base Color'],
                  mix_colour.outputs['Color'])
        lColourVec4 = mix_colour.outputs['Color']

    if (8 in mat_data['Flags'] or 10 in mat_data['Flags'] or
            21 in mat_data['Flags']):
        # Handle transparency
        alpha_mix = nodes.new(type='ShaderNodeMixShader')
        alpha_shader = nodes.new(type='ShaderNodeBsdfTransparent')
        if 0 in mat_data['Flags']:
            # If there is a diffuse texture we use this to get rid of
            # transparent pixels
            discard_node = nodes.new(type="ShaderNodeMath")
            discard_node.operation = 'LESS_THAN'
            discard_node.inputs[1].default_value = kfAlphaThreshold
            lColourVec4_a = diffuse_texture.outputs['Alpha']

            links.new(discard_node.inputs[0], lColourVec4_a)
            lColourVec4_a = discard_node.outputs['Value']

            if 10 in mat_data['Flags']:
                clamp_node = nodes.new(type='ShaderNodeClamp')
                clamp_node.clamp_type = 'RANGE'
                clamp_node.location = (500, -300)
                clamp_node.inputs['Min'].default_value = kfAlphaThreshold
                clamp_node.inputs['Max'].default_value = kfAlphaThresholdMax

                links.new(clamp_node.inputs['Value'], lColourVec4_a)
                lColourVec4_a = clamp_node.outputs['Result']

            links.new(alpha_mix.inputs['Fac'], lColourVec4_a)
            # If the material has any transparency we want to specify this in
            # the material
            mat.blend_method = 'BLEND'
        else:
            # if there isn't we will use the material colour as the base
            # colour of the transparency shader
            links.new(alpha_shader.inputs['Color'],
                      lColourVec4)

        links.new(alpha_mix.inputs[1],
                  FRAGMENT_COLOUR0)
        links.new(alpha_mix.inputs[2],
                  alpha_shader.outputs['BSDF'])

        FRAGMENT_COLOUR0 = alpha_mix.outputs['Shader']

    if 50 in mat_data['Flags']:
        # #ifdef _F51_DECAL_DIFFUSE
        # FRAGMENT_COLOUR0 = vec4( lOutColours0Vec4.xyz, lColourVec4.a );
        alpha_mix_decal = nodes.new(type='ShaderNodeMixShader')
        alpha_shader = nodes.new(type='ShaderNodeBsdfTransparent')
        links.new(alpha_mix_decal.inputs['Fac'],
                  diffuse_texture.outputs['Alpha'])
        links.new(alpha_mix_decal.inputs[1],
                  alpha_shader.outputs['BSDF'])
        links.new(alpha_mix_decal.inputs[2],
                  FRAGMENT_COLOUR0)
        FRAGMENT_COLOUR0 = alpha_mix_decal.outputs['Shader']

    # Link up the diffuse colour to the base colour on the prinicipled BSDF
    # shader.
    links.new(principled_BSDF.inputs['Base Color'],
              lColourVec4)

    # Finally, link the fragment colour to the output material.
    links.new(output_material.inputs['Surface'],
              FRAGMENT_COLOUR0)

    # link some nodes up according to the uberfragment.bin shader
    # TODO: fix this at some point...
    # https://blender.stackexchange.com/questions/21533/totally-white-shadeless-material-in-cycles
    # if 6 in mat_data['Flags']:
    #    mat.use_shadeless = True
    material_cache[mat_path] = mat

    return mat
