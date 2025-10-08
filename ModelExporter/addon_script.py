# stdlib imports
from math import radians, degrees
import os
import os.path as op
import shutil
# blender imports
import bpy
from bpy.types import Mesh as BlenderMesh
from bpy.types import Light as BlenderLight
import bmesh
from idprop.types import IDPropertyGroup
from mathutils import Matrix, Vector
# Internal imports
from ModelExporter.utils import calc_tangents
from utils.misc import CompareMatrices, get_obj_name
from utils.image_convert import convert_image
from ModelExporter.animations import process_anims
from ModelExporter.export import Export
from ModelExporter.Descriptor import Descriptor
from NMS.classes import (TkMaterialData, TkMaterialFlags, TkVolumeTriggerType,
                           TkMaterialSampler, TkMaterialUniform_Float, TkMaterialUniform_UInt,
                           TkRotationComponentData, TkPhysicsComponentData)
from NMS.classes import TkAnimationComponentData, TkAnimationData
from NMS.classes import List, Vector4f, Vector4i
from NMS.classes import TkAttachmentData
from NMS.classes.Object import Object, Model, Mesh, Locator, Reference, Collision, Light, Joint
from NMS.LOOKUPS import MATERIALFLAGS
from ModelExporter.ActionTriggerParser import ParseNodes
from serialization.NMS_Structures.Structures import TkTransformData

import numpy as np


ROT_X_MAT = Matrix.Rotation(radians(-90), 4, 'X')


def triangulate_mesh_new(mesh):
    """ Triangule the provided mesh.

    Note
    ----
    This will modify the original mesh. To avoid this you should ALWAYS pass in
    a temporary mesh object and do manipulations on this.
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces, ngon_method='EAR_CLIP')
    bm.to_mesh(mesh)
    bm.free()
    del bm


def triangulate_mesh(mesh):
    """ Triangule the provided mesh.

    Note
    ----
    This will modify the original mesh. To avoid this you should ALWAYS pass in
    a temporary mesh object and do manipulations on this.
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    data = bmesh.ops.triangulate(bm, faces=bm.faces, ngon_method='EAR_CLIP')
    face_mapping = data['face_map']
    # This face mapping should be able to be used to map the new triangles back
    # to the original polygons so that we can group them. When grouping we need
    # to ensure that each subsequent value contains 2 of the previous values so
    # that the triangulation method works. Or we can potentially just make some
    # improvements to the method that determines if the triangles are part of
    # a polygon.

    # Create a new list of the tris sorted by polygon.
    _poly_tris = sorted(face_mapping.items(), key=lambda x: x[1].index)
    face_idxs = []
    for face, _ in _poly_tris:
        face_idxs.append(tuple(x.index for x in face.verts))
    bm.to_mesh(mesh)
    bm.free()
    del bm
    return face_idxs


def generate_hull(mesh, determine_indexes=False):
    """ Generate the convex hull for a mesh.

    Parameters
    ----------
    determine_indexes : bool
        Whether to determine the index buffer for the convex hull.
        This is only needed for mesh collisions

    Returns
    -------
    chverts : list of tuples
        The list of vertex points for the convex hull of the given mesh.
    indexes : list of ints (optional)
        The index buffer for the verts.
    """
    chverts = list()
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.new()
    bm.from_mesh(mesh)
    # convex hull data. Includes face and edges and stuff...
    ch = bmesh.ops.convex_hull(bm, input=bm.verts)['geom']
    faces = list()
    for i in ch:
        if isinstance(i, bmesh.types.BMVert):
            chverts.append((i.co[0], i.co[1], i.co[2], 1.0))
        elif isinstance(i, bmesh.types.BMFace):
            if determine_indexes:
                faces.append(i)
    # determine the index stream
    if determine_indexes:
        indexes = list()
        for face in faces:
            for loop in face.loops:
                indexes.append(loop.vert.index)
    bm.free()
    del ch
    del bm
    bpy.ops.object.mode_set(mode='OBJECT')
    if determine_indexes:
        return chverts, indexes
    else:
        return chverts


def create_sampler(image, sampler_name: str, texture_dir: str,
                   output_dir: str, force_overwrite: bool = False,
                   force_material_name: str = None):
    """ Create a sampler using the specified image and paths.

    Parameters
    ----------
    image
        A Blender Image object. Extracted from the shader node and contains a
        bunch of info.
    sampler_name
        The name of the sampler. One of ('gDiffuseMap', 'gNormalMap',
        'gMasksMap').
    texture_dir
        The path relative to output_dir that the textures will be stored in.
    output_dir
        The root output directory.
    """
    if not image.filepath:
        raise Exception(
            f"Missing Image in Texture: {image.name}")

    type_ = sampler_name[1:-3].lower()
    # Determine before we convert what it should be called and where it should
    # be located. This way we can determine if it exists before we convert to
    # allow us to skip converting if we don't want to if it already exists.
    if force_material_name is not None:
        if type_ == 'diffuse':
            new_fname = f'{force_material_name}.DDS'.upper()
        else:
            new_fname = f'{force_material_name}.{type_}.DDS'.upper()
    else:
        # Clean the file name a bit and then extract the actual name from it.
        fpath = op.normpath(image.filepath.lstrip('/\\'))
        new_fname = op.splitext(op.basename(fpath))[0].upper() + '.DDS'
    relpath = op.join(texture_dir, new_fname)
    out_tex_path = op.join(output_dir, relpath)

    if op.exists(out_tex_path) and not force_overwrite:
        print(f'Found existing texture at {out_tex_path}. Using this.')
        return TkMaterialSampler(Name=sampler_name, Map=relpath, IsSRGB=False)

    # If the textures are packed into the blend file, unpack them.
    if len(image.packed_files) > 0:
        image.unpack(method="WRITE_LOCAL")

    if op.splitext(image.filepath)[1].lower() != '.dds':
        tex_path = convert_image(image.filepath_from_user(),
                                 out_tex_path,
                                 sampler_name[1:-3].lower(),
                                 tuple(image.size))
    else:
        # In this case we already have the image in .dds format. Just move it.
        tex_path = image.filepath_from_user()
        shutil.copy(tex_path, out_tex_path)
    if op.exists(out_tex_path):
        return TkMaterialSampler(Name=sampler_name, Map=relpath, IsSRGB=False)
    else:
        raise FileNotFoundError(f'Texture not written to {out_tex_path}')


