# stdlib imports
from math import radians
import os.path as op

# Blender imports
from bpy.props import (StringProperty, BoolProperty, EnumProperty, IntProperty)
import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.types import Operator, PropertyGroup
from mathutils import Matrix

# internal imports
from .ModelImporter.import_scene import ImportScene
from .ModelExporter.addon_script import Exporter
from .ModelExporter.utils import get_all_actions_in_scene, get_all_actions
from .utils.settings import read_settings, write_settings
from .BlenderExtensions.UIWidgets import ShowMessageBox


def set_import_export_defaults(cls, context):
    if hasattr(cls, 'settings_loaded'):
        if not cls.settings_loaded:
            default_settings = context.scene.nmsdk_default_settings
            cls.export_directory = default_settings.export_directory
            cls.group_name = default_settings.group_name
            cls.settings_loaded = True
    # If there is an imported node, then get some default info from it.
    # TODO: This needs a bit of work...
    if bpy.context.scene.get('scene_node') and cls.preserve_node_info:
        scene_node = bpy.context.scene.get('scene_node')
        scene_path = scene_node['imported_from']
        export_dir = op.dirname(scene_path)
        cls.export_directory, cls.group_name = op.split(export_dir)
        cls.preserve_node_info = True
        if hasattr(cls, 'scene_name'):
            cls.scene_name = op.basename(scene_node['imported_from'])


# Operators to be used for the public API
# Import/Export operators

class ImportSceneOperator(Operator):
    """ Import an entire scene into the current blender context."""
    bl_idname = "nmsdk.import_scene"
    bl_label = "Import NMS Scene file"

    path: StringProperty(default="")

    clear_scene: BoolProperty(
        name='Clear scene',
        description='Whether or not to clear the currently exiting scene in '
                    'blender.',
        default=True)

    draw_hulls: BoolProperty(
        name='Draw bounded hulls',
        description='Whether or not to draw the points that make up the '
                    'bounded hulls of the materials. This is only for research'
                    '/debugging, so can safely be left as False.',
        default=False)
    import_collisions: BoolProperty(
        name='Import collisions',
        description='Whether or not to import the collision objects.',
        default=True)
    show_collisions: BoolProperty(
        name='Draw collisions',
        description='Whether or not to draw the collision objects.',
        default=False)
    import_recursively: BoolProperty(
        name='Import recursively',
        description='Whether or not to import reference nodes automatically.\n'
                    'For large scenes with many referenced scenes it is better'
                    ' to set this as False to avoid long wait times, and then '
                    'only import the scenes you want after it has loaded.',
        default=True)
    # Animation related properties
    import_bones: BoolProperty(
        name='Import bones',
        description="Whether or not to import the models' bones",
        default=False)
    max_anims: IntProperty(
        name='Max loaded animations',
        description='Maximum number of animations to load',
        default=10,
        soft_min=-1)

    def execute(self, context):
        keywords = self.as_keywords()
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict(),
                               settings=keywords)
        importer.render_scene()
        return importer.state


class ImportMeshOperator(Operator):
    """ Import one or more individual meshes from a single scene into the
    current blender context. """
    bl_idname = "nmsdk.import_mesh"
    bl_label = "Import NMS meshes"

    path: StringProperty(default="")
    mesh_id: StringProperty(default="")

    def execute(self, context):
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict())
        importer.render_mesh(str(self.mesh_id))
        return importer.state


