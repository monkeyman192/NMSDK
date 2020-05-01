#!/bin/bash

PYTHON=../../../python/bin/python.exe

# run the tests with the blender python
if $PYTHON -m pip freeze | grep 'pytest' > /dev/null 2>&1; then
    $PYTHON ./run_tests.py;
else
    $PYTHON -m pip install pytest;
    $PYTHON ./run_tests.py;
fi