""" Main exporter class with all the other functions contained in one place """


class Exporter():
    """
    The main function which handles reading all the information about
    objects in the scene and delegates the conversion of this data to the
    export.py script among others.

    Parameters
    ----------
    output_directory : str
        The absolute path to the location that all data will be exported
        to.
    export_directory : str
        The name of the folder(s) relative to the PCBANKS folder which the data
        will be placed inside.
    group_name : str
        This is the subfolder(s) which indicate the location the scene
        file should be located relative to `export_directory`.
    scene_name : str
        The name the exported scene will have.
    settings : dict
        A dictionary containing a number of settings from the export
        helper.
    """

    def __init__(self, output_directory, export_directory='CUSTOMMODELS',
                 group_name='', scene_name='', settings=dict()):
        self.global_scene = bpy.context.scene
        # set the frame to be the first one, just in case an export has already
        # been run
        self.global_scene.frame_set(0)
        self.output_directory = output_directory
        self.export_dir = export_directory
        self.export_fname = scene_name.replace(' ', '_')
        self.settings = settings

        self.state = None
        self.warnings = {}

        self.material_dict = {}
        self.material_ids = []

        # current number of joints. This is incremented as required.
        self.joints = 0

        # dictionary containing the info for each object about the entity info
        # it contains
        self.global_entitydata = dict()

        # Get a list of all reference scenes.
        # These will each be exported as their own scene.
        self.export_scenes = list()
        for obj in self.global_scene.objects:
            if obj.NMSNode_props.node_types == 'Reference':
                if (obj.NMSReference_props.reference_path == '' or
                        obj.parent is None):
                    self.export_scenes.append(obj)

        if self.settings.get('AT_only', False):
            # in this case we want to export just the entity with action
            # trigger data, nothing else
            entitydata = ParseNodes()
            entity = TkAttachmentData(Components=List(entitydata))
            entity.make_elements(main=True)
            entity.tree.write('{}.ENTITY.mxml'.format(
                op.join(self.output_directory, self.export_dir, group_name,
                        scene_name)))
            self.state = {'FINISHED'}
            return

        # run the program normally
        # if there is a name for the group, use it.
        if group_name != '':
            self.group_name = group_name.upper()
        else:
            self.group_name = self.export_fname.upper()

        # pre-process the animation information.

        # Blender object that was specified as controlling the animations.
        self.anim_controller_obj = None

        # Refresh the list of animations to ensure that
        # context.scene.nmsdk_anim_data.loaded_anims contains the list of all
        # the actions in the scene
        bpy.ops.nmsdk._refresh_anim_list()

        # A dictionary to contains the names of all the nodes in a given NMS
        # scene that either contain animation data or have a local
        # transformation matrix that is not the identity.
        self.anim_node_data = dict()
        # Populate this dictionary
        for obj in self.export_scenes:
            self.anim_node_data[obj.name] = self.get_animated_children(obj)

        self.scene_anim_data = dict()
        if len(bpy.data.actions) != 0 and self.settings.get('export_anims'):
            self.scene_anim_data = process_anims(self.anim_node_data)

        # Go over each object in the list of nodes that are to be exported
        for obj in self.export_scenes:
            name = obj.NMSReference_props.scene_name
            if name == '':
                name = get_obj_name(obj, self.export_fname)
            self.scene_directory = op.join(self.export_dir,
                                           self.group_name)
            self.inner_scene_path = op.join(self.scene_directory, name)
            print(f'inner scene path: {self.inner_scene_path}')
            # Sort out any descriptors
            descriptor = None
            if obj.NMSReference_props.is_proc:
                descriptor = self.descriptor_generator(obj)
            print('Located Object for export', name)
            orig_node_data = dict()
            if self.settings.get('preserve_node_info', False):
                orig_node_data = obj.get('scene_node', dict())
            # Get the LOD distances
            lod_distances = []
            if obj.NMSReference_props.has_lods:
                lod_distances = list(obj.NMSReference_props.lod_levels)
            scene = Model(Name=name, orig_node_data=orig_node_data,
                          lod_distances=lod_distances)
            # We don't want to actually add the main object to the scene,
            # Just its children.
            for sub_obj in obj.children:
                self.parse_object(sub_obj, scene)

            self.generate_entity_anim_data(obj.name)

            Export(self.output_directory,
                   self.scene_directory,
                   name,
                   scene,
                   self.scene_anim_data.get(obj.name, dict()),
                   descriptor,
                   self.settings)

        self.global_scene.frame_set(0)

        self.state = {'FINISHED'}

    def select_only(self, ob):
        # sets only the provided object to be selected
        for obj in bpy.context.selected_objects:
            obj.select = False
        ob.select = True

    # TODO: I thought this was fixed so this function was no longer needed...
    def get_animated_children(self, parent):
        objects = list()
        for child in parent.children:
            if (not CompareMatrices(child.matrix_local, Matrix.Identity(4),
                                    1E-6) or
                    child.animation_data is not None):
                # we want every object that either has animation data, or has a
                # transform that isn't the identity transform
                objects.append(child.name)
            objects.extend(self.get_animated_children(child))
        return objects

    def parse_material(self, ob):
        # This function returns a tkmaterialdata object with all necessary
        # material information

        # Get Material stuff
        if ob.get('MATERIAL', None) is not None:
            # if a material path has been specified simply use that
            matpath = str(ob['MATERIAL'])
            return matpath
        else:
            # otherwise parse the actual material data
            slot = ob.material_slots[0]
            mat = slot.material
            if len(ob.material_slots) > 1:
                print('WARNING: More than one material slot was found for '
                      f'{ob}. Only the first will be used. If you want '
                      'multiple split the mesh by material and try again.')

            # find any additional material flags specificed by the user
            add_matflags = set()
            for i in ob.NMSMaterial_props.material_additions:
                # 0 is just the empty one we don't care about
                if i != 0:
                    # subtract 1 to account for the index start in the struct
                    add_matflags.add(i - 1)

            # Create the material
            matflags = List()
            matsamplers = List()
            matuniforms = List()

            # Find the texture nodes
            tslots = [x for x in mat.node_tree.nodes if x.type == 'TEX_IMAGE']
            # Try and determine which of the nodes belongs to which texture
            diffuse_image = None
            normal_image = None
            mask_image = None
            for ts in tslots:
                if ('diffuse' in ts.image.name.lower()
                        or 'diffuse' in ts.label.lower()):
                    diffuse_image = ts.image
                elif ('normal' in ts.image.name.lower()
                        or 'normal' in ts.label.lower()):
                    normal_image = ts.image
                elif ('mask' in ts.image.name.lower()
                        or 'mask' in ts.label.lower()):
                    mask_image = ts.image

            if not any([diffuse_image, normal_image, mask_image]):
                raise Exception(
                    f"No texture files found for material {mat.name}.\n"
                    "Please ensure that it has textures and the nodes in the "
                    "node tree are labelled correctly (ie. diffuse in the "
                    "label for the diffuse texture, etc.")

            # Fetch Uniforms
            matuniforms.append(TkMaterialUniform_Float(Name="gMaterialColourVec4",
                                                 Values=Vector4f(X=1.000000,
                                                                 Y=1.000000,
                                                                 Z=1.000000,
                                                                 W=1.000000)))
            matuniforms.append(TkMaterialUniform_Float(Name="gMaterialParamsVec4",
                                                 Values=Vector4f(X=1.000000,
                                                                 Y=0.500000,
                                                                 Z=1.000000,
                                                                 W=0.000000)))
            matuniforms.append(TkMaterialUniform_Float(Name="gMaterialParams2Vec4",
                                                 Values=Vector4f(X=1.000000,
                                                                 Y=0.500000,
                                                                 Z=1.000000,
                                                                 W=0.000000)))
            matuniforms.append(TkMaterialUniform_Float(Name="gMaterialSFXVec4",
                                                 Values=Vector4f(X=0.000000,
                                                                 Y=0.000000,
                                                                 Z=0.000000,
                                                                 W=0.000000)))
            matuniforms.append(TkMaterialUniform_Float(Name="gMaterialSFXColVec4",
                                                 Values=Vector4f(X=0.000000,
                                                                 Y=0.000000,
                                                                 Z=0.000000,
                                                                 W=0.000000)))
            matuniforms.append(TkMaterialUniform_UInt(Name="gDynamicFlags",
                                                 Values=Vector4i(X=3,
                                                                 Y=0,
                                                                 Z=0,
                                                                 W=0)))

            if self.settings.get('use_shared_textures'):
                texture_dir = self.settings.get('shared_texture_folder')
            else:
                texture_dir = os.path.join(self.inner_scene_path, 'TEXTURES')

            if any([diffuse_image, mask_image, normal_image]):
                os.makedirs(op.join(self.output_directory, texture_dir),
                            exist_ok=True)

            texture_overwrite_name = None
            if self.settings.get('rename_textures', False):
                texture_overwrite_name = mat.name
            # Sort out Diffuse
            if diffuse_image:
                # Set _F01_DIFFUSEMAP
                add_matflags.add(0)
                # Add the sampler to the list
                matsamplers.append(create_sampler(
                    diffuse_image, "gDiffuseMap", texture_dir,
                    self.output_directory,
                    self.settings.get('overwrite_textures', False),
                    texture_overwrite_name
                ))

            # Sort out Mask
            if mask_image:
                # Set _F25_MASKS_MAP
                add_matflags.add(24)
                # Add the sampler to the list
                matsamplers.append(create_sampler(
                    mask_image, "gMasksMap", texture_dir,
                    self.output_directory,
                    self.settings.get('overwrite_textures', False),
                    texture_overwrite_name
                ))

            # Sort out Normal Map
            if normal_image:
                # Set _F03_NORMALMAP
                add_matflags.add(2)
                # Add the sampler to the list
                matsamplers.append(create_sampler(
                    normal_image, "gNormalMap", texture_dir,
                    self.output_directory,
                    self.settings.get('overwrite_textures', False),
                    texture_overwrite_name
                ))

            # Check shadeless status
            # TODO: Not compatible with 2.8x
            """
            if (mat.use_shadeless):
                # Set _F07_UNLIT
                add_matflags.add(6)
            """

            # convert to list so we can order
            lst = list(add_matflags)
            lst.sort()
            for flag in lst:
                matflags.append(
                    TkMaterialFlags(MaterialFlag=MATERIALFLAGS[flag]))

            # Create materialdata struct
            tkmatdata = TkMaterialData(Name=mat.name,
                                       Class='Opaque',
                                       CastShadow=True,
                                       Flags=matflags,
                                       Uniforms=matuniforms,
                                       Samplers=matsamplers)

            return tkmatdata

    def descriptor_generator(self, obj):
        """ Generate a descriptor for the specified object."""
        # NOTE: This will not work correctly for descriptors where the ID
        # is truncated due to the field being only 0x10 long.
        # TODO: fix this...
        descriptor_struct = Descriptor()

        def descriptor_recurse(obj, structure):
            # Recurse the object and add the object to the structure
            prefixes = set()
            important_children = []
            for child in obj.children:
                if child.NMSDescriptor_props.proc_prefix != '':
                    p = child.NMSDescriptor_props.proc_prefix
                    # Let's do a bit of processing on the prefix first to make
                    # sure all is good.
                    # The user may or may not have put a leading or trailing
                    # underscore, so we'll get rid of them and add our own
                    # just in case...
                    prefix = '_{0}_'.format(p.strip('_')).upper()
                    prefixes.add(prefix)
                    # Add only children we like to the list (ie. those with
                    # some proc info)
                    important_children.append(child)

            for prefix in prefixes:
                # adds a Node_List type child object
                structure.add_child(prefix)

            # now recurse over the children with proc info
            for child in important_children:
                # this will add a Node_Data object and return it
                p = child.NMSDescriptor_props.proc_prefix
                prefix = '_{0}_'.format(p.strip('_')).upper()
                name = get_obj_name(child, self.export_fname)
                if not name.upper().startswith(prefix):
                    # If the name doesn't start with the prefix
                    child.NMSNode_props.override_name = "{0}{1}".format(
                        prefix, name.lstrip('_'))
                node = structure.get_child(prefix).add_child(child)
                if child.NMSNode_props.node_types != 'Reference':
                    descriptor_recurse(child, node)

        descriptor_recurse(obj, descriptor_struct)

        # Get the objects name. We do this again now in case it has changed
        name = get_obj_name(obj, self.export_fname)
        # Give the descriptor its path
        descriptor_struct.path = op.join(self.scene_directory, name).upper()

        return descriptor_struct

    # Main Mesh parser
    def mesh_parser(self, ob, is_coll_mesh: bool = False):
        print(f'parsing mesh {ob.name}')
        bpy.context.view_layer.objects.active = ob
        chverts = []        # convex hull vert data
        # Matrices
        # object_matrix_wrld = ob.matrix_world
        # ob.matrix_world = rot_x_mat*ob.matrix_world
        # scale_mat = Matrix.Scale(1, 4)
        # norm_mat = rot_x_mat.inverted().transposed()

        data = ob.data
        data_is_fake = False
        # Raise exception if UV Map is missing
        if not is_coll_mesh:
            uvcount = len(data.uv_layers)
            if uvcount < 1:
                raise Exception(f"Object {ob.name} missing UV map")

        # is_triangulated = all([len(poly.vertices) == 3 for poly in data.polygons])
        # if not is_triangulated:
        #     triangulate_mesh_new(data)

        # _num_verts = len(data.vertices)
        _num_indexes = len(data.loops)

        # np_verts = np.empty((3 * _num_verts, 1))
        # data.vertices.foreach_get("co", np_verts)
        np_indexes = np.empty((_num_indexes, ), dtype=np.uint32)
        data.loops.foreach_get("vertex_index", np_indexes)
        # if not is_coll_mesh:
        #     np_uvs = np.empty((2 * _num_indexes, 1))
        #     data.uv_layers.active.data.foreach_get("uv", np_uvs)
        #     np_uvs = np_uvs.reshape((_num_indexes, 2))
        #     np_uvs[..., 1] = 1 - np_uvs[..., 1]
        #     np_uvs = np.hstack((np_uvs, np.zeros((_num_indexes, 1)), np.ones((_num_indexes, 1))))

        # np_verts.reshape((_num_verts, 3))
        # np_verts = np.hstack((np_verts, np.ones((_num_verts, 1))))

        # print(np_verts)
        # print(np_indexes)
        # if not is_coll_mesh:
        #     print(np_uvs)

        # Lists
        _num_verts = len(data.vertices)
        indexes = []
        verts = [None] * _num_verts
        if not is_coll_mesh:
            uvs = [None] * _num_verts
            normals = [None] * _num_verts
            tangents = [None] * _num_verts
            colours = [None] * _num_verts
        else:
            # For mesh collisions we don't need any of this data, but we do
            # need to return it.
            uvs = normals = tangents = colours = None

        # Get the polys before the mesh is triangulated
        poly_indexes = [tuple(p.vertices) for p in data.polygons]
        # We can check to see if the mesh needs to be triangulated cheaply by
        # checking to see if the lengths of all the polys are 3.
        if not all([len(x) == 3 for x in poly_indexes]):
            data = ob.to_mesh(preserve_all_data_layers=True)
            data_is_fake = True
            tri_indexes = triangulate_mesh(data)
            # The trinagulated data is in a weird order it seems. We can make
            # it look a lot more like how it looks in the games files. It
            # won't be perfect... But pretty close!
            tri_indexes.sort(key=lambda x: x[0])
        else:
            tri_indexes = poly_indexes

        # TODO: if there is normal data, use it. Otherwise determine the
        # normals based on the face normal of the polygon.

        # TODO: Once we have the normal, we can calculate the tangent.
        # Unfortunately the algorithm isn't exactly correct, but it seems
        # pretty close...

        # Need to assign UV data *after* any possible triangulation
        if not is_coll_mesh:
            uv_layer_data = data.uv_layers.active.data

        # Determine if the model has colour data
        export_colours = bool(len(data.vertex_colors))
        # If we have an overwrite to say not to export them then don't
        if self.settings.get('no_vert_colours', False):
            export_colours = False
        if export_colours and not is_coll_mesh:
            colour_data = data.vertex_colors.active.data
        else:
            colours = None

        bpy.ops.object.mode_set(mode='OBJECT')

        # TODO: We can detect dangling vertexes/ones which don't belong to a
        # face by using:
        # [v for v in bm.verts if not v.link_faces]
        # `link_faces` is a property of a bmesh.types.BMVert object.
        # Can probably filter to remove these either permanently or just adjust
        # the exported data to not include them (but then may need to adjust the
        # counts all over the place which may be tricky.)
        # TBD once I get a model with this issue I can test with.

        for poly in data.polygons:
            norm = poly.normal
            poly_verts = []
            _modified_poly_verts = []
            poly_indexes = []
            for _loop_index in poly.loop_indices:
                poly_verts.append(data.loops[_loop_index].vertex_index)
                poly_indexes.append(data.loops[_loop_index].index)
            for i in range(poly.loop_total):
                vi = poly_verts[i]
                li = poly_indexes[i]
                # Flag which indicates that the vert needs to be duplicated in
                # the exported mesh. This will happen when a vert which is
                # shared by multiple tri's has a different uv value depending
                # on the tri it's used by.
                vert_needs_split = False
                # Loop over the indices
                if verts[vi] is None:
                    v = data.vertices[vi].co
                    verts[vi] = (v[0], v[1], v[2], 1)
                if is_coll_mesh:
                    # If we are parsing the collision mesh, we don't need to
                    # try and get any data other than the verts and indexes
                    continue
                if uvs[vi] is None:
                    uv = uv_layer_data[li].uv
                    uvs[vi] = (uv[0], 1 - uv[1], 0, 1)
                else:
                    # Calculate the uv value to write then compare it to what
                    # we have already to see if we need to split the vert.
                    uv = uv_layer_data[li].uv
                    uv = (uv[0], 1 - uv[1], 0, 1)
                    if uv != uvs[vi]:
                        vert_needs_split = True
                        uvs.append(uv)
                if normals[vi] is None:
                    normals[vi] = (norm[0], norm[1], norm[2], 1)
                elif vert_needs_split:
                    normals.append((norm[0], norm[1], norm[2], 1))
                if tangents[vi] is None:
                    if poly.loop_total == 3:
                        tang = calc_tangents(
                            tuple(data.vertices[j].co for j in poly_verts),
                            tuple(uv_layer_data[j].uv for j in poly_indexes),
                            norm)
                        tangents[vi] = (tang[0], tang[1], tang[2], 1)
                    else:
                        print('This mesh is not currently supported.')
                        print('If you see this message please raise an issue '
                              'on discord and attach this blend file.')
                        raise NotImplementedError('Polygons need to be tris')
                elif vert_needs_split:
                    if poly.loop_total == 3:
                        tang = calc_tangents(
                            tuple(data.vertices[j].co for j in poly_verts),
                            tuple(uv_layer_data[j].uv for j in poly_indexes),
                            norm)
                    tangents.append((tang[0], tang[1], tang[2], 1))
                if export_colours:
                    if not colours[vi]:
                        vcol = colour_data[li].color
                        colours[vi] = (int(255 * vcol[0]),
                                       int(255 * vcol[1]),
                                       int(255 * vcol[2]))
                    elif vert_needs_split:
                        vcol = colour_data[li].color
                        colours.append((int(255 * vcol[0]),
                                        int(255 * vcol[1]),
                                        int(255 * vcol[2])))
                if vert_needs_split:
                    # If the vert got split, we need to add an extra index also
                    # This will be 1 less than the length as we have already
                    # added the new uv value to the list up above.
                    new_idx = len(uvs) - 1
                    # Change the value of the index in the poly_verts list so
                    # that when we write the tri it will be correct.
                    if not _modified_poly_verts:
                        _modified_poly_verts = poly_verts[:]
                    _modified_poly_verts[i] = new_idx
                    # If we split the vert, add it to the end of the vert list.
                    verts.append(verts[vi])
            if _modified_poly_verts:
                indexes += _modified_poly_verts
            else:
                indexes += poly_verts

        # finally, let's find the convex hull data of the mesh:
        chverts = generate_hull(data)

        # Check to see if any of the meshes are missing values. If they are,
        # then fill them in with the original values.
        if not is_coll_mesh:
            # Might as well put the actual vert data since we know it anyway.
            if not all(verts):
                bad_verts_count = 0
                for i, v in enumerate(verts):
                    if v is None:
                        _vert = data.vertices[i].co
                        verts[i] = (_vert[0], _vert[1], _vert[2], 1)
                        bad_verts_count += 1
                if bad_verts_count:
                    print((f'Found {bad_verts_count} verts not belonging to '
                           'any faces. Consider removing them.'))
            # For the rest, put empty data as it's not worth calculating for
            # points that won't be seen.
            if not all(uvs):
                for i, v in enumerate(uvs):
                    if v is None:
                        uvs[i] = (0, 0, 0, 1)
            if not all(normals):
                for i, v in enumerate(normals):
                    if v is None:
                        normals[i] = (0, 0, 0, 1)
            if not all(tangents):
                for i, v in enumerate(tangents):
                    if v is None:
                        tangents[i] = (0, 0, 0, 1)
            if export_colours and not all(colours):
                for i, v in enumerate(colours):
                    if v is None:
                        colours[i] = (0, 0, 0)

        if data_is_fake:
            # If we created a temporary data object then delete it
            del data

        if not is_coll_mesh:
            print(f'Exported with {len(verts)} verts, {len(uvs)} uvs, '
                  f'{len(normals)} normals, {len(indexes)} indexes')
            if isinstance(colours, list):
                print(f'Also exported {len(colours)} colours')
            elif colours:
                print(f'Colours is: {colours}')
        else:
            print(f'Exported collisions with {len(verts)} verts, '
                  f'{len(indexes)} indexes')

        return verts, normals, tangents, uvs, indexes, chverts, colours, np_indexes

    def recurce_entity(self, parent, obj, list_element=None, index=0):
        # this will return the class object of the property recursively

        # Just doing all in one line because it's going to be nasty either way
        print('obj: ', obj)
        try:
            if list_element is None:
                cls = eval(
                    getattr(parent, obj).__class__.__name__.split('_')[1])
            else:
                cls = eval(
                    getattr(
                        parent, obj)[index].__class__.__name__.split('_')[1])
        except TypeError:
            print(obj)

        properties = dict()

        if list_element is None:
            prop_group = getattr(parent, obj)
            entries = prop_group.keys()
        else:
            prop_group = getattr(parent, obj)[index]
            entries = list_element.keys()

        # iterate through each of the keys in the property group
        for prop in entries:     # parent[obj]
            # if it isn't a property group itself then just add the data to the
            # properties dict
            if not isinstance(prop_group[prop], IDPropertyGroup):
                properties[prop] = getattr(prop_group, prop)
            else:
                # otherwise call this function on the property
                print('recursing ', prop)
                properties[prop] = self.recurce_entity(prop_group, prop)
        return cls(**properties)

    def parse_object(self, ob, parent: Object):
        newob = None
        # Some objects (eg. imported bounded hulls) shouldn't be exported.
        # If the object has this custom property then ignore it.
        if ob.get('_dont_export', False):
            return
        # TODO: this is currently only true for models that are imported then
        # modified then exported again.
        trans, rot_q, scale = ob.matrix_local.decompose()
        rot = rot_q.to_euler('XYZ')

        transform = TkTransformData(TransX=trans[0],
                                    TransY=trans[1],
                                    TransZ=trans[2],
                                    RotX=degrees(rot[0]),
                                    RotY=degrees(rot[1]),
                                    RotZ=degrees(rot[2]),
                                    ScaleX=scale[0],
                                    ScaleY=scale[1],
                                    ScaleZ=scale[2])

        entitydata = dict()         # this is the local entity data

        # If the user has chosen to export an imported scene then we want to
        # try and preserve as much info as possible
        orig_node_data = dict()
        if self.settings.get('preserve_node_info', False):
            orig_node_data = ob.get('scene_node', dict())

        # let's first sort out any entity data that is specified:
        if ob.NMSMesh_props.has_entity or ob.NMSLocator_props.has_entity:
            # we need to pull information from two places:
            # ob.NMSEntity_props
            # check to see if the mesh's entity will get the action trigger
            # data
            if ('/' in ob.NMSEntity_props.name_or_path or
                    '\\' in ob.NMSEntity_props.name_or_path):
                # in this case just set the data to be a string with a path
                entitydata = ob.NMSEntity_props.name_or_path
            else:
                entitydata[ob.NMSEntity_props.name_or_path] = list()
                if ob.NMSEntity_props.has_action_triggers:
                    entitydata[ob.NMSEntity_props.name_or_path].append(
                        ParseNodes())
                # and ob.EntityStructs
                # this could potentially be it's own class?
                for struct in ob.EntityStructs:
                    # create an instance of the struct
                    _cls = eval(struct.name)
                    properties = dict()
                    # this is the list of all the properties in the struct
                    sub_props = getattr(ob,
                                        'NMS_{0}_props'.format(struct.name))
                    # iterate over each of the sub-properties
                    for prop in sub_props.keys():
                        if isinstance(sub_props[prop], IDPropertyGroup):
                            properties[prop] = self.recurce_entity(sub_props,
                                                                   prop)
                        elif isinstance(sub_props[prop], list):
                            properties[prop] = List()
                            counter = 0
                            for le in sub_props[prop]:
                                properties[prop].append(
                                    self.recurce_entity(sub_props, prop,
                                                        list_element=le,
                                                        index=counter))
                                counter += 1
                        else:
                            properties[prop] = getattr(sub_props, prop)
                    # add the struct to the entity data with all the supplied
                    # values
                    entitydata[ob.NMSEntity_props.name_or_path].append(
                        _cls(**properties))
                # do a check for whether there is physics data required
                if ob.NMSEntity_props.custom_physics:
                    entitydata[ob.NMSEntity_props.name_or_path].append(
                        TkPhysicsComponentData(
                            VolumeTriggerType=TkVolumeTriggerType(
                                VolumeTriggerType=ob.NMSPhysics_props.VolumeTriggerType)))  # noqa

        # Main switch to identify meshes or locators/references
        if ob.NMSNode_props.node_types == 'Collision':
            # COLLISION MESH
            colType = ob.NMSCollision_props.collision_types

            # The object will have its name in the scene so that any data
            # required can be linked up. This name will be overwritten by the
            # exporter to be the path name of the scene.
            optdict = {
                'Name': get_obj_name(ob, None),
                'orig_node_data': orig_node_data,
            }

            # Let's do a check on the values of the scale and the dimensions.
            # We can have it so that the user can apply scale, even if by
            # accident, or have it so that if the user wants a stretched
            # spherical or cylindrical collision that is also fine.
            dims = ob.dimensions
            if ob.NMSCollision_props.transform_type == "Transform":
                trans_scale = (1, 1, 1)
                dims = scale
                # relative scale factor (to correct for the scaling due to the
                # transform)
                # TODO: confirm; this may not be needed if we can add the
                # meshes in the correct way.
                factor = (1, 1, 1)
            else:
                trans_scale = scale
                # swap coords to match the NMS coordinate system
                dims = (ob.dimensions[0], ob.dimensions[2], ob.dimensions[1])
                factor = scale

            optdict['Transform'] = TkTransformData(
                TransX=trans[0],
                TransY=trans[1],
                TransZ=trans[2],
                RotX=degrees(rot[0]),
                RotY=degrees(rot[1]),
                RotZ=degrees(rot[2]),
                ScaleX=trans_scale[0],
                ScaleY=trans_scale[1],
                ScaleZ=trans_scale[2])
            optdict['CollisionType'] = colType

            if colType == "Mesh":
                # Mesh collisions will only have convex hull data.
                # We'll give them some "fake" vertex data which consists of
                # no actual vertex data, but an index that doesn't point to
                # anything.
                verts, norms, tangs, luvs, indexes, chverts, _, np_indexes = self.mesh_parser(ob, True)

                # Reset Transforms on meshes

                optdict['Vertices'] = verts
                optdict['Indexes'] = indexes
                optdict['Normals'] = norms
                optdict['Tangents'] = tangs
                optdict['CHVerts'] = chverts
                optdict['np_indexes'] = np_indexes
            # Handle Primitives
            elif colType == "Box":
                optdict['Width'] = dims[0] / factor[0]
                optdict['Depth'] = dims[2] / factor[2]
                optdict['Height'] = dims[1] / factor[1]
            elif colType == "Sphere":
                # take the minimum value to find the 'base' size (effectively)
                optdict['Radius'] = min([0.5 * dims[0] / factor[0],
                                         0.5 * dims[1] / factor[1],
                                         0.5 * dims[2] / factor[2]])
            elif colType == "Cylinder":
                optdict['Radius'] = min([dims[0] / factor[0],
                                         dims[1] / factor[1]])
                optdict['Height'] = dims[2] / factor[2]
            elif colType == "Capsule":
                optdict['Radius'] = min([dims[0] / factor[0],
                                         dims[2] / factor[2]])
                optdict['Height'] = dims[1] / factor[1]
            else:
                raise Exception("Unsupported Collision")

            newob = Collision(**optdict)
        elif ob.NMSNode_props.node_types == 'Mesh':
            # ACTUAL MESH
            # Parse object Geometry
            verts, norms, tangs, luvs, indexes, chverts, colours, np_indexes = self.mesh_parser(ob)

            # check whether the mesh has any child nodes we care about (such as
            # a rotation vector)
            """ This will need to be re-done!!! """
            for child in ob.children:
                if child.name.upper() == 'ROTATION':
                    # take the properties of the rotation vector and give it
                    # to the mesh as part of it's entity data
                    axis = child.rotation_quaternion * Vector((0, 0, 1))
                    print(axis)
                    rotation_data = TkRotationComponentData(
                        Speed=child.NMSRotation_props.speed,
                        Axis=Vector4f(x=axis[0], y=axis[1], z=axis[2], t=0))
                    entitydata.append(rotation_data)

            # Create Mesh Object
            newob = Mesh(Name=get_obj_name(ob, None),
                         Transform=transform,
                         Vertices=verts,
                         UVs=luvs,
                         Normals=norms,
                         Tangents=tangs,
                         Indexes=indexes,
                         CHVerts=chverts,
                         Colours=colours,
                         ExtraEntityData=entitydata,
                         HasAttachment=ob.NMSMesh_props.has_entity,
                         orig_node_data=orig_node_data,
                         np_indexes=np_indexes)

            # Check to see if the mesh's entity will be animation controller,
            # if so assign to the anim_controller_obj variable.
            if (ob.NMSEntity_props.is_anim_controller and
                    ob.NMSMesh_props.has_entity):
                # tuple, first entry is the name of the entity, the second is
                # the actual mesh object...
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path, newob)

            # Try to parse material
            if ob.NMSMesh_props.material_path != "":
                newob.Material = ob.NMSMesh_props.material_path
            else:
                try:
                    mat = ob.material_slots[0].material
                    if mat.name not in self.material_dict:
                        print("Parsing Material " + mat.name)
                        material_ob = self.parse_material(ob)
                        self.material_dict[mat.name] = material_ob
                    else:
                        material_ob = self.material_dict[mat.name]

                    # Attach material to Mesh
                    newob.Material = material_ob
                # TODO: Determine if this is the right error
                except AttributeError:
                    raise Exception("Missing Material")

        # Locator and Reference Objects
        elif ob.NMSNode_props.node_types == 'Reference':
            actualname = get_obj_name(ob, None)
            scenegraph = ob.NMSReference_props.reference_path
            if scenegraph == '':
                # We'd prefer the name to be set by the scene_name property
                name = ob.NMSReference_props.scene_name
                # But if not, just use the node name.
                if name == '':
                    name = get_obj_name(ob, None)
                scenegraph = op.join(self.scene_directory, name)
                scenegraph += '.SCENE.MBIN'
                scenegraph = scenegraph.upper()

            newob = Reference(Name=actualname,
                              Transform=transform,
                              Scenegraph=scenegraph,
                              orig_node_data=orig_node_data)
            ob.NMSReference_props.ref_path = scenegraph
        elif ob.NMSNode_props.node_types == 'Locator':
            actualname = get_obj_name(ob, None)
            HasAttachment = ob.NMSLocator_props.has_entity

            newob = Locator(Name=actualname,
                            Transform=transform,
                            ExtraEntityData=entitydata,
                            HasAttachment=HasAttachment,
                            orig_node_data=orig_node_data)

            if (ob.NMSEntity_props.is_anim_controller and
                    ob.NMSLocator_props.has_entity):
                # tuple, first entry is the name of the entity, the second is
                # the actual mesh object...
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path,
                                            newob)

        elif ob.NMSNode_props.node_types == 'Joint':
            actualname = get_obj_name(ob, None)
            self.joints += 1
            joint_num = ob.NMSJoint_props.joint_id or self.joints

            newob = Joint(Name=actualname,
                          Transform=transform,
                          JointIndex=joint_num,
                          orig_node_data=orig_node_data)

        # Light Objects
        elif ob.NMSNode_props.node_types == 'Light':
            actualname = get_obj_name(ob, None)
            # Get Color
            if actualname:
                if isinstance(ob.data, BlenderMesh):
                    col = tuple(ob.color)
                    if 'light_is_mesh' in self.warnings:
                        self.warnings['light_is_mesh'].append(actualname)
                    else:
                        self.warnings['light_is_mesh'] = [actualname, ]
                elif isinstance(ob.data, BlenderLight):
                    col = tuple(ob.data.color)
            # Get Intensity
            intensity = ob.NMSLight_props.intensity_value

            newob = Light(Name=actualname,
                          Transform=transform,
                          Colour=col,
                          Intensity=intensity,
                          FOV=ob.NMSLight_props.FOV_value,
                          orig_node_data=orig_node_data)

        if newob:
            parent.add_child(newob)

        # add the local entity data to the global dict:
        self.global_entitydata[ob.name] = entitydata

        # If we parsed a reference node or a collision node, stop.
        if (ob.NMSNode_props.node_types == 'Collision' or
                (ob.NMSNode_props.node_types == 'Reference' and
                 ob.NMSReference_props.reference_path != '')):
            return

        # Parse children
        for child in ob.children:
            self.parse_object(child, newob)

    def generate_entity_anim_data(self, scene_name):
        """ From the generated animation data for this scene, create the
        information for the animation controller so it can be written to the
        entity file later.

        Parameters
        ----------
        scene_name : str
            Name of the scene that contains the animations.
        """
        # Do nothing if there are no animations
        if len(bpy.data.actions) == 0 or not self.anim_controller_obj:
            return
        # First, check to see if there is an idle animation
        idle_anim = self.settings.get('idle_anim', '')
        if idle_anim != '':
            # If the script is being called from the cli.
            self.global_scene.nmsdk_anim_data.idle_anim = idle_anim
        idle_anim_name = self.global_scene.nmsdk_anim_data.idle_anim
        Idle = None
        Anims = List()
        if idle_anim_name != 'None':
            Idle = TkAnimationData()
        for anim_name in self.global_scene.nmsdk_anim_data.loaded_anims:
            if anim_name == 'None' or anim_name == idle_anim_name:
                continue
            # For every other anim, we want to construct the paths to be in the
            # anims folder.
            path = op.join(self.scene_directory, 'ANIMS')
            AnimationData = TkAnimationData(
                Anim=anim_name,
                Filename=op.join(
                    path,
                    "{}.ANIM.MBIN".format(anim_name.upper())))
            Anims.append(AnimationData)

        # construct the entity data
        anim_entity = TkAnimationComponentData(Idle=Idle, Anims=Anims)
        # update the entity data directly
        self.anim_controller_obj[1].ExtraEntityData[
            self.anim_controller_obj[0]].append(anim_entity)
        self.anim_controller_obj[1].rebuild_entity()
