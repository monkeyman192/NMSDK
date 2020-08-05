# Test NMSDK
from bpy.types import (Operator,PropertyGroup)
from bpy.props import EnumProperty
import os
import subprocess
import ensurepip
import bpy

class NMSTests(PropertyGroup):

    tests: EnumProperty(
        name='Available tests',
        description='List of all available tests',
        items=[ 
            ( '\\tests\\import_tests\\import_crystal.py', 'Import large crystal', '' ),
            ( '\\tests\\import_tests\\import_toycube.py', 'Import toy cube','' ),
    ])

class RunTest(Operator):
    """Run a test"""
    bl_idname = "nmsdk.run_test"
    bl_label = "Run test"

    def execute(self, context):
        try:
            import pytest
            print("enum state:",context.scene.nmsdk_tests.tests)
            print(os.path.dirname(__file__))
            pytest.main([os.path.dirname(__file__)+context.scene.nmsdk_tests.tests])
#import sys
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#import sample
#            
            return {'FINISHED'}
        except ModuleNotFoundError:
            print ('Pytest not installed')
            return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

# Pip is provided with 2.81
# cf. https://blender.stackexchange.com/questions/139718/install-pip-and-packages-from-within-blender-os-independently
# To uninstall pytest:
#    -b --python-expr "import bpy; import subprocess; import ensurepip; ensurepip.bootstrap(); subprocess.check_call([bpy.app.binary_path_python, '-m', 'pip', 'uninstall', 'pytest'])"
class InstallPytest(Operator):
    """Install Pytest"""
    bl_idname = "nmsdk.install_pytest"
    bl_label = "Install Pytest"
    
    def execute(self, context):
        ensurepip.bootstrap()
        # Bootstrap modifies a necessary system variable cf. https://developer.blender.org/T71856
        os.environ.pop("PIP_REQ_TRACKER", None)
        subprocess.check_call([bpy.app.binary_path_python, '-m', 'pip', 'install', 'pytest'])
        bpy.ops.script.reload()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)