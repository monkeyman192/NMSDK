import bpy
import os.path as op
import tempfile
import struct


with tempfile.TemporaryDirectory() as tempdir:
    export_path = op.join(tempdir, 'CUSTOMMODELS')
    res = bpy.ops.export_mesh.nms(export_directory=export_path,
                                  group_name='ANIM_TEST',
                                  idle_anim='IDLE')
    assert res == {'FINISHED'}
    # Check some properties of the animation
    anim_path = op.join(export_path, 'ANIM_TEST', 'ANIM_TEST.ANIM.MBIN')
    assert op.exists(anim_path)
    with open(anim_path, 'rb') as f:
        f.seek(0x60)
        # The very first value in an animation file is the number of frames
        assert struct.unpack('<I', f.read(0x4))[0] == 151
