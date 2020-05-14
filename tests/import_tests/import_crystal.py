import bpy
import os.path as op


# Path is relative to the plugin directory
TEST_DATA_PATH = op.join(op.dirname(__file__), 'data')
CRYSTAL_BASE_PATH = 'MODELS\\PLANETS\\BIOMES\\COMMON\\CRYSTALS\\LARGE'
CRYSTAL_PATH = op.join(TEST_DATA_PATH,
                       CRYSTAL_BASE_PATH,
                       'CRYSTAL_LARGE.SCENE.MBIN')


res = bpy.ops.nmsdk.import_scene(path=CRYSTAL_PATH)
# First, make sure that it ran
assert res == {'FINISHED'}
# Then, we can check that some values of the scene are correct...
assert 'CRYSTAL_LARGE.SCENE' in bpy.data.objects
# Assign this now and we'll come back to it later...
crystal_scene = bpy.data.objects['CRYSTAL_LARGE.SCENE']
assert '_Crystal_A' in bpy.data.objects
crystal_ob = bpy.data.objects['_Crystal_A']
assert len(crystal_ob.data.vertices) == 852
# Check that the mesh collision is loaded correctly
assert op.join(CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE_COLL') in bpy.data.objects
mesh_coll_ob = bpy.data.objects[op.join(CRYSTAL_BASE_PATH,
                                        'CRYSTAL_LARGE_COLL')]
# Let's make sure that the ability to toggle collisions' visibility works
assert bpy.ops.nmsdk._toggle_collision_visibility()
# Now, check that the collision mesh has the right number of verts
assert len(mesh_coll_ob.data.vertices) == 32
# check that some custom properties have been loaded correctly
assert crystal_scene.NMSNode_props.node_types == 'Reference'
assert crystal_scene.NMSReference_props.reference_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE.SCENE.MBIN')
assert crystal_ob.NMSNode_props.node_types == 'Mesh'
assert crystal_ob.NMSMesh_props.material_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE\\CRYSTAL_LARGE.MATERIAL.MBIN')
assert crystal_ob.NMSEntity_props.name_or_path == op.join(
    CRYSTAL_BASE_PATH, 'CRYSTAL_LARGE\\ENTITIES\\CRYSTAL_LARGE.ENTITY.MBIN')
