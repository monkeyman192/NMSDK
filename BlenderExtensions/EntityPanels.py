# All the custom panels and properties for all the different object types

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty

""" Various properties for each of the different panel types """

def get_structname(name):
    # damnit blender why do I need to do this!?!
    return name

class NMSEntityProperties(bpy.types.PropertyGroup):
    name_or_path = StringProperty(name = "Name or path",
                          description = "Name or path of the entity file to be produced.\nThis name can be shared by other objects in the scene\nAny name here with forward or backslashes will be assume to be a path")
    is_anim_controller = BoolProperty(name = "Is animation controller?",
                                      description = "When ticked, this entity contains all the required animation information. Only tick this for one entity per scene.",
                                      default = False)
    has_action_triggers = BoolProperty(name = "Has ActionTriggers?",
                                       description = "Whether or not this entity file will be give the data for the action triggers.",
                                       default = False)

class EntityItem(bpy.types.PropertyGroup):
    # very simple property group to contain the names
    name = bpy.props.StringProperty(name = "Struct Name")

class NMS_GcObjectPlacementComponentData_Properties(bpy.types.PropertyGroup):
    """ Properties for GcObjectPlacementComponentData """

    #structname = StringProperty(get = lambda: get_structname('GcObjectPlacementComponentData'))
    
    GroupNodeName = StringProperty(name = "GroupNodeName",
                                   default = "_Clump")
    ActivationType = EnumProperty(name = "ActivationType",
                                  items = [("Locator", "Locator", "Objects are placed at the locators"),
                                           ("GroupNode", "GroupNode", "I don't know...")])
    FractionOfNodesActive = FloatProperty(name = "FractionOfNodesActive",
                                          description = "Percentage of nodes that should be active",
                                          min = 0,
                                          max = 1)
    MaxNodesActivated = IntProperty(name = "MaxNodesActivated",
                                    default = 0)
    MaxGroupsActivated = IntProperty(name = "MaxGroupsActivated",
                                    default = 0)
    UseRaycast = BoolProperty(name = "UseRaycast",
                              default = False)

class NMS_GcScannerIconTypes_Properties(bpy.types.PropertyGroup):
    """ Properties for GcScannerIconTypes """

    #_structname = 'GcScannerIconTypes'
    structname = StringProperty()
    
    ScanIconType = EnumProperty(name = "ScanIconType",
                                items = [('None', 'None', 'None'),
                                         ('Health', 'Health', 'Health'),
                                         ('Shield', 'Shield', 'Shield'),
                                         ('Hazard', 'Hazard', 'Hazard'),
                                         ('Tech', 'Tech', 'Tech'),
                                         ('Heridium', 'Heridium', 'Heridium'),
                                         ('Platinum', 'Platinum', 'Platinum'),
                                         ('Chrysonite', 'Chrysonite', 'Chrysonite'),
                                         ('Signal', 'Signal', 'Signal'),
                                         ('Fuel', 'Fuel', 'Fuel'),
                                         ('Carbon', 'Carbon', 'Carbon'),
                                         ('Plutonium', 'Plutonium', 'Plutonium'),
                                         ('Thamium', 'Thamium', 'Thamium'),
                                         ('Mineral', 'Mineral', 'Mineral'),
                                         ('Iron', 'Iron', 'Iron'),
                                         ('Zinc', 'Zinc', 'Zinc'),
                                         ('Titanium', 'Titanium', 'Titanium'),
                                         ('Multi', 'Multi', 'Multi'),
                                         ('Artifact', 'Artifact', 'Artifact'),
                                         ('TechRecipe', 'TechRecipe', 'TechRecipe'),
                                         ('RareProp', 'RareProp', 'RareProp'),
                                         ('Trade', 'Trade', 'Trade'),
                                         ('Exotic', 'Exotic', 'Exotic')])

class NMS_GcScannableComponentData_Properties(bpy.types.PropertyGroup):
    """ Properties for GcScannableComponentData """
    
    #structname = StringProperty(get = lambda: get_structname('GcScannableComponentData'))
    
    ScanRange = FloatProperty(name = "ScanRange",
                              description = "Distance away the object can be picked up by a scanner")
    ScanName = StringProperty(name = "ScanName")
    ScanTime = FloatProperty(name = "ScanTime")
    IconType = bpy.props.PointerProperty(name = 'GcScannerIconTypes', type=NMS_GcScannerIconTypes_Properties)
    PermanentIcon = BoolProperty(name = "PermanentIcon")
    PermanentIconRadius = FloatProperty(name = "PermanentIconRadius")

# this function is essentially a wrapper for the boxes so they have a top section with name and a button to remove the box
# I wanted this to be able to be implemented as a decorator but I am bad at python :'(
def entityPanelTop(box, name):
    row = box.row()
    row.label(text = name)     # name is an EntityItem object
    s = row.split()
    s.alignment = 'RIGHT'
    s.operator('wm.remove_entity_struct', text = '', icon = 'PANEL_CLOSE', emboss = False).remove_name = name
    newbox = box.box()
    return newbox    

