import subprocess
import os.path as op


SELF_DIR = op.dirname(__file__)
BLENDER_PATH = op.realpath(op.join(SELF_DIR, '../../../../../../blender.exe'))

ANIM_TEST_PATH = op.join(SELF_DIR, 'export_animations.py')


def run_test(test_path, test_blend):
    proc = subprocess.Popen([BLENDER_PATH, '-b', '-noaudio', test_blend,
                             '--python', test_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # Capture the stderr
    _, stderr = proc.communicate()
    # Ensure that there were no errors
    assert stderr.decode() == ''


def test_export_animation():
    # Test the importing of a model with mesh collisions
    run_test(ANIM_TEST_PATH, op.join(SELF_DIR, 'anim_export_test.blend'))
