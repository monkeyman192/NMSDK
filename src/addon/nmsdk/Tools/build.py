#!/usr/bin/env python

# Zip the current source files as a blender addon

import os
import shutil
import tempfile

COPYFILES = ['BlenderExtensions', 'ModelExporter', 'ModelImporter',
             'NMS', 'serialization', 'utils', '__init__.py', 'NMSDK.py']


nmsdk_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
zip_dst = os.path.join(nmsdk_path, 'build', 'nmsdk')

with tempfile.TemporaryDirectory() as tempdir:
    nmsdk_src = os.path.join(tempdir, 'nmsdk')
    os.mkdir(nmsdk_src)
    os.mkdir(os.path.join(nmsdk_path, 'build'))
    for fname in COPYFILES:
        src = os.path.join(nmsdk_path, fname)
        dst = os.path.join(nmsdk_src, fname)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)
    shutil.make_archive(zip_dst, 'zip', tempdir)
