import subprocess
import os.path as op


SELF_DIR = op.dirname(__file__)
# The blender files we will be exporting are in `tests/blender_files`
BLENDER_FILES_PATH = op.join(SELF_DIR, '..', 'blender_files')
BLENDER_PATH = op.realpath(op.join(SELF_DIR, '../../../../../../blender.exe'))

CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_export_crystal.py')


def run_test(test_path):
    proc = subprocess.Popen([BLENDER_PATH, '-b', '-noaudio',
                             '--python', test_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # Capture the stderr
    _, stderr = proc.communicate()
    # Ensure that there were no errors
    assert stderr.decode() == ''


def test_import_export_crystal():
    # Test the importing the exporting of a model with mesh collisions
    run_test(CRYSTAL_TEST_PATH)
