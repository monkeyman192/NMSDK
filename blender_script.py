import bpy
import bmesh
import os
import sys
from math import radians
from mathutils import Matrix,Vector

# Add script path to sys.path
scriptpath = bpy.context.space_data.text.filepath
dir = os.path.dirname(scriptpath)
print(dir)

if not dir in sys.path:
    sys.path.append(dir )
    #print(sys.path)

from main import Create_Data


scn = bpy.context.scene

icounter = 0
vcounter = 0
vertices = []
normals  = [] 
indices  = []
uvs      = []
tangents = []

objects  = []


for ob in scn.objects:
    if not ob.name.startswith('NMS'):
        continue
    
    print('Located Object for export', ob.name)
    objects.append(ob.name.upper())
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    
    # Matrices
    object_matrix_wrld = ob.matrix_world
    rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
    scale_mat = Matrix.Scale(1, 4)
    norm_mat = ob.matrix_world.inverted().transposed()
    
    uvcount = len(bm.loops.layers.uv)
    colcount = len(bm.loops.layers.color)
    
    # Store Positions into list
    verts = []
    norms = []
    vcount = len(bm.verts)
    icount = 3 * len(bm.faces) # Assume triangulated mesh
    for v in bm.verts:
        co = scale_mat * rot_x_mat * object_matrix_wrld * v.co
        norm = scale_mat * rot_x_mat * norm_mat * v.normal
        verts.append((round(co.x,5), round(co.y,5), round(co.z,5), 1))
        norms.append(tuple(norm))
        
    #Store uvs into List
    luvs = []
    #Init at first
    for v in range(vcount):
        luvs.append((0.0, 0.0, 0.0, 0.0))
    
    #Store uvs this time
    for f in bm.faces:
        for l in f.loops:
            vid = l.vert.index  # Get vertex index
            # get only the first layer
            layer = bm.loops.layers.uv[0]
            u = l[layer].uv.x
            v = 1. - l[layer].uv.y
            luvs[vid] = (round(u,5), round(v,5), 0.0, 0.0)
    
    # I should add code for the tangent calculations
    # Leaving it for now
    
    vcounter += vcount    # Increasing the offset counter
    
    #Storing Indices
    bm.faces.ensure_lookup_table()
    faces = []
    for f in bm.faces:
        faces.append((icounter + f.verts[0].index,
                        icounter + f.verts[1].index,
                        icounter + f.verts[2].index))
        #indices.append((0,1,2))
        
        #print(len(f.verts), vertices[f.verts[0].index],
        #      vertices[f.verts[1].index],
        #      vertices[f.verts[2].index])
        
        #indices.append(icounter + f.verts[1].index)
        #indices.append(icounter + f.verts[2].index)
    
    #Final Storage
    vertices.append(verts)
    normals.append(norms)
    uvs.append(luvs)
    indices.append(faces)
    icounter += icount


Create_Data('SUZANNE',
            r"J:\Installs\Steam\steamapps\common\No Man's Sky\GAMEDATA\PCBANKS\TEST",
            objects,
            index_stream = indices,
            vertex_stream = vertices,
            uv_stream = uvs
            )
