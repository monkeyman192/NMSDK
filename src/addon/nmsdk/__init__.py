# pyright: reportInvalidTypeForm=false

import json
import os
import os.path as op
import time

import bpy
from bpy.types import Operator
from bpy.props import PointerProperty, StringProperty
from bpy.utils import register_class, unregister_class

# extensions to blender UI
from .BlenderExtensions import ContextMenus, NMSEntities, NMSNodes, NMSPanels, SettingsPanels

# External API operators
# Main IO operators
# NMSDK object node handling operators
# Internal operators
# Settings
# Animation classes
from .NMSDK import (
    AnimProperties,
    CreateNMSDKScene,
    ExportSceneOperator,
    ImportMeshOperator,
    ImportSceneOperator,
    NMS_Export_Operator,
    NMS_Import_Operator,
    NMSDKDefaultSettings,
    NMSDKSettings,
    _ChangeAnimation,
    _FixActionNames,
    _FixOldFormat,
    _ImportReferencedScene,
    _LoadAnimation,
    _PauseAnimation,
    _PlayAnimation,
    _RefreshAnimations,
    _SaveDefaultSettings,
    _StopAnimation,
    _ToggleCollisionVisibility,
)
from .utils.io import hide_path
from .utils.settings import read_settings, write_settings

customNodes = NMSNodes()


# @persistent
# def load_vfs_data(*args):
#     addon_prefs = bpy.context.preferences.addons[__package__].preferences
#     print(addon_prefs.pcbanks_dir)
#     if addon_prefs.pcbanks_dir and op.exists(addon_prefs.pcbanks_dir):
#         if op.exists(op.join(addon_prefs.pcbanks_dir, ".scene_vfs")):
#             if op.exists(op.join(addon_prefs.pcbanks_dir, ".scene_vfs", "index.json")):
#                 with open(op.join(addon_prefs.pcbanks_dir, ".scene_vfs", "index.json")) as f:
#                     pak_data = json.load(f)
#     print("loaded VFS data")


def save_preferences(cls: "NMSDKPreferences", context: bpy.types.Context):
    preferences = cls.as_dict()
    current_settings = read_settings()
    current_pcbanks_dir = current_settings.get("pcbanks_dir")
    new_pcbanks_dir = preferences.get("pcbanks_dir")
    settings_file = write_settings(preferences)
    print(f"Saved preferences to {settings_file}")
    from hgpaktool import HGPAKFile
    if new_pcbanks_dir and current_pcbanks_dir != new_pcbanks_dir:
        t0 = time.perf_counter()
        out_dir = op.join(new_pcbanks_dir, ".scene_vfs")
        if not op.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            hide_path(out_dir)
        # Load the data from the pak files.
        print("Creating vfs... This may take a little while (but it will be worth it!)")
        index = {}
        counter = 0
        for pakfname in os.listdir(new_pcbanks_dir):
            if pakfname.lower().endswith(".pak"):
                with HGPAKFile(op.join(new_pcbanks_dir, pakfname)) as pak:
                    for fname in pak.filenames:
                        lfname = fname.lower()
                        if lfname.endswith(".scene.mbin"):
                            counter += 1
                            dest_fname = op.join(out_dir, lfname)
                            if not op.exists(dest_fname):
                                dest_dir = op.join(out_dir, op.dirname(fname))
                                os.makedirs(dest_dir, exist_ok=True)
                                with open(dest_fname, "w"):
                                    pass
                    for fname in pak.filenames:
                        index[fname] = pakfname
        cls.pak_mapping_data = index
        with open(op.join(out_dir, "index.json"), "w") as f:
            json.dump(index, f)
        t1 = time.perf_counter()
        print(f"Loaded {counter} scenes into VFS in {t1 - t0:.4f}s")


class IndexPAKPath(Operator):
    """Index all the pak files"""
    bl_idname = "nmsdk.index_paks"
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        from hgpaktool import HGPAKFile

        addon_prefs: NMSDKPreferences = context.preferences.addons[__package__].preferences

        t0 = time.perf_counter()
        out_dir = op.join(addon_prefs.pcbanks_dir, ".scene_vfs")
        if not op.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            hide_path(out_dir)
        print("Creating vfs... This may take a little while (but it will be worth it!)")
        index = {}
        counter = 0
        for pakfname in os.listdir(addon_prefs.pcbanks_dir):
            if pakfname.lower().endswith(".pak"):
                with HGPAKFile(op.join(addon_prefs.pcbanks_dir, pakfname)) as pak:
                    for fname in pak.filenames:
                        lfname = fname.lower()
                        if lfname.endswith(".scene.mbin"):
                            counter += 1
                            dest_fname = op.join(out_dir, lfname)
                            if not op.exists(dest_fname):
                                dest_dir = op.join(out_dir, op.dirname(fname))
                                os.makedirs(dest_dir, exist_ok=True)
                                with open(dest_fname, "w"):
                                    pass
                    for fname in pak.filenames:
                        index[fname] = pakfname
        with open(op.join(out_dir, "index.json"), "w") as f:
            json.dump(index, f)
        t1 = time.perf_counter()
        print(f"Loaded {counter} scenes into VFS in {t1 - t0:.4f}s")

        return {'FINISHED'}


