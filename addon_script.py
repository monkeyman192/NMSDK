bl_info = {  
 "name": "NMS Exporter",  
 "author": "gregkwaste, credits: monkeyman192",  
 "version": (0, 8),
 "blender": (2, 7, 0),  
 "location": "File > Export",  
 "description": "Exports to NMS File format",  
 "warning": "",
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Export"} 
 
import bpy
import bmesh
import os
import sys
from math import radians, degrees
from mathutils import Matrix,Vector

#Attempt to find 'blender.exe path'

for path in sys.path:
    if os.path.isdir(path):
        if 'nms_imp' in os.listdir(path):
            print("Found nms_imp at: ", path)
            os.chdir(path)
            break


# Add script path to sys.path
scriptpath = os.path.join(os.getcwd(),'nms_imp')
#scriptpath = bpy.context.space_data.text.filepath
#scriptpath = "J:\\Projects\\NMS_Model_Importer\\blender_script.py"
#proj_path = os.path.dirname(scriptpath)
#proj_path is set in the parse_material function

print(scriptpath)

if not scriptpath in sys.path:
    sys.path.append(scriptpath)
    #print(sys.path)
    
    
from main import Create_Data
from classes import TkMaterialData, TkMaterialFlags, TkMaterialUniform, TkMaterialSampler, TkTransformData
from classes import List, Vector4f
#Import Object Classes
from classes.Object import Model, Mesh, Locator, Reference, Collision, Light
from LOOKUPS import MATERIALFLAGS

import main
print(main.__file__)

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


def write_some_data(context, filepath, use_some_setting):
    print("running write_some_data...")
    f = open(filepath, 'w', encoding='utf-8')
    f.write("Hello World %s" % use_some_setting)
    f.close()

    return {'FINISHED'}


def parse_material(ob):
    # This function returns a tkmaterialdata object with all necessary material information
    
    #Get Material stuff

    slot = ob.material_slots[0]
    mat = slot.material
    print(mat.name)

    proj_path = bpy.path.abspath('//')
    
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
    
    #Check shadeless status
    if (mat.use_shadeless):
        #Set _F07_UNLIT
        matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[6]))    
    
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

    matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[46]))
    
    #Create materialdata struct
    tkmatdata = TkMaterialData(Name=mat.name,
                               Class='Opaque',
                               Flags=matflags,
                               Uniforms=matuniforms,
                               Samplers=matsamplers)
        
    return tkmatdata

#Tangent Calculator
def calc_tangents(faces, verts, norms, uvs):
    tangents = []
    #Init tangents
    for i in range(len(verts)):
        tangents.append(Vector((0,0,0,0)))
    
    #We assume that verts length will be a multiple of 3 since
    #the mesh has been triangulated
    
    trisNum = len(faces)
    #Iterate in triangles
    for i in range(trisNum):
        tri = faces[i]
        vert_1 = tri[0]
        vert_2 = tri[1]
        vert_3 = tri[2]
        
        #Get Point Positions
        P0 = Vector((verts[vert_1]));
        P1 = Vector((verts[vert_2])) - P0;
        P2 = Vector((verts[vert_3])) - P0;
        
        #print('Poss: ', P1, P2)
        
        P0_uv = Vector((uvs[vert_1]))
        P1_uv = Vector((uvs[vert_2])) - P0_uv
        P2_uv = Vector((uvs[vert_3])) - P0_uv
        #Keep only the 1st uvmap
        P1_uv = P1_uv.xy
        P2_uv = P2_uv.xy
        
        
        print('Uvs', P1_uv, P2_uv)
        
        #Matrix determinant
        D = P1_uv[0] * P2_uv[1] - P2_uv[0] * P1_uv[0]
        D = 1.0 / max(D, 0.0001) #Store the inverse right away
        
        #Apply equation
        tang = D * (P2_uv[1] * P1 - P1_uv[1] * P2)
        
        #Orthogonalize Gram-Shmidt
        n = Vector(norms[vert_1]);
        tang = tang - n * tang.dot(n)
        tang.normalize()
        
        #Add to existing
        #Vert_1
        tang1 = Vector(tangents[vert_1]) + tang;
        tang1.normalize()
        tangents[vert_1] = (tang1[0], tang1[1], tang1[2], 1.0)
        #Vert_2
        tang2 = Vector(tangents[vert_2]) + tang;
        tang2.normalize()
        tangents[vert_2] = (tang2[0], tang2[1], tang2[2], 1.0)
        #Vert_3
        tang3 = Vector(tangents[vert_3]) + tang;
        tang3.normalize()
        tangents[vert_3] = (tang3[0], tang3[1], tang3[2], 1.0)
        

    return tangents

