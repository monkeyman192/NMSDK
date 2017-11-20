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

class NMS_TkTextureResource_Properties(bpy.types.PropertyGroup):
    """ Properties for TkTextureResource """
	
    Filename = StringProperty(name = "Filename", maxlen = 0x80)
	
class NMS_GcStatTrackType_Properties(bpy.types.PropertyGroup):
    """ Properties for GcStatTrackType """

    StatTrackType = EnumProperty(name = "StatTrackType",
                          items = [("Set", "Set", "Set"),
                                  ("Add", "Add", "Add"),
                                  ("Max", "Max", "Max"),
                                  ("Min", "Min", "Min")])


class NMS_GcRarity_Properties(bpy.types.PropertyGroup):
    """ Properties for GcRarity """

    Rarity = EnumProperty(name = "Rarity",
                          items = [("Common", "Common", "Common"),
                                  ("Uncommon", "Uncommon", "Uncommon"),
                                  ("Rare", "Rare", "Rare"),
                                  ("Extraordinary", "Extraordinary", "Extraordinary"),
                                  ("None", "None", "None")])
	
class NMS_GcRealitySubstanceCategory_Properties(bpy.types.PropertyGroup):
    """ Properties for GcRealitySubstanceCategory """

    SubstanceCategory = EnumProperty(name = "SubstanceCategory",
                          items = [("Commodity", "Commodity", "Commodity"),
                                  ("Technology", "Technology", "Technology"),
                                  ("Fuel", "Fuel", "Fuel"),
                                  ("Tradeable", "Tradeable", "Tradeable"),
                                  ("Special", "Special", "Special"),
                                  ("BuildingPart", "BuildingPart", "BuildingPart")])
								  
class NMS_GcSubstanceAmount_Properties(bpy.types.PropertyGroup):
    """ Properties for GcSubstanceAmount """
	
    AmountMin = IntProperty(name = "AmountMin", default = 0)
    AmountMax = IntProperty(name = "AmountMax", default = 0)
    Specific = StringProperty(name = "Specific", maxlen = 0x10)
    SubstanceCategory = PointerProperty(type = NMS_GcRealitySubstanceCategory_Properties)
    Rarity = PointerProperty(type = NMS_GcRarity_Properties)
	
class NMS_GcDestructableComponentData_Properties(bpy.types.PropertyGroup):
    """ Properties for GcDestructableComponentData """

    Explosion = StringProperty(name = "Explosion", maxlen = 0x10)
    ExplosionScale = FloatProperty(name = "ExplosionScale")
    ExplosionScaleToBounds = BoolProperty(name = "ExplosionScaleToBounds", default = False)
    VehicleDestroyEffect = StringProperty(name = "VehicleDestroyEffect", maxlen = 0x10)
    TriggerAction = StringProperty(name = "TriggerAction", maxlen = 0x10)
    IncreaseWanted = IntProperty(name = "IncreaseWanted", default = 0, min = 0, max = 5)
    LootReward = StringProperty(name = "LootReward", maxlen = 0x10)
    LootRewardAmountMin = IntProperty(name = "LootRewardAmountMin", default = 0)
    LootRewardAmountMax = IntProperty(name = "LootRewardAmountMax", default = 0)
    GivesSubstances = CollectionProperty(type = NMS_GcSubstanceAmount_Properties)
    StatsToTrack = PointerProperty(type = NMS_GcStatTrackType_Properties)
    GivesReward = StringProperty(name = "GivesReward", maxlen = 0x10)
    HardModeSubstanceMultiplier = FloatProperty(name = "HardModeSubstanceMultiplier")
    RemoveModel = BoolProperty(name = "RemoveModel", default = True)
    DestroyedModel = PointerProperty(type = NMS_TkTextureResource_Properties)
    DestroyedModelUsesScale = BoolProperty(name = "DestroyedModelUsesScale", default = False)
    DestroyForce = FloatProperty(name = "DestroyForce")
    DestroyForceRadius = FloatProperty(name = "DestroyForceRadius")
    DestroyEffect = StringProperty(name = "DestroyEffect", maxlen = 0x10)
    DestroyEffectPoint = StringProperty(name = "DestroyEffectPoint", maxlen = 0x10)
    DestroyEffectTime = FloatProperty(name = "DestroyEffectTime")
    ShowInteract = BoolProperty(name = "ShowInteract", default = False)
    ShowInteractRange = FloatProperty(name = "ShowInteractRange")
    GrenadeSingleHit = BoolProperty(name = "GrenadeSingleHit", default = True)

