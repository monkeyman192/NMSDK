# All the custom panels and properties for all the different object types

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import (StringProperty, BoolProperty, EnumProperty,
                       FloatProperty, IntVectorProperty, FloatVectorProperty,
                       IntProperty)
from ..utils.misc import getParentRefScene

""" Various properties for each of the different node types """


class NMSNodeProperties(bpy.types.PropertyGroup):
    """ Properties for the NMS Nodes """
    node_types: EnumProperty(
        name="Node Types",
        description="Select what type of Node this will be",
        items=[("Mesh", "Mesh", "Standard mesh for visible objects."),
               ("Collision", "Collision", "Shape of collision for object."),
               ("Locator", "Locator",
                "Locator object, used for interaction locations etc."),
               ("Reference", "Reference",
                "Node used to allow other scenes to be placed at this point "
                "in space."),
               # TODO: remove this description if not true?
               ("Joint", "Joint",
                "Node used primarily for animations. All meshes that are to "
                "be animated MUST be a direct child of a joint object."),
               ("Light", "Light",
                "Light that will emit light of a certain colour."),
               ("None", "None",
                "Object that will not be exported.")])
    override_name: StringProperty(
        name="Override name",
        description=("A name to be used to override the name given from "
                     "blender. This should be used with caution and sparingly."
                     " Only use if you require multiple nodes in the scene to "
                     "have the same name. Will not work for Collisions."))


class NMSMeshProperties(bpy.types.PropertyGroup):
    has_entity: BoolProperty(
        name="Requires Entity",
        description="Whether or not the mesh requires an entity file. "
                    "Not all meshes require an entity file. Read the detailed "
                    "guidelines in the readme for more details.",
        default=False)
    material_path: StringProperty(
        name="Material",
        description="(Optional) Path to material mbin file to use instead "
                    "of automatical exporting material attached to this mesh.")


class NMSMaterialProperties(bpy.types.PropertyGroup):
    material_additions: IntVectorProperty(
        name="Force material properties",
        description="List of flags to be added (use int prefix). Ie. "
                    "'_F14_UVSCROLL' == 14",
        min=0, max=64, soft_min=0, soft_max=64, size=5)


class NMSLightProperties(bpy.types.PropertyGroup):
    intensity_value: FloatProperty(name="Intensity",
                                   description="Intensity of the light.")
    FOV_value: FloatProperty(
        name="FOV", description="Field of View of the lightsource.",
        default=360, min=0, max=360)


class NMSAnimationProperties(bpy.types.PropertyGroup):
    anim_name: StringProperty(
        name="Animation Name",
        description="Name of the animation. All animations with the same "
                    "name here will be combined into one.")
    anim_loops_choice: EnumProperty(
        name="Animation Type", description="Type of animation",
        items=[("OneShot", "OneShot", "Animation runs once (per trigger)"),
               ("Loop", "Loop", "Animation loops continuously")])


class NMSLocatorProperties(bpy.types.PropertyGroup):
    has_entity: BoolProperty(
        name="Requires Entity",
        description="Whether or not the mesh requires an entity file. Not "
                    "all meshes require an entity file. Read the detailed "
                    "guidelines in the readme for more details.",
        default=False)


class NMSRotationProperties(bpy.types.PropertyGroup):
    speed: FloatProperty(
        name="Speed",
        description="Speed of the rotation around the specified axis.")


class NMSReferenceProperties(bpy.types.PropertyGroup):
    reference_path: StringProperty(
        name="Reference Path",
        description="Path to scene to be referenced at this location.",
        subtype='FILE_PATH')
    ref_path: StringProperty(
        name="Reference Path (internal)",
        description="Internal use only reference path variable.")
    scene_name: StringProperty(
        name="Scene name",
        description="Name of the scene for exporting purposes.")
    is_proc: BoolProperty(
        name="Is a proc-gen scene?",
        description="If checked, then a new panel will appear that can be "
                    "used to describe the proc-gen nature of the scene",
        default=False)
    has_lods: BoolProperty(
        name="Has custom LOD levels",
        description="Whether the scene has any custom LOD level (INTERNAL)",
        default=False)
    lod_levels: FloatVectorProperty(
        name="LOD levels",
        description="The distances for each LOD level",
        min=0)
    num_lods: IntProperty(
        name="Number of LOD levels",
        description="This is usually 3, but some models may have more or less "
                    "LOD levels. This is used internally to ensure that the "
                    "exported model will retain the original number of "
                    "LOD levels.")
    has_been_imported: BoolProperty(
        name="Has been imported?",
        description="Whether or not the scene is one that has been imported.",
        default=False)