def apply_local_transforms(rotmat, verts, norms, tangents):
    norm_mat = rotmat.inverted().transposed()
    
    print(len(verts), len(norms), len(tangents))
    for i in range(len(verts)):
        #Load Vertex
        vert = rotmat * Vector((verts[i]))
        #Store Transformed
        verts[i] = (vert[0], vert[1], vert[2], 1.0)
        #Load Normal
        norm = norm_mat * Vector((norms[i]))
        norm.normalize()
        #Store Transformed normal
        norms[i] = (norm[0], norm[1], norm[2], 1.0)
        #Load Tangent
        tang = norm_mat * Vector((tangents[i]))
        tang.normalize()
        #Store Transformed tangent
        tangents[i] = (tang[0], tang[1], tang[2], 1.0)
        
#Main Mesh parser
def mesh_parser(ob):
    #Lists
    verts = []
    norms = []
    tangents = []
    luvs = []
    faces = []
    # Matrices
    object_matrix_wrld = ob.matrix_world
    rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
    scale_mat = Matrix.Scale(1, 4)
    norm_mat = rot_x_mat.inverted().transposed()
    
    data = ob.data
    #Raise exception if UV Map is missing
    uvcount = len(data.uv_layers)
    if (uvcount < 1):
        raise Exception("Missing UV Map")
        
    
    #data.update(calc_tessface=True)  # convert ngons to tris
    data.calc_tessface()
    #try:
        #pass
    #    data.calc_tangents(data.uv_layers[0].name)
    #except:
    #    raise Exception("Please Triangulate your Mesh")
    
    
    
    colcount = len(data.vertex_colors)
    id = 0
    for f in data.tessfaces:  # indices
        #polygon = data.polygons[f.index] #Load Polygon
        if len(f.vertices) == 4:
            faces.append((id, id + 1, id + 2))
            faces.append((id, id + 2, id + 3))
            id += 4
        else:
            faces.append((id, id + 1, id + 2))
            id += 3

        for vert in range(len(f.vertices)):
            #Store them untransformed and we will fix them after tangent calculation
            co = data.vertices[f.vertices[vert]].co
            #norm = data.vertices[f.vertices[vert]].normal #Save Vertex Normal
            norm = f.normal #Save face normal
            
            #norm =    100 * norm_mat * data.loops[f.vertices[vert]].normal
            #tangent = 100 * norm_mat * data.loops[f.vertices[vert]].tangent
            verts.append((co[0], co[1], co[2], 1.0)) #Invert YZ to match NMS game coords
            norms.append((norm[0], norm[1], norm[2], 1.0))
            #tangents.append((tangent[0], tangent[1], tangent[2], 0.0))

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

    #At this point mesh is triangulated
    #I can get the triangulated input and calculate the tangents 
    tangents = calc_tangents(faces, verts, norms, luvs)
    
    #Apply rotation and normal matrices on vertices and normal vectors
    apply_local_transforms(rot_x_mat, verts, norms, tangents)
    
    return verts, norms, tangents, luvs, faces

