""" Tests for import functionality. """
import bpy
import os
import os.path as op
# We need a weird import path so that the function can be imported when running
# blender from subprocess with pytest...
from nmsdk.utils.test_helpers import assert_or_exit as _check  # noqa pylint: disable=import-error, no-name-in-module


# Path is relative to the plugin directory
CRYSTAL_PATH = "tests\\import_tests\\data\\MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE.SCENE.MBIN"  # noqa


res = bpy.ops.nmsdk.import_scene(path=op.join(os.getcwd(), CRYSTAL_PATH))
# First, make sure that it ran
_check(res == {'FINISHED'})
# Then, we can check that some values of the scene are correct...
_check('_Crystal_A' in bpy.data.objects)
crystal_ob = bpy.data.objects['_Crystal_A']
_check(len(crystal_ob.data.vertices) == 852)
# Check that the mesh collision is loaded correctly
_check('MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE_COLL' in bpy.data.objects)  # noqa
mesh_coll_ob = bpy.data.objects['MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE_COLL']  # noqa
# Let's make sure that the ability to toggle collisions' visibility works
_check(bpy.ops.nmsdk._toggle_collision_visibility())
# Now, check that the collision mesh has the right number of verts
_check(len(mesh_coll_ob.data.vertices) == 32)
# check that some custom properties have been loaded correctly
_check(crystal_ob.NMSNode_props.node_types == 'Mesh')
_check(crystal_ob.NMSMesh_props.material_path == 'MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE\\CRYSTAL_LARGE.MATERIAL.MBIN')  # noqa
_check(crystal_ob.NMSEntity_props.name_or_path == 'MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE\\CRYSTAL_LARGE\\ENTITIES\\CRYSTAL_LARGE.ENTITY.MBIN')  # noqa