class NMSCollisionProperties(bpy.types.PropertyGroup):
    collision_types: EnumProperty(
        name="Collision Types",
        description="Type of collision to be used",
        items=[("Mesh", "Mesh", "Mesh Collision"),
               ("Box", "Box", "Box (rectangular prism collision"),
               ("Sphere", "Sphere", "Spherical collision"),
               ("Cylinder", "Cylinder", "Cylindrical collision"),
               ("Capsule", "Capsule", "Capsule-shaped collision")])
    transform_type: EnumProperty(
        name="Scale Transform",
        description="Whether or not to use the transform data, or the "
                    "dimensions of the primitive",
        items=[("Transform", "Transform", "Use Scale transform data"),
               ("Dimensions", "Dimensions", "Use the inherent object "
                                            "dimensions (will also retain the "
                                            "transform data in the scene)")])


class NMSDescriptorProperties(bpy.types.PropertyGroup):
    choice_types: EnumProperty(
        name="Proc type",
        description="Whether or not to have the model always eselected, or "
                    "randomly selected.",
        items=[("Always", "Always", "Node is always rendered (provided "
                                    "parents are rendered)"),
               ("Random", "Random", "Node is randomly selected out of all "
                                    "others in the same hierarchy")])
    proc_prefix: StringProperty(
        name="Proc prefix",
        description="The prefix to put in front of the part name to indicate "
                    "what procedural rule to be grouped with.")


""" Various panels for each of the property types """


class NMSDK_PT_NodePropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Node Properties"
    bl_idname = "NMSDK_PT_NodePropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        # display if the object is a child of a NMS reference scene, or if the
        # object has no parent (to allow for new NMS scenes to be added).
        if (getParentRefScene(context.object) is not None or
                context.object.parent is None):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSNode_props, "node_types", expand=True)


class test_OT_op(bpy.types.Operator):
    bl_label = "test"
    bl_idname = "test.op"

    def execute(self, context):
        print(context.object)
        return {'FINISHED'}


class NMSDK_PT_ReferencePropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Reference Properties"
    bl_idname = "NMSDK_PT_ReferencePropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.NMSNode_props.node_types == 'Reference':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSReference_props, "reference_path")
        row = layout.row()
        row.prop(obj.NMSReference_props, "scene_name")
        if obj.parent is None and obj.NMSReference_props.has_lods:
            # Only draw the LOD distances if the object is the parent scene
            row = layout.row()
            row.prop(obj.NMSReference_props, "lod_levels")
        row = layout.row()
        row.prop(obj.NMSReference_props, "is_proc")
        row = layout.row()
        row.operator("nmsdk._import_ref_scene")


class NMSDK_PT_MaterialPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Material Properties"
    bl_idname = "NMSDK_PT_MaterialPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.NMSNode_props.node_types == 'Mesh'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSMaterial_props, "material_additions")


class NMSDK_PT_MeshPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Mesh Properties"
    bl_idname = "NMSDK_PT_MeshPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.NMSNode_props.node_types == 'Mesh'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSMesh_props, "has_entity")
        row = layout.row()
        row.prop(obj.NMSMesh_props, "material_path")


class NMSDK_PT_AnimationPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Animation Properties"
    bl_idname = "NMSDK_PT_AnimationPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.animation_data):
            if context.object.animation_data.action:
                return True
            else:
                return False
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSAnimation_props, "anim_name")
        row = layout.row()
        row.prop(obj.NMSAnimation_props, "anim_loops_choice", expand=True)


class NMSDK_PT_LocatorPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Locator Properties"
    bl_idname = "NMSDK_PT_LocatorPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.NMSNode_props.node_types == 'Locator'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSLocator_props, "has_entity")


class NMSDK_PT_RotationPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Rotation Properties"
    bl_idname = "NMSDK_PT_RotationPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.name.upper() == 'ROTATION'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSRotation_props, "speed")


