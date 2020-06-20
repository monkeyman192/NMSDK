import bpy
import os.path as op


# The NMS game data to test the importing with is in the main test folder.
TEST_DATA_PATH = op.join(op.dirname(__file__), '..', 'NMS_DATA')
PROP_BASE_PATH = 'MODELS\\PLANETS\\BIOMES\\COMMON\\BUILDINGS\\PROPS\\SMALLPROPS'  # noqa
PROP_PATH = op.join(TEST_DATA_PATH,
                    PROP_BASE_PATH,
                    'SMALLPROPA.SCENE.MBIN')


# First, try import the scene without any animations
res = bpy.ops.nmsdk.import_scene(path=PROP_PATH, max_anims=0)
assert res == {'FINISHED'}
assert len(bpy.data.actions) == 0

# Now, try import with animations
res = bpy.ops.nmsdk.import_scene(path=PROP_PATH)
# First, make sure that it ran
assert res == {'FINISHED'}
# Make sure that there is only one animation loaded
anim_data = bpy.context.scene.nmsdk_anim_data.loaded_anims
assert len(anim_data) == 2  # include 'None'
assert 'IDLE' in anim_data
# Check that this animation has the right number of frames
for action in bpy.data.actions:
    assert int(action.frame_range[1]) == 220
