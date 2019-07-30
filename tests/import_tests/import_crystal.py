""" Tests for import functionality. """
import bpy
import os
import os.path as op
# We need a weird import path so that the function can be imported when running
# blender from subprocess with pytest...
from nmsdk.utils.test_helpers import assert_or_exit


# Path is relative to the plugin directory
CRYSTAL_PATH = "tests\\import_tests\\data\\MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE.SCENE.MBIN"  # noqa


res = bpy.ops.nmsdk.import_scene(path=op.join(os.getcwd(), CRYSTAL_PATH))
# First, make sure that it ran
assert_or_exit(res == {'FINISHED'}, 1)
# Then, we can check that some values of the scene are correct...
assert_or_exit('_Crystal_A' in bpy.data.objects, 2)
crystal_ob = bpy.data.objects['_Crystal_A']
assert_or_exit(len(crystal_ob.data.vertices) == 852, 3)