class ExportSceneOperator(Operator):
    """ Export the current scene to a SCENE.MBIN file and associated geometry,
    animation, entity and other files.
    """
    bl_idname = "nmsdk.export_scene"
    bl_label = "Export to NMS scene"

    output_directory: StringProperty(
        name="Output Directory",
        description="The directory the exported data is to be placed in.")
    export_directory: StringProperty(
        name="Export Directory",
        description="The base path relative to the PCBANKS folder under which "
                    "all models will be exported.",
        default="CUSTOMMODELS")
    group_name: StringProperty(
        name="Group Name",
        description="Group name so that models that all belong in the same "
                    "folder are placed there (path becomes "
                    "group_name/scene_name).")
    scene_name: StringProperty(
        name="Scene Name",
        description="Name of the scene to be exported.")
    preserve_node_info: BoolProperty(
        name="Preserve Node Info",
        description="If the exported scene was originally imported, preserve "
                    "the details of any nodes that were in the original scene."
                    "\nNote that this will not currently export any geometry "
                    "data, so adding mesh collisions to an existing scene is "
                    "not currently possible.",
        default=False)
    AT_only: BoolProperty(
        name="ActionTriggers Only",
        description="If this box is ticked, all the action trigger data will "
                    "be exported directly to an ENTITY file in the specified "
                    "location with the project name. Anything else in the "
                    "project is ignored",
        default=False)
    no_vert_colours: BoolProperty(
        name="Don't export vertex colours",
        description="Ticking this box will force vertex colours to not be "
                    "exported. Use this if you have accidentally added vertex "
                    "colours to a mesh and don't know how to get rid of them.",
        default=False)
    idle_anim: StringProperty(
        name="Idle animation name",
        description="The name of the animation that is the idle animation.")

    def execute(self, context):
        set_import_export_defaults(self, context)
        keywords = self.as_keywords()
        keywords.pop('output_directory')
        keywords.pop('export_directory')
        keywords.pop('group_name')
        keywords.pop('scene_name')
        main_exporter = Exporter(self.output_directory, self.export_directory,
                                 self.group_name, self.scene_name, keywords)
        status = main_exporter.state
        if status == {'FINISHED'}:
            path = op.join(self.export_directory, self.group_name,
                           self.scene_name)
            self.report({'INFO'}, f"Models Exported Successfully to {path}")
        return status


# Operators to create various NMSDK objects


class CreateNMSDKScene(Operator):
    """Add the currently selected object to the NMSDK scene node. """
    bl_idname = "nmsdk.create_root_scene"
    bl_label = "Create empty NMSDK scene"

    def execute(self, context):
        empty_mesh = bpy.data.meshes.new('NMS_Scene')
        empty_obj = bpy.data.objects.new('NMS_Scene', empty_mesh)
        empty_obj.NMSNode_props.node_types = 'Reference'
        # Set the empty object to have a 90 degree rotation around the x-axis
        # to emulate the NMS coordinate system.
        empty_obj.matrix_world = Matrix.Rotation(radians(90), 4, 'X')
        bpy.context.scene.collection.objects.link(empty_obj)
        bpy.context.view_layer.objects.active = empty_obj
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}


# Private operators for internal use


class _FixActionNames(Operator):
    """Fix any incorrect action names."""
    bl_idname = "nmsdk._fix_action_names"
    bl_label = "Fix any incorrect action names"

    def _correct_name(self, action, obj_name):
        """ Correct the name of an action if it needs to be... """
        action_name = action.name.split('.')[0]
        correct_name = '{0}.{1}'.format(action_name, obj_name)
        if action.name != correct_name:
            action.name = correct_name

    def execute(self, context):
        for obj in context.scene.objects:
            obj_name = obj.name
            for action in get_all_actions(obj):
                self._correct_name(action[2], obj_name)
                action[2].use_fake_user = True
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class _FixOldFormat(Operator):
    """Change the type of node an object has"""
    bl_idname = "nmsdk._fix_old_format"
    bl_label = "Change NMS Node type"

    def execute(self, context):
        try:
            context.scene.objects[
                'NMS_SCENE'].NMSNode_props.node_types = 'Reference'
            return {'FINISHED'}
        except KeyError:
            return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class _ImportReferencedScene(Operator):
    """Import a referenced scene into an existing node"""
    bl_idname = "nmsdk._import_ref_scene"
    bl_label = "Import referenced NMS scene file"

    def execute(self, context):
        obj = context.object
        scene_path = obj.NMSReference_props.reference_path
        if not scene_path:
            # Can't import anything. Give up.
            return {'FINISHED'}
        if obj.children:
            # It already has children. For now, do nothing...
            return {'FINISHED'}
        # If we get here, then the node has no children, and has a path to
        # import. Try and do so...
        # TODO: globalize the ref_scenes or the importer itself. This will
        # allow the referenced scenes to be potentially taken from a previously
        # imported scene.
        PCBANKS_dir = context.scene.nmsdk_default_settings.PCBANKS_directory
        full_path = op.join(PCBANKS_dir, scene_path)
        importer = ImportScene(full_path, parent_obj=obj, ref_scenes=dict(),
                               settings={'clear_scene': False})
        importer.render_scene()
        return importer.state


