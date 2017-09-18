bl_info = {  
 "name": "NMS Model Toolkit",  
 "author": "gregkwaste, monkeyman192",  
 "version": (0, 9),
 "blender": (2, 7, 0),  
 "location": "File > Export",  
 "description": "Exports to NMS File format",  
 "warning": "",
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Export"} 

import bpy
from BlenderExtensions import *
from addon_script import NMS_Export_Operator

customNodes = NMSNodes()

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname, text="Export to NMS XML Format ")

def register():
    bpy.utils.register_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    NMSPanels.register()
    customNodes.register()


def unregister():
    bpy.utils.unregister_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    NMSPanels.unregister()
    customNodes.unregister()


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.nms(filepath="J:\\Installs\\Steam\\steamapps\\common\\No Man's Sky\\GAMEDATA\\PCBANKS\\CUBE_ODD")
