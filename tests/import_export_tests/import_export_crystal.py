import os.path as op
import tempfile
import sys

import bpy

# Fix up the system path to include the nmsdk directory...
# I can't think of a better way of doing this right now... If this becomes
# needed in more tests (it will!!), then we may need to start investigating
# better solutions.
nmsdk_dir = op.normpath(op.join(op.dirname(__file__), '..', '..'))
if nmsdk_dir not in sys.path:
    sys.path.append(nmsdk_dir)

from utils.utils import scene_to_dict  # noqa pylint: E402
from utils.io import convert_file  # noqa pylint: E402

# The NMS game data to test the importing with is in the main test folder.
TEST_DATA_PATH = op.join(op.dirname(__file__), '..', 'NMS_DATA')
CRYSTAL_BASE_PATH = 'MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE'
CRYSTAL_PATH = op.join(TEST_DATA_PATH,
                       CRYSTAL_BASE_PATH,
                       'CRYSTAL_LARGE.SCENE.MBIN')

# FIRST - we import the scene into blender...

# Import with `draw_hulls = True` to ensure that there is no issue exporting
# in this case.
res = bpy.ops.nmsdk.import_scene(path=CRYSTAL_PATH, draw_hulls=True)
# First, make sure that it ran
assert res == {'FINISHED'}
# Then, we can check that some values of the scene are correct...
assert 'CRYSTAL_LARGE.SCENE' in bpy.data.objects
# Assign this now and we'll come back to it later...
crystal_scene = bpy.data.objects['CRYSTAL_LARGE.SCENE']
assert '_Crystal_A' in bpy.data.objects
crystal_ob = bpy.data.objects['_Crystal_A']
assert len(crystal_ob.data.vertices) == 852
# Check that the mesh collision is loaded correctly
assert 'CRYSTAL_LARGE_COLL' in bpy.data.objects
mesh_coll_ob = bpy.data.objects['CRYSTAL_LARGE_COLL']
# Let's make sure that the ability to toggle collisions' visibility works
assert bpy.ops.nmsdk._toggle_collision_visibility()
# Now, check that the collision mesh has the right number of verts
assert len(mesh_coll_ob.data.vertices) == 32
# check that some custom properties have been loaded correctly
assert crystal_scene.NMSNode_props.node_types == 'Reference'
assert crystal_scene.NMSReference_props.reference_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE.SCENE.MBIN')
assert crystal_ob.NMSNode_props.node_types == 'Mesh'
assert crystal_ob.NMSMesh_props.material_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE\\CRYSTAL_LARGE.MATERIAL.MBIN')
assert crystal_ob.NMSEntity_props.name_or_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE\\ENTITIES\\CRYSTAL_LARGE.ENTITY.MBIN')

# SECOND - check the exported data
with tempfile.TemporaryDirectory() as tempdir:
    res = bpy.ops.nmsdk.export_scene(output_directory=tempdir,
                                     preserve_node_info=True)
    assert res == {'FINISHED'}

    export_path = op.join(tempdir, 'CUSTOMMODELS')
    out_path = op.join(tempdir, CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE.SCENE.MBIN')
    # Let's ensure it exists
    assert op.exists(out_path)
    # Now, let's have a look at the scene and check that it matches the
    # original one...
    # First we need to convert it to an exml file...
    new_exml_scene = convert_file(out_path)
    new_scene = scene_to_dict(new_exml_scene)
    # Then convert the original scene file...
    orig_exml_scene = convert_file(CRYSTAL_PATH)
    orig_scene = scene_to_dict(orig_exml_scene)
    # Now let's compare it to the original
    assert new_scene == orig_scene
