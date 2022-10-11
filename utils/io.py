# stdlib imports
import os
import os.path as op
from pathlib import Path
import subprocess

# Blender imports
import bpy


def get_NMS_dir(fpath: str) -> str:
    """ Returns the NMS file directory from the given filepath. """
    # If a PCBANKS path is specified in the scene, return it instead.
    if bpy.context.scene.nmsdk_default_settings.PCBANKS_directory != "":
        return bpy.context.scene.nmsdk_default_settings.PCBANKS_directory
    # Otherwise, determine as normal
    path = Path(fpath)
    parts = path.parts
    try:
        PCBANKS_path = str(Path(*parts[:parts.index('MODELS')]))
        bpy.context.scene.nmsdk_default_settings.PCBANKS_directory = PCBANKS_path  # noqa
        return PCBANKS_path
    except ValueError:
        # In this case we may be loading a model in a custom folder.
        # We need to go back until we find a folder with a 'MODELS' folder in
        # it.
        for parent in path.parents:
            if Path(parent, 'MODELS').exists():
                # Cache the PCBANKS folder
                bpy.context.scene.nmsdk_default_settings.PCBANKS_directory = str(parent)  # noqa
                return str(parent)


def get_MBINCompiler_path() -> str:
    """ Return the location of the MBINCompiler exe if it is registered on the
    path. """
    _path = ''
    for p in os.environ['PATH'].split(';'):
        test_path = op.join(p, 'MBINCompiler.exe')
        if op.exists(test_path):
            _path = test_path
            break
    return _path


def base_path(abs_path: str, rel_path: str):
    """ Return the base path that the rel_path is contained in the abs_path
    For example, if abs_path is a/b/c/d, and rel_path is c/d, then this will
    return a/b
    """
    a_parts = list(Path(abs_path).parts)
    r_parts = Path(rel_path).parts
    for part in r_parts[::-1]:
        if a_parts[-1] == part:
            a_parts.pop(-1)
        else:
            raise ValueError(f"{rel_path} doesn't stem from {abs_path}")
    if a_parts:
        return op.join(*a_parts)
    else:
        print(f'There may be an issue with the paths: {abs_path}, {rel_path}')
        return ''


def realize_path(fpath: str, local_root_directory: str) -> str:
    """ Return the provided path relativized to the PCBANKS folder or the local
    root directory if it exists. """
    local_path = op.join(local_root_directory, fpath)
    if op.exists(local_path):
        return local_path
    # Get the NMS directory. This has to have been initialized already
    base = get_NMS_dir("")
    if base == "":
        raise ValueError
    try:
        return op.join(base, fpath)
    except ValueError:
        return None


def convert_file(fpath: str) -> str:
    """ Convert an mbin or exml file to an exml or mbin file and return the
    path of the produced file.
    """
    exts = {'.MBIN': '.EXML', '.EXML': '.MBIN'}
    mbincompiler_path = bpy.context.scene.nmsdk_default_settings.MBINCompiler_path  # noqa
    retcode = subprocess.call(
        [mbincompiler_path, "-y", "-f", "-Q", fpath])
    if retcode == 0:
        _path, _ext = op.splitext(fpath)
        return _path + exts[_ext.upper()]
    else:
        raise ValueError('Provided file cannot be processed by MBINCompiler')
