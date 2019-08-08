# stdlib imports
import os
import sys
from math import radians, degrees
# blender imports
import bpy  # pylint: disable=import-error
import bmesh  # pylint: disable=import-error
from idprop.types import IDPropertyGroup  # pylint: disable=import-error
from mathutils import Matrix, Vector  # pylint: disable=import-error
# Internal imports
from ..utils.misc import CompareMatrices, get_obj_name
from .utils import (apply_local_transform, transform_to_NMS_coords,
                    get_actions_with_name)
from .export import Export
from .Descriptor import Descriptor
from ..NMS.classes import (TkMaterialData, TkMaterialFlags,
                           TkVolumeTriggerType, TkMaterialSampler,
                           TkTransformData, TkMaterialUniform,
                           TkRotationComponentData, TkPhysicsComponentData)
# Animation objects
from ..NMS.classes import (TkAnimMetadata, TkAnimNodeData, TkAnimNodeFrameData)
from ..NMS.classes import TkAnimationComponentData, TkAnimationData
from ..NMS.classes import List, Vector4f, Quaternion
from ..NMS.classes import TkAttachmentData
# Object Classes
from ..NMS.classes import (Model, Mesh, Locator, Reference, Collision, Light,
                           Joint)
from ..NMS.LOOKUPS import MATERIALFLAGS
from .ActionTriggerParser import ParseNodes


ROT_X_MAT = Matrix.Rotation(radians(-90), 4, 'X')


# Attempt to find 'blender.exe path'

# TODO: do we need any of this??

for path in sys.path:
    if os.path.isdir(path):
        if 'ModelExporter' in os.listdir(path):
            print("Found ModelExporter at: ", path)
            os.chdir(path)
            break


# Add script path to sys.path
scriptpath = os.path.join(os.getcwd(), 'ModelExporter')

print(scriptpath)

if scriptpath not in sys.path:
    sys.path.append(scriptpath)
    # print(sys.path)


