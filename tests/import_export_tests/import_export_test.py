import os.path as op


SELF_DIR = op.dirname(__file__)

CRYSTAL_TEST_PATH = op.join(SELF_DIR, 'import_export_crystal.py')


def test_import_export_crystal(run_test):
    # Test the importing the exporting of a model with mesh collisions
    run_test(CRYSTAL_TEST_PATH)