def parse_object(ob, parent):
    newob = None
    global material_dict
    #Apply location/rotation/scale
    #bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    #Get transform
    matrix = ob.matrix_local
    yzmat = Matrix()
    yzmat[0] = Vector((1.0, 0.0, 0.0, 0.0))
    yzmat[1] = Vector((0.0, 0.0, 1.0, 0.0))
    yzmat[2] = Vector((0.0, 1.0, 0.0, 0.0))
    yzmat[3] = Vector((0.0, 0.0, 0.0, 1.0))
    
    trans, rot, scale = (yzmat * ob.matrix_local * yzmat).decompose()
    rot = rot.to_euler()
    print(trans)
    print(rot)
    print(scale)
    
    #transform = TkTransformData(TransX=trans[0],
    #                           TransY=trans[1],
    #                           TransZ=trans[2],
    #                           RotX=degrees(rot[0]),
    #                           RotY=degrees(rot[1]),
    #                           RotZ=degrees(rot[2]),
    #                           ScaleX=scale[0],
    #                           ScaleY=scale[1],
    #                           ScaleZ=scale[2])
    transform = TkTransformData(TransX=trans[0],
                               TransY=trans[1],
                               TransZ=trans[2],
                               RotX=degrees(rot[0]),
                               RotY=degrees(rot[1]),
                               RotZ=degrees(rot[2]),
                               ScaleX=scale[0],
                               ScaleY=scale[1],
                               ScaleZ=scale[2])
    
    # Main switch to identify meshes or locators/references
    if ob.type == 'MESH':
        if ob.name.startswith("NMS_COLLISION"):     # syntax: NMS_COLLISION_<NAME>_<CTYPE>
            # COLLISION MESH
            print("Collision found: ", ob.name)
            split = ob.name.split("_")
            colType = split[2]
            
            optdict = {}
            optdict['Name'] = split[3]
            optdict['Transform'] = transform
            optdict['CollisionType'] = colType
            
            if (colType == "Mesh"):
                c_verts,c_norms,c_tangs,c_uvs,c_faces = mesh_parser(ob)
                
                #Reset Transforms on meshes
                
                optdict['Vertices'] = c_verts
                optdict['Indexes'] = c_faces
                optdict['UVs'] = c_uvs
                optdict['Normals'] = c_norms
                optdict['Tangents'] = c_tangs
            #HANDLE Primitives
            elif (colType == "Box"):
                optdict['Width']  = ob.dimensions[0]
                optdict['Depth']  = ob.dimensions[1]
                optdict['Height'] = ob.dimensions[2]
            elif (colType == "Sphere"):
                optdict['Radius'] = ob.dimensions[0] / 2.0
            elif (colType == "Cylinder"):
                optdict['Radius'] = ob.dimensions[0] / 2.0
                optdict['Height'] = ob.dimensions[2]
            else:
                raise Exception("Unsupported Collision")
            
            newob = Collision(**optdict)
        else:
            # ACTUAL MESH
            #Parse object Geometry
            print('Exporting: ', ob.name)
            verts,norms,tangs,luvs,faces = mesh_parser(ob)
            print("Object Count: ", len(verts), len(luvs), len(norms), len(faces))
            print("Object Rotation: ", degrees(rot[0]), degrees(rot[2]), degrees(rot[1]))
            #Create Mesh Object
            actualname = ob.name.split("_")[1]      # syntax: NMS_<NAME>
            newob = Mesh(actualname, Transform = transform, Vertices=verts, UVs=luvs, Normals=norms, Tangents=tangs, Indexes=faces)
            
            #Try to parse material
            try:
                slot = ob.material_slots[0]
                mat = slot.material
                print(mat.name)
                if not mat.name in material_dict:
                    print("Parsing Material " + mat.name)
                    material_ob = parse_material(ob)
                    material_dict[mat.name] = material_ob
                else:
                    material_ob = material_dict[mat.name]
                
                print(material_ob)
                #Attach material to Mesh
                newob.Material = material_ob
                
            except:
                raise Exception("Missing Material")
    
    #Locator and Reference Objects
    elif (ob.type=='EMPTY'):
        if (ob.name.startswith('NMS_REFERENCE')):
            print("Reference Detected")
            actualname = ob.name.split("_")[2]      # syntax: NMS_REFERENCE_<NAME>
            try:
                scenegraph = ob["REF"]
            except:
                raise Exception("Missing REF Property, Set it")
            
            newob = Reference(Name = ob.name, Transform = transform, Scenegraph = scenegraph)
        elif (ob.name.startswith('NMS_LOCATOR')):
            print("Locator Detected")
            actualname = ob.name.split("_")[2]      # syntax: NMS_LOCATOR_<NAME>
            try:
                HasAttachment = ob["HasAttachment"]
                if HasAttachment == "True":
                    HasAttachment = True
                else:
                    HasAttachment = False
            except:
                HasAttachment = False
                        
            newob = Locator(Name = actualname, Transform = transform, HasAttachment = HasAttachment)
    #Light Objects
    elif (ob.type =='LAMP'):
        actualname = ob.name.split("_")[2]      # syntax: NMS_LIGHT_<NAME>
        #Get Color
        col = tuple(ob.data.color)
        print("colour: {}".format(col))
        #Get Intensity
        intensity = ob.data.energy
        
        newob = Light(Name=actualname, Transform = transform, Colour = col, Intensity = intensity)
    
    parent.add_child(newob)
    
    #Parse children
    for child in ob.children:
        if not (child.name.startswith('NMS') or child.name.startswith('COLLISION')):
            continue
        child_ob = parse_object(child, newob)
        #newob.add_child(child_ob)
        
    return newob


