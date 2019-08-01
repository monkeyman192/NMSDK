import subprocess
import os
import os.path as op
import pytest


PLUGIN_PATH = os.getcwd()
TESTS_PATH = 'tests\\import_tests'

CRYSTAL_TEST_PATH = op.join(PLUGIN_PATH, TESTS_PATH, 'import_crystal.py')
BAD_IMPORT_TEST_PATH = op.join(PLUGIN_PATH, TESTS_PATH, 'import_bad.py')
SMALLPROPA_TEST_PATH = op.join(PLUGIN_PATH, TESTS_PATH, 'import_smallpropa.py')


def run_test(test_path):
    proc = subprocess.Popen(['blender', '-b', '-noaudio',
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


def test_import_smallpropa():
    # Test the importing of a model with animations
    run_test(SMALLPROPA_TEST_PATH)


@pytest.mark.skip(reason="Test doesn't work yet... :(")
def test_import_bad():
    # Test the importing of data that is bad and should raise errors
    run_test(BAD_IMPORT_TEST_PATH)
