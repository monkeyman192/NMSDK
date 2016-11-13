import bpy
import bmesh
import os
import sys
from math import radians
from mathutils import Matrix,Vector

# Add script path to sys.path
#scriptpath = bpy.context.space_data.text.filepath
scriptpath = "J:\\Projects\\NMS_Model_Importer\\blender_script.py"
dir = os.path.dirname(scriptpath)
proj_path = bpy.path.abspath('//')
print(dir)

if not dir in sys.path:
    sys.path.append(dir )
    #print(sys.path)

from main import Create_Data
from classes import TkMaterialData, TkMaterialFlags, TkMaterialUniform, TkMaterialSampler
from classes import List, Vector4f
from LOOKUPS import MATERIALFLAGS

scn = bpy.context.scene

icounter = 0
vcounter = 0
vertices = []
normals  = [] 
indices  = []
uvs      = []
tangents = []

objects  = []
materials = []
material_dict = {}
material_ids = []

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
        #Handle quad
        if (len(f.verts) == 4):
            faces.append((f.verts[0].index, f.verts[1].index, f.verts[2].index))
            faces.append((f.verts[0].index, f.verts[2].index, f.verts[3].index))
        #Triangle
        else:
            faces.append((f.verts[0].index, f.verts[1].index, f.verts[2].index))
    
    
    
    #Get Material stuff
    try:
        slot = ob.material_slots[0]
        mat = slot.material
        print(mat.name)
        #CHeck if material exists
        if (mat.name in material_dict):
            material_ids.append(material_dict[mat.name])
        else:
            #Create the material
            matflags = List()
            matsamplers = List()
            matuniforms = List()
            
            tslots = mat.texture_slots
            
            #Fetch Uniforms
            matuniforms.append(TkMaterialUniform(Name="gMaterialColourVec4",
                                                 Values=Vector4f(x=mat.diffuse_color.r,
                                                                 y=mat.diffuse_color.g,
                                                                 z=mat.diffuse_color.b,
                                                                 t=1.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialParamsVec4",
                                                 Values=Vector4f(x=0.0,
                                                                 y=0.0,
                                                                 z=0.0,
                                                                 t=0.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialSFXVec4",
                                                 Values=Vector4f(x=0.0,
                                                                 y=0.0,
                                                                 z=0.0,
                                                                 t=0.0)))
            matuniforms.append(TkMaterialUniform(Name="gMaterialSFXColVec4",
                                                 Values=Vector4f(x=0.0,
                                                                 y=0.0,
                                                                 z=0.0,
                                                                 t=0.0)))
            #Fetch Diffuse
            texpath = ""
            if tslots[0]:
                #Set _F01_DIFFUSEMAP
                matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[0]))
                #Create gDiffuseMap Sampler
                
                tex = tslots[0].texture
                #Check if there is no texture loaded
                if not tex.type=='IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)
                
                texpath = os.path.join(proj_path, tex.image.filepath[2:])
            print(texpath)
            sampl = TkMaterialSampler(Name="gDiffuseMap", Map=texpath, IsSRGB=True)
            matsamplers.append(sampl)
            
            #Fetch Mask
            texpath = ""
            if tslots[1]:
                #Set _F24_AOMAP
                matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[23]))
                #Create gMaskMap Sampler
                
                tex = tslots[1].texture
                #Check if there is no texture loaded
                if not tex.type=='IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)
                
                texpath = os.path.join(proj_path, tex.image.filepath[2:])
            
            sampl = TkMaterialSampler(Name="gMaskMap", Map=texpath, IsSRGB=False)
            matsamplers.append(sampl)
            
            #Fetch Normal Map
            texpath = ""
            if tslots[2]:
                #Set _F03_NORMALMAP
                matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[2]))
                #Create gNormalMap Sampler
                
                tex = tslots[2].texture
                #Check if there is no texture loaded
                if not tex.type=='IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)
                
                texpath = os.path.join(proj_path, tex.image.filepath[2:])
            
            sampl = TkMaterialSampler(Name="gNormalMap", Map=texpath, IsSRGB=False)
            matsamplers.append(sampl)
            
            #Create materialdata struct
            tkmatdata = TkMaterialData(Name=mat.name,
                                       Class='Opaque',
                                       Flags=matflags,
                                       Uniforms=matuniforms,
                                       Samplers=matsamplers)
            
            
            #Store the material
            material_dict[mat.name] = len(materials)
            material_ids.append(material_dict[mat.name])
            materials.append(tkmatdata)
                        
    except:
        raise Exception("Missing Material")
        
    
    #Final Storage
    vertices.append(verts)
    normals.append(norms)
    uvs.append(luvs)
    indices.append(faces)
    icounter += icount

print('Blender Script')
print('Create Data Call')
print(material_ids, len(material_ids))
print(materials)
print(len(matsamplers))
Create_Data('SUZANNE',
            "TEST",
            objects,
            index_stream = indices,
            vertex_stream = vertices,
            uv_stream = uvs,
            materials = materials,
            mat_indices = material_ids
            )
