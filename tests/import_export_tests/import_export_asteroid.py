import os.path as op
import tempfile
import sys
import pprint

# Blender imports
import bpy
from mathutils import Matrix, Vector

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
ASTEROID_BASE_PATH = 'MODELS\\SPACE\\ASTEROIDS'
ASTEROID_PATH = op.join(TEST_DATA_PATH,
                        ASTEROID_BASE_PATH,
                        'ASTEROIDXL.SCENE.MBIN')

# FIRST - we import the scene into blender...

res = bpy.ops.nmsdk.import_scene(path=ASTEROID_PATH)
# Get the root object
root_scene = bpy.data.objects['ASTEROIDXL.SCENE']
assert root_scene.NMSReference_props.has_lods is True
assert list(root_scene.NMSReference_props.lod_levels) == [500, 1000, 2500]
# Let's modify the value to make sure it's in the exported data
root_scene.NMSReference_props.lod_levels[0] = 750.25
root_scene.NMSReference_props.lod_levels[1] = 1250
root_scene.NMSReference_props.lod_levels[2] = 3000

# Let's change the shape of one of the nodes too
obj = bpy.data.objects['_Asteroid_07']
obj.matrix_local = obj.matrix_local @ Matrix.Scale(0.5, 4, Vector((0, 1, 0)))

# SECOND - check the exported data
with tempfile.TemporaryDirectory() as tempdir:
    res = bpy.ops.nmsdk.export_scene(output_directory=tempdir,
                                     preserve_node_info=True)
    assert res == {'FINISHED'}

    export_path = op.join(tempdir, 'CUSTOMMODELS')
    out_path = op.join(tempdir, ASTEROID_BASE_PATH, 'ASTEROIDXL.SCENE.MBIN')
    # Let's ensure it exists
    assert op.exists(out_path)
    # Now, let's have a look at the scene and check that it matches the
    # original one (other than where modified)
    # First we need to convert it to an exml file...
    new_exml_scene = convert_file(out_path)
    new_scene = scene_to_dict(new_exml_scene)
    # Let's check to see if the new LOD values are there
    assert float(new_scene['Attributes'][1]['Value']) == 750.25
    assert float(new_scene['Attributes'][2]['Value']) == 1250
    assert float(new_scene['Attributes'][3]['Value']) == 3000
    # We should also have the number of LOD's as 4
    assert int(new_scene['Attributes'][4]['Value']) == 4
    # remove this data to ensure it isn't in the comparison
    del new_scene['Attributes'][1:4]
    # Check to see that the _Asteroid_07 node has been scaled correctly
    assert float(new_scene['Children'][0]['Transform']['ScaleY']) == 0.5
    # And then remove it from the comparison
    del new_scene['Children'][0]['Transform']['ScaleY']
    # Then convert the original scene file...
    orig_exml_scene = convert_file(ASTEROID_PATH)
    orig_scene = scene_to_dict(orig_exml_scene)
    # Delete the modified values from this scene too.
    del orig_scene['Attributes'][1:4]
    del orig_scene['Children'][0]['Transform']['ScaleY']
    # Now let's compare it to the original
    assert new_scene == orig_scene
