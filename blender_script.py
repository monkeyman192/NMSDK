import bpy
import bmesh

from main import Create_Data

obj = bpy.context.scene.objects.active
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.quads_convert_to_tris()
mesh = obj.data
bm = bmesh.from_edit_mesh(mesh)

def uv_from_vert_first(uv_layer, v):
    for l in v.link_loops:
        uv_data = l[uv_layer]
        return uv_data.uv
    return None

name = obj.name
#print('name: {}'.format(obj.name))

vertices = list((v.co.x, v.co.y, v.co.z, 1) for v in mesh.vertices)

indexes = list()
uvs = list()
for poly in mesh.polygons:
    indexes.append(tuple(mesh.loops[i].vertex_index for i in range(poly.loop_start, poly.loop_start + poly.loop_total)))

uv_layer = bm.loops.layers.uv.active

uvs = list()

for v in bm.verts:
    uv_vect = uv_from_vert_first(uv_layer, v)
    uvs.append((uv_vect[0], uv_vect[1], 0, 1))
    

#print(vertices)
#print(indexes)
#print(uvs)

bpy.ops.object.mode_set(mode='OBJECT')

Create_Data(str(name),
            'TEST',
            [str(name)],
            index_stream = [indexes],
            vertex_stream = [vertices],
            uv_stream = [uvs])
