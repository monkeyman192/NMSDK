# All the custom panels and properties for all the different object types

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, PointerProperty, CollectionProperty
from functools import reduce

""" Various properties for each of the different panel types """

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

def ListProperty(type_):
    # this will return a CollectionProperty with type type_
    return bpy.props.CollectionProperty(type = type_)

""" Struct specific properties """

class NMS_GcObjectPlacementComponentData_Properties(bpy.types.PropertyGroup):
    """ Properties for GcObjectPlacementComponentData """
    
    GroupNodeName = StringProperty(name = "Group Node Name",
                                   default = "_Clump")
    ActivationType = EnumProperty(name = "Activation Type",
                                  items = [("Locator", "Locator", "Objects are placed at the locators"),
                                           ("GroupNode", "GroupNode", "I don't know...")])
    FractionOfNodesActive = FloatProperty(name = "Fraction Of Nodes Active",
                                          description = "Percentage of nodes that should be active",
                                          min = 0,
                                          max = 1)
    MaxNodesActivated = IntProperty(name = "Max Nodes Activated",
                                    default = 0)
    MaxGroupsActivated = IntProperty(name = "Max Groups Activated",
                                    default = 0)
    UseRaycast = BoolProperty(name = "Use Raycast",
                              default = False)

class NMS_GcScannerIconTypes_Properties(bpy.types.PropertyGroup):
    """ Properties for GcScannerIconTypes """

    list_index_ = IntProperty()         # this will be an internal variable used to track it's index in a list (just in case this object ends up in a list...)
    
    ScanIconType = EnumProperty(name = "Scan Icon Type",
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
    
    ScanRange = FloatProperty(name = "Scan Range",
                              description = "Distance away the object can be picked up by a scanner")
    ScanName = StringProperty(name = "Scan Name")
    ScanTime = FloatProperty(name = "Scan Time")
    IconType = PointerProperty(type=NMS_GcScannerIconTypes_Properties)
    PermanentIcon = BoolProperty(name = "Permanent Icon")
    PermanentIconRadius = FloatProperty(name = "Permanent Icon Radius")

class NMS_GcProjectileImpactType_Properties(bpy.types.PropertyGroup):
    """ Properties for GcProjectileImpactType """

    list_index_ = IntProperty()         # this will be an internal variable used to track it's index in a list (just in case this object ends up in a list...)

    Impact = EnumProperty(name = "Impact",
                          items = [("Default", "Default", "Default"),
                                  ("Terrain", "Terrain", "Terrain"),
                                  ("Substance", "Substance", "Substance"),
                                  ("Rock", "Rock", "Rock"),
                                  ("Asteroid", "Asteroid", "Asteroid"),
                                  ("Shield", "Shield", "Shield"),
                                  ("Creature", "Creature", "Creature"),
                                  ("Robot", "Robot", "Robot"),
                                  ("Freighter", "Freighter", "Freighter"),
                                  ("Cargo", "Cargo", "Cargo"),
                                  ("Ship", "Ship", "Ship"),
                                  ("Plant", "Plant", "Plant")])

class NMS_GcShootableComponentData_Properties(bpy.types.PropertyGroup):
    """ Properties for GcShootableComponentData """

    Health = IntProperty(name = "Health", default = 200, min = 0)
    AutoAimTarget = BoolProperty(name = "Auto Aim Target", default = False)
    PlayerOnly = BoolProperty(name = "Player Only", default = False)
    ImpactShake = BoolProperty(name = "Impact Shake", default = True)
    ImpactShakeEffect = StringProperty(name = "Impact Shake Effect", maxlen = 0x10)
    ForceImpactType = PointerProperty(type = NMS_GcProjectileImpactType_Properties)
    IncreaseWanted = IntProperty(name = "Increase Wanted", default = 0, min = 0, max = 5)
    IncreaseWantedThresholdTime = FloatProperty(name = "Increase Wanted Threshold Time", default = 0.5)
    UseMiningDamage = BoolProperty(name = "Use Mining Damage", default = False)
    MinDamage = IntProperty(name = "Min Damage", default = 0)
    StaticUntilShot = BoolProperty(name = "Static Until Shot", default = False)
    RequiredTech = StringProperty(name = "Required Tech", maxlen = 0x20)

    TestList = CollectionProperty(type = NMS_GcProjectileImpactType_Properties)

def rgetattr(obj, attr):
    def _getattr(obj, name):
        return getattr(obj, name)
    return reduce(_getattr, [obj]+attr.split('.'))

def ListBox(cls, obj, layout, list_struct, prop_name, name):
    # a container function to be called to create a list box
    # class is required so that the panel layout can pass itself into this so the correct attributes can be found
    listbox = ListEntryAdder(layout.box(), list_struct, prop_name)
    j = 0
    for i in obj.NMS_GcShootableComponentData_props.TestList:
        print(i)
        box = ListEntityTop(listbox, list_struct, prop_name, name, j)
        # add the object and give it the appropriate index
        getattr(cls, name)(box, obj, index = j)
        j += 1

# this function is essentially a wrapper for the boxes so they have a top section with name and a button to remove the box
# I wanted this to be able to be implemented as a decorator but I am bad at python :'(
def EntityPanelTop(layout, name):
    row = layout.row()
    row.label(text = name)
    s = row.split()
    s.alignment = 'RIGHT'
    s.operator('wm.remove_entity_struct', text = '', icon = 'PANEL_CLOSE', emboss = False).remove_name = name
    newbox = layout.box()
    return newbox

def ListEntityTop(layout, list_struct, prop_name, name, index):
    box = layout.box()
    row = box.row()
    row.label(text = name)
    s = row.split()
    s.alignment = 'RIGHT'
    op = s.operator('wm.remove_list_struct', text = '', icon = 'PANEL_CLOSE', emboss = False)
    op.remove_index = index
    op.prop_name = prop_name
    op.list_struct = list_struct
    return box

# a function to return a ui box with the name and a plus button to add extra entries
def ListEntryAdder(box, list_struct, prop_name):
    row = box.row()
    row.label(text = prop_name)
    s = row.split()
    s.alignment = 'RIGHT'
    # create a new operator to add the sub structs
    op = s.operator('wm.add_list_struct', text = '', icon = 'PLUS', emboss = False)
    op.prop_name = prop_name
    op.list_struct = list_struct
    return box

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
            box = EntityPanelTop(l, struct.name)
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

    def GcShootableComponentData(self, layout, obj):
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "Health")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "AutoAimTarget")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "PlayerOnly")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "ImpactShake")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "ImpactShakeEffect")
        # sub box for the ForceImpactType
        box = layout.box()
        box.label(text = "ForceImpactType")
        row = box.row()
        row.prop(obj.NMS_GcShootableComponentData_props.ForceImpactType, "Impact")
        #end IconType box
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "IncreaseWanted")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "IncreaseWantedThresholdTime")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "UseMiningDamage")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "MinDamage")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "StaticUntilShot")
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props, "RequiredTech")

        ListBox(self, obj, layout, "NMS_GcShootableComponentData_props", "TestList", "GcProjectileImpactType")      # this is a bit long... would be nicer if it could be more concise... :/           

    def GcProjectileImpactType(self, layout, obj, index = 0):
        row = layout.row()
        row.prop(obj.NMS_GcShootableComponentData_props.TestList[index], "Impact")

