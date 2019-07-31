import bpy
import os
import os.path as op


# Path is relative to the plugin directory
TEST_DATA_PATH = 'tests\\import_tests\\data'
PROP_BASE_PATH = 'MODELS\\PLANETS\\BIOMES\\COMMON\\BUILDINGS\\PROPS\\SMALLPROPS'  # noqa
PROP_PATH = op.join(TEST_DATA_PATH,
                    PROP_BASE_PATH,
                    'SMALLPROPA.SCENE.MBIN')


res = bpy.ops.nmsdk.import_scene(path=op.join(os.getcwd(), PROP_PATH))
# First, make sure that it ran
assert res == {'FINISHED'}
