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


class AnimationsPanel(bpy.types.Panel):
    bl_idname = 'AnimationsPanel'
    bl_label = 'Animation controls'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        anim_data = context.scene.nmsdk_anim_data
        if anim_data.anims_loaded is False:
            if len(anim_data.loadable_anim_data) != 0:
                # In this case, have a menu to allow for the animations to be
                # loaded
                layout.operator_menu_enum('nmsdk._load_animation',
                                          'loadable_anim_name',
                                          text='Add an animation')
        anim_names = anim_data.loaded_anims
        if not isinstance(anim_names, list):
            anim_names = anim_data.loaded_anims.to_list()
        if anim_names == ['None']:
            layout.label(text="No loaded animations")
        else:
            try:
                anim_choice_text = 'Current animation: {0}'.format(
                    context.scene['curr_anim'])
            except KeyError:
                anim_choice_text = 'Select an animation'
            layout.operator_menu_enum("nmsdk._change_animation",
                                      "anim_names",
                                      text=anim_choice_text)
            row = layout.row()
            row.operator("nmsdk._play_animation",
                         icon='PLAY', emboss=False)
            row.operator("nmsdk._pause_animation",
                         icon='PAUSE', emboss=False)
            row.operator("nmsdk._stop_animation",
                         icon='REW', emboss=False)


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        bpy.utils.register_class(UpdateSettingsPanel)
        bpy.utils.register_class(ToolsPanel)
        bpy.utils.register_class(DefaultsPanel)
        bpy.utils.register_class(AnimationsPanel)

    @staticmethod
    def unregister():
        # Unregister panels
        bpy.utils.unregister_class(UpdateSettingsPanel)
        bpy.utils.unregister_class(ToolsPanel)
        bpy.utils.unregister_class(DefaultsPanel)
        bpy.utils.unregister_class(AnimationsPanel)
