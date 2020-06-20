import bpy
import os.path as op


# The NMS game data to test the importing with is in the main test folder.
TEST_DATA_PATH = op.join(op.dirname(__file__), '..', 'NMS_DATA')
CUBE_BASE_PATH = ('MODELS\\PLANETS\\BIOMES\\COMMON\\BUILDINGS\\PARTS\\'
                  'BUILDABLEPARTS\\DECORATION')
CUBE_PATH = op.join(TEST_DATA_PATH,
                    CUBE_BASE_PATH,
                    'TOY_CUBE.SCENE.MBIN')


# First, try import the scene without any animations
res = bpy.ops.nmsdk.import_scene(path=CUBE_PATH, max_anims=0,
                                 import_bones=True)
assert res == {'FINISHED'}
assert len(bpy.data.actions) == 0

# Now, try import with animations
res = bpy.ops.nmsdk.import_scene(path=CUBE_PATH, import_bones=True)
# First, make sure that it ran
assert res == {'FINISHED'}
# Check the animation data
anim_data = bpy.context.scene.nmsdk_anim_data.loaded_anims
# assert len(anim_data) == 1
assert 'IDLE' in anim_data
# Check that this animation has the right number of frames
# for action in bpy.data.actions:
#    assert int(action.frame_range[1]) == 220
