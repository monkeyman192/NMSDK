import bpy
import bmesh
import os
import sys
from math import radians, degrees
from mathutils import Matrix,Vector

# Add script path to sys.path
#scriptpath = bpy.context.space_data.text.filepath
scriptpath = "J:\\Projects\\NMS_Model_Importer\\blender_script.py"
dir = os.path.dirname(scriptpath)
proj_path = bpy.path.abspath('//')
print('Proj Path: ', proj_path)
print(dir)

if not dir in sys.path:
    sys.path.append(dir)
    #print(sys.path)

from main import Create_Data
from classes import TkMaterialData, TkMaterialFlags, TkMaterialUniform, TkMaterialSampler, TkTransformData
from classes import List, Vector4f, Collision
from LOOKUPS import MATERIALFLAGS

scn = bpy.context.scene


#Main Mesh parser
def mesh_parser(ob):
    #Lists
    verts = []
    norms = []
    luvs = []
    faces = []
    # Matrices
    object_matrix_wrld = ob.matrix_world
    rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
    scale_mat = Matrix.Scale(1, 4)
    norm_mat = ob.matrix_world.inverted().transposed()
    
    data = ob.data
    #data.update(calc_tessface=True)  # convert ngons to tris
    data.calc_tessface()
    uvcount = len(data.uv_layers)
    colcount = len(data.vertex_colors)
    id = 0
    for f in data.tessfaces:  # indices
        if len(f.vertices) == 4:
            faces.append((id, id + 1, id + 2))
            faces.append((id + 3, id, id + 2))
            id += 4
        else:
            faces.append((id, id + 1, id + 2))
            id += 3

        for vert in range(len(f.vertices)):
            co = scale_mat * rot_x_mat * object_matrix_wrld * \
                data.vertices[f.vertices[vert]].co
            norm = scale_mat * rot_x_mat * norm_mat * \
                data.vertices[f.vertices[vert]].normal
            verts.append((co[0], co[1], co[2], 1.0))
            norms.append((norm[0], norm[1], norm[2], 0.0))

            #Get Uvs
            uv = getattr(data.tessface_uv_textures[0].data[f.index], 'uv'+str(vert + 1))
            luvs.append((uv.x, 1.0 - uv.y, 0.0, 0.0))
#            for k in range(colcount):
#                r = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
#                    f.index) + '].color' + str(vert + 1) + '[0]*1023')
#                g = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
#                    f.index) + '].color' + str(vert + 1) + '[1]*1023')
#                b = eval('data.tessface_vertex_colors[' + str(k) + '].data[' + str(
#                    f.index) + '].color' + str(vert + 1) + '[2]*1023')
#                eval('col_' + str(k) + '.append((r,g,b))')

    return verts,norms,luvs,faces


icounter = 0
vcounter = 0
vertices = []
normals  = [] 
indices  = []
uvs      = []
tangents = []

objects  = []
materials = []
collisions = []
material_dict = {}
material_ids = []

for ob in scn.objects:
    if not ob.name.startswith('NMS'):
        continue
    
    print('Located Object for export', ob.name)
    objects.append(ob.name.upper())
    #Parse Geometry
    verts,norms,luvs,faces = mesh_parser(ob)
    print(len(verts), len(luvs), len(norms), len(faces))
    #Detect Collisions
    colOb = None
    if len(ob.children)>0:
        # Assuming that the first child is a collision object for now
        # I'll have to change that in order to handle actual children 
        # mesh/locator objects in the future
        col = ob.children[0]
        
        
        
        if col.name.startswith("COLLISION"):
            print("Collision found: ", col.name)
            split = col.name.split("_")
            colType = split[1]
            
            optdict = {}
            rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
            trans, rot, scale = (rot_x_mat * col.matrix_local).decompose()
            rot = rot.to_euler()
            print(trans)
            print(rot)
            print(scale)
            optdict['Transform'] = TkTransformData(TransX=trans[0],
                                                   TransY=trans[2],
                                                   TransZ=trans[1],
                                                   RotX=degrees(rot[0]),
                                                   RotY=degrees(rot[2]),
                                                   RotZ=degrees(rot[1]),
                                                   ScaleX=scale[0],
                                                   ScaleY=scale[2],
                                                   ScaleZ=scale[1])
            
            optdict['Type'] = colType
            if (colType == "Mesh"):
                c_verts,c_norms,c_uvs,c_faces = mesh_parser(col)
                
                #Reset Transforms on meshes
                optdict['Transform'] = TkTransformData(TransX=0.0, TransY=0.0, TransZ=0.0,
                                                   RotX=0.0, RotY=0.0, RotZ=0.0,
                                                   ScaleX=1.0, ScaleY=1.0, ScaleZ=1.0)
                                                   
                optdict['Vertices'] = c_verts
                optdict['Indexes'] = c_faces
            #HANDLE Primitives
            elif (colType == "Box"):
                optdict['Width']  = col.dimensions[0]
                optdict['Depth']  = col.dimensions[1]
                optdict['Height'] = col.dimensions[2]
            elif (colType == "Sphere"):
                optdict['Radius'] = col.dimensions[0] / 2.0
            elif (colType == "Cylinder"):
                optdict['Radius'] = col.dimensions[0] / 2.0
                optdict['Height'] = col.dimensions[2]
            else:
                raise Exception("Unsupported Collision")
            
            colOb = Collision(**optdict)
            
    collisions.append(colOb)
      
    
    
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

print('Blender Script')
print('Create Data Call')
print(material_ids, len(material_ids))
print(materials)
print(len(matsamplers))
print("Checking List Counts:", len(vertices), len(indices), len(collisions))
Create_Data('TS_ALIEN',
            "TEST",
            objects,
            index_stream = indices,
            vertex_stream = vertices,
            uv_stream = uvs,
            materials = materials,
            mat_indices = material_ids,
            collisions = collisions
            )
