import bpy


class UpdateSettingsPanel(bpy.types.Panel):
    bl_idname = 'UpdateSettingsPanel'
    bl_label = 'NMSDK model Update tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("nmsdk._fix_old_format")


class ToolsPanel(bpy.types.Panel):
    bl_idname = 'ToolsPanel'
    bl_label = 'NMSDK model tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        nmsdk_settings = context.scene.nmsdk_settings
        coll_visibility = nmsdk_settings.show_collisions
        layout = self.layout
        if coll_visibility:
            label = "Collisions: Visible"
            icon = "VISIBLE_IPO_ON"
        else:
            label = "Collisions: Not Visible"
            icon = "VISIBLE_IPO_OFF"
        layout.operator("nmsdk._toggle_collision_visibility",
                        icon=icon, text=label)


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        bpy.utils.register_class(UpdateSettingsPanel)
        bpy.utils.register_class(ToolsPanel)

    @staticmethod
    def unregister():
        # Unregister panels
        bpy.utils.unregister_class(UpdateSettingsPanel)
        bpy.utils.unregister_class(ToolsPanel)
