import bpy
import bmesh
import os
import sys
from idprop.types import IDPropertyGroup
from math import radians, degrees
from mathutils import Matrix,Vector
from BlenderExtensions import *

BASEPATH = 'CUSTOMMODELS'

customNodes = NMSNodes()

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
from classes import *
from Descriptor import Node_List, Node_Data, Descriptor
#from classes import TkMaterialData, TkMaterialFlags, TkMaterialUniform, TkMaterialSampler, TkTransformData, TkRotationComponentData
#from classes import TkAnimMetadata, TkAnimNodeData, TkAnimNodeFrameData             # imports relating to animations
#from classes import TkAnimationComponentData, TkAnimationData                       # entity animation classes
#from classes import List, Vector4f
#from classes import TkAttachmentData
#Import Object Classes
from classes.Object import Model, Mesh, Locator, Reference, Collision, Light, Joint
from LOOKUPS import MATERIALFLAGS
from ActionTriggerParser import ParseNodes

import main
print(main.__file__)

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator, NodeTree, Node, NodeSocket


def write_some_data(context, filepath, use_some_setting):
    print("running write_some_data...")
    f = open(filepath, 'w', encoding='utf-8')
    f.write("Hello World %s" % use_some_setting)
    f.close()

    return {'FINISHED'}

def object_is_animated(ob):
    # this will check a blender object to see if it's parent has any anim data (and it's parent recursively)
    if ob.animation_data is not None:
        # in this case just return true that the object has animation data
        return True
    else:
        if ob.parent is not None:
            return object_is_animated(ob.parent)
        else:
            return False

def get_all_actions(obj):
    """Retrieve all actions given a blender object. Includes NLA-actions
       Full credit to this code goes to misnomer on blender.stackexchange
       (cf. https://blender.stackexchange.com/questions/14204/how-to-tell-which-object-uses-which-animation-action)"""
    # slightly modified to return the name of the object, and the action
    if obj.animation_data:
        if obj.animation_data.action:
            yield obj.name, obj.NMSAnimation_props.anim_name, obj.animation_data.action
        for track in obj.animation_data.nla_tracks:
            for strip in track.strips:
                yield obj.name, obj.NMSAnimation_props.anim_name, strip.action

def get_children(obj, curr_children, obj_types, just_names = False):
    # return a flattened list of all the children of an object of a specified type.
    # if just_name is True, then only return the names, otherwise return the actual objects themselves
    if type(obj_types) == str:
        obj_types = [obj_types]
    # otherwise we'll just assume that it is a list of strings
    for child in obj.children:
        print(child.name, child.NMSNode_props.node_types)
        if child.NMSNode_props.node_types in obj_types:
            if just_names:
                curr_children.append(child.name)
            else:
                curr_children.append(child)
        curr_children += get_children(child, list(), obj_types, just_names)
    return curr_children

""" Misc. functions for transforming data """

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
        
        
        #print('Uvs', P1_uv, P2_uv)
        
        #Matrix determinant
        D = P1_uv[0] * P2_uv[1] - P2_uv[0] * P1_uv[0]
        D = 1.0 / max(D, 0.0001) #Store the inverse right away
        
        #Apply equation
        tang = D * (P2_uv[1] * P1 - P1_uv[1] * P2)
        
        #Orthogonalize Gram-Shmidt
        n = Vector(norms[vert_1]);
        tang = tang - n * tang.dot(n)
        # tang.normalize()
        
        #Add to existing
        #Vert_1
        tangents[vert_1] += tang
        #Vert_2
        tangents[vert_2] += tang
        #Vert_3
        #tang3 = Vector(tangents[vert_3]) + tang;
        #tang3.normalize()
        tangents[vert_3] += tang

    #Fix tangents
    for i in range(len(verts)):
        tang = tangents[i]
        tang.normalize()
        tangents[i] = (tangents[i].x, tangents[i].y, tangents[i].z, 1.0)       # (tangents[i].x, tangents[i].z, -tangents[i].y, 1.0)
    

    return tangents

def apply_local_transforms(rotmat, verts, norms, tangents, chverts):
    norm_mat = rotmat.inverted().transposed()
    
    print(len(verts), len(norms), len(tangents), len(chverts))
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
    for i in range(len(chverts)):
        chvert = rotmat* Vector((chverts[i]))
    #    chvert = chverts[i]
        chverts[i] = Vector4f(x = chvert[0], y = chvert[1], z = chvert[2], t = 1.0)

def transform_to_NMS_coords(ob):
    # this will return the local transform, rotation and scale of the object in the NMS coordinate system
    
    M = Matrix()
    M[0] = Vector((1.0, 0.0, 0.0, 0.0))
    M[1] = Vector((0.0, 0.0, 1.0, 0.0))
    M[2] = Vector((0.0, -1.0, 0.0, 0.0))
    M[3] = Vector((0.0, 0.0, 0.0, 1.0))

    Minv = Matrix()
    Minv[0] = Vector((1.0, 0.0, 0.0, 0.0))
    Minv[1] = Vector((0.0, 0.0, -1.0, 0.0))
    Minv[2] = Vector((0.0, 1.0, 0.0, 0.0))
    Minv[3] = Vector((0.0, 0.0, 0.0, 1.0))

    return (M*ob.matrix_local*Minv).decompose()

""" Main exporter class with all the other functions contained in one place """

class Exporter():
    # class to contain all the exporting functions

    def __init__(self, exportpath):
        self.global_scene = bpy.context.scene
        self.global_scene.frame_set(0)      # set the frame to be the first one, just in case an export has already been run
        self.mname = os.path.basename(exportpath)

        #self.blend_to_NMS_mat = Matrix.Rotation(radians(-90), 4, 'X')
        """self.blend_to_NMS_mat = Matrix()
        self.blend_to_NMS_mat[0] = Vector((1.0, 0.0, 0.0, 0.0))
        self.blend_to_NMS_mat[1] = Vector((0.0, 0.0, 1.0, 0.0))
        self.blend_to_NMS_mat[2] = Vector((0.0, -1.0, 0.0, 0.0))
        self.blend_to_NMS_mat[3] = Vector((0.0, 0.0, 0.0, 1.0))"""

        self.state = None
        
        icounter = 0
        vcounter = 0
        vertices = []
        normals  = [] 
        indices  = []
        uvs      = []
        tangents = []
        chverts = []

        materials = []
        collisions = []
        self.material_dict = {}
        self.material_ids = []
        
        self.anim_frame_data = dict()

        self.CollisionIndexCount = 0        # this is the total number of collision indexes. The geometry file as of 1.3 requires it.

        self.joints = 0     # current number of joints. This is incremented as required.

        self.global_entitydata = dict()        # disctionary containing the info for each object about the entity info it contains
        
        #Try to fetch NMS_SCENE node
        try:
            self.NMSScene = self.global_scene.objects['NMS_SCENE']
        except:
            raise Exception("Missing NMS_SCENE Node, Create it!")

        # to ensure the rotation is applied correctly, first delect any selected objects in the scene,
        # then select and activate the NMS_SCENE object
        #self.select_only(self.NMSScene)

        """# apply rotation to entire model
        self.global_scene.objects.active = self.NMSScene
        self.NMSScene.matrix_world = self.blend_to_NMS_mat*self.NMSScene.matrix_world
        # apply rotation to all child nodes
        self.rotate_all(self.NMSScene)"""

        # check whether or not we will be exporting in batch mode
        if self.NMSScene.NMSScene_props.batch_mode:
            batch_export = True
        else:
            batch_export = False

        if self.NMSScene.NMSScene_props.AT_only:
            # in this case we want to export just the entity with action trigger data, nothing else
            entitydata = ParseNodes()
            entity = TkAttachmentData(Components = List(entitydata))
            entity.make_elements(main = True)
            mpath = os.path.dirname(os.path.abspath(exportpath))
            os.chdir(mpath)
            entity.tree.write("{}.ENTITY.exml".format(self.mname))
        else:
            # run the program normally
            # if there is a name for the group, use it.
            if self.NMSScene.NMSScene_props.group_name != "":
                self.group_name = self.NMSScene.NMSScene_props.group_name
            else:
                self.group_name = self.mname

            # if we aren't doing a batch export, set the scene as a model object that all will use as a parent
            if batch_export == False:
                #Create main scene model now
                scene = Model(Name = self.mname)

            # let's sort out the descriptor first as it may re-name some of the objects in the scene:
            self.descriptor = self.descriptor_generator()

            # pre-process the animation information.
            self.scene_actions = set()      # set to contain all the actions that are used in the scene
            self.joint_anim_data = dict()       # this will be a dictionary with the key being the joint name, and the data being the actions associated with it
            self.animation_anim_data = dict()   # this will be a dictionary with the key being the animation name, and the data being the actions associated with it
            self.anim_controller_obj = None     # this is the blender object that was specified as controlling the animations

            # get all the animation data first, so we can decide how we deal with anims. This data can be used to determine how many animations we actually have.
            self.add_to_anim_data(self.NMSScene)
            self.anim_frames = self.global_scene.frame_end        # number of frames        (same... for now)
            print(self.scene_actions)
            #print(self.joint_anim_data)
            print(self.animation_anim_data)

            # create any commands that need to be sent to the main script:
            commands = {'dont_compile': self.NMSScene.NMSScene_props.dont_compile}

            """ This will probably need to be re-worked to make sure it works... """
            for ob in self.NMSScene.children:
                if not ob.name.startswith('NMS'):
                    continue
                print('Located Object for export', ob.name)
                if batch_export:
                    # we will need to create an individual scene object for each mesh
                    if ob.NMSNode_props.node_types == "Mesh" or ob.NMSNode_props.node_types == "Locator":
                        name = ob.name[len("NMS_"):].upper()
                        self.scene_directory = os.path.join(BASEPATH, self.group_name, name)
                        print("Processing object {}".format(name))
                        scene = Model(Name = name)
                        self.parse_object(ob, scene)#, scn, process_anim = animate is not None, anim_frame_data = anim_frame_data, extra_data = extra_data)
                        anim = self.anim_generator()
                        directory = os.path.dirname(exportpath)
                        mpath = os.path.dirname(os.path.abspath(exportpath))
                        os.chdir(mpath)
                        Create_Data(name,
                                    self.group_name,
                                    scene,
                                    anim,
                                    self.descriptor,
                                    **commands)
                            
                else:
                    # parse the entire scene all in one go.
                    self.scene_directory = os.path.join(BASEPATH, self.group_name, self.mname)      # set this here because... why not
                    self.parse_object(ob, scene)#, scn, process_anim = animate is not None, anim_frame_data = anim_frame_data, extra_data = extra_data)

            self.process_anims()

            print('Creating .exmls')
            #Convert Paths
            if not batch_export:
                # we only want to run this if we aren't doing a batch export
                directory = os.path.dirname(exportpath)
                mpath = os.path.dirname(os.path.abspath(exportpath))
                os.chdir(mpath)
                # create the animation stuff if necissary:
                print('bloop')
                anim = self.anim_generator()
                Create_Data(self.mname,
                            self.group_name,
                            scene,
                            anim,
                            self.descriptor,
                            **commands)
                
        """# undo rotation
        self.select_only(self.NMSScene)
        self.global_scene.objects.active = self.NMSScene
        self.NMSScene.matrix_world = self.blend_to_NMS_mat.inverted()*self.NMSScene.matrix_world
        # apply rotation to all child nodes
        self.rotate_all(self.NMSScene)"""

        self.global_scene.frame_set(0)
        

        self.state = 'FINISHED'

    def select_only(self, ob):
        # sets only the provided object to be selected
        for obj in bpy.context.selected_objects:
            obj.select = False
        ob.select = True

    def rotate_all(self, ob):
        # this will apply the rotation transform the object, and then call this function on it's children
        self.global_scene.objects.active = ob
        self.select_only(ob)
        bpy.ops.object.transform_apply(rotation = True)
        for child in ob.children:
            if child.name.upper() != 'ROTATION':
                self.rotate_all(child)

    def add_to_anim_data(self, ob):
        for child in ob.children:
            if child.NMSNode_props.node_types == "Joint":
                # iterate over each child that is a joint
                for name_action in get_all_actions(child):
                    self.scene_actions.add(name_action[2])
                    if name_action[1] not in self.animation_anim_data:
                        self.animation_anim_data[name_action[1]] = list()
                    self.animation_anim_data[name_action[1]].append([name_action[0], name_action[2]])
            self.add_to_anim_data(child)                    

    def parse_material(self, ob):
        # This function returns a tkmaterialdata object with all necessary material information
        
        #Get Material stuff
        if ob.get('MATERIAL', None) is not None:
            # if a material path has been specified simply use that
            matpath = str(ob['MATERIAL'])
            return matpath
        else:
            # otherwise parse the actual material data
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
                #matflags.append(TkMaterialFlags(MaterialFlag=MATERIALFLAGS[23]))
                #Create gMaskMap Sampler
                
                tex = tslots[1].texture
                #Check if there is no texture loaded
                if not tex.type=='IMAGE':
                    raise Exception("Missing Image in Texture: " + tex.name)
                
                texpath = os.path.join(proj_path, tex.image.filepath[2:])
            
            sampl = TkMaterialSampler(Name="gMasksMap", Map=texpath, IsSRGB=False)
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
                                       CastShadow = True,
                                       Flags=matflags,
                                       Uniforms=matuniforms,
                                       Samplers=matsamplers)
                
            return tkmatdata

    def anim_generator(self):
        # process the anim data into a TkAnimMetadata structure
        joint_list = get_children(self.NMSScene, list(), "Joint", just_names = True)        # list of the names of every joint
        print("joint list:", joint_list)
        num_nodes = len(joint_list)
        AnimationFiles = {}
        for action in self.anim_frame_data:     #action is the name of the action, as specified by the animation panel
            action_data = self.anim_frame_data[action]
            NodeData = List()
            active_nodes = list(action_data.keys())
            print("active nodes ", active_nodes, " for {}".format(action))
            ordered_nodes = list() + active_nodes                # list of all the nodes with the ones with animation data first (empty ones will be appended on)
            for node in joint_list:
                # only need to add on empty ones to the end
                if node not in active_nodes:
                    ordered_nodes.append(node)
            print(ordered_nodes)
            for node in range(num_nodes):
                kwargs = {'Node': ordered_nodes[node][len("NMS_"):], 'RotIndex': str(node), 'TransIndex': str(node), 'ScaleIndex': str(node)}
                NodeData.append(TkAnimNodeData(**kwargs))
            AnimFrameData = List()
            stillRotations = List()
            stillTranslations = List()
            stillScales = List()
            for frame in range(self.anim_frames):
                Rotations = List()
                Translations = List()
                Scales = List()
                # the active nodes will be in the same order as the ordered list because we constructed it that way
                # only iterate over the active nodes
                for node in active_nodes:
                    trans = action_data[node][frame][0]
                    rot = action_data[node][frame][1]
                    scale = action_data[node][frame][2]
                    Rotations.append(Vector4f(x = rot[0], y = rot[1], z = rot[2], t = rot[3]))
                    Translations.append(Vector4f(x = trans[0], y = trans[1], z = trans[2], t = 1.0))
                    Scales.append(Vector4f(x = scale[0], y = scale[1], z = scale[2], t = 1.0))
                    if frame == 0:
                        # set all the still frame data (I assume this is right?? Don't think it has to be...)
                        stillRotations.append(Vector4f(x = rot[0], y = rot[1], z = rot[2], t = rot[3]))
                        stillTranslations.append(Vector4f(x = trans[0], y = trans[1], z = trans[2], t = 1.0))
                        stillScales.append(Vector4f(x = scale[0], y = scale[1], z = scale[2], t = 1.0))
                FrameData = TkAnimNodeFrameData(Rotations = Rotations, Translations = Translations, Scales = Scales)
                AnimFrameData.append(FrameData)
            StillFrameData = TkAnimNodeFrameData(Rotations = stillRotations, Translations = stillTranslations, Scales = stillScales)

            AnimationFiles[action] = (TkAnimMetadata(FrameCount = str(self.anim_frames),
                                                     NodeCount = str(num_nodes),
                                                     NodeData = NodeData,
                                                     AnimFrameData = AnimFrameData,
                                                     StillFrameData = StillFrameData))
        return AnimationFiles

    def descriptor_generator(self):
        # go over the entire scene and create a descriptor.
        # Note: This will currently not work with scenes exported ia the batch option.

        descriptor_struct = Descriptor()

        def descriptor_recurse(obj, structure):
            # will recurse the object and add the object to the structure
            prefixes = set()
            important_children = []
            for child in obj.children:
                if not child.name.startswith('NMS'):
                    continue
                if child.NMSDescriptor_props.proc_prefix != "":
                    p = child.NMSDescriptor_props.proc_prefix
                    # let's do a bit of processing on the prefix first to make sure all is good
                    # the user may or may not have put a leading or trailing underscore, so we'll get rid of them and add our own just in case...
                    prefix = "_{0}_".format(p.strip("_"))
                    prefixes.add(prefix)
                    important_children.append(child)        # add only children we like to the list (ie. those with some proc info)

            for prefix in prefixes:
                structure.add_child(prefix)                 # adds a Node_List type child object
            
            # now recurse over the children with proc info
            for child in important_children:
                node = structure.get_child("_{0}_".format(child.NMSDescriptor_props.proc_prefix.strip("_"))).add_child(child)      # this will add a Node_Data object and return it
                descriptor_recurse(child, node)
                # we also need to rename the object so that it is consistent with the descriptor:
                prefix = child.NMSDescriptor_props.proc_prefix.strip("_")
                stripped_name = child.name[len("NMS_"):].upper()
                if stripped_name.strip('_').upper().startswith(prefix):
                    child.NMSNode_props.override_name = "_{0}".format(stripped_name.strip('_').upper())
                else:
                    # hopefully the user hasn't messed anything up...
                    child.NMSNode_props.override_name = "_{0}_{1}".format(prefix, stripped_name.strip('_').upper())

        descriptor_recurse(self.NMSScene, descriptor_struct)
        
        print(descriptor_struct)

        return descriptor_struct.to_exml()
        
    #Main Mesh parser
    def mesh_parser(self, ob):
        self.global_scene.objects.active = ob
        #Lists
        verts = []
        norms = []
        tangents = []
        luvs = []
        faces = []
        chverts = []        # convex hull vert data
        # Matrices
        #object_matrix_wrld = ob.matrix_world
        rot_x_mat = Matrix.Rotation(radians(-90), 4, 'X')
        #ob.matrix_world = rot_x_mat*ob.matrix_world
        #scale_mat = Matrix.Scale(1, 4)
        #norm_mat = rot_x_mat.inverted().transposed()
        
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
                norm = data.vertices[f.vertices[vert]].normal #Save Vertex Normal
                #norm = f.normal #Save face normal
                
                #norm =    100 * norm_mat * data.loops[f.vertices[vert]].normal
                #tangent = 100 * norm_mat * data.loops[f.vertices[vert]].tangent
                verts.append((co[0], co[1], co[2], 1.0)) #Invert YZ to match NMS game coords       # (co[0], co[2], -co[1], 1.0)
                norms.append((norm[0], norm[1], norm[2], 1.0))         # y and z components have - sign to what they had before...
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
        if (self.NMSScene.NMSScene_props.create_tangents):
            tangents = calc_tangents(faces, verts, norms, luvs)
        else:
            tangents = []

        # finally, let's find the convex hull data of the mesh:
        """ This may need to be modified a bit so that the hull is added as a sibling to the collision object? """
        bpy.ops.object.mode_set(mode = 'EDIT')
        bm = bmesh.from_edit_mesh(data)
        ch = bmesh.ops.convex_hull(bm, input = bm.verts)['geom']        #convex hull data. Includes face and edges and stuff...
        for i in ch:
            if type(i) == bmesh.types.BMVert:
                chverts.append((i.co[0], i.co[1], i.co[2], 1.0))
                #chverts.append(Vector4f(x = i.co[0], y = i.co[1], z = i.co[2], t = 1.0))
        del ch
        del bm
        bpy.ops.object.mode_set(mode = 'OBJECT')

        #ob.matrix_world = rot_x_mat.inverted()*ob.matrix_world
        
        
        #Apply rotation and normal matrices on vertices and normal vectors
        apply_local_transforms(rot_x_mat, verts, norms, tangents, chverts)
        
        return verts, norms, tangents, luvs, faces, chverts

    def recurce_entity(self, parent, obj, list_element = None, index = 0):
        # this will return the class object of the property recursively

        # Just doing all in one line because it's going to be nasty either way...
        print('obj: ', obj)
        try:
            if list_element is None:
                cls = eval(getattr(parent, obj).__class__.__name__.split('_')[1])     # ewwwwww. If there is a better way to do this I'd LOVE to know!
                #cls = eval(getattr(parent, parent[obj].name).__class__.__name__.split('_')[1])     # ewwwwww. If there is a better way to do this I'd LOVE to know!
            else:
                cls = eval(getattr(parent, obj)[index].__class__.__name__.split('_')[1])     # ewwwwww. If there is a better way to do this I'd LOVE to know!
        except TypeError:
            print('shit!')
            print(obj)

        properties = dict()

        if list_element is None:
            prop_group = getattr(parent, obj)
            entries = prop_group.keys()
        else:
            prop_group = getattr(parent, obj)[index]
            entries = list_element.keys()

        # iterate through each of the keys in the property group
        for prop in entries:     #  parent[obj]
            # if it isn't a property group itself then just add the data to the properties dict
            if not isinstance(prop_group[prop], IDPropertyGroup):
                properties[prop] = getattr(prop_group, prop)
            else:
                # otherwise call this function on the property
                print('recursing ', prop)
                properties[prop] = self.recurce_entity(prop_group, prop)
                #properties[prop] = self.recurce_entity(prop_group, prop_group[prop])
        return cls(**properties)
        

    def parse_object(self, ob, parent):#, global_scene, process_anim = False, anim_frame_data = dict(), extra_data = dict()):
        newob = None
        #Apply location/rotation/scale
        #bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # get the objects' location and convert to NMS coordinates
        print(ob.matrix_local.decompose())
        trans, rot_q, scale = transform_to_NMS_coords(ob) #ob.matrix_local.decompose()
        rot = rot_q.to_euler()
        print(trans)
        print(rot)
        print(scale)

        transform = TkTransformData(TransX=trans[0],
                                   TransY=trans[1],
                                   TransZ=trans[2],
                                   RotX=degrees(rot[0]),
                                   RotY=degrees(rot[1]),
                                   RotZ=degrees(rot[2]),
                                   ScaleX=scale[0],
                                   ScaleY=scale[1],
                                   ScaleZ=scale[2])

        entitydata = dict()         # this is the local entity data

        # let's first sort out any entity data that is specified:
        if ob.NMSMesh_props.has_entity or ob.NMSLocator_props.has_entity:
            print('this has an entity:', ob)
            # we need to pull information from two places:
            # ob.NMSEntity_props
            # check to see if the mesh's entity will get the action trigger data
            if '/' in ob.NMSEntity_props.name_or_path or '\\' in ob.NMSEntity_props.name_or_path:
                # in this case just set the data to be a string with a path
                entitydata = ob.NMSEntity_props.name_or_path
            else:
                entitydata[ob.NMSEntity_props.name_or_path] = list()
                if ob.NMSEntity_props.has_action_triggers:
                    entitydata[ob.NMSEntity_props.name_or_path].append(ParseNodes())
            # and ob.EntityStructs
            # this could potentially be it's own class?
            for struct in ob.EntityStructs:
                # this is the name of the struct
                cls = eval(struct.name)         # create an instance of the struct
                properties = dict()
                sub_props = getattr(ob, 'NMS_{0}_props'.format(struct.name))        # this is the list of all the properties in the struct
                # iterate over each of the sub-properties
                for prop in sub_props.keys():
                    if isinstance(sub_props[prop], IDPropertyGroup):
                        properties[prop] = self.recurce_entity(sub_props, prop)
                    elif isinstance(sub_props[prop], list):
                        properties[prop] = List()
                        counter = 0
                        for le in sub_props[prop]:      # le = list_element
                            properties[prop].append(self.recurce_entity(sub_props, prop, list_element = le, index = counter))
                            counter += 1
                    else:
                        properties[prop] = getattr(sub_props, prop)
                entitydata[ob.NMSEntity_props.name_or_path].append(cls(**properties))
        
        # Main switch to identify meshes or locators/references
        if ob.NMSNode_props.node_types == 'Collision':
            # COLLISION MESH
            print("Collision found: ", ob.name)
            colType = ob.NMSCollision_props.collision_types
            
            optdict = {}
            optdict['Name'] = self.scene_directory
            # do a slightly modified transform data as we want the scale to always be (1,1,1)

            # let's do a check on the values of the scale and the dimensions.
            # we can have it so that the user can apply scale, even if by accident, or have it so that if the
            # user wants a stretched spherical or cylindrical collision that is also fine
            dims = ob.dimensions
            if ob.NMSCollision_props.transform_type == "Transform":
                trans_scale = (1,1,1)
                dims = scale
                factor = (0.5, 0.5, 0.5)        # relative scale factor (to correct for the scaling due to the transform)
            else:
                trans_scale = scale
                dims = (ob.dimensions[0], ob.dimensions[2], ob.dimensions[1])       # swap coords to match the NMS coordinate system
                factor = scale
            
            optdict['Transform'] = TkTransformData(TransX=trans[0],
                                   TransY=trans[1],
                                   TransZ=trans[2],
                                   RotX=degrees(rot[0]),
                                   RotY=degrees(rot[1]),
                                   RotZ=degrees(rot[2]),
                                   ScaleX=trans_scale[0],
                                   ScaleY=trans_scale[1],
                                   ScaleZ=trans_scale[2])
            optdict['CollisionType'] = colType
            
            if (colType == "Mesh"):
                c_verts, c_norms, c_tangs, c_uvs, c_faces, c_chverts = self.mesh_parser(ob)
                
                #Reset Transforms on meshes
                
                optdict['Vertices'] = c_verts
                optdict['Indexes'] = c_faces
                optdict['UVs'] = c_uvs
                optdict['Normals'] = c_norms
                optdict['Tangents'] = c_tangs
                optdict['CHVerts'] = c_chverts
                self.CollisionIndexCount += len(c_faces)        # I think?
            #HANDLE Primitives
            elif (colType == "Box"):
                optdict['Width']  = dims[0]/factor[0]
                optdict['Depth']  = dims[2]/factor[2]
                optdict['Height'] = dims[1]/factor[1]
            elif (colType == "Sphere"):
                optdict['Radius'] = min([0.5*dims[0]/factor[0], 0.5*dims[1]/factor[1], 0.5*dims[2]/factor[2]])            # take the minimum value to find the 'base' size (effectively)
            elif (colType == "Cylinder"):
                optdict['Radius'] = min([0.5*dims[0]/factor[0], 0.5*dims[2]/factor[2]])
                optdict['Height'] = dims[1]/factor[1]
            else:
                raise Exception("Unsupported Collision")
            
            newob = Collision(**optdict)
        elif ob.NMSNode_props.node_types == 'Mesh':
            # ACTUAL MESH
            #Parse object Geometry
            print('Exporting: ', ob.name)
            verts, norms, tangs, luvs, faces, chverts = self.mesh_parser(ob)
            print("Object Count: ", len(verts), len(luvs), len(norms), len(faces), len(chverts))
            print("Object Rotation: ", degrees(rot[0]), degrees(rot[1]), degrees(rot[2]))

            # check whether the mesh has any child nodes we care about (such as a rotation vector)
            """ This will need to be re-done!!! """
            for child in ob.children:
                if child.name.upper() == 'ROTATION':
                    # take the properties of the rotation vector and give it to the mesh as part of it's entity data
                    axis = child.rotation_quaternion*Vector((0,0,1))
                    #axis = Matrix.Rotation(radians(-90), 4, 'X')*(rot*Vector((0,1,0)))
                    print(axis)
                    rotation_data = TkRotationComponentData(Speed = child.NMSRotation_props.speed, Axis = Vector4f(x=axis[0],y=axis[1],z=axis[2],t=0))
                    entitydata.append(rotation_data)
            
            #Create Mesh Object
            if ob.NMSNode_props.override_name != "":
                actualname = ob.NMSNode_props.override_name
            else:
                actualname = ob.name[len("NMS_"):].upper()
            newob = Mesh(Name = actualname,
                         Transform = transform,
                         Vertices=verts,
                         UVs=luvs,
                         Normals=norms,
                         Tangents=tangs,
                         Indexes=faces,
                         CHVerts = chverts,
                         ExtraEntityData = entitydata,
                         HasAttachment = ob.NMSMesh_props.has_entity)

            # check to see if the mesh's entity will be animation controller, if so assign to the anim_controller_obj variable
            if ob.NMSEntity_props.is_anim_controller and ob.NMSMesh_props.has_entity:
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path, newob)         # tuple, first entry is the name of the entity, the second is the actual mesh object...
            
            #Try to parse material
            if ob.NMSMesh_props.material_path != "":
                newob.Material = ob.NMSMesh_props.material_path
            else:
                try:
                    slot = ob.material_slots[0]
                    mat = slot.material
                    print(mat.name)
                    if not mat.name in self.material_dict:
                        print("Parsing Material " + mat.name)
                        material_ob = self.parse_material(ob)
                        self.material_dict[mat.name] = material_ob
                    else:
                        material_ob = self.material_dict[mat.name]
                    
                    print(material_ob)
                    #Attach material to Mesh
                    newob.Material = material_ob
                    
                except:
                    raise Exception("Missing Material")
        
        #Locator and Reference Objects
        elif ob.NMSNode_props.node_types == 'Reference':
            print("Reference Detected")
            if ob.NMSNode_props.override_name != "":
                actualname = ob.NMSNode_props.override_name
            else:
                actualname = ob.name[len("NMS_"):].upper()
            try:
                scenegraph = ob.NMSReference_props.reference_path
            except:
                raise Exception("Missing REF Property, Set it")
            
            newob = Reference(Name = actualname, Transform = transform, Scenegraph = scenegraph)
        elif ob.NMSNode_props.node_types == 'Locator':
            print("Locator Detected")
            if ob.NMSNode_props.override_name != "":
                actualname = ob.NMSNode_props.override_name
            else:
                actualname = ob.name[len("NMS_"):].upper()
            HasAttachment = ob.NMSLocator_props.has_entity
                        
            newob = Locator(Name = actualname, Transform = transform, ExtraEntityData = entitydata, HasAttachment = HasAttachment)

            if ob.NMSEntity_props.is_anim_controller and ob.NMSLocator_props.has_entity:
                self.anim_controller_obj = (ob.NMSEntity_props.name_or_path, newob)         # tuple, first entry is the name of the entity, the second is the actual mesh object...

        elif ob.NMSNode_props.node_types == 'Joint':
            print("Joint Detected")
            if ob.NMSNode_props.override_name != "":
                actualname = ob.NMSNode_props.override_name
            else:
                actualname = ob.name[len("NMS_"):].upper()
            self.joints += 1
            newob = Joint(Name = actualname, Transform = transform, JointIndex = self.joints)
                
        #Light Objects
        elif ob.NMSNode_props.node_types == 'Light':
            if ob.NMSNode_props.override_name != "":
                actualname = ob.NMSNode_props.override_name
            else:
                actualname = ob.name[len("NMS_"):].upper()
            #Get Color
            col = tuple(ob.data.color)
            print("colour: {}".format(col))
            #Get Intensity
            intensity = ob.NMSLight_props.intensity_value
            
            newob = Light(Name=actualname, Transform = transform, Colour = col, Intensity = intensity, FOV = ob.NMSLight_props.FOV_value)
        
        parent.add_child(newob)

        # add the local entity data to the global dict:
        self.global_entitydata[ob.name] = entitydata
        
        #Parse children
        for child in ob.children:
            if not (child.name.startswith('NMS') or child.name.startswith('COLLISION')):
                continue
            child_ob = self.parse_object(child, newob)#, global_scene, process_anim, anim_frame_data, extra_data)

        return newob

    def process_anims(self):
        # get all the data. We will then consider number of actions globally and process the entity stuff accordingly
        anim_loops = dict()
        for anim_name in self.animation_anim_data:
            print("processing anim {}".format(anim_name))
            action_data = dict()
            for jnt_action in self.animation_anim_data[anim_name]:
                self.global_scene.objects[jnt_action[0]].animation_data.action = jnt_action[1]      # set the actions of each joint (with this action) to be the current active one
                action_data[jnt_action[0]] = list()         # initialise an empty list for the data to be put into with the requisite key
                anim_loops[anim_name] = self.global_scene.objects[jnt_action[0]].NMSAnimation_props.anim_loops_choice       # set whether or not the animation is to loop
                    
            for frame in range(self.anim_frames):       # let's hope none of the anims have different amounts of frames... should be easy to fix though... later...
                # need to change the frame of the scene to appropriate one
                self.global_scene.frame_set(frame)
                # now need to re-get the data
                #print("processing frame {}".format(frame))
                for jnt_action in self.animation_anim_data[anim_name]:
                    name = jnt_action[0]        # name of the joint that is animated
                    ob = self.global_scene.objects[name]
                    trans, rot_q, scale = transform_to_NMS_coords(ob)   # ob.matrix_local.decompose()
                    action_data[name].append((trans, rot_q, scale))      # this is the anim_data that will be processed later
            # add all the animation data to the anim frame data for the particular action
            self.anim_frame_data[anim_name] = action_data

        # now semi-process the animation data to generate data for the animation controller entity file
        if len(self.anim_frame_data) == 1:
            # in this case we only have the idle animation.
            path = os.path.join(BASEPATH, self.group_name.upper(), self.mname.upper())
            anim_entity = TkAnimationComponentData(Idle = TkAnimationData(AnimType = list(anim_loops.values())[0]))
            self.anim_controller_obj[1].ExtraEntityData[self.anim_controller_obj[0]].append(anim_entity)      # update the entity data directly
            self.anim_controller_obj[1].rebuild_entity()
        elif len(self.anim_frame_data) > 1:
            # in this case all the anims are not idle ones, and we need some kind of real data
            Anims = List()
            path = os.path.join(BASEPATH, self.group_name.upper(), 'ANIMS')
            for action in self.anim_frame_data:
                name = action
                AnimationData = TkAnimationData(Anim = name,
                                                Filename = os.path.join(path, "{}.ANIM.MBIN".format(name.upper())),
                                                FlagsActive = True)
                Anims.append(AnimationData)
            anim_entity = TkAnimationComponentData(Idle = TkAnimationData(),
                                                   Anims = Anims)
            self.anim_controller_obj[1].ExtraEntityData[self.anim_controller_obj[0]].append(anim_entity)      # update the entity data directly
            self.anim_controller_obj[1].rebuild_entity()
            print(self.anim_controller_obj.Name, self.anim_controller_obj.EntityData)


class NMS_Export_Operator(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_mesh.nms"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export to NMS XML Format"

    # ExportHelper mixin class uses this
    filename_ext = ""

    def execute(self, context):
        main_exporter = Exporter(self.filepath)
        status = main_exporter.state
        self.report({'INFO'}, "Models Exported Successfully")
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
