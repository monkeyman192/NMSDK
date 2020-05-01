import bpy
from bpy.utils import register_class, unregister_class


class NMSDK_PT_UpdateSettingsPanel(bpy.types.Panel):
    bl_idname = 'NMSDK_PT_UpdateSettingsPanel'
    bl_label = 'Update Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("nmsdk._fix_old_format")
        layout.operator("nmsdk._fix_action_names")


class NMSDK_PT_ToolsPanel(bpy.types.Panel):
    bl_idname = 'NMSDK_PT_ToolsPanel'
    bl_label = 'Scene Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
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
            icon = "HIDE_ON"
        else:
            label = "Collisions: Not Visible"
            icon = "HIDE_OFF"
        layout.operator("nmsdk._toggle_collision_visibility",
                        icon=icon, text=label)


class NMSDK_PT_DefaultsPanel(bpy.types.Panel):
    bl_idname = 'NMSDK_PT_DefaultsPanel'
    bl_label = 'Default Values'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
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
        row = layout.split(factor=0.85, align=True)
        row.alignment = 'LEFT'
        row.operator("nmsdk._find_pcbanks", icon='ZOOM_ALL',
                     text='PCBANKS location')
        row.separator()
        row.operator('nmsdk._remove_pcbanks',
                     icon='X', emboss=False, text=" ")
        _dir = context.scene.nmsdk_default_settings.PCBANKS_directory
        if _dir != "":
            layout.label(text=_dir)
        row = layout.split(factor=0.85, align=True)
        row.alignment = 'LEFT'
        row.operator("nmsdk._find_mbincompiler", icon='ZOOM_ALL',
                     text='MBINCompiler location')
        row.separator()
        row.operator('nmsdk._remove_mbincompiler',
                     icon='X', emboss=False, text=" ")
        _dir = context.scene.nmsdk_default_settings.MBINCompiler_location
        if _dir != "":
            layout.label(text=_dir)
        layout.operator("nmsdk._save_default_settings", icon='FILE_TICK',
                        text='Save settings')


class NMSDK_PT_AnimationsPanel(bpy.types.Panel):
    bl_idname = 'NMSDK_PT_AnimationsPanel'
    bl_label = 'Animation controls'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
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
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.label(text="No loaded animations")
            row.operator('nmsdk._refresh_anim_list',
                         icon='FILE_REFRESH', emboss=False, text=" ")
        else:
            try:
                anim_choice_text = 'Current animation: {0}'.format(
                    context.scene['curr_anim'])
            except KeyError:
                anim_choice_text = 'Select an animation'
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.operator_menu_enum("nmsdk._change_animation", "anim_names",
                                   text=anim_choice_text)
            row.operator('nmsdk._refresh_anim_list',
                         icon='FILE_REFRESH', emboss=False, text=" ")
            row = layout.row()
            row.operator("nmsdk._play_animation",
                         icon='PLAY', emboss=False)
            row.operator("nmsdk._pause_animation",
                         icon='PAUSE', emboss=False)
            row.operator("nmsdk._stop_animation",
                         icon='REW', emboss=False)
            row = layout.row()
            row.label(text="Idle animation: ")
            row.prop_menu_enum(context.scene.nmsdk_anim_data, "idle_anim",
                               text=context.scene.nmsdk_anim_data.idle_anim)


classes = (NMSDK_PT_UpdateSettingsPanel,
           NMSDK_PT_ToolsPanel,
           NMSDK_PT_DefaultsPanel,
           NMSDK_PT_AnimationsPanel)


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        for cls in classes:
            register_class(cls)

    @staticmethod
    def unregister():
        # Unregister panels
        for cls in reversed(classes):
            unregister_class(cls)
