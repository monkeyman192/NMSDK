import bpy
from mathutils import Vector

import os.path as op

from NMS.LOOKUPS import DIFFUSE, MASKS, NORMAL, DIFFUSE2
from ModelImporter.readers import read_material
from utils.io import realize_path


def create_material_node(mat_path: str, local_root_directory: str):
    # Read the material data directly from the material MBIN
    mat_data = read_material(mat_path)
    if mat_data is None:
        # no texture data so just exit this function.
        return
    # Create a new material
    mat = bpy.data.materials.new(name=mat_data.Name)

    uniforms = {x.Name: x for x in mat_data.Uniforms_Float}

    flags = [x.MaterialFlagEnum for x in mat_data.Flags]

    # Since we are using cycles we want to have node-based materials
    mat.use_nodes = True

    # Add some material settings:
    if mat_data.CastShadow:
        mat.use_transparent_shadow = False

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
    if 10 in flags:
        kfAlphaThreshold = 0.45
        kfAlphaThresholdMax = 0.8
    else:
        kfAlphaThreshold = 0.0001

    if 0 not in flags:
        rgb_input = nodes.new(type='ShaderNodeRGB')
        mat_colour = uniforms['gMaterialColourVec4'].Values
        rgb_input.outputs[0].default_value[0] = mat_colour[0]
        rgb_input.outputs[0].default_value[1] = mat_colour[1]
        rgb_input.outputs[0].default_value[2] = mat_colour[2]
        rgb_input.outputs[0].default_value[3] = mat_colour[3]
        lColourVec4 = rgb_input.outputs['Color']

    # TODO: restructure all this to be as similar to the actual shaders as
    # possible

    samplers = {x.Name: x.Map for x in mat_data.Samplers}

    # create the diffuse, mask and normal nodes and give them their images
    for tex_type, tex_path in samplers.items():
        img = None
        if tex_type == DIFFUSE:
            # texture
            _path = realize_path(tex_path, local_root_directory)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
            diffuse_texture = nodes.new(type='ShaderNodeTexImage')
            diffuse_texture.name = diffuse_texture.label = 'Texture Image - Diffuse'  # noqa
            diffuse_texture.image = img
            diffuse_texture.location = (-600, 300)
            lColourVec4 = diffuse_texture.outputs['Color']
            if 15 in flags:
                # #ifdef _F16_DIFFUSE2MAP
                if 16 not in flags:
                    # #ifndef _F17_MULTIPLYDIFFUSE2MAP
                    diffuse2_path = realize_path(samplers[DIFFUSE2], local_root_directory)
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
        elif tex_type == MASKS:
            # texture
            _path = realize_path(tex_path, local_root_directory)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
                img.colorspace_settings.name = 'Linear Rec.2020'
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
            if 43 not in flags:
                # #ifndef _F44_IMPOSTER
                if 24 in flags:
                    # #ifdef _F25_MASKS_MAP
                    
                    # lfRoughness = 1 - lMasks.r
                    # subtract the red channel from 1:
                    sub_1 = nodes.new(type="ShaderNodeMath")
                    sub_1.operation = 'SUBTRACT'
                    sub_1.location = (-200, 0)
                    sub_1.inputs[0].default_value = 1.0
                    lfRoughness = sub_1.outputs['Value']
                    # link them up
                    links.new(sub_1.inputs[1], separate_rgb.outputs['R'])
                    
                    # lfMetallic = lMasks.b;
                    links.new(principled_BSDF.inputs['Metallic'],
                              separate_rgb.outputs['B'])
                else:
                    roughness_value = nodes.new(type='ShaderNodeValue')
                    roughness_value.outputs[0].default_value = 1.0
                    lfRoughness = roughness_value.outputs['Value']
                    # Need to do the same for metallic default value?
                # lfRoughness *= lUniforms.mpCustomPerMaterial->gMaterialParamsVec4.x;  # noqa
                mult_param_x = nodes.new(type="ShaderNodeMath")
                mult_param_x.operation = 'MULTIPLY'
                mult_param_x.inputs[1].default_value = uniforms['gMaterialParamsVec4'].Values[0]
                links.new(mult_param_x.inputs[0], lfRoughness)
                lfRoughness = mult_param_x.outputs['Value']
            if lfRoughness is not None:
                links.new(principled_BSDF.inputs['Roughness'],
                          lfRoughness)
            # If the roughness wasn't ever defined then the default value is 1
            # which is what blender has as the default anyway
        elif tex_type == NORMAL:
            # texture
            _path = realize_path(tex_path, local_root_directory)
            if _path is not None and op.exists(_path):
                img = bpy.data.images.load(_path)
                img.colorspace_settings.name = 'Linear Rec.2020'
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

    # Apply some final transforms to the data before connecting it to the
    # Material output node

    if 20 in flags or 28 in flags:
        # #ifdef _F21_VERTEXCUSTOM
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

    if (8 in flags or 10 in flags or
            21 in flags):
        # Handle transparency
        alpha_mix = nodes.new(type='ShaderNodeMixShader')
        alpha_shader = nodes.new(type='ShaderNodeBsdfTransparent')
        if 0 in flags:
            # If there is a diffuse texture we use this to get rid of
            # transparent pixels
            discard_node = nodes.new(type="ShaderNodeMath")
            discard_node.operation = 'LESS_THAN'
            discard_node.inputs[1].default_value = kfAlphaThreshold
            lColourVec4_a = diffuse_texture.outputs['Alpha']

            links.new(discard_node.inputs[0], lColourVec4_a)
            lColourVec4_a = discard_node.outputs['Value']

            if 10 in flags:
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

    if 50 in flags:
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
    # if 6 in flags:
    #    mat.use_shadeless = True

    return mat
