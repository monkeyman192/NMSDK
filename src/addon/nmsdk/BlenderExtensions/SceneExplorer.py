import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty, IntProperty,
                       FloatProperty)
from bpy.types import NodeTree, Node, NodeSocket, UIList, Panel
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem


def retBool(x):
    return bool(x)


# custom button in the node editor to change the mode to the custom NMS mode
# class SceneExplorer(UIList):
#     '''NMS Scene explorer'''
#     bl_idname = 'NMSSceneExplorer'
#     bl_label = 'NMS Scene Explorer'
#     bl_icon = 'DESKTOP'


class SceneExplorerPanel(Panel):
    bl_idname = 'SceneExplorerPanel'
    bl_label = 'NMS Scene Explorer'
    bl_icon = 'DESKTOP'
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout

        obj = context.object

        layout.template_list("UI_UL_list", "", obj, "material_slots", obj, "active_material_index")
        # layout.template_list("MATERIAL_UL_matslots_example", "", obj, "material_slots", obj, "active_material_index")



class NMSSceneExplorer():
    def register(self):
        # register base classes
        bpy.utils.register_class(SceneExplorerPanel)

    def unregister(self):
        bpy.utils.unregister_class(SceneExplorerPanel)
