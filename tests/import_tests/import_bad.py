""" Tests for import functionality. """
import bpy
import pytest


""" THIS TEST DOESN'T WORK RIGHT NOW..."""


with pytest.raises(FileNotFoundError):
    res = bpy.ops.nmsdk.import_scene(path='fake_file.mbin')

with pytest.raises(TypeError):
    res = bpy.ops.nmsdk.import_scene(path='fake_file')