def rgetattr(obj, attr):
    def _getattr(obj, name):
        return getattr(obj, name)
    return reduce(_getattr, [obj]+attr.split('.'))

# this function is essentially a wrapper for the boxes so they have a top section with name and a button to remove the box
# I wanted this to be able to be implemented as a decorator but I am bad at python :'(
def EntityPanelTop(layout, name):
    row = layout.row()
    row.label(text = name)
    s = row.split()
    s.alignment = 'RIGHT'
    s.operator('wm.move_entity_struct_up', text = '', icon = 'TRIA_UP', emboss = False).struct_name = name
    s.operator('wm.move_entity_struct_down', text = '', icon = 'TRIA_DOWN', emboss = False).struct_name = name
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

class RowGen():
    """ simple wrapper class to make the individual functions in DATA_PT_entities half the size... """
    def __init__(self, ctx, layout):
        """
        ctx is the object property that will be read from
        layout is the blender layout to write the rows to
        """
        self.ctx = ctx
        self.layout = layout

    def row(self, prop):
        """ Just create a new row and add a new property with the specified name """
        r = self.layout.row()
        r.prop(self.ctx, prop)

    def mrow(self, props = []):
        # not sure if I'll use this... but might be nice
        for prop in props:
            self.row(prop)

    def box(self, prop):
        new_ctx = getattr(self.ctx, prop)
        new_layout = self.layout.box()
        new_layout.label(text = prop)
        return RowGen(new_ctx, new_layout)

    def listbox(self, cls, obj, list_struct, prop_name, name):
        # a container function to be called to create a list box
        # class is required so that the panel layout can pass itself into this so the correct attributes can be found
        listbox = ListEntryAdder(self.layout.box(), list_struct, prop_name)
        j = 0
        for i in getattr(self.ctx, prop_name):
            box = ListEntityTop(listbox, list_struct, prop_name, name, j)
            # add the object and give it the appropriate index
            getattr(cls, name)(box, obj, index = j)
            j += 1

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
        r = RowGen(obj.NMS_GcObjectPlacementComponentData_props, layout)
        r.row("GroupNodeName")
        r.row("ActivationType")
        r.row("FractionOfNodesActive")
        r.row("MaxNodesActivated")
        r.row("MaxGroupsActivated")
        r.row("UseRaycast")

    def GcScannableComponentData(self, layout, obj):
        r = RowGen(obj.NMS_GcScannableComponentData_props, layout)
        r.row("ScanRange")
        r.row("ScanName")
        r.row("ScanTime")
        b = r.box("IconType")
        b.row("ScanIconType")
        r.row("PermanentIcon")
        r.row("PermanentIconRadius")

    def GcShootableComponentData(self, layout, obj):
        r = RowGen(obj.NMS_GcShootableComponentData_props, layout)
        r.row("Health")
        r.row("AutoAimTarget")
        r.row("PlayerOnly")
        r.row("ImpactShake")
        r.row("ImpactShakeEffect")
        b = r.box("ForceImpactType")
        b.row("Impact")
        r.row("IncreaseWanted")
        r.row("IncreaseWantedThresholdTime")
        r.row("UseMiningDamage")
        r.row("MinDamage")
        r.row("StaticUntilShot")
        r.row("RequiredTech")

        #ListBox(self, obj, layout, "NMS_GcShootableComponentData_props", "TestList", "GcProjectileImpactType")      # this is a bit long... would be nicer if it could be more concise... :/

    def GcDestructableComponentData(self, layout, obj):
        r = RowGen(obj.NMS_GcDestructableComponentData_props, layout)
        r.row("Explosion")
        r.row("ExplosionScale")
        r.row("ExplosionScaleToBounds")
        r.row("VehicleDestroyEffect")
        r.row("TriggerAction")
        r.row("IncreaseWanted")
        r.row("LootReward")
        r.row("LootRewardAmountMin")
        r.row("LootRewardAmountMax")
        r.listbox(self, obj, "NMS_GcDestructableComponentData_props", "GivesSubstances", "GcSubstanceAmount")
        b = r.box("StatsToTrack")
        b.row("StatTrackType")
        r.row("GivesReward")
        r.row("HardModeSubstanceMultiplier")
        r.row("RemoveModel")
        b = r.box("DestroyedModel")
        b.row("Filename")
        r.row("DestroyedModelUsesScale")
        r.row("DestroyForce")
        r.row("DestroyForceRadius")
        r.row("DestroyEffect")
        r.row("DestroyEffectPoint")
        r.row("DestroyEffectTime")
        r.row("ShowInteract")
        r.row("ShowInteractRange")
        r.row("GrenadeSingleHit")

    def GcSubstanceAmount(self, layout, obj, index = 0):
        r = RowGen(obj.NMS_GcDestructableComponentData_props.GivesSubstances[index], layout)
        r.row("AmountMin")
        r.row("AmountMax")
        r.row("Specific")
        b = r.box("SubstanceCategory")
        b.row("SubstanceCategory")
        b = r.box("Rarity")
        b.row("Rarity")

