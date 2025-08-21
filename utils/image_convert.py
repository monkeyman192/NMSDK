# Convert images to .DDS
# This uses the Texconv application created by Microsoft.
# The source code and download links can be found here:
# https://github.com/microsoft/DirectXTex
#
# Version included in this tool: January 9, 2021 Release:
# https://github.com/microsoft/DirectXTex/releases/tag/jan2021
import math
import os
import os.path as op
import shutil
import subprocess

FORMATS = {
    'diffuse': 'BC1_UNORM',
    'masks': 'BC3_UNORM',
    'normal': 'BC5_UNORM'
}

TEXCONV_PATH = op.join(op.dirname(__file__), 'DirectXTex', 'texconv.exe')
CONVERT_COMAMND = [TEXCONV_PATH, '-y', '-m', '13', '-f']


def upper_name_exists(fpath: str) -> bool:
    """ Determine if the upper-case version of the provided fpath exists. """
    dir_, fname = op.split(fpath)
    return fname.upper() in os.listdir(dir_)


def convert_image(fpath: str, out_fpath: str, type_: str, size: tuple) -> str:
    """ Take an image and convert it to .DDS. """
    # We can only generate as many mip maps as the image will allow based on
    # size.
    if min(size) == 0:
        # There is an issue with reading the dimensions... raise an error
        raise ValueError(f'Cannot determine dimensions of {fpath}. '
                         'Please check the image is valid in blender.')
    mips = math.floor(math.log(min(size), 2))
    CONVERT_COMAMND[2] = str(mips)
    command = CONVERT_COMAMND + [FORMATS[type_], fpath, '-o',
                                 op.dirname(out_fpath)]
    subprocess.call(command)
    if not upper_name_exists(out_fpath):
        # In this case the actual filename may be different. Move the converted
        # file to have this new file name.
        # If the file is deemed to exist by windows then moving it to have a
        # different case will fail to do anything. We instead need to rename it
        # then rename it back with the changed case.
        if not op.exists(out_fpath):
            # In this case the file doesn't exist at all, so we can do the
            # simple move.
            shutil.move(
                op.join(op.dirname(out_fpath),
                        op.splitext(op.basename(fpath))[0]).upper() + '.DDS',
                out_fpath)
        else:
            # Rename to some dummy name then back.
            shutil.move(
                op.join(op.dirname(out_fpath),
                        op.splitext(op.basename(fpath))[0]).upper() + '.DDS',
                out_fpath + '.DUMMY')
            shutil.move(out_fpath + '.DUMMY', out_fpath)
    return out_fpath
