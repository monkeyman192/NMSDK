import os.path as op


SELF_DIR = op.dirname(__file__)
# The blender files we will be exporting are in `tests/blender_files`
BLENDER_FILES_PATH = op.join(SELF_DIR, '..', 'blender_files')

ANIM_TEST_PATH = op.join(SELF_DIR, 'export_animations.py')


def test_export_animation(run_test):
    # Test the importing of a model with mesh collisions
    run_test(ANIM_TEST_PATH, op.join(BLENDER_FILES_PATH,
                                     'anim_export_test.blend'))