class NMSDKPreferences(bpy.types.AddonPreferences):
    # This must match the add-on name, use `__package__`
    # when defining this for add-on extensions or a sub-module of a Python package.
    bl_idname = __package__

    default_settings = read_settings()

    pcbanks_dir: StringProperty(
        name="PCBANKS Directory",
        description="Path to your PCBANKS directory itself. This should contain the vanilla game .pak files",
        subtype='DIR_PATH',
        update=save_preferences,
        default=default_settings.get("pcbanks_dir", "")
    )
    unpacked_pcbanks_dir: StringProperty(
        name="Unpacked PCBANKS Directory (Optional)",
        description="Path to your unpacked game files. This is not required.",
        subtype='DIR_PATH',
        update=save_preferences,
        default=default_settings.get("unpacked_pcbanks_dir", "")
    )
    mbincompiler_path: StringProperty(
        name="MBINCompiler Executable (Optional)",
        description=(
            "Path to the MBINCompiler executable. This is only required if you want to read/write MXML files"
        ),
        subtype='FILE_PATH',
        update=save_preferences,
        default=default_settings.get("mbincompiler_path", "")
    )

    pak_mapping_data: dict[str, str]

    def draw(self, context):
        layout = self.layout
        layout.label(text="NMSDK preferences")
        row = layout.row(align=True)
        row.prop(self, "pcbanks_dir")
        row.operator("nmsdk.index_paks", icon="FILE_REFRESH", text_ctxt="Refresh pak index")
        layout.prop(self, "unpacked_pcbanks_dir")
        layout.prop(self, "mbincompiler_path")

    def as_dict(self):
        return {
            "pcbanks_dir": self.pcbanks_dir,
            "unpacked_pcbanks_dir": self.unpacked_pcbanks_dir,
            "mbincompiler_path": self.mbincompiler_path
        }


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname,
                         text="Export to NMS XML Format ")


def menu_func_import(self, context):
    self.layout.operator(NMS_Import_Operator.bl_idname,
                         text="Import NMS SCENE")


classes = (
    NMS_Export_Operator,
    NMS_Import_Operator,
    NMSDKSettings,
    NMSDKDefaultSettings,
    ImportSceneOperator,
    ImportMeshOperator,
    ExportSceneOperator,
    CreateNMSDKScene,
    _FixOldFormat,
    _FixActionNames,
    _ImportReferencedScene,
    _ToggleCollisionVisibility,
    _SaveDefaultSettings,
    _ChangeAnimation,
    _RefreshAnimations,
    _LoadAnimation,
    _PlayAnimation,
    _PauseAnimation,
    _StopAnimation,
    AnimProperties,
)


def register():
    # bpy.app.handlers.load_post.append(load_vfs_data)
    bpy.utils.register_class(IndexPAKPath)
    bpy.utils.register_class(NMSDKPreferences)
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.nmsdk_settings = PointerProperty(type=NMSDKSettings)
    bpy.types.Scene.nmsdk_default_settings = PointerProperty(
        type=NMSDKDefaultSettings)
    bpy.types.Scene.nmsdk_anim_data = PointerProperty(type=AnimProperties)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    NMSPanels.register()
    # NMSShaderNode.register()
    customNodes.register()
    NMSEntities.register()
    SettingsPanels.register()
    ContextMenus.register()


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.nmsdk_settings
    del bpy.types.Scene.nmsdk_default_settings
    del bpy.types.Scene.nmsdk_anim_data
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    NMSPanels.unregister()
    # NMSShaderNode.unregister()
    customNodes.unregister()
    NMSEntities.unregister()
    SettingsPanels.unregister()
    ContextMenus.unregister()
    bpy.utils.unregister_class(NMSDKPreferences)
    bpy.utils.unregister_class(IndexPAKPath)
    # bpy.app.handlers.load_post.remove(load_vfs_data)


if __name__ == '__main__':
    register()
