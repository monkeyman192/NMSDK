# stdlib imports
import ctypes
import os
import os.path as op
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

# Blender imports
import bpy
from hgpaktool import HGPAKFile
from hgpaktool.utils import normalise_path

ctypes.windll.kernel32.SetFileAttributesW.argtypes = (ctypes.c_wchar_p, ctypes.c_uint32)


@contextmanager
def load_file(fpath: Union[str, os.PathLike[str]], root_dir: str, from_pak: bool, pak_data: dict):
    fpath = normalise_path(fpath)
    if from_pak:
        if (pakfile_path := pak_data.get(fpath)) is not None:
            if not op.isabs(pakfile_path):
                pakfile_path = op.join(root_dir, pakfile_path)
            # with HGPAKFile(pakfile_path) as pak:
                # for _, fdata in pak.extract(fpath):
                #     print(len(fdata))
                #     yield BytesIO(fdata)
            pak = HGPAKFile(pakfile_path)
            data = pak.extract_specific(fpath, True)
            data.seek(0)
            yield data
        else:
            raise ValueError(f"Could not find {fpath!r} in pak index...")
    else:
        if op.isabs(fpath):
            with open(fpath, "rb") as f:
                yield f
        else:
            with open(op.join(root_dir, fpath), "rb") as f:
                yield f


def load_file_unsafe(fpath: Union[str, os.PathLike[str]], root_dir: str, from_pak: bool, pak_data: dict):
    # Same as the above function, but without any potential clean up.
    # When loading from a pak file this is fine, but for loading from a disk it is not and we need to be
    # careful...
    fpath = normalise_path(fpath)
    if from_pak:
        if (pakfile_path := pak_data.get(fpath)) is not None:
            if not op.isabs(pakfile_path):
                pakfile_path = op.join(root_dir, pakfile_path)
            pak = HGPAKFile(pakfile_path)
            return pak.extract_specific(fpath, True)
        else:
            raise ValueError(f"Could not find {fpath!r} in pak index...")
    else:
        if op.isabs(fpath):
            return open(fpath, "rb")
        else:
            return open(op.join(root_dir, fpath), "rb")


def hide_path(fpath: str):
    FILE_ATTRIBUTE_HIDDEN = 0x02

    ret = ctypes.windll.kernel32.SetFileAttributesW(fpath, FILE_ATTRIBUTE_HIDDEN)
    if ret:
        print('attribute set to Hidden')
    else:  # return code of zero indicates failure -- raise a Windows error
        raise ctypes.WinError()


def is_subdir(path: str, root: str):
    """ Check to see if `path` stems from `root`."""
    path = os.path.realpath(path)
    root = os.path.realpath(root)

    if op.splitdrive(path)[0] != op.splitdrive(root)[0]:
        return False

    relative = os.path.relpath(path, root)

    if relative.startswith(os.pardir):
        return False
    else:
        return True


def get_NMS_dir(fpath: Optional[str]) -> Optional[str]:
    """ Returns the NMS file directory from the given filepath. """
    if not fpath:
        return None
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
    a_parts = list(Path(abs_path.lower()).parts)
    r_parts = Path(rel_path.lower()).parts
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


def post_path(full_path: str, base_path: str):
    """ Return the part of `full_path` after the `base_part` component."""
    if not is_subdir(full_path, base_path):
        return None
    f_parts = list(Path(full_path.lower()).parts)
    b_parts = Path(base_path.lower()).parts
    return str(Path(*f_parts[len(b_parts):]))


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
    """ Convert an mbin or mxml file to an mxml or mbin file and return the
    path of the produced file.
    """
    exts = {'.MBIN': '.MXML', '.MXML': '.MBIN'}
    mbincompiler_path = bpy.context.scene.nmsdk_default_settings.MBINCompiler_path  # noqa
    retcode = subprocess.call(
        [mbincompiler_path, "-y", "-f", "-Q", fpath])
    if retcode == 0:
        _path, _ext = op.splitext(fpath)
        return _path + exts[_ext.upper()]
    else:
        raise ValueError('Provided file cannot be processed by MBINCompiler')
