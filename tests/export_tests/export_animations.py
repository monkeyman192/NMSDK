import bpy
import os.path as op
import tempfile
import struct


# TODO: This script will fail at the moment due to the calling of exporting
# from the command line not being mature enough. This will come in a future
# update.


with tempfile.TemporaryDirectory() as tempdir:
    res = bpy.ops.nmsdk.export_scene(output_directory=tempdir,
                                     export_directory='CUSTOMMODELS',
                                     group_name='ANIM_TEST',
                                     idle_anim='IDLE')
    assert res == {'FINISHED'}

    export_path = op.join(tempdir, 'CUSTOMMODELS')

    # Check the other animation also
    anim_path = op.join(export_path, 'ANIM_TEST', 'ANIMS', 'OSC.ANIM.MBIN')
    assert bpy.context.scene.nmsdk_anim_data.idle_anim == 'IDLE'
    with open(anim_path, 'rb') as f:
        f.seek(0x60)
        # The very first value in an animation file is the number of frames
        assert struct.unpack('<I', f.read(0x4))[0] == 41

    # Check some properties of the animation
    anim_path = op.join(export_path, 'ANIM_TEST', 'ANIM_TEST.ANIM.MBIN')
    assert op.exists(anim_path)
    with open(anim_path, 'rb') as f:
        f.seek(0x60)
        # The very first value in an animation file is the number of frames
        assert struct.unpack('<I', f.read(0x4))[0] == 151

    # Do some checks on the entity file
    entity = op.join(export_path, 'ANIM_TEST', 'ANIM_TEST', 'ENTITIES',
                     'INTERACTION.ENTITY.MBIN')
    with open(entity, 'rb') as f:
        # Read the file and jump to the start of the path of the animation file
        data = f.read()
        loc = data.find(b'cTkAnimationComponentData')
        f.seek(loc - 0x8)
        jump = struct.unpack('<I', f.read(0x4))[0]
        f.seek(jump - 0x4, 1)
        f.seek(0x138, 1)
        jump = struct.unpack('<I', f.read(0x4))[0]
        f.seek(jump - 0x4, 1)
        f.seek(0x10, 1)
        assert f.read(0xC) == b'CUSTOMMODELS'
