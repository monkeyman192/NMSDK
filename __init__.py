bl_info = {
    "name": "No Man's Sky Development Kit",
    "author": "gregkwaste, monkeyman192",
    "version": (0, 9, "28-pre8"),
    "blender": (4, 2, 0),
    "location": "File > Export/Import",
    "description": "Create NMS scene structures and export to NMS File format",
    "warning": "",
    "wiki_url": "https://monkeyman192.github.io/NMSDK/",
    "tracker_url": "https://github.com/monkeyman192/NMSDK/issues",
    "category": "Import-Export"}


import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import PointerProperty

# Inject the directory this file is in into the sys.path so that the imports
# become significantly nicer...
import sys
import os.path as op
sys.path.append(op.dirname(__file__))

# External API operators
from .NMSDK import ImportSceneOperator, ImportMeshOperator, ExportSceneOperator
# Main IO operators
from .NMSDK import NMS_Export_Operator, NMS_Import_Operator
# NMSDK object node handling operators
from .NMSDK import CreateNMSDKScene
# Internal operators
from .NMSDK import (_FixOldFormat, _ToggleCollisionVisibility,
                    _SaveDefaultSettings, _FixActionNames, _GetPCBANKSFolder,
                    _RemovePCBANKSFolder, _GetMBINCompilerLocation,
                    _RemoveMBINCompilerLocation, _ImportReferencedScene)
# Settings
from .NMSDK import NMSDKSettings, NMSDKDefaultSettings
# Animation classes
from .NMSDK import (_ChangeAnimation, _PlayAnimation, _PauseAnimation,
                    _StopAnimation, _LoadAnimation, AnimProperties,
                    _RefreshAnimations)
from .ModelImporter.animation_handler import AnimationHandler
# extensions to blender UI
from .BlenderExtensions import (NMSNodes, NMSEntities, NMSPanels,
                                SettingsPanels, ContextMenus)  # , NMSShaderNode)
# Note: The NMSShaderNode is broken for 2.8. This needs a lot of work anyway
# and isn't being used so we'll just not load it for now...

customNodes = NMSNodes()


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname,
                         text="Export to NMS XML Format ")


def menu_func_import(self, context):
    self.layout.operator(NMS_Import_Operator.bl_idname,
                         text="Import NMS SCENE")


classes = (NMS_Export_Operator,
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
           AnimProperties)


def register():
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


if __name__ == '__main__':
    register()
