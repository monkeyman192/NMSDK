#!/bin/bash

BLENDER=$( reg query "HKEY_CLASSES_ROOT\blendfile\shell\open\command" | grep 'blender' | cut -d '"' -f2 )
PYTHON=$( "$BLENDER" -b --disable-autoexec -noaudio --factory-startup --python-expr "import bpy; import sys; print(bpy.app.binary_path_python, file=sys.stderr)" 3>&1 1>/dev/null 2>&3 )

TESTS="";
LOGGING="";

while getopts "p:b:hl" opt "${EXTRAS[@]}"; do
    case $opt in
        b)
            PYTHON="$OPTARG";
            ;;
        p)
            BLENDER="$OPTARG";
            ;;
        h)
            echo -e "NMSDK test usage instructions:\n";
            echo "ARGUMENTS:";
            echo "-b <blender path> (optional, defaults to what opens your .blend files)"
            echo -e "\tThe relative or absolute path to the blender executable.";
            echo "-p <python path> (optional, defaults to the Python configured in Blender)"
            echo -e "\tThe relative or absolute path to the python executable.";
            echo -e "\tThis should be the executable that blender executable provided by -b uses.";
            echo "-l"
            echo -e "\tLog the stdout and stderr of the tests run."
            echo "-h";
            echo -e "\tDisplay this help message.";
            echo -e "Any further arguments are passed to pytest.\n";
            echo "To run a specific test, pass the path to the test, remembering that if you want to run a sub-test, it must be run as follows:";
            echo "./run_tests.sh tests/import_tests/import_test.py::test_import_crystal";
            exit 0;
            ;;
        l)
            LOGGING="--logging";
            ;;
    esac
done
shift $((OPTIND-1))

if [ "$@" ]; then
    TESTS="$@";
fi

export BLENDERPATH=$(realpath "$BLENDER");

# run the tests with the blender python
if "$PYTHON" -m pip freeze | grep 'pytest' > /dev/null 2>&1; then
    "$PYTHON" -m pytest -vv "$LOGGING" "$TESTS";
else
    "$PYTHON" -m pip install pytest;
    "$PYTHON" -m pytest -vv "$LOGGING" "$TESTS";
fi
