import os.path as op
import pytest


SELF_DIR = op.dirname(__file__)

CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_crystal.py')
MISPLACED_CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_misplaced_crystal.py')
BAD_IMPORT_TEST_PATH = op.join(SELF_DIR, 'import_bad.py')
SMALLPROPA_TEST_PATH = op.join(SELF_DIR, 'import_smallpropa.py')
TOYCUBE_TEST_PATH = op.join(SELF_DIR, 'import_toycube.py')
JELLY_TEST_PATH = op.join(SELF_DIR, 'import_jelly.py')


def test_import_crystal(run_test):
    # Test the importing of a model with mesh collisions
    run_test(CRYSTAL_TEST_PATH)


def test_import_misplaced_crystal(run_test):
    # Test the importing of a crystal model which is in a different folder
    # to the rest of its data by using the PCBANKS_directory setting.
    run_test(MISPLACED_CRYSTAL_TEST_PATH)


def test_import_smallpropa(run_test):
    # Test the importing of a model with animations
    run_test(SMALLPROPA_TEST_PATH)


def test_import_jelly(run_test):
    # Test the importing of a model with animated bones
    run_test(JELLY_TEST_PATH)


def test_import_toycube(run_test):
    # Test the importing of a model with animated bones
    run_test(TOYCUBE_TEST_PATH)


@pytest.mark.skip(reason="Test doesn't work yet... :(")
def test_import_bad(run_test):
    # Test the importing of data that is bad and should raise errors
    run_test(BAD_IMPORT_TEST_PATH)