def triangulate_mesh(mesh):
    """ Triangule the provided mesh.

    Note
    ----
    This will modify the original mesh. To avoid this you should ALWAYS pass in
    a temporary mesh object and do manipulations on this.
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    del bm


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
        if type(i) == bmesh.types.BMVert:
            chverts.append((i.co[0], i.co[1], i.co[2], 1.0))
        elif type(i) == bmesh.types.BMFace:
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


""" Main exporter class with all the other functions contained in one place """


class Exporter():
    # class to contain all the exporting functions

    def __init__(self, exportpath, settings):
        self.global_scene = bpy.context.scene
        # set the frame to be the first one, just in case an export has already
        # been run
        self.global_scene.frame_set(0)
        self.export_name = os.path.basename(exportpath)
        self.settings = settings

        # self.blend_to_NMS_mat = Matrix.Rotation(radians(-90), 4, 'X')
        """self.blend_to_NMS_mat = Matrix()
        self.blend_to_NMS_mat[0] = Vector((1.0, 0.0, 0.0, 0.0))
        self.blend_to_NMS_mat[1] = Vector((0.0, 0.0, 1.0, 0.0))
        self.blend_to_NMS_mat[2] = Vector((0.0, -1.0, 0.0, 0.0))
        self.blend_to_NMS_mat[3] = Vector((0.0, 0.0, 0.0, 1.0))"""

        self.state = None

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
                if obj.NMSReference_props.reference_path == '':
                    self.export_scenes.append(obj)

        if self.settings['AT_only']:
            # in this case we want to export just the entity with action
            # trigger data, nothing else
            entitydata = ParseNodes()
            entity = TkAttachmentData(Components=List(entitydata))
            entity.make_elements(main=True)
            mpath = os.path.dirname(os.path.abspath(exportpath))
            os.chdir(mpath)
            entity.tree.write('{}.ENTITY.exml'.format(self.export_name))
            self.state = {'FINISHED'}
            return

        # run the program normally
        # get the base path as specified
        if self.settings['export_directory'] != '':
            self.basepath = self.settings['export_directory']
        else:
            self.basepath = 'CUSTOMMODELS'
        # if there is a name for the group, use it.
        if self.settings['group_name'] != '':
            self.group_name = self.settings['group_name']
        else:
            self.group_name = self.export_name

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

        self.scene_anim_data = self.process_anims()

        # Go over each object in the list of nodes that are to be exported
        for obj in self.export_scenes:
            # First, sort out any descriptors
            descriptor = None
            if obj.NMSReference_props.is_proc:
                descriptor = self.descriptor_generator(obj)
            name = obj.NMSReference_props.scene_name
            if name == '':
                name = get_obj_name(obj, self.export_name)
            print('Located Object for export', name)
            scene = Model(Name=name)
            scene_directory = os.path.join(
                self.basepath, self.group_name, self.export_name)
            # We don't want to actually add the main object to the scene,
            # Just its children.
            for sub_obj in obj.children:
                self.parse_object(sub_obj, scene)

            self.generate_entity_anim_data(obj.name, scene_directory)

            mpath = os.path.dirname(os.path.abspath(exportpath))
            os.chdir(mpath)
            Export(name,
                   self.group_name,
                   self.basepath,
                   scene,
                   self.scene_anim_data[obj.name],
                   descriptor)

        self.global_scene.frame_set(0)

        self.state = {'FINISHED'}

    def select_only(self, ob):
        # sets only the provided object to be selected
        for obj in bpy.context.selected_objects:
            obj.select = False
        ob.select = True

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
        # TODO: This will all become obsolete at some point
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
            print(mat.name)

            # find any additional material flags specificed by the user
            add_matflags = set()
            for i in ob.NMSMaterial_props.material_additions:
                # 0 is just the empty one we don't care about
                if i != 0:
                    # subtract 1 to account for the index start in the struct
                    add_matflags.add(i - 1)

            proj_path = bpy.path.abspath('//')

            # Create the material
            matflags = List()
            matsamplers = List()
            matuniforms = List()

            tslots = mat.texture_slots

            # Fetch Uniforms
            matuniforms.append(TkMaterialUniform(Name="gMaterialColourVec4",
                                                 Values=Vector4f(x=1.0,
                                                                 y=1.0,
                                                                 z=1.0,
                                                                 t=1.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialParamsVec4",
                                                 Values=Vector4f(x=1.0,
                                                                 y=0.5,
                                                                 z=1.0,
                                                                 t=0.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialSFXVec4",
                                                 Values=Vector4f(x=0.0,
                                                                 y=0.0,
                                                                 z=0.0,
                                                                 t=0.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialSFXColVec4",
                                                 Values=Vector4f(x=0.0,
                                                                 y=0.0,
                                                                 z=0.0,
                                                                 t=0.0)))
            # Fetch Diffuse
            texpath = ""
            if tslots[0]:
                # Set _F01_DIFFUSEMAP
                add_matflags.add(0)
                # matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[0]))
                # Create gDiffuseMap Sampler

                tex = tslots[0].texture
                # Check if there is no texture loaded
                if not tex.type == 'IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)

                texpath = os.path.join(proj_path, tex.image.filepath[2:])
            print(texpath)
            sampl = TkMaterialSampler(Name="gDiffuseMap", Map=texpath,
                                      IsSRGB=True)
            matsamplers.append(sampl)

            # Check shadeless status
            if (mat.use_shadeless):
                # Set _F07_UNLIT
                add_matflags.add(6)

            # Fetch Mask
            texpath = ""
            if tslots[1]:
                # Create gMaskMap Sampler

                tex = tslots[1].texture
                # Check if there is no texture loaded
                if not tex.type == 'IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)

                texpath = os.path.join(proj_path, tex.image.filepath[2:])

            sampl = TkMaterialSampler(Name="gMasksMap", Map=texpath,
                                      IsSRGB=False)
            matsamplers.append(sampl)

            # Fetch Normal Map
            texpath = ""
            if tslots[2]:
                # Set _F03_NORMALMAP
                add_matflags.add(2)
                # Create gNormalMap Sampler

                tex = tslots[2].texture
                # Check if there is no texture loaded
                if not tex.type == 'IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)

                texpath = os.path.join(proj_path, tex.image.filepath[2:])

            sampl = TkMaterialSampler(Name="gNormalMap", Map=texpath,
                                      IsSRGB=False)
            matsamplers.append(sampl)

            add_matflags.add(24)
            add_matflags.add(38)
            add_matflags.add(46)

            lst = list(add_matflags)        # convert to list so we can order
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
                name = get_obj_name(child, self.export_name)
                if not name.startswith(prefix):
                    # If the name doesn't start with the prefix
                    child.NMSNode_props.override_name = "{0}{1}".format(
                        prefix, name.lstrip('_').upper())
                node = structure.get_child(prefix).add_child(child)
                if child.NMSNode_props.node_types != 'Reference':
                    descriptor_recurse(child, node)

        descriptor_recurse(obj, descriptor_struct)

        # Get the objects name. We do this again now in case it has changed
        name = get_obj_name(obj, self.export_name)
        # Give the descriptor its path
        descriptor_struct.path = os.path.join(self.basepath, self.group_name,
                                              name).upper()

        return descriptor_struct

    # Main Mesh parser
    def mesh_parser(self, ob):
        self.global_scene.objects.active = ob
        # Lists
        indexes = []
        verts = []
        uvs = []
        normals = []
        tangents = []
        colours = []
        chverts = []        # convex hull vert data
        # Matrices
        # object_matrix_wrld = ob.matrix_world
        # ob.matrix_world = rot_x_mat*ob.matrix_world
        # scale_mat = Matrix.Scale(1, 4)
        # norm_mat = rot_x_mat.inverted().transposed()

        data = ob.data
        data_is_temp = False
        # Raise exception if UV Map is missing
        uvcount = len(data.uv_layers)
        if uvcount < 1:
            raise Exception("Missing UV Map")

        uv_layer_name = data.uv_layers.active.name

        # Calculate the tangents and normals from the uv map
        try:
            data.calc_tangents(uvmap=uv_layer_name)
        except RuntimeError:
            data = ob.to_mesh(self.global_scene, False, 'PREVIEW')
            data_is_temp = True
            triangulate_mesh(data)
            data.calc_tangents(uvmap=uv_layer_name)

        # Need to assign UV data *after* any possible triangulation
        uv_layer_data = data.uv_layers.active.data

        # Determine if the model has colour data
        export_colours = bool(len(data.vertex_colors))
        # If we have an overwrite to say not to export them then don't
        if self.settings['no_vert_colours']:
            export_colours = False
        if export_colours:
            colour_data = data.vertex_colors.active.data
        else:
            colours = None

        bpy.ops.object.mode_set(mode='OBJECT')

        # Iterate over all the MeshLoops of the mesh
        for ml in data.loops:
            index = ml.index
            vert_index = ml.vertex_index
            indexes.append(index)
            vert = data.vertices[vert_index].co
            verts.append((vert[0], vert[1], vert[2], 1))
            uv = uv_layer_data[index].uv
            uvs.append((uv[0], 1 - uv[1], 0, 1))
            normal = ml.normal
            normals.append((normal[0], normal[1], normal[2], 1))
            tangent = ml.tangent
            tangents.append((tangent[0], tangent[1], tangent[2], 1))
            if export_colours:
                vcol = colour_data[index].color
                colours.append([int(255 * vcol[0]),
                                int(255 * vcol[1]),
                                int(255 * vcol[2])])

        # finally, let's find the convex hull data of the mesh:
        chverts = generate_hull(data)
        if data_is_temp:
            # If we created a temporary data object then delete it
            del data

        # Apply rotation and normal matrices on vertices and normal vectors
        apply_local_transform(ROT_X_MAT, verts, normalize=False)
        apply_local_transform(ROT_X_MAT, normals, use_norm_mat=True)
        apply_local_transform(ROT_X_MAT, tangents, use_norm_mat=True)
        apply_local_transform(ROT_X_MAT, chverts, normalize=False)

        return verts, normals, tangents, uvs, indexes, chverts, colours

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

    def parse_object(self, ob, parent):
        newob = None
        # Apply location/rotation/scale
        # bpy.ops.object.transform_apply(location=False, rotation=True,
        #                                scale=True)

        # get the objects' location and convert to NMS coordinates
        trans, rot_q, scale = transform_to_NMS_coords(ob)
        rot = rot_q.to_euler()      # TODO: should be 'ZXY'??

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

        # let's first sort out any entity data that is specified:
        if ob.NMSMesh_props.has_entity or ob.NMSLocator_props.has_entity:
            print('this has an entity:', ob)
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
            optdict = {'Name': get_obj_name(ob, None)}

            # Let's do a check on the values of the scale and the dimensions.
            # We can have it so that the user can apply scale, even if by
            # accident, or have it so that if the user wants a stretched
            # spherical or cylindrical collision that is also fine.
            dims = ob.dimensions
            if ob.NMSCollision_props.transform_type == "Transform":
                trans_scale = (1, 1, 1)
                dims = scale
                # relative scale factor (to correct for the scaling due to the\
                # transform)
                factor = (0.5, 0.5, 0.5)
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

                chverts, chindexes = generate_hull(ob.data, True)

                # Apply rotation to the convex hull
                apply_local_transform(ROT_X_MAT, chverts, normalize=False)

                # Reset Transforms on meshes

                optdict['CHVerts'] = chverts
                optdict['CHIndexes'] = chindexes
            # Handle Primitives
            elif colType == "Box":
                optdict['Width'] = dims[0]/factor[0]
                optdict['Depth'] = dims[2]/factor[2]
                optdict['Height'] = dims[1]/factor[1]
            elif colType == "Sphere":
                # take the minimum value to find the 'base' size (effectively)
                optdict['Radius'] = min([0.5*dims[0]/factor[0],
                                         0.5*dims[1]/factor[1],
                                         0.5*dims[2]/factor[2]])
            elif colType == "Cylinder":
                optdict['Radius'] = min([0.5*dims[0]/factor[0],
                                         0.5*dims[2]/factor[2]])
                optdict['Height'] = dims[1]/factor[1]
            else:
                raise Exception("Unsupported Collision")

            newob = Collision(**optdict)
        elif ob.NMSNode_props.node_types == 'Mesh':
            # ACTUAL MESH
            # Parse object Geometry
            verts, norms, tangs, luvs, indexes, chverts, colours = self.mesh_parser(ob)  # noqa

            # check whether the mesh has any child nodes we care about (such as
            # a rotation vector)
            """ This will need to be re-done!!! """
            for child in ob.children:
                if child.name.upper() == 'ROTATION':
                    # take the properties of the rotation vector and give it
                    # to the mesh as part of it's entity data
                    axis = child.rotation_quaternion*Vector((0, 0, 1))
                    # axis = Matrix.Rotation(
                    #    radians(-90), 4, 'X')*(rot*Vector((0,1,0)))
                    print(axis)
                    rotation_data = TkRotationComponentData(
                        Speed=child.NMSRotation_props.speed,
                        Axis=Vector4f(x=axis[0], y=axis[1], z=axis[2], t=0))
                    entitydata.append(rotation_data)

            # Create Mesh Object
            actualname = get_obj_name(ob, None)
            newob = Mesh(Name=actualname,
                         Transform=transform,
                         Vertices=verts,
                         UVs=luvs,
                         Normals=norms,
                         Tangents=tangs,
                         Indexes=indexes,
                         CHVerts=chverts,
                         Colours=colours,
                         ExtraEntityData=entitydata,
                         HasAttachment=ob.NMSMesh_props.has_entity)

            # Check to see if the mesh's entity will be animation controller,
            # if so assign to the anim_controller_obj variable.
            if (ob.NMSEntity_props.is_anim_controller and
                    ob.NMSMesh_props.has_entity):
                # tuple, first entry is the name of the entity, the second is
                # the actual mesh object...
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path,
                                            newob)

            # Try to parse material
            if ob.NMSMesh_props.material_path != "":
                newob.Material = ob.NMSMesh_props.material_path
            else:
                try:
                    slot = ob.material_slots[0]
                    mat = slot.material
                    print(mat.name)
                    if mat.name not in self.material_dict:
                        print("Parsing Material " + mat.name)
                        material_ob = self.parse_material(ob)
                        self.material_dict[mat.name] = material_ob
                    else:
                        material_ob = self.material_dict[mat.name]

                    print(material_ob)
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
                scenegraph = os.path.join(self.basepath, self.group_name, name)
                scenegraph += '.SCENE.MBIN'
                scenegraph = scenegraph.upper()

            newob = Reference(Name=actualname,
                              Transform=transform,
                              Scenegraph=scenegraph)
            ob.NMSReference_props.ref_path = scenegraph
        elif ob.NMSNode_props.node_types == 'Locator':
            actualname = get_obj_name(ob, None)
            HasAttachment = ob.NMSLocator_props.has_entity

            newob = Locator(Name=actualname,
                            Transform=transform,
                            ExtraEntityData=entitydata,
                            HasAttachment=HasAttachment)

            if (ob.NMSEntity_props.is_anim_controller and
                    ob.NMSLocator_props.has_entity):
                # tuple, first entry is the name of the entity, the second is
                # the actual mesh object...
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path,
                                            newob)

        elif ob.NMSNode_props.node_types == 'Joint':
            actualname = get_obj_name(ob, None)
            self.joints += 1
            newob = Joint(Name=actualname,
                          Transform=transform,
                          JointIndex=self.joints)

        # Light Objects
        elif ob.NMSNode_props.node_types == 'Light':
            actualname = get_obj_name(ob, None)
            # Get Color
            col = tuple(ob.data.color)
            print("colour: {}".format(col))
            # Get Intensity
            intensity = ob.NMSLight_props.intensity_value

            newob = Light(Name=actualname,
                          Transform=transform,
                          Colour=col,
                          Intensity=intensity,
                          FOV=ob.NMSLight_props.FOV_value)

        parent.add_child(newob)

        # add the local entity data to the global dict:
        self.global_entitydata[ob.name] = entitydata

        # If we parsed a reference node or a collision node, stop.
        if (ob.NMSNode_props.node_types == 'Collision' or
                (ob.NMSNode_props.node_types == 'Reference' and
                 ob.NMSReference_props.reference_path == '')):
            return

        # Parse children
        for child in ob.children:
            self.parse_object(child, newob)

    def process_anims(self):
        # TODO: move to separate file. This doesn't need to be part of this
        # class.
        # Iterate over all the actions in the scene
        anim_data = dict()

        for anim_name in self.global_scene.nmsdk_anim_data.loaded_anims:
            # Ignore the 'None' action.
            if anim_name == 'None':
                continue
            # Get the list of all the actions with the base name.
            actions = get_actions_with_name(anim_name)

            print('Processing animation {0}'.format(anim_name))

            action_frames = None

            # Apply the current animation to any object that uses it.
            bpy.ops.nmsdk._change_animation(anim_names=anim_name)

            objs_in_action = list()
            varying_components = dict()

            for action in actions:
                # Ensure that the name of the action is valid.
                try:
                    obj_name = action.name.split('.', 1)[1]
                except IndexError:
                    raise ValueError(
                        'The action {0} has an invalid name. Please fix it '
                        'manually or by running the fix actions tool in the '
                        'NMSDK settings panel.'.format(action.name))
                # Add the name of the object to the list of objects that are
                # animated in this action
                objs_in_action.append(obj_name)
                # Get the set of which components in the action change.
                _varying = set()
                for fcurve in action.fcurves:
                    _varying.add(fcurve.data_path)
                # Make sure that there is only one kind of rotation applied
                if ('rotation_euler' in _varying and
                        'rotation_quaternion' in _varying):
                    raise ValueError(
                        'Action {0} contains two different types of rotations.'
                        'Please only use one.'.format(action.name))
                # Sanitize the set a little to homogenise the 'rotation_euler'
                # and 'rotation_quaternion' values if they exist.
                if 'rotation_euler' in _varying:
                    _varying.remove('rotation_euler')
                    _varying.add('rotation')
                if 'rotation_quaternion' in _varying:
                    _varying.remove('rotation_quaternion')
                    _varying.add('rotation')

                # Get the number of frames and ensure that it is the same as
                # all the other actions in the same animation.
                if action_frames is None:
                    action_frames = int(action.frame_range[1])
                else:
                    if int(action.frame_range[1]) != action_frames:
                        raise ValueError(
                            'Action {0} has a different number of frames to '
                            'the other actions in the animation. Please ensure'
                            ' that all actions with the same name have the '
                            'same number of frames.'.format(action.name))

                # Assign the components that vary to the dictionary
                varying_components[obj_name] = _varying

            # Determine the indexes of the rotation, translation and scales
            anim_rot, still_rot = (0, 0)
            anim_loc, still_loc = (0, 0)
            anim_sca, still_sca = (0, 0)
            rot_index, loc_index, sca_index = (0, 0, 0)
            indexes = dict()
            NodeData = List()
            # Go over each of the objects and assign the indexes.
            # The index for animated objects will be real, but the one for
            # still types will not be. They will need the `anim_<~>` variable
            # added to them
            for scene_name, animated_objs in self.anim_node_data.items():
                if not set(objs_in_action).issubset(set(animated_objs)):
                    # We only want to generate data for animations that are
                    # actually in this scene
                    continue
                scene_anim_data = dict()

                for obj_name in animated_objs:
                    varying = varying_components.get(obj_name, set())
                    if 'rotation' in varying:
                        rot_index = anim_rot
                        anim_rot += 1
                    else:
                        rot_index = still_rot
                        still_rot += 1
                    if 'location' in varying:
                        loc_index = anim_loc
                        anim_loc += 1
                    else:
                        loc_index = still_loc
                        still_loc += 1
                    if 'scale' in varying:
                        sca_index = anim_sca
                        anim_sca += 1
                    else:
                        sca_index = still_sca
                        still_sca += 1
                    indexes[obj_name] = (rot_index, loc_index, sca_index)

                # Rectify the indexes of any still frame data
                for obj_name in animated_objs:
                    varying = varying_components.get(obj_name, set())
                    rot_index, loc_index, sca_index = indexes[obj_name]
                    if 'rotation' not in varying:
                        rot_index += anim_rot
                    if 'location' not in varying:
                        loc_index += anim_loc
                    if 'scale' not in varying:
                        sca_index += anim_sca
                    # add the anim node data
                    NodeData.append(TkAnimNodeData(Node=obj_name.upper(),
                                                   RotIndex=str(rot_index),
                                                   TransIndex=str(loc_index),
                                                   ScaleIndex=str(sca_index)))

                AnimFrameData = List()
                stillTranslations = List()
                stillRotations = List()
                stillScales = List()

                # Finally, we want to run the animation and get all the frame
                # data.
                for frame in range(action_frames + 1):
                    # need to change the frame of the scene to appropriate one.
                    self.global_scene.frame_set(frame)

                    Translations = List()
                    Rotations = List()
                    Scales = List()

                    for obj_name in animated_objs:
                        obj = bpy.data.objects[obj_name]
                        # TODO: is it better to just get the data directly from
                        # the fcurve.co??
                        trans, rot_q, scale = transform_to_NMS_coords(obj)

                        # Add the location data
                        if 'location' in varying_components.get(obj_name,
                                                                set()):
                            Translations.append(Vector4f(x=trans.x,
                                                         y=trans.y,
                                                         z=trans.z,
                                                         t=1.0))
                        else:
                            if frame == 0:
                                stillTranslations.append(Vector4f(x=trans.x,
                                                                  y=trans.y,
                                                                  z=trans.z,
                                                                  t=1.0))
                        # Add the rotation data
                        if 'rotation' in varying_components.get(obj_name,
                                                                set()):
                            Rotations.append(Quaternion(x=rot_q.x,
                                                        y=rot_q.y,
                                                        z=rot_q.z,
                                                        w=rot_q.w))
                        else:
                            if frame == 0:
                                stillRotations.append(Quaternion(x=rot_q.x,
                                                                 y=rot_q.y,
                                                                 z=rot_q.z,
                                                                 w=rot_q.w))
                        # Add the scale data
                        if 'scale' in varying_components.get(obj_name, set()):
                            Scales.append(Vector4f(x=scale.x,
                                                   y=scale.y,
                                                   z=scale.z,
                                                   t=1.0))
                        else:
                            if frame == 0:
                                stillScales.append(Vector4f(x=scale.x,
                                                            y=scale.y,
                                                            z=scale.z,
                                                            t=1.0))
                    FrameData = TkAnimNodeFrameData(Rotations=Rotations,
                                                    Translations=Translations,
                                                    Scales=Scales)
                    AnimFrameData.append(FrameData)

                # Assign the still frame data
                StillFrameData = TkAnimNodeFrameData(
                    Rotations=stillRotations,
                    Translations=stillTranslations,
                    Scales=stillScales)

                scene_anim_data[anim_name] = TkAnimMetadata(
                    FrameCount=str(action_frames + 1),
                    NodeCount=str(len(animated_objs)),
                    NodeData=NodeData,
                    AnimFrameData=AnimFrameData,
                    StillFrameData=StillFrameData)
                if scene_name in anim_data:
                    anim_data[scene_name].update(scene_anim_data)
                else:
                    anim_data[scene_name] = scene_anim_data

        return anim_data

    def generate_entity_anim_data(self, scene_name, scene_directory):
        """ From the generated animation data for this scene, create the
        information for the animation controller so it can be written to the
        entity file later.

        Parameters
        ----------
        scene_name : str
            Name of the scene that contains the animations.
        scene_directory : str
            Output directory for the scene files.
        """
        # First, check to see if there is an idle animation
        idle_anim_name = self.global_scene.nmsdk_anim_data.idle_anim
        Idle = None
        Anims = List()
        if idle_anim_name != 'None':
            path = os.path.join(self.basepath, self.group_name.upper(),
                                self.export_name.upper())
            Idle = TkAnimationData()
        for anim_name in self.global_scene.nmsdk_anim_data.loaded_anims:
            if anim_name == 'None' or anim_name == idle_anim_name:
                continue
            # For every other anim, we want to construct the paths to be in the
            # anims folder.
            path = os.path.join(self.basepath, self.group_name.upper(),
                                'ANIMS')
            AnimationData = TkAnimationData(
                Anim=anim_name,
                Filename=os.path.join(
                    path, "{}.ANIM.MBIN".format(anim_name.upper())))
            Anims.append(AnimationData)

        # construct the entity data
        anim_entity = TkAnimationComponentData(Idle=Idle, Anims=Anims)
        # update the entity data directly
        self.anim_controller_obj[1].ExtraEntityData[
            self.anim_controller_obj[0]].append(anim_entity)
        self.anim_controller_obj[1].rebuild_entity()
