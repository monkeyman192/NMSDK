# All the custom panels and properties for all the different object types

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty

""" Various properties for each of the different node types """

class NMSNodeProperties(bpy.types.PropertyGroup):
    """ Properties for the NMS Nodes """
    is_NMS_node = BoolProperty(name = "Is NMS Node?",
                               description = "Enable if the object is a node in the scene file",
                               default = True)
    
    node_types = EnumProperty(name = "Node Types",
                              description = "Select what type of Node this will be",
                              items = [("Mesh" , "Mesh" , "Standard mesh for visible objects."),
                                       ("Collision", "Collision", "Shape of collision for object."),
                                       ("Locator", "Locator", "Locator object, used for interaction locations etc."),
                                       ("Reference", "Reference", "Node used to allow other scenes to be placed at this point in space"),
                                       ("Joint", "Joint", "Node used primarily for animations. All meshes that are to be animated MUST be a direct child of a joint object"),
                                       ("Light", "Light", "Light that will emit light of a certain colour")])

class NMSMeshProperties(bpy.types.PropertyGroup):
    has_entity = BoolProperty(name = "Requires Entity",
                              description = "Whether or not the mesh requires an entity file. Not all meshes require an entity file. Read the detailed guidelines in the readme for more details.",
                              default = False)
    create_tangents = BoolProperty(name = "Create Tangents",
                              description = "Whether or not to generate tangents along with the mesh conversion (Enable only if you are sure about your UV Map).",
                              default = False)
    material_path = StringProperty(name = "Material",
                                   description = "(Optional) Path to material mbin file to use instead of automattical exporting material attached to this mesh.")

class NMSLightProperties(bpy.types.PropertyGroup):
    intensity_value = FloatProperty(name = "Intensity",
                                    description = "Intensity of the light.")
    FOV_value = FloatProperty(name = "FOV",
                              description = "Field if View of the lightsource.",
                              default = 360,
                              min = 0,
                              max = 360)

class NMSEntityProperties(bpy.types.PropertyGroup):
    is_anim_controller = BoolProperty(name = "Is animation controller?",
                                      description = "When ticked, this entity contains all the required animation information. Only tick this for one entity per scene.",
                                      default = False)
    has_action_triggers = BoolProperty(name = "Has ActionTriggers?",
                                       description = "Whether or not this entity file will be give the data for the action triggers.",
                                       default = False)
    is_flyable = BoolProperty(name = "Is flyable?",
                              description = "If true, the entity file will contain the required components to make the object pilotable.",
                              default = False)

class NMSAnimationProperties(bpy.types.PropertyGroup):
    anim_name = StringProperty(name = "Animation Name",
                                   description = "Name of the animation. All animations with the same name here will be combined into one.")
    anim_loops_choice = EnumProperty(name = "Animation Type",
                                   description = "Type of animation",
                                   items = [("OneShot" , "OneShot" , "Animation runs once (per trigger)"),
                                            ("Loop", "Loop", "Animation loops continuously")])

class NMSLocatorProperties(bpy.types.PropertyGroup):
    has_entity = BoolProperty(name = "Requires Entity",
                              description = "Whether or not the mesh requires an entity file. Not all meshes require an entity file. Read the detailed guidelines in the readme for more details.",
                              default = False)

class NMSReferenceProperties(bpy.types.PropertyGroup):
    reference_path = StringProperty(name = "Reference Path",
                                    description = "Path to scene to be referenced at this location.")

class NMSSceneProperties(bpy.types.PropertyGroup):
    batch_mode = BoolProperty(name = "Batch Mode",
                              description = "If ticked, each direct child of this node will be exported separately",
                              default = False)
    group_name = StringProperty(name = "Group Name",
                                description = "Group name so that models that all belong in the same folder are placed there (path becomes group_name/name)")
    dont_compile = BoolProperty(name = "Don't compile to .mbin",
                                description = "If true, the exml files will not be compiled to an mbin file. This saves a lot of time waiting for the geometry files to compile",
                                default = False)

class NMSCollisionProperties(bpy.types.PropertyGroup):
    collision_types = EnumProperty(name = "Collision Types",
                                   description = "Type of collision to be used",
                                   items = [("Mesh" , "Mesh" , "Mesh Collision"),
                                            ("Box", "Box", "Box (rectangular prism collision"),
                                            ("Sphere", "Sphere", "Spherical collision"),
                                            ("Cylinder", "Cylinder", "Cylindrical collision")])

""" Various panels for each of the property types """

class NMSNodePropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Node Properties"
    bl_idname = "OBJECT_PT_node_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and not context.object.name.startswith("NMS_SCENE"):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSNode_props, "node_types", expand=True)

class NMSReferencePropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Reference Properties"
    bl_idname = "OBJECT_PT_reference_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.NMSNode_props.node_types == 'Reference':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSReference_props, "reference_path")

class NMSMeshPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Mesh Properties"
    bl_idname = "OBJECT_PT_mesh_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.NMSNode_props.node_types == 'Mesh' and not context.object.name.startswith("NMS_SCENE"):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSMesh_props, "has_entity")
        row = layout.row()
        row.prop(obj.NMSMesh_props, "create_tangents")
        row = layout.row()
        row.prop(obj.NMSMesh_props, "material_path")

class NMSEntityPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Entity Properties"
    bl_idname = "OBJECT_PT_entity_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and (context.object.NMSMesh_props.has_entity or context.object.NMSLocator_props.has_entity):
            # only a mesh or locator can have an associated entity file
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSEntity_props, "is_anim_controller")
        row = layout.row()
        row.prop(obj.NMSEntity_props, "has_action_triggers")
        #row = layout.row()
        #row.prop(obj.NMSEntity_props, "is_flyable")

class NMSAnimationPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Animation Properties"
    bl_idname = "OBJECT_PT_animation_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.animation_data:
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
        row.prop(obj.NMSAnimation_props, "anim_loops_choice", expand = True)

class NMSLocatorPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Locator Properties"
    bl_idname = "OBJECT_PT_locator_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.NMSNode_props.node_types == 'Locator':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSLocator_props, "has_entity")

class NMSLightPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Light Properties"
    bl_idname = "OBJECT_PT_light_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.NMSNode_props.node_types == 'Light':
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

class NMSCollisionPropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Collision Properties"
    bl_idname = "OBJECT_PT_collision_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        if context.object.name.startswith("NMS") and context.object.NMSNode_props.node_types == 'Collision':
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSCollision_props, "collision_types", expand=True)

class NMSScenePropertyPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NMS Scene Properties"
    bl_idname = "OBJECT_PT_scene_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        # this should only show for an object that is called NMS_SCENE
        if context.object.name.startswith("NMS_SCENE"):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()
        row.prop(obj.NMSScene_props, "batch_mode")
        row = layout.row()
        row.prop(obj.NMSScene_props, "group_name", expand = True)
        row = layout.row()
        row.prop(obj.NMSScene_props, "dont_compile")

class NMSPanels():
    @staticmethod
    def register():
        # register the properties
        bpy.utils.register_class(NMSNodeProperties)
        bpy.utils.register_class(NMSSceneProperties)
        bpy.utils.register_class(NMSMeshProperties)
        bpy.utils.register_class(NMSReferenceProperties)
        bpy.utils.register_class(NMSLocatorProperties)
        bpy.utils.register_class(NMSLightProperties)
        bpy.utils.register_class(NMSEntityProperties)
        bpy.utils.register_class(NMSAnimationProperties)
        bpy.utils.register_class(NMSCollisionProperties)
        # link the properties with the objects' internal variables
        bpy.types.Object.NMSNode_props = bpy.props.PointerProperty(type=NMSNodeProperties)
        bpy.types.Object.NMSScene_props = bpy.props.PointerProperty(type=NMSSceneProperties)
        bpy.types.Object.NMSMesh_props = bpy.props.PointerProperty(type=NMSMeshProperties)
        bpy.types.Object.NMSReference_props = bpy.props.PointerProperty(type=NMSReferenceProperties)
        bpy.types.Object.NMSLocator_props = bpy.props.PointerProperty(type=NMSLocatorProperties)
        bpy.types.Object.NMSLight_props = bpy.props.PointerProperty(type=NMSLightProperties)
        bpy.types.Object.NMSEntity_props = bpy.props.PointerProperty(type=NMSEntityProperties)
        bpy.types.Object.NMSAnimation_props = bpy.props.PointerProperty(type=NMSAnimationProperties)
        bpy.types.Object.NMSCollision_props = bpy.props.PointerProperty(type=NMSCollisionProperties)
        # register the panels
        bpy.utils.register_class(NMSScenePropertyPanel)
        bpy.utils.register_class(NMSNodePropertyPanel)
        bpy.utils.register_class(NMSMeshPropertyPanel)
        bpy.utils.register_class(NMSReferencePropertyPanel)
        bpy.utils.register_class(NMSLocatorPropertyPanel)
        bpy.utils.register_class(NMSLightPropertyPanel)
        bpy.utils.register_class(NMSEntityPropertyPanel)
        bpy.utils.register_class(NMSAnimationPropertyPanel)
        bpy.utils.register_class(NMSCollisionPropertyPanel)

    @staticmethod
    def unregister():
        # unregister the property classes
        bpy.utils.unregister_class(NMSNodeProperties)
        bpy.utils.unregister_class(NMSSceneProperties)
        bpy.utils.unregister_class(NMSMeshProperties)
        bpy.utils.unregister_class(NMSReferenceProperties)
        bpy.utils.unregister_class(NMSLocatorProperties)
        bpy.utils.unregister_class(NMSLightProperties)
        bpy.utils.unregister_class(NMSEntityProperties)
        bpy.utils.unregister_class(NMSAnimationProperties)
        bpy.utils.unregister_class(NMSCollisionProperties)
        # delete the properties from the objects
        del bpy.types.Object.NMSNode_props
        del bpy.types.Object.NMSScene_props
        del bpy.types.Object.NMSMesh_props
        del bpy.types.Object.NMSReference_props
        del bpy.types.Object.NMSLocator_props
        del bpy.types.Object.NMSLight_props
        del bpy.types.Object.NMSEntity_props
        del bpy.types.Object.NMSAnimation_props
        del bpy.types.Object.NMSCollision_props
        # unregister the panels
        bpy.utils.unregister_class(NMSScenePropertyPanel)
        bpy.utils.unregister_class(NMSNodePropertyPanel)
        bpy.utils.unregister_class(NMSMeshPropertyPanel)
        bpy.utils.unregister_class(NMSReferencePropertyPanel)
        bpy.utils.unregister_class(NMSLocatorPropertyPanel)
        bpy.utils.unregister_class(NMSLightPropertyPanel)
        bpy.utils.unregister_class(NMSEntityPropertyPanel)
        bpy.utils.unregister_class(NMSAnimationPropertyPanel)
        bpy.utils.unregister_class(NMSCollisionPropertyPanel)