class NMSDK_PT_LightPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Light Properties"
    bl_idname = "NMSDK_PT_LightPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.NMSNode_props.node_types == 'Light'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSLight_props, "intensity_value")
        row = layout.row()
        row.prop(obj.NMSLight_props, "FOV_value")


class NMSDK_PT_CollisionPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Collision Properties"
    bl_idname = "NMSDK_PT_CollisionPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if (getParentRefScene(context.object) is not None and
                context.object.NMSNode_props.node_types == 'Collision'):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSCollision_props, "collision_types", expand=True)
        row = layout.row()
        row.prop(obj.NMSCollision_props, "transform_type", expand=True)


class NMSDK_PT_DescriptorPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Descriptor Properties"
    bl_idname = "NMSDK_PT_DescriptorPropertyPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        parentrefscene = getParentRefScene(context.object)
        if (parentrefscene is not None
                and (context.object.NMSNode_props.node_types == 'Mesh' or
                     context.object.NMSNode_props.node_types == "Locator" or
                     context.object.NMSNode_props.node_types == "Reference")
                and parentrefscene.NMSReference_props.is_proc is True):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSDescriptor_props, "choice_types", expand=False)
        row = layout.row()
        row.prop(obj.NMSDescriptor_props, "proc_prefix")


classes = (NMSNodeProperties,
           NMSMeshProperties,
           NMSMaterialProperties,
           NMSReferenceProperties,
           NMSLocatorProperties,
           NMSLightProperties,
           NMSRotationProperties,
           NMSAnimationProperties,
           NMSCollisionProperties,
           NMSDescriptorProperties,
           test_OT_op)
panel_classes = (NMSDK_PT_NodePropertyPanel,
                 NMSDK_PT_MeshPropertyPanel,
                 NMSDK_PT_MaterialPropertyPanel,
                 NMSDK_PT_ReferencePropertyPanel,
                 NMSDK_PT_LocatorPropertyPanel,
                 NMSDK_PT_RotationPropertyPanel,
                 NMSDK_PT_LightPropertyPanel,
                 NMSDK_PT_AnimationPropertyPanel,
                 NMSDK_PT_CollisionPropertyPanel,
                 NMSDK_PT_DescriptorPropertyPanel)


class NMSPanels():
    @staticmethod
    def register():
        # register the properties
        for cls_ in classes:
            register_class(cls_)
        # link the properties with the objects' internal variables
        bpy.types.Object.NMSNode_props = bpy.props.PointerProperty(
            type=NMSNodeProperties)
        bpy.types.Object.NMSMesh_props = bpy.props.PointerProperty(
            type=NMSMeshProperties)
        bpy.types.Object.NMSMaterial_props = bpy.props.PointerProperty(
            type=NMSMaterialProperties)
        bpy.types.Object.NMSReference_props = bpy.props.PointerProperty(
            type=NMSReferenceProperties)
        bpy.types.Object.NMSLocator_props = bpy.props.PointerProperty(
            type=NMSLocatorProperties)
        bpy.types.Object.NMSRotation_props = bpy.props.PointerProperty(
            type=NMSRotationProperties)
        bpy.types.Object.NMSLight_props = bpy.props.PointerProperty(
            type=NMSLightProperties)
        bpy.types.Object.NMSAnimation_props = bpy.props.PointerProperty(
            type=NMSAnimationProperties)
        bpy.types.Object.NMSCollision_props = bpy.props.PointerProperty(
            type=NMSCollisionProperties)
        bpy.types.Object.NMSDescriptor_props = bpy.props.PointerProperty(
            type=NMSDescriptorProperties)
        # register the panels
        for cls_ in panel_classes:
            register_class(cls_)

    @staticmethod
    def unregister():
        # unregister the property classes
        for cls_ in reversed(classes):
            unregister_class(cls_)
        # delete the properties from the objects
        del bpy.types.Object.NMSNode_props
        del bpy.types.Object.NMSMesh_props
        del bpy.types.Object.NMSMaterial_props
        del bpy.types.Object.NMSReference_props
        del bpy.types.Object.NMSRotation_props
        del bpy.types.Object.NMSLocator_props
        del bpy.types.Object.NMSLight_props
        del bpy.types.Object.NMSAnimation_props
        del bpy.types.Object.NMSCollision_props
        del bpy.types.Object.NMSDescriptor_props
        # unregister the panels
        for cls_ in reversed(panel_classes):
            unregister_class(cls_)
