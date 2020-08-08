import os
import sys
import subprocess
import pytest


# TODO: create a fixture which uses the pytest fixture (?) or property which
# gets the path of the executed test file so that only the name of the test
# file needs to be provided.


def pytest_addoption(parser):
    parser.addoption("--logging", action="store_true", default=False,
                     help="Whether to log the stdout/stderr.")


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    if 'logging' in metafunc.fixturenames:
        metafunc.parametrize("logging", [metafunc.config.getoption('logging')])


@pytest.fixture
def run_test(logging):
    """ A fixture that is used to run each test by calling some python code
    from blender. """
    def _run_test(test_path: list, blend_path: str = None,
                  req_stderr: str = ""):
        """
        Parameters
        ----------
        test_path:
            The absolute path the the test.
        blender_path:
            The absolute path to the blender exe running the tests.
        req_stderr:
            A string or list of strings that are to match the stderr.
        """
        if os.path.basename(sys.executable) == 'blender.exe':
            _blender_path = sys.executable
        else:
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
        stdout, stderr = proc.communicate()
        # If we want to log the stdout and stderr, do so.
        if logging:
            with open('std.out', 'w') as so:
                so.write(stdout.decode())
            with open('std.err', 'w') as se:
                se.write(stderr.decode())
        # Ensure that there were no errors
        assert stderr.decode() == req_stderr
    return _run_test
