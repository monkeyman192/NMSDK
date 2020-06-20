# Add some right click options

import bpy
from bpy.types import Menu, Operator


class WM_OT_button_context_test(Operator):
    """Add this object to a new or existing NMSDK scene"""
    bl_idname = "wm.add_to_nmsdk_scene"
    bl_label = "Add object to NMSDK scene"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_obj = getattr(context, "selected_objects", None)
        print(selected_obj)

        return {'FINISHED'}


def menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator('nmsdk.create_scene')


class ContextMenus():
    @staticmethod
    def register():
        bpy.utils.register_class(WM_OT_button_context_test)
        bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)

    @staticmethod
    def unregister():
        bpy.utils.unregister_class(WM_OT_button_context_test)
        bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