class _ToggleCollisionVisibility(Operator):
    """Toggle whether the collision objects are visible or not"""
    bl_idname = "nmsdk._toggle_collision_visibility"
    bl_label = "Toggle collision visibility"

    def execute(self, context):
        nmsdk_settings = context.scene.nmsdk_settings
        nmsdk_settings.toggle_collision_visibility()
        # For every collision object in the scene, set its visibility to the
        # value specified by the `show_collisions` button.
        for obj in bpy.context.scene.objects:
            if obj.NMSNode_props.node_types == 'Collision':
                obj.hide_set(not nmsdk_settings.show_collisions)
        return {'FINISHED'}


class _SaveDefaultSettings(Operator):
    """Save any default settings"""
    bl_idname = "nmsdk._save_default_settings"
    bl_label = "Save Settings"

    def execute(self, context):
        default_settings = context.scene.nmsdk_default_settings
        default_settings.save()
        # TODO: spawn a new thread which can display this then un-display it
        # after some time...
        # bpy.types.WorkSpace.status_text_set(text="Settings saved")
        return {'FINISHED'}


class _GetPCBANKSFolder(Operator):
    """Select the PCBANKS folder location"""
    # Code modified from https://blender.stackexchange.com/a/126596
    bl_idname = "nmsdk._find_pcbanks"
    bl_label = "Specify PCBANKS location"

    # Define this to tell 'fileselect_add' that we want a directoy
    directory: StringProperty(
        name="PCBANKS path",
        description="Location of the PCBANKS folder")

    filter_folder: BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        # Set the PCBANKS_directory value
        context.scene.nmsdk_default_settings.PCBANKS_directory = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See:
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        self.directory = context.scene.nmsdk_default_settings.PCBANKS_directory
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}


class _RemovePCBANKSFolder(Operator):
    """Reset the PCBANKS folder location"""
    bl_idname = "nmsdk._remove_pcbanks"
    bl_label = "Remove PCBANKS location"

    def execute(self, context):
        # Set the PCBANKS_directory as blank
        context.scene.nmsdk_default_settings.PCBANKS_directory = ""
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class _GetMBINCompilerLocation(Operator):
    """Select the MBINCompiler executable location"""
    # Code modified from https://blender.stackexchange.com/a/126596
    bl_idname = "nmsdk._find_mbincompiler"
    bl_label = "Specify MBINCompiler location"

    filepath: StringProperty(
        name="MBINCompiler Location",
        description="Location of the MBINCompiler executable")

    def execute(self, context):
        # Set the PCBANKS_directory value
        context.scene.nmsdk_default_settings.MBINCompiler_path = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        # Open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # See:
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        self.directory = context.scene.nmsdk_default_settings.MBINCompiler_path
        context.window_manager.fileselect_add(self)
        # Tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}


class _RemoveMBINCompilerLocation(Operator):
    """Reset the MBINCompiler executable location"""
    bl_idname = "nmsdk._remove_mbincompiler"
    bl_label = "Remove MBINCompiler location"

    def execute(self, context):
        # Set the PCBANKS_directory as blank
        context.scene.nmsdk_default_settings.MBINCompiler_path = ""
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# Animation classes and functions
# TODO: move...

def get_loaded_anim_names(self, context):
    try:
        names = context.scene.nmsdk_anim_data.loadable_anim_data.keys()
        # Only show the names of animations that haven't been loaded
        return list(tuple([name] * 3) for name in names if name not in
                    context.scene.nmsdk_anim_data.loaded_anims)
    except KeyError:
        return [('None', 'None', 'None')]


def get_anim_names(self, context):
    try:
        names = context.scene.nmsdk_anim_data.loaded_anims
        return list(tuple([name] * 3) for name in names)
    except KeyError:
        return [('None', 'None', 'None')]


