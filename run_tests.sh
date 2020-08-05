#!/bin/bash

PYTHON=../../../python/bin/python.exe;
BLENDER=../../../../blender.exe;
TESTS="";

while getopts "p:b:h" opt "${EXTRAS[@]}"; do
    case $opt in
        b)
            PYTHON="$OPTARG";
            ;;
        p)
            BLENDER="$OPTARG"
            ;;
        h)
            echo -e "NMSDK test usage instructions:\n";
            echo "ARGUMENTS:";
            echo "-b <blender path> (optional, defaults to '.../../../../blender.exe')";
            echo -e "\tThe relative or absolue path to the blender executable.";
            echo "-p <python path> (optional, defaults to '../../../python/bin/python.exe')";
            echo -e "\tThe relative or absolute path to the python executable.";
            echo -e "\tThis should be the executable that blender executable provided by -b uses.";
            echo "-h";
            echo -e "\tDisplay this help message.";
            echo -e "Any further arguments are passed to pytest.\n";
            echo "To run a specific test, pass the path to the test, remembering that if you want to run a sub-test, it must be run as follows:";
            echo "./run_tests.sh tests/import_tests/import_test.py::test_import_crystal";
            exit 0;
    esac
done
shift $((OPTIND-1))

if [ "$@" ]; then
    TESTS="$@";
fi

export BLENDERPATH=$(realpath $BLENDER);

# run the tests with the blender python
if $PYTHON -m pip freeze | grep 'pytest' > /dev/null 2>&1; then
    $PYTHON -m pytest -vv "$TESTS";
else
    $PYTHON -m pip install pytest;
    $PYTHON -m pytest -vv "$TESTS";
fi
