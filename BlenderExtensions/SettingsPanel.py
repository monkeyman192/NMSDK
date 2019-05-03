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


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        bpy.utils.register_class(UpdateSettingsPanel)

    @staticmethod
    def unregister():
        # Unregister panels
        bpy.utils.unregister_class(UpdateSettingsPanel)
