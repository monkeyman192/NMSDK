import subprocess


CRYSTAL_TEST_PATH = "C:\\Program Files\\Blender Foundation\\Blender\\2.79\\scripts\\addons\\nmsdk\\tests\\import_tests\\import_crystal.py"  # noqa


def test_import_crystal():
    proc = subprocess.Popen(['blender', '-b', '-noaudio',
                             '--python', CRYSTAL_TEST_PATH], shell=True)
    proc.wait()
    assert proc.returncode == 0
