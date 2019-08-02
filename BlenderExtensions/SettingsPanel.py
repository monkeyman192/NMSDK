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


class DescriptorPanel(bpy.types.Panel):
    bl_idname = 'DescriptorPanel'
    bl_label = 'Descriptor handler'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    groups = dict()

    @classmethod
    def poll(self, context):
        return True

    def determine_categories(self):
        """ Determine the categories for each object based on the information.
        """
        # If the group data has already been determined, do nothing.
        # TODO: This may need to change to be able to handle when the actual
        # proc-gen structure of a scene changes.
        if self.groups != dict():
            return
        # Otherwise, recurse over all the objects in the scene and determine
        # all the group names and the objects existing in each group
        for obj in bpy.context.scene.objects:
            if obj.NMSReference_props.is_proc:
                group_name = obj.NMSDescriptor_props.proc_prefix
                if obj.NMSDescriptor_props.choice_types == 'Random':
                    if group_name not in self.groups:
                        self.groups[group_name] = [obj.name]
                    else:
                        self.groups[group_name].append(obj.name)

    def draw(self, context):
        layout = self.layout
        # If the scene is not proc-gen, simply display a label saying so.
        if context.scene.nmsdk_settings.is_proc_gen is False:
            layout.label(text='Scene contains no procedurally generated '
                              'elements')
            return
        # Otherwise, we want to display a number of things...
        # For now while testing, let's just dyanimcally display some labels...
        # First we need the categories
        self.determine_categories()
        for group_name in self.groups:
            layout.label(text=str(group_name))


class SettingsPanels():

    @staticmethod
    def register():
        # Register panels
        bpy.utils.register_class(UpdateSettingsPanel)
        bpy.utils.register_class(ToolsPanel)
        bpy.utils.register_class(DefaultsPanel)
        bpy.utils.register_class(AnimationsPanel)
        bpy.utils.register_class(DescriptorPanel)

    @staticmethod
    def unregister():
        # Unregister panels
        bpy.utils.unregister_class(UpdateSettingsPanel)
        bpy.utils.unregister_class(ToolsPanel)
        bpy.utils.unregister_class(DefaultsPanel)
        bpy.utils.unregister_class(AnimationsPanel)
        bpy.utils.unregister_class(DescriptorPanel)
