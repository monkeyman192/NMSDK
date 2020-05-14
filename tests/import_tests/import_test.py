import subprocess
import os.path as op
import pytest


SELF_DIR = op.dirname(__file__)
BLENDER_PATH = op.realpath(op.join(SELF_DIR, '../../../../../../blender.exe'))

CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_crystal.py')
MISPLACED_CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_misplaced_crystal.py')
BAD_IMPORT_TEST_PATH = op.join(SELF_DIR, 'import_bad.py')
SMALLPROPA_TEST_PATH = op.join(SELF_DIR, 'import_smallpropa.py')


def run_test(test_path):
    proc = subprocess.Popen([BLENDER_PATH, '-b', '-noaudio',
                             '--python', test_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # Capture the stderr
    _, stderr = proc.communicate()
    # Ensure that there were no errors
    assert stderr.decode() == ''


def test_import_crystal():
    # Test the importing of a model with mesh collisions
    run_test(CRYSTAL_TEST_PATH)


def test_import_misplaced_crystal():
    # Test the importing of a crystal model which is in a different folder
    # to the rest of its data by using the PCBANKS_directory setting.
    run_test(MISPLACED_CRYSTAL_TEST_PATH)


def test_import_smallpropa():
    # Test the importing of a model with animations
    run_test(SMALLPROPA_TEST_PATH)


@pytest.mark.skip(reason="Test doesn't work yet... :(")
def test_import_bad():
    # Test the importing of data that is bad and should raise errors
    run_test(BAD_IMPORT_TEST_PATH)
