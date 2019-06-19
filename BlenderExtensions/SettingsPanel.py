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
        nmsdk_settings = context.scene.nmsdk_settings
        if nmsdk_settings.anims_loaded is False:
            if context.scene['_loadable_anim_names'] != []:
                # In this case, have a menu to allow for the animations to be
                # loaded
                layout.operator_menu_enum('nmsdk._load_animation',
                                          'anim_names',
                                          text='Add an animation')
        try:
            anim_names = context.scene['_anim_names']
            if not isinstance(anim_names, list):
                anim_names = context.scene['_anim_names'].to_list()
            if anim_names == list():
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
                """
                try:
                    layout.label(text="Current animation: {0}".format(
                        context.scene['curr_anim']))
                except KeyError:
                    layout.label(text="No animation currently selected")
                """
                row = layout.row()
                row.operator("nmsdk._play_animation",
                             icon='PLAY', emboss=False)
                row.operator("nmsdk._pause_animation",
                             icon='PAUSE', emboss=False)
                row.operator("nmsdk._stop_animation",
                             icon='REW', emboss=False)
        except KeyError:
            layout.label(text="No loaded animations")


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
