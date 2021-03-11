# Convert images to .DDS
# This uses the Texconv application created by Microsoft.
# The source code and download links can be found here:
# https://github.com/microsoft/DirectXTex
#
# Version included in this tool: January 9, 2021 Release:
# https://github.com/microsoft/DirectXTex/releases/tag/jan2021
import math
import os.path as op
import subprocess

FORMATS = {
    'diffuse': 'BC1_UNORM',
    'masks': 'BC3_UNORM',
    'normal': 'BC5_UNORM'
}

TEXCONV_PATH = op.join(op.dirname(__file__), 'DirectXTex', 'texconv.exe')
CONVERT_COMAMND = [TEXCONV_PATH, '-y', '-m', '13', '-f']


def convert_image(fpath, type_, size):
    """ Take an image and convert it to .DDS. """
    # We can only generate as many mip maps as the image will allow based on
    # size.
    out_fpath = op.splitext(fpath)[0] + '.DDS'
    mips = math.floor(math.log(min(size), 2))
    CONVERT_COMAMND[2] = str(mips)
    command = CONVERT_COMAMND + [FORMATS[type_], fpath, '-o',
                                 op.dirname(out_fpath)]
    subprocess.call(command)
    if op.exists(out_fpath):
        return out_fpath
    else:
        raise FileNotFoundError
