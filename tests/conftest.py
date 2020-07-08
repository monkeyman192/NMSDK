import os
import pytest
import subprocess


# TODO: create a fixture which uses the pytest fixture (?) or property which
# gets the path of the executed test file so that only the name of the test
# file needs to be provided.

# TODO: pytest has a builtin `capsys` fixture which may be useful...
# https://docs.pytest.org/en/stable/reference.html#std:fixture-capsys

@pytest.fixture
def run_test():
    """ A fixture that is used to run each test by calling some python code
    from blender. """
    def _run_test(test_path: list, blend_path=None):
        _blender_path = os.environ.get('BLENDERPATH')
        if _blender_path:
            cmd = [_blender_path, '-b', '-noaudio']
            if blend_path:
                cmd.append(blend_path)
            cmd.extend(['--python', test_path])
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        else:
            pytest.fail("No blender path provided")
        # Capture the stderr
        _, stderr = proc.communicate()
        # Ensure that there were no errors
        assert stderr.decode() == ''
    return _run_test