class AddListStruct(bpy.types.Operator):
    bl_idname = 'wm.add_list_struct'
    bl_label = "Add List Struct"

    list_struct = StringProperty()      # name of the struct that is to be added
    prop_name = StringProperty()        # name of the property containing the CollectionProperty
    curr_index = IntProperty()
    #sub_name = StringProperty()

    def execute(self, context):
        obj = context.object
        list_obj = rgetattr(obj, "{0}.{1}".format(self.list_struct, self.prop_name)).add()
        #list_obj.list_index_ = self.curr_index
        #self.curr_index += 1
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class RemoveListStruct(bpy.types.Operator):
    bl_idname = 'wm.remove_list_struct'
    bl_label = "Remove Entity Struct"

    remove_index = IntProperty()
    list_struct = StringProperty()
    prop_name = StringProperty()

    def execute(self, context):
        obj = context.object
        list_obj = rgetattr(obj, "{0}.{1}".format(self.list_struct, self.prop_name)).remove(self.remove_index)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

# this will add the selected struct to the selectable list
class AddEntityStruct(bpy.types.Operator):
    bl_idname = 'wm.add_entity_struct'
    bl_label = "Add Entity Struct"

    structs = EnumProperty(items = [("GcObjectPlacementComponentData", "GcObjectPlacementComponentData", "Relates to placements of objects in the SelectableObjectsTable in Metadata"),
                                    ("GcScannableComponentData", "GcScannableComponentData", "This allows the entity to be scannable"),
                                    ("GcShootableComponentData", "GcShootableComponentData", "Describes how the entity reacts to being shot")])

    def execute(self, context):
        # add the struct name to the objects' list of structs so that it can be drawn in the UI
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
        bpy.types.Object.EntityStructs = CollectionProperty(type = EntityItem)

        # register the properties
        bpy.utils.register_class(NMS_GcObjectPlacementComponentData_Properties)
        bpy.utils.register_class(NMS_GcScannerIconTypes_Properties)
        bpy.utils.register_class(NMS_GcScannableComponentData_Properties)
        bpy.utils.register_class(NMS_GcProjectileImpactType_Properties)
        bpy.utils.register_class(NMS_GcShootableComponentData_Properties)
        bpy.utils.register_class(AddListStruct)
        bpy.utils.register_class(RemoveListStruct)
        bpy.utils.register_class(AddEntityStruct)
        bpy.utils.register_class(RemoveEntityStruct)
        bpy.utils.register_class(NMSEntityProperties)

        # link the properties with the objects' internal variables
        
        bpy.types.Object.NMS_GcObjectPlacementComponentData_props = PointerProperty(type=NMS_GcObjectPlacementComponentData_Properties)
        bpy.types.Object.NMS_GcScannableComponentData_props = PointerProperty(type=NMS_GcScannableComponentData_Properties)
        bpy.types.Object.NMS_GcShootableComponentData_props = PointerProperty(type=NMS_GcShootableComponentData_Properties)
        bpy.types.Object.NMSEntity_props = PointerProperty(type=NMSEntityProperties)

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
        bpy.utils.unregister_class(NMS_GcProjectileImpactType_Properties)
        bpy.utils.unregister_class(NMS_GcShootableComponentData_Properties)
        bpy.utils.unregister_class(AddListStruct)
        bpy.utils.unregister_class(RemoveListStruct)
        bpy.utils.unregister_class(AddEntityStruct)
        bpy.utils.unregister_class(RemoveEntityStruct)
        bpy.utils.unregister_class(NMSEntityProperties)

        #delete the properties from the objects
        del bpy.types.Object.EntityStructs
        del bpy.types.Object.NMS_GcObjectPlacementComponentData_props
        del bpy.types.Object.NMS_GcShootableComponentData_props
        del bpy.types.Object.NMSEntity_props

        # unregister the panels
        bpy.utils.unregister_class(DATA_PT_entities)
