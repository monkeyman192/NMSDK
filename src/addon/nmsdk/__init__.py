# pyright: reportInvalidTypeForm=false

import os
import os.path as op
import time

import bpy
from bpy.props import PointerProperty, StringProperty
from bpy.utils import register_class, unregister_class

# extensions to blender UI
from .BlenderExtensions import ContextMenus, NMSEntities, NMSNodes, NMSPanels, SettingsPanels
from .ModelImporter.animation_handler import AnimationHandler

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
    _GetMBINCompilerLocation,
    _GetPCBANKSFolder,
    _ImportReferencedScene,
    _LoadAnimation,
    _PauseAnimation,
    _PlayAnimation,
    _RefreshAnimations,
    _RemoveMBINCompilerLocation,
    _RemovePCBANKSFolder,
    _SaveDefaultSettings,
    _StopAnimation,
    _ToggleCollisionVisibility,
)
from .utils.pak_handler import PakInfo
from .utils.settings import read_settings, write_settings

customNodes = NMSNodes()


def save_preferences(cls: "NMSDKPreferences", context: bpy.types.Context):
    print("Saving preferences")
    preferences = cls.as_dict()
    current_settings = read_settings()
    current_pcbanks_dir = current_settings.get("pcbanks_dir")
    new_pcbanks_dir = preferences.get("pcbanks_dir")
    write_settings(preferences)
    from hgpaktool import HGPAKFile
    if new_pcbanks_dir and current_pcbanks_dir != new_pcbanks_dir:
        t0 = time.perf_counter()
        # Load the data from the pak files.
        for pakfname in os.listdir(new_pcbanks_dir):
            if pakfname.lower().endswith(".pak"):
                with HGPAKFile(op.join(new_pcbanks_dir, pakfname)) as pak:
                    for fname in pak.filenames:
                        lfname = fname.lower()
                        if lfname.endswith(".scene.mbin"):
                            context.scene.nmsdk_pak_data.scene_paths.append(fname)
                            context.scene.nmsdk_pak_data.file_mapping[fname] = pakfname
                            # scene_paths.append(fname)
                            # file_mapping[fname] = pakfname
                        # elif lfname.endswith(".")
        t1 = time.perf_counter()
        print(f"Loaded {len(context.scene.nmsdk_pak_data.scene_paths)} scenes in {t1 - t0:.4f}s")


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
        default=default_settings.get('pcbanks_dir', "")
    )
    unpacked_pcbanks_dir: StringProperty(
        name="Unpacked PCBANKS Directory (Optional)",
        description="Path to your unpacked game files. This is not required.",
        subtype='DIR_PATH',
        update=save_preferences,
        default=default_settings.get('unpacked_pcbanks_dir', "")
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="NMSDK preferences")
        layout.prop(self, "pcbanks_dir")
        layout.prop(self, "unpacked_pcbanks_dir")

    def as_dict(self):
        return {
            "pcbanks_dir": self.pcbanks_dir,
            "unpacked_pcbanks_dir": self.unpacked_pcbanks_dir
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
    _GetPCBANKSFolder,
    _RemovePCBANKSFolder,
    _GetMBINCompilerLocation,
    _RemoveMBINCompilerLocation,
    _ToggleCollisionVisibility,
    _SaveDefaultSettings,
    _ChangeAnimation,
    _RefreshAnimations,
    _LoadAnimation,
    _PlayAnimation,
    _PauseAnimation,
    _StopAnimation,
    AnimationHandler,
    AnimProperties,
    PakInfo,
)


def register():
    bpy.utils.register_class(NMSDKPreferences)
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.nmsdk_pak_data = PointerProperty(type=PakInfo)
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
    del bpy.types.Scene.nmsdk_pak_data
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    NMSPanels.unregister()
    # NMSShaderNode.unregister()
    customNodes.unregister()
    NMSEntities.unregister()
    SettingsPanels.unregister()
    ContextMenus.unregister()
    bpy.utils.unregister_class(NMSDKPreferences)


if __name__ == '__main__':
    register()