# this is the main class that contains all the information... It's going to be BIG with all the structs in it...
class DATA_PT_entities(bpy.types.Panel):
    bl_idname = "OBJECT_MT_entity_menu"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "NMS Entity Constructor"

    @classmethod
    def poll(cls, context):
        if context.object.NMSMesh_props.has_entity or context.object.NMSLocator_props.has_entity:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        obj = context.object

        row = layout.row()
        row.prop(obj.NMSEntity_props, "name_or_path")
        row = layout.row()
        row.prop(obj.NMSEntity_props, "is_anim_controller")
        row = layout.row()
        row.prop(obj.NMSEntity_props, "has_action_triggers")

        layout.operator_menu_enum("wm.add_entity_struct", "structs", text = "Select an entity struct to add")

        for struct in obj.EntityStructs:
            l = layout.box()
            box = entityPanelTop(l, struct.name)
            # now call the actual layout on this modified box
            getattr(self, struct.name)(box, obj)

    def GcObjectPlacementComponentData(self, layout, obj):
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "GroupNodeName")
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "ActivationType")
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "FractionOfNodesActive")
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "MaxNodesActivated")
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "MaxGroupsActivated")
        row = layout.row()
        row.prop(obj.NMS_GcObjectPlacementComponentData_props, "UseRaycast")

    def GcScannableComponentData(self, layout, obj):
        row = layout.row()
        row.prop(obj.NMS_GcScannableComponentData_props, "ScanRange")
        row = layout.row()
        row.prop(obj.NMS_GcScannableComponentData_props, "ScanName")
        row = layout.row()
        row.prop(obj.NMS_GcScannableComponentData_props, "ScanTime")
        # sub box for the IconType
        box = layout.box()
        box.label(text = "IconType")
        row = box.row()
        row.prop(obj.NMS_GcScannableComponentData_props.IconType, "ScanIconType")
        #end IconType box
        row = layout.row()
        row.prop(obj.NMS_GcScannableComponentData_props, "PermanentIcon")
        row = layout.row()
        row.prop(obj.NMS_GcScannableComponentData_props, "PermanentIconRadius")
        

# this will add the selected struct to the selectable list
class AddEntityStruct(bpy.types.Operator):
    bl_idname = 'wm.add_entity_struct'
    bl_label = "Add Entity Struct"

    structs = EnumProperty(items = [("GcObjectPlacementComponentData", "GcObjectPlacementComponentData", "Relates to placements of objects in the SelectableObjectsTable in Metadata"),
                                    ("GcScannableComponentData", "GcScannableComponentData", "This allows the entity to be scannable")])

    def execute(self, context):
        obj = context.object
        new_name = obj.EntityStructs.add()
        new_name.name = self.structs
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

# this will allow the cross to remove the box from the entity panel
class RemoveEntityStruct(bpy.types.Operator):
    bl_idname = 'wm.remove_entity_struct'
    bl_label = "Remove Entity Struct"

    remove_name = StringProperty(name = 'remove_name')

    def execute(self, context):
        obj = context.object
        # gotta remove it in a really annoying way since the collection property only allows you to remove by index, not anything else...
        i = 0
        for struct_name in obj.EntityStructs:
            if struct_name.name == self.remove_name:
                obj.EntityStructs.remove(i)
            else:
                i += 1
        #obj.EntityStructs.discard(self.remove_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)
        

class NMSEntities():
    @staticmethod
    def register():
        # give the objects a custom empty set
        # this will be checked by the addon_script to find out what data the entity is being given..
        #print('hi')
        #bpy.types.Object.EntityStructs = set()
        # do entity items first...
        bpy.utils.register_class(EntityItem)
        bpy.types.Object.EntityStructs = bpy.props.CollectionProperty(type = EntityItem)

        # register the properties
        bpy.utils.register_class(NMS_GcObjectPlacementComponentData_Properties)
        bpy.utils.register_class(NMS_GcScannerIconTypes_Properties)
        bpy.utils.register_class(NMS_GcScannableComponentData_Properties)
        bpy.utils.register_class(AddEntityStruct)
        bpy.utils.register_class(RemoveEntityStruct)
        bpy.utils.register_class(NMSEntityProperties)

        # link the properties with the objects' internal variables
        
        bpy.types.Object.NMS_GcObjectPlacementComponentData_props = bpy.props.PointerProperty(type=NMS_GcObjectPlacementComponentData_Properties)
        bpy.types.Object.NMS_GcScannableComponentData_props = bpy.props.PointerProperty(type=NMS_GcScannableComponentData_Properties)
        bpy.types.Object.NMSEntity_props = bpy.props.PointerProperty(type=NMSEntityProperties)

        # register the panels
        bpy.utils.register_class(DATA_PT_entities)

    @staticmethod
    def unregister():
        #del bpy.types.Object.EntityStructs
        
        # unregister the property classes
        bpy.utils.unregister_class(EntityItem)
        bpy.utils.unregister_class(NMS_GcObjectPlacementComponentData_Properties)
        bpy.utils.register_class(NMS_GcScannerIconTypes_Properties)
        bpy.utils.unregister_class(NMS_GcScannableComponentData_Properties)
        bpy.utils.unregister_class(AddEntityStruct)
        bpy.utils.unregister_class(RemoveEntityStruct)
        bpy.utils.unregister_class(NMSEntityProperties)

        #delete the properties from the objects
        del bpy.types.Object.EntityStructs
        del bpy.types.Object.NMS_GcObjectPlacementComponentData_props
        del bpy.types.Object.NMSEntity_props

        # unregister the panels
        bpy.utils.unregister_class(DATA_PT_entities)
