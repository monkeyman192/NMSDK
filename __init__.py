import bpy
from .BlenderExtensions import (NMSNodes, NMSEntities, NMSPanels,
                                NMSShaderNode, SettingsPanels)
from bpy.props import PointerProperty, EnumProperty  # noqa pylint: disable=import-error, no-name-in-module

# External API operators
from .NMSDK import ImportSceneOperator, ImportMeshOperator
# Main IO operators
from .NMSDK import NMS_Export_Operator, NMS_Import_Operator
# Internal operators
from .NMSDK import (_FixOldFormat, _ToggleCollisionVisibility,
                    _SaveDefaultSettings)
# Settings
from .NMSDK import NMSDKSettings, NMSDKDefaultSettings
# Animation classes
from .NMSDK import (_ChangeAnimation, _PlayAnimation, _PauseAnimation,
                    _StopAnimation)

customNodes = NMSNodes()

bl_info = {
    "name": "No Man's Sky Development Kit",
    "author": "gregkwaste, monkeyman192",
    "version": (0, 9, 12),
    "blender": (2, 79, 0),
    "location": "File > Export",
    "description": "Create NMS scene structures and export to NMS File format",
    "warning": "",
    "wiki_url": "https://github.com/monkeyman192/NMSDK/wiki",
    "tracker_url": "https://github.com/monkeyman192/NMSDK/issues",
    "category": "Import-Export"}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname,
                         text="Export to NMS XML Format ")


def menu_func_import(self, context):
    self.layout.operator(NMS_Import_Operator.bl_idname,
                         text="Import NMS SCENE.EXML")


def register():
    bpy.utils.register_class(NMS_Export_Operator)
    bpy.utils.register_class(NMS_Import_Operator)
    bpy.utils.register_class(NMSDKSettings)
    bpy.utils.register_class(NMSDKDefaultSettings)
    bpy.utils.register_class(ImportSceneOperator)
    bpy.utils.register_class(ImportMeshOperator)
    bpy.utils.register_class(_FixOldFormat)
    bpy.utils.register_class(_ToggleCollisionVisibility)
    bpy.utils.register_class(_SaveDefaultSettings)
    bpy.utils.register_class(_ChangeAnimation)
    bpy.utils.register_class(_PlayAnimation)
    bpy.utils.register_class(_PauseAnimation)
    bpy.utils.register_class(_StopAnimation)
    bpy.types.Scene.nmsdk_settings = PointerProperty(type=NMSDKSettings)
    bpy.types.Scene.nmsdk_default_settings = PointerProperty(
        type=NMSDKDefaultSettings)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    NMSPanels.register()
    NMSShaderNode.register()
    customNodes.register()
    NMSEntities.register()
    SettingsPanels.register()


def unregister():
    bpy.utils.unregister_class(NMS_Export_Operator)
    bpy.utils.unregister_class(NMS_Import_Operator)
    bpy.utils.unregister_class(NMSDKSettings)
    bpy.utils.unregister_class(NMSDKDefaultSettings)
    bpy.utils.unregister_class(ImportSceneOperator)
    bpy.utils.unregister_class(ImportMeshOperator)
    bpy.utils.unregister_class(_FixOldFormat)
    bpy.utils.unregister_class(_ToggleCollisionVisibility)
    bpy.utils.unregister_class(_SaveDefaultSettings)
    bpy.utils.unregister_class(_ChangeAnimation)
    bpy.utils.unregister_class(_PlayAnimation)
    bpy.utils.unregister_class(_PauseAnimation)
    bpy.utils.unregister_class(_StopAnimation)
    del bpy.types.Scene.nmsdk_settings
    del bpy.types.Scene.nmsdk_default_settings
    del bpy.types.Scene.anim_names
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    NMSPanels.unregister()
    NMSShaderNode.unregister()
    customNodes.unregister()
    NMSEntities.unregister()
    SettingsPanels.unregister()