def get_anim_names_not_none(self, context):
    try:
        # make a copy of the names just to be safe
        names = list(context.scene.nmsdk_anim_data.loaded_anims)
        if 'None' in names:
            names.remove('None')
        return list(tuple([name] * 3) for name in names)
    except KeyError:
        return [('None', 'None', 'None')]


class AnimProperties(PropertyGroup):
    anims_loaded: BoolProperty(
        name='Animations loaded',
        description='Whether the animations are loaded or not',
        default=True)
    has_bound_mesh: BoolProperty(
        name='Has bound mesh',
        description='Whether or not the mesh of the object is bound to bones',
        default=False)
    idle_anim: EnumProperty(
        name='Idle animation',
        description='Animation that is played idly',
        items=get_anim_names_not_none)

    # key: name of animation
    # value: path to animation data
    loadable_anim_data = dict()
    # names of loaded animations. Instantiate with the default 'None'
    loaded_anims = ['None']
    # List of joint names
    joints = list()

    def reset(self):
        """ Reset all the values back to their original ones. """
        self.anims_loaded = False
        self.loadable_anim_data.clear()
        self.loaded_anims.clear()
        self.loaded_anims.extend(['None'])
        self.joints.clear()


class _RefreshAnimations(Operator):
    """Refresh the animation data"""
    bl_idname = "nmsdk._refresh_anim_list"
    bl_label = "Refresh Animation List"

    def execute(self, context):
        # Set the variables
        actions = get_all_actions_in_scene(context.scene)
        if len(actions) != 0:
            for action in actions:
                if action not in context.scene.nmsdk_anim_data.loaded_anims:
                    context.scene.nmsdk_anim_data.loaded_anims.append(action)
            context.scene.nmsdk_anim_data.anims_loaded = True
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class _LoadAnimation(Operator):
    """Load the selected animation data"""
    bl_idname = "nmsdk._load_animation"
    bl_label = "Load Animation"

    loadable_anim_name: EnumProperty(
        name='Available animations',
        description='List of all available animations for the scene',
        items=get_loaded_anim_names)

    def execute(self, context):
        # Set the variables
        loadable_anim_names = context.scene.nmsdk_anim_data.loadable_anim_data
        anim_name = self.loadable_anim_name
        anim_data = loadable_anim_names.pop(anim_name)
        bpy.ops.nmsdk.animation_handler(
            anim_name=anim_name,
            anim_path=anim_data['Filename'])
        # Set the current animation as the one we just selected
        bpy.ops.nmsdk._change_animation(anim_names=anim_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class _ChangeAnimation(Operator):
    """Change the currently selected animation"""
    bl_idname = "nmsdk._change_animation"
    bl_label = "Change Animation"

    anim_names: EnumProperty(
        name='Available animations',
        description='List of all available animations for the scene',
        items=get_anim_names)

    def execute(self, context):
        """Set every node in the scene to have the appropriate action.
        If the node is not animated in the current animation then set its
        action to None.
        """
        context.scene['curr_anim'] = self.anim_names

        # If the selected animation is none, reset everything to base.
        if self.anim_names == 'None':
            for armature in bpy.data.armatures:
                armature.pose_position = 'REST'
            for obj in bpy.data.objects:
                if obj.animation_data:
                    obj.animation_data.action = None
                    for track in obj.animation_data.nla_tracks:
                        track.mute = True
            context.scene.frame_end = 0
            return {'FINISHED'}

        frame_count = 0
        for armature in bpy.data.armatures:
            armature.pose_position = 'POSE'

        # Apply the action to each object
        for obj in context.scene.objects:
            action_name = '{0}.{1}'.format(self.anim_names, obj.name)
            if action_name in bpy.data.actions:
                obj.animation_data.action = bpy.data.actions[action_name]
                frame_count = max(frame_count,
                                  obj.animation_data.action.frame_range[1])
            else:
                # If the action doesn't exist, then the object isn't animated
                if obj.animation_data is not None:
                    obj.animation_data.action = None

        # Set the final frame count
        context.scene.frame_end = frame_count
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class _PlayAnimation(Operator):
    """Play the currently selected animation"""
    bl_idname = "nmsdk._play_animation"
    bl_label = "Play"

    def execute(self, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class _PauseAnimation(Operator):
    """Pause the currently playing animation"""
    bl_idname = "nmsdk._pause_animation"
    bl_label = "Pause"

    def execute(self, context):
        bpy.ops.screen.animation_cancel(restore_frame=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


class _StopAnimation(Operator):
    """Stop the currently selected animation"""
    bl_idname = "nmsdk._stop_animation"
    bl_label = "Stop"

    def execute(self, context):
        bpy.ops.screen.animation_cancel()
        bpy.ops.screen.frame_jump(end=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)


# Settings classes


class NMSDKSettings(PropertyGroup):
    show_collisions: BoolProperty(
        name='Draw collisions',
        description='Whether or not to draw the collision objects.',
        default=False)

    def toggle_collision_visibility(self):
        """ Toggle the collision visibility state. """
        self.show_collisions = not self.show_collisions


class NMSDKDefaultSettings(PropertyGroup):

    default_settings = read_settings()

    export_directory: StringProperty(
        name="Export Directory",
        description="The base path under which all models will be exported.",
        default=default_settings.get('export_directory', ""))
    group_name: StringProperty(
        name="Group Name",
        description="Group name so that models that all belong in the same "
                    "folder are placed there (path becomes group_name/name)",
        default=default_settings.get('group_name', ""))
    PCBANKS_directory: StringProperty(
        name="PCBANKS directory",
        description="Path to the PCBANKS folder",
        default=default_settings.get('PCBANKS_directory', ""))
    MBINCompiler_path: StringProperty(
        name="MBINCompiler location",
        description="Path to the Mbincompiler executable",
        default=default_settings.get('MBINCompiler_path', ""))

    def save(self):
        """ Save the current settings. """
        settings = {'export_directory': self.export_directory,
                    'group_name': self.group_name,
                    'PCBANKS_directory': self.PCBANKS_directory}
        write_settings(settings)


# Operators to be added to the blender UI for various tasks


class NMS_Export_Operator(Operator, ExportHelper):
    """Export scene to NMS compatible files"""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "export_mesh.nms"
    bl_label = "Export to NMS XML Format"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )
    export_directory: StringProperty(
        name="Export Directory",
        description="The base path relative to the PCBANKS folder under which "
                    "all models will be exported.",
        default="CUSTOMMODELS")
    group_name: StringProperty(
        name="Group Name",
        description="Group name so that models that all belong in the same "
                    "folder are placed there (path becomes group_name/name)")
    preserve_node_info: BoolProperty(
        name="Preserve Node Info",
        description="If the exported scene was originally imported, preserve "
                    "the details of any nodes that were in the original scene."
                    "\nNote that this will not currently export any geometry "
                    "data, so adding mesh collisions to an existing scene is "
                    "not currently possible.",
        default=False)
    AT_only: BoolProperty(
        name="ActionTriggers Only",
        description="If this box is ticked, all the action trigger data will "
                    "be exported directly to an ENTITY file in the specified "
                    "location with the project name. Anything else in the "
                    "project is ignored",
        default=False)
    no_vert_colours: BoolProperty(
        name="Don't export vertex colours",
        description="Ticking this box will force vertex colours to not be "
                    "exported. Use this if you have accidentally added vertex "
                    "colours to a mesh and don't know how to get rid of them.",
        default=False)
    idle_anim: StringProperty(
        name="Idle animation name",
        description="The name of the animation that is the idle animation.")

    # ExportHelper mixin class uses this.
    filename_ext = ""

    # Track whether some values have been read from the settings file to avoid
    # constantly reading from them.
    settings_loaded = False

    def invoke(self, context, _event):
        """ Override the default behavior so that we can provide a scene
        file name automatically. """
        if bpy.context.scene.get('scene_node'):
            scene_node = bpy.context.scene.get('scene_node')
            scene_name = op.basename(scene_node['imported_from'])
            self.filepath = scene_name
        return super().invoke(context, _event)

    def draw(self, context):
        set_import_export_defaults(self, context)
        layout = self.layout
        layout.prop(self, 'export_directory')
        layout.prop(self, 'group_name')
        layout.prop(self, 'preserve_node_info')
        layout.prop(self, 'AT_only')
        layout.prop(self, 'no_vert_colours')

    def execute(self, context):
        keywords = self.as_keywords()
        # Split the filepath provided as the final part is the name of the file
        export_path, scene_name = op.split(self.filepath)
        keywords.pop('export_directory')
        keywords.pop('group_name')
        if not bpy.context.scene.nmsdk_default_settings.MBINCompiler_path:
            ShowMessageBox("No MBINCompiler specified or found", "Error",
                           'ERROR')
            print("[ERROR]: No MBINCompiler specified or found")
            return {'CANCELLED'}
        main_exporter = Exporter(export_path, self.export_directory,
                                 self.group_name, scene_name, keywords)
        status = main_exporter.state
        if status == {'FINISHED'}:
            self.report({'INFO'}, "Models Exported Successfully")
        return status


class NMS_Import_Operator(Operator, ImportHelper):
    """Import NMS Scene files"""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "import_mesh.nms"
    bl_label = "Import from SCENE.EXML"

    # ImportHelper mixin class uses this
    filename_ext = ".EXML"
    filter_glob: StringProperty(
        default="*.scene.exml;*.SCENE.EXML;*.scene.mbin;*.SCENE.MBIN",
        options={"HIDDEN"})

    clear_scene: BoolProperty(
        name='Clear scene',
        description='Whether or not to clear the currently exiting scene in '
                    'blender.',
        default=True)

    draw_hulls: BoolProperty(
        name='Draw bounded hulls',
        description='Whether or not to draw the points that make up the '
                    'bounded hulls of the materials. This is only for research'
                    '/debugging, so can safely be left as False.',
        default=False)
    import_collisions: BoolProperty(
        name='Import collisions',
        description='Whether or not to import the collision objects.',
        default=True)
    show_collisions: BoolProperty(
        name='Draw collisions',
        description='Whether or not to draw the collision objects.',
        default=False)
    import_recursively: BoolProperty(
        name='Import recursively',
        description='Whether or not to import reference nodes automatically.\n'
                    'For large scenes with many referenced scenes it is better'
                    ' to set this as False to avoid long wait times, and then '
                    'only import the scenes you want after it has loaded.',
        default=True)
    # Animation related properties
    import_bones: BoolProperty(
        name='Import bones',
        description="Whether or not to import the models' bones",
        default=False)
    max_anims: IntProperty(
        name='Max loaded animations',
        description='Maximum number of animations to load. To Disable loading '
                    'animations set this to 0, or to force loading all set '
                    'this to -1',
        default=10,
        soft_min=-1)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'draw_hulls')
        layout.prop(self, 'clear_scene')
        layout.prop(self, 'import_recursively')
        coll_box = layout.box()
        coll_box.label(text='Collisions')
        coll_box.prop(self, 'import_collisions')
        coll_box.prop(self, 'show_collisions')

        animation_box = layout.box()
        animation_box.label(text='Animation')
        animation_box.prop(self, 'import_bones')
        animation_box.prop(self, 'max_anims')

    def execute(self, context):
        keywords = self.as_keywords()
        # set the state of the show_collisions button from the value specified
        # when the import occurs
        context.scene.nmsdk_settings.show_collisions = self.show_collisions
        # Reset the animation data
        context.scene.nmsdk_anim_data.reset()
        fdir = self.properties.filepath
        context.scene['_anim_names'] = ['None']
        print(fdir)
        if not bpy.context.scene.nmsdk_default_settings.MBINCompiler_path:
            ShowMessageBox("No MBINCompiler specified or found", "Error",
                           'ERROR')
            print("[ERROR]: No MBINCompiler specified or found")
            return {'CANCELLED'}
        importer = ImportScene(fdir, parent_obj=None, ref_scenes=dict(),
                               settings=keywords)
        importer.render_scene()
        status = importer.state
        self.report({'INFO'}, "Models Imported Successfully")
        print('Scene imported!')
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
