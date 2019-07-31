import subprocess


CRYSTAL_TEST_PATH = "C:\\Program Files\\Blender Foundation\\Blender\\2.79\\scripts\\addons\\nmsdk\\tests\\import_tests\\import_crystal.py"  # noqa


def test_import_crystal():
    proc = subprocess.Popen(['blender', '-b', '-noaudio',
                             '--python', CRYSTAL_TEST_PATH],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # Capture the stderr
    _, stderr = proc.communicate()
    # Ensure that there were no errors
    assert stderr.decode() == ''
