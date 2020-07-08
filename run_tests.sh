#!/bin/bash

# Check to see if a path for python has been provided
if [ -z "$1" ]; then
    PYTHON=../../../python/bin/python.exe;
else
    PYTHON="$1";
fi

# Check to see if a path for Blender has been provided
if [ -z "$2" ]; then
    BLENDER=../../../../blender.exe;
else
    BLENDER="$2";
fi

export BLENDERPATH=$(realpath $BLENDER);
echo $BLENDERPATH;

# run the tests with the blender python
if $PYTHON -m pip freeze | grep 'pytest' > /dev/null 2>&1; then
    $PYTHON -m pytest -vv;
else
    $PYTHON -m pip install pytest;
    $PYTHON -m pytest -vv;
fi
