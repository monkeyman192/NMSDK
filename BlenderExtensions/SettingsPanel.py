import bpy


class UpdateSettingsPanel(bpy.types.Panel):
    bl_idname = 'UpdateSettingsPanel'
    bl_label = 'Update Tools'
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
    bl_label = 'Scene Tools'
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


class DefaultsPanel(bpy.types.Panel):
    bl_idname = 'DefaultsPanel'
    bl_label = 'Default Values'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        default_settings = context.scene.nmsdk_default_settings
        layout = self.layout
        layout.prop(default_settings, 'export_directory')
        layout.prop(default_settings, 'group_name')
        layout.operator("nmsdk._save_default_settings", icon='SAVE_PREFS',
                        text='Save settings')


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        bpy.utils.register_class(UpdateSettingsPanel)
        bpy.utils.register_class(ToolsPanel)
        bpy.utils.register_class(DefaultsPanel)

    @staticmethod
    def unregister():
        # Unregister panels
        bpy.utils.unregister_class(UpdateSettingsPanel)
        bpy.utils.unregister_class(ToolsPanel)
        bpy.utils.unregister_class(DefaultsPanel)
