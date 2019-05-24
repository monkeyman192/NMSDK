#!/usr/bin/env bash
# Read the version of NMSDK from .__init__.py

# First, get just the line with the version in it
ver_line=$(grep 'version' ./__init__.py)
# Then split it to get just the numbers
numbers=$(echo "$ver_line" | grep -o -E '[0-9]+')

# Function c/o https://stackoverflow.com/a/17841619
function join_by { local IFS="$1"; shift; echo "$*"; }

# Finally, join the numbers together with a '.'
ver_str=$(join_by . $numbers)

# Return the version
echo "v$ver_str"