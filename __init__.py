bl_info = {
    "name": "No Man's Sky Development Kit",
    "author": "gregkwaste, monkeyman192",
    "version": (0, 9, 17),
    "blender": (2, 79, 0),
    "location": "File > Export",
    "description": "Create NMS scene structures and export to NMS File format",
    "warning": "",
    "wiki_url": "https://monkeyman192.github.io/NMSDK/",
    "tracker_url": "https://github.com/monkeyman192/NMSDK/issues",
    "category": "Import-Export"}


import bpy  # pylint: disable=import-error
from bpy.props import PointerProperty, EnumProperty  # noqa pylint: disable=import-error, no-name-in-module

# External API operators
from .NMSDK import ImportSceneOperator, ImportMeshOperator, ExportSceneOperator
# Main IO operators
from .NMSDK import NMS_Export_Operator, NMS_Import_Operator
# Internal operators
from .NMSDK import (_FixOldFormat, _ToggleCollisionVisibility,
                    _SaveDefaultSettings, _FixActionNames, _GetPCBANKSFolder,
                    _RemovePCBANKSFolder)
# Settings
from .NMSDK import NMSDKSettings, NMSDKDefaultSettings
# Animation classes
from .NMSDK import (_ChangeAnimation, _PlayAnimation, _PauseAnimation,
                    _StopAnimation, _LoadAnimation, AnimProperties,
                    _RefreshAnimations)
from .ModelImporter.animation_handler import AnimationHandler
# extensions to blender UI
from .BlenderExtensions import (NMSNodes, NMSEntities, NMSPanels,
                                NMSShaderNode, SettingsPanels)

customNodes = NMSNodes()


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname,
                         text="Export to NMS XML Format ")


def menu_func_import(self, context):
    self.layout.operator(NMS_Import_Operator.bl_idname,
                         text="Import NMS SCENE")


def register():
    bpy.utils.register_class(NMS_Export_Operator)
    bpy.utils.register_class(NMS_Import_Operator)
    bpy.utils.register_class(NMSDKSettings)
    bpy.utils.register_class(NMSDKDefaultSettings)
    bpy.utils.register_class(ImportSceneOperator)
    bpy.utils.register_class(ImportMeshOperator)
    bpy.utils.register_class(ExportSceneOperator)
    bpy.utils.register_class(_FixOldFormat)
    bpy.utils.register_class(_FixActionNames)
    bpy.utils.register_class(_GetPCBANKSFolder)
    bpy.utils.register_class(_RemovePCBANKSFolder)
    bpy.utils.register_class(_ToggleCollisionVisibility)
    bpy.utils.register_class(_SaveDefaultSettings)
    bpy.utils.register_class(_ChangeAnimation)
    bpy.utils.register_class(_RefreshAnimations)
    bpy.utils.register_class(_LoadAnimation)
    bpy.utils.register_class(_PlayAnimation)
    bpy.utils.register_class(_PauseAnimation)
    bpy.utils.register_class(_StopAnimation)
    bpy.utils.register_class(AnimationHandler)
    bpy.utils.register_class(AnimProperties)
    bpy.types.Scene.nmsdk_settings = PointerProperty(type=NMSDKSettings)
    bpy.types.Scene.nmsdk_default_settings = PointerProperty(
        type=NMSDKDefaultSettings)
    bpy.types.Scene.nmsdk_anim_data = PointerProperty(type=AnimProperties)
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
    bpy.utils.unregister_class(ExportSceneOperator)
    bpy.utils.unregister_class(_FixOldFormat)
    bpy.utils.unregister_class(_FixActionNames)
    bpy.utils.unregister_class(_GetPCBANKSFolder)
    bpy.utils.unregister_class(_RemovePCBANKSFolder)
    bpy.utils.unregister_class(_ToggleCollisionVisibility)
    bpy.utils.unregister_class(_SaveDefaultSettings)
    bpy.utils.unregister_class(_ChangeAnimation)
    bpy.utils.unregister_class(_RefreshAnimations)
    bpy.utils.unregister_class(_LoadAnimation)
    bpy.utils.unregister_class(_PlayAnimation)
    bpy.utils.unregister_class(_PauseAnimation)
    bpy.utils.unregister_class(_StopAnimation)
    bpy.utils.unregister_class(AnimationHandler)
    bpy.utils.unregister_class(AnimProperties)
    del bpy.types.Scene.nmsdk_settings
    del bpy.types.Scene.nmsdk_default_settings
    del bpy.types.Scene.anim_data
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    NMSPanels.unregister()
    NMSShaderNode.unregister()
    customNodes.unregister()
    NMSEntities.unregister()
    SettingsPanels.unregister()


if __name__ == '__main__':
    register()