def main_exporter(exportpath):
    scn = bpy.context.scene
    mname = os.path.basename(exportpath)
    
    icounter = 0
    vcounter = 0
    vertices = []
    normals  = [] 
    indices  = []
    uvs      = []
    tangents = []

    materials = []
    collisions = []
    global material_dict
    material_dict = {}
    material_ids = []

    #Create main scene model
    scene = Model(Name = mname)
    
    #Try to fetch NMS_SCENE node
    try:
        main_ob = scn.objects['NMS_SCENE']
    except:
        raise Exception("Missing NMS_SCENE Node, Create it!")
    
    for ob in main_ob.children:
        if not ob.name.startswith('NMS'):
            continue
        print('Located Object for export', ob.name)
        parse_object(ob, scene)
        #scene.add_child(parse_object(ob))
        

    print('Blender Script')
    print('Create Data Call')
    
    print('Creating .exmls')
    #Convert Paths
    directory = os.path.dirname(exportpath)
    mpath = os.path.dirname(os.path.abspath(exportpath))
    os.chdir(mpath)
    Create_Data(mname,
                mname,
                scene)
                
    return {'FINISHED'}

    return True


class NMS_Export_Operator(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_mesh.nms"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export to NMS XML Format"

    # ExportHelper mixin class uses this
    filename_ext = ""

#    filter_glob = StringProperty(
#            default="*.txt",
#            options={'HIDDEN'},
#            maxlen=255,  # Max internal buffer length, longer would be clamped.
#            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
#    use_setting = BoolProperty(
#            name="Example Boolean",
#            description="Example Tooltip",
#            default=True,
#            )

#    type = EnumProperty(
#            name="Example Enum",
#            description="Choose between two items",
#            items=(('OPT_A', "First Option", "Description one"),
#                   ('OPT_B', "Second Option", "Description two")),
#            default='OPT_A',
#            )

    def execute(self, context):
        status = main_exporter(self.filepath)
        self.report({'INFO'}, "Models Exported Successfully")
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(NMS_Export_Operator.bl_idname, text="Export to NMS XML Format ")


def register():
    bpy.utils.register_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(NMS_Export_Operator)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mesh.nms(filepath="J:\\Installs\\Steam\\steamapps\\common\\No Man's Sky\\GAMEDATA\\PCBANKS\\CONSTRUCTRAMP")