""" Operators required for button functionality in the UI elements """

class AddListStruct(bpy.types.Operator):
    bl_idname = 'wm.add_list_struct'
    bl_label = "Add List Struct"

    list_struct = StringProperty()      # name of the struct that is to be added
    prop_name = StringProperty()        # name of the property containing the CollectionProperty
    curr_index = IntProperty()          # not needed??

    def execute(self, context):
        obj = context.object
        list_obj = rgetattr(obj, "{0}.{1}".format(self.list_struct, self.prop_name)).add()
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
                                    ("GcShootableComponentData", "GcShootableComponentData", "Describes how the entity reacts to being shot"),
                                    ("GcDestructableComponentData", "GcDestructableComponentData", "Decribes what happens when the object is destroyed")])

    def execute(self, context):
        # add the struct name to the objects' list of structs so that it can be drawn in the UI
        obj = context.object
        # only add the struct if it isn't already in the list
        if not self.entity_exists(obj, self.structs):
            new_name = obj.EntityStructs.add()
            new_name.name = self.structs
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

    @staticmethod
    def entity_exists(obj, name):
        #  returns True if the named struct is already in the obj's EntityStructs
        for i in obj.EntityStructs:
            if i.name == name:
                return True
        return False

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

class MoveEntityUp(bpy.types.Operator):
    bl_idname = 'wm.move_entity_struct_up'
    bl_label = "Move Entity Struct Up"

    struct_name = StringProperty(name = 'struct_name')

    def execute(self, context):
        obj = context.object
        i = self.get_index(obj)

        # make sure that the object isn't at the top of the list and move
        if i != 0:
            obj.EntityStructs.move(i, i-1)

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def get_index(self, obj):
        for i, struct in enumerate(obj.EntityStructs):
            if struct.name == self.struct_name:
                return i

class MoveEntityDown(bpy.types.Operator):
    bl_idname = 'wm.move_entity_struct_down'
    bl_label = "Move Entity Struct Down"

    struct_name = StringProperty(name = 'struct_name')

    def execute(self, context):
        obj = context.object
        i = self.get_index(obj)

        # make sure that the object isn't at the top of the list and move
        if i != len(obj.EntityStructs):
            obj.EntityStructs.move(i, i+1)

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def get_index(self, obj):
        for i, struct in enumerate(obj.EntityStructs):
            if struct.name == self.struct_name:
                return i

