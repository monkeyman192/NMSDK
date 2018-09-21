import bpy
from BlenderExtensions import NMSNodes, NMSEntities, NMSPanels
from addon_script import NMS_Export_Operator
from plugin_info import PLUGIN_INFO

bl_info = PLUGIN_INFO

customNodes = NMSNodes()


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname,
                         text="Export to NMS XML Format ")


def register():
    bpy.utils.register_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    NMSPanels.register()
    customNodes.register()
    NMSEntities.register()


def unregister():
    bpy.utils.unregister_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    NMSPanels.unregister()
    customNodes.unregister()
    NMSEntities.unregister()


# TODO: remove
if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.nms(filepath="J:\\Installs\\Steam\\steamapps\\common\\No Man's Sky\\GAMEDATA\\PCBANKS\\CUBE_ODD")  # noqa