""" Class to contain all the registration information to be called from the nmsdk.py file """

class NMSEntities():
    @staticmethod
    def register():
        # do entity items first...
        bpy.utils.register_class(EntityItem)
        bpy.types.Object.EntityStructs = CollectionProperty(type = EntityItem)

        # register the properties
        bpy.utils.register_class(NMS_GcObjectPlacementComponentData_Properties)
        bpy.utils.register_class(NMS_GcScannerIconTypes_Properties)
        bpy.utils.register_class(NMS_GcScannableComponentData_Properties)
        bpy.utils.register_class(NMS_GcProjectileImpactType_Properties)
        bpy.utils.register_class(NMS_GcShootableComponentData_Properties)
        bpy.utils.register_class(NMS_TkTextureResource_Properties)
        bpy.utils.register_class(NMS_GcStatTrackType_Properties)
        bpy.utils.register_class(NMS_GcRarity_Properties)
        bpy.utils.register_class(NMS_GcRealitySubstanceCategory_Properties)
        bpy.utils.register_class(NMS_GcSubstanceAmount_Properties)
        bpy.utils.register_class(NMS_GcDestructableComponentData_Properties)
        bpy.utils.register_class(AddListStruct)
        bpy.utils.register_class(RemoveListStruct)
        bpy.utils.register_class(AddEntityStruct)
        bpy.utils.register_class(RemoveEntityStruct)
        bpy.utils.register_class(MoveEntityDown)
        bpy.utils.register_class(MoveEntityUp)
        bpy.utils.register_class(NMSEntityProperties)

        # link the properties with the objects' internal variables
        
        bpy.types.Object.NMS_GcObjectPlacementComponentData_props = PointerProperty(type=NMS_GcObjectPlacementComponentData_Properties)
        bpy.types.Object.NMS_GcScannableComponentData_props = PointerProperty(type=NMS_GcScannableComponentData_Properties)
        bpy.types.Object.NMS_GcShootableComponentData_props = PointerProperty(type=NMS_GcShootableComponentData_Properties)
        bpy.types.Object.NMS_GcDestructableComponentData_props = PointerProperty(type=NMS_GcDestructableComponentData_Properties)
        bpy.types.Object.NMSEntity_props = PointerProperty(type=NMSEntityProperties)

        # register the panel
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
        bpy.utils.unregister_class(NMS_TkTextureResource_Properties)
        bpy.utils.unregister_class(NMS_GcStatTrackType_Properties)
        bpy.utils.unregister_class(NMS_GcRarity_Properties)
        bpy.utils.unregister_class(NMS_GcRealitySubstanceCategory_Properties)
        bpy.utils.unregister_class(NMS_GcSubstanceAmount_Properties)
        bpy.utils.unregister_class(NMS_GcDestructableComponentData_Properties)
        bpy.utils.unregister_class(AddListStruct)
        bpy.utils.unregister_class(RemoveListStruct)
        bpy.utils.unregister_class(AddEntityStruct)
        bpy.utils.unregister_class(RemoveEntityStruct)
        bpy.utils.unregister_class(MoveEntityDown)
        bpy.utils.unregister_class(MoveEntityUp)
        bpy.utils.unregister_class(NMSEntityProperties)

        #delete the properties from the objects
        del bpy.types.Object.EntityStructs
        del bpy.types.Object.NMS_GcObjectPlacementComponentData_props
        del bpy.types.Object.NMS_GcShootableComponentData_props
        del bpy.types.Object.NMS_GcDestructableComponentData_props
        del bpy.types.Object.NMSEntity_props

        # unregister the panel
        bpy.utils.unregister_class(DATA_PT_entities)
