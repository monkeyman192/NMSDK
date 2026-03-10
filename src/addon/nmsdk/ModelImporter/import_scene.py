# stdlib imports
import json
import os
import os.path as op
import shutil
import subprocess
import time
import traceback
from math import radians
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Optional, cast

import bmesh

# Blender imports
import bpy
import numpy as np
from bpy.types import Armature
from hgpaktool.utils import normalise_path
from mathutils import Matrix, Quaternion, Vector

from ..NMS.LOOKUPS import REV_SEMANTICS, VERT_TYPE_MAP
from ..NMS.material_node import create_material_node

# Internal imports

if TYPE_CHECKING:
    from .. import NMSDKPreferences
from ..serialization.formats import np_read_int_2_10_10_10_rev
from ..serialization.NMS_Structures.NMS_types import MBINHeader
from ..serialization.NMS_Structures.Structures import (
    NAMEHASH_MAPPING,
    TkAnimationComponentData,
    TkAnimationData,
    TkAnimMetadata,
    TkAttachmentData,
    TkGeometryData,
    TkJointBindingData,
    TkModelDescriptorList,
    TkSceneNodeData,
    ctx_nonignored_namehashes,
)
from ..utils.bpyutils import SceneOp, edit_object, select_object
from ..utils.io import base_path, get_NMS_dir, load_file, load_file_unsafe, post_path
from ..utils.stopwitch import witch
from .animation_handler import add_animation_to_scene
from .mesh_utils import BB_transform_matrix
from .readers import gstream_info
from .SceneNodeData import SceneNodeData

ROT_MATRIX = Matrix.Rotation(radians(90), 4, 'X')
DATA_PATH_MAP = {'Rotation': 'rotation_quaternion',
                 'Translation': 'location',
                 'Scale': 'scale'}

TYPE_MAP = {'MESH': 'Mesh', 'LOCATOR': 'Locator', 'REFERENCE': 'Reference',
            'JOINT': 'Joint', 'LIGHT': 'Light'}


BLENDER_MAJOR_VERSION, BLENDER_MINOR_VERSION, BLENDER_REVISION_VERSION = bpy.app.version
if BLENDER_MAJOR_VERSION >= 4 and BLENDER_MINOR_VERSION >= 2:
    RENDER_ENGINE = "BLENDER_EEVEE_NEXT"
else:
    RENDER_ENGINE = "BLENDER_EEVEE"


# Get the parent package name.
_package = __package__.rpartition(".")[0]


class MeshError(Exception):
    pass


class ImportScene():
    """ Load a scene into blender.

    Parameters
    ----------
    fpath : string
        Filepath to the scene file to be loaded.
    parent_obj : obj
        The parent object. For a first-class scene this will always be none
        and an empty NMS_SCENE node will be generated for the scene to be
        placed in.
        For scenes that are referenced by another scene this will be that
        reference object.
    ref_scenes : dict
        A dictionary with the path to another scene as the key, and the blender
        object that has already been loaded as the value.
    """
    @witch.section("__init__")
    def __init__(
        self,
        fpath: str,
        parent_obj=None,
        ref_scenes: Optional[dict] = None,
        settings: Optional[dict] = None,
        from_pak: bool = False,
    ):
        self.from_pak = from_pak
        self.ref_scenes = ref_scenes or {}

        addon_prefs: NMSDKPreferences = bpy.context.preferences.addons[_package].preferences
        if self.from_pak:
            # Get the vfs path.
            vfs_path = op.join(addon_prefs.pcbanks_dir, ".scene_vfs")
            self.root_dir = addon_prefs.pcbanks_dir
            if op.exists(op.join(vfs_path, "index.json")):
                with open(op.join(vfs_path, "index.json")) as f:
                    self.pak_data_mapping = json.load(f)
        else:
            vfs_path = None
            self.pak_data_mapping = {}

        mbincompiler_path = addon_prefs.mbincompiler_path

        if settings is None:
            settings = {}
        if self.from_pak is True:
            self.local_directory = None
            self.scene_path = fpath
        else:
            self.local_directory, _ = op.split(fpath)
            self.root_dir = get_NMS_dir(fpath)
            self.scene_path = post_path(fpath, self.root_dir)
            if self.scene_path is None:
                self.scene_path = fpath
        # Scene_basename is the final component of the scene path.
        # Ie. the file name without the extension
        self.scene_basename, _ = op.splitext(self.scene_path)
        if self.scene_basename.lower().endswith(".scene"):
            self.scene_basename = self.scene_basename[:-6]

        # To optimise loading of referenced scenes, check to see if the current scene has already been loaded
        # into blender. If so, simply make a copy of the mesh object and place it appropriately.
        if self.scene_path in self.ref_scenes:
            self._add_existing_to_scene()
            self.requires_render = False
            return

        tmpdir = mkdtemp()

        # Determine the type of file provided and get the mxml and mbin file
        # paths for that file.
        if not self.scene_path.lower().endswith(".mbin"):
            # Use the original full path to convert
            # TODO: This will not work on linux.
            cmd = [mbincompiler_path, f"--output-dir={normalise_path(tmpdir)}", fpath]
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
                pass
            # There will be only one file here...
            self.scene_path = op.join(tmpdir, os.listdir(tmpdir)[0])

        # Annoyingly, some nodes may have the same name. As we traverse the
        # tree in order we should be able to just have the index stored here
        # and increment as needed.
        self.name_clash_orders = dict()

        self.parent_obj = parent_obj
        self.settings = settings
        self.dep_graph = bpy.context.evaluated_depsgraph_get()
        # When scenes contain reference nodes there can be clashes with names.
        # To ensure correct parenting of objects in blender, we will keep track
        # of what objects exist within a scene as there will be no name clashes
        # within each scene.
        self.local_objects = dict()

        self.requires_render = True
        self.has_errors = False
        self.scn = bpy.context.scene
        self.scene_ctx = SceneOp(bpy.context)

        # Find the local name of the scene (relative to the NMS PCBANKS dir)
        # This needs to be read from the mbin file, so ensure we are either
        # reading from it or construct the name.
        with witch.section("read_scene"):
            with load_file(self.scene_path, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                MBINHeader.read(f)
                self._scene_node_data = TkSceneNodeData.read(f)
                self.scene_name = self._scene_node_data.Name
        print(f"Loading {self.scene_name}")
        shutil.rmtree(tmpdir)

        self.ref_scenes[self.scene_path] = list()

        self.data = None
        self.position_vertex_elements = []
        self.vertex_elements = []
        self.bh_data = []
        self.materials = {}
        self.entities: set[str] = set()
        self.animations = {}
        # This list of joints is used to add all the bones if needed
        self.joints: list[SceneNodeData] = []
        self.skinned_meshes = []
        self.mesh_binding_data = None
        # Inverse bind matrices are the global transforms of the joints parent
        self.inv_bind_matrices = {}
        # Bind matrices are the local transforms of the intial states of the
        # joint itself.
        self.bind_matrices = {}

        # Change to render with cycles
        self.scn.render.engine = RENDER_ENGINE

        self.scene_node_data = SceneNodeData(self._scene_node_data)
        # Once we have loaded this, we need to do a sanity check to make sure
        # that the scene file actually has an associated geometry file.
        # Some do not (such as emitter scenes, more of which were added in the
        # 3.80 update.)
        if not self.scene_node_data.Attribute('GEOMETRY'):
            self.requires_render = False
            return
        if not self.from_pak:
            self.directory = op.dirname(self.scene_node_data.Name)
            self.local_root_folder = base_path(self.local_directory, self.directory)
        # remove the name of the top level object
        self.scene_node_data.info.Name = None
        # Try and find the geometry file locally.
        self.geometry_fname = self.scene_node_data.Attribute("GEOMETRY").lower() + ".pc"
        if not self.from_pak:
            self.geometry_fname = op.join(
                self.local_directory,
                op.relpath(
                    self.scene_node_data.Attribute("GEOMETRY"),
                    self.directory
                ) + ".PC"
            )
            if op.exists(self.geometry_fname):
                self.geometry_fname = op.join(
                    self.root_dir,
                    self.scene_node_data.Attribute("GEOMETRY") + ".PC"
                )

        self.descriptor_data = TkModelDescriptorList([])

        self.geometry_stream_file = self.geometry_fname.lower().replace('geometry', 'geometry.data')

        # Get the information about what data the geometry file contains
        with witch.section("read_geometry"):
            with load_file(self.geometry_fname, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                header = MBINHeader.read(f)
                assert header.header_namehash == NAMEHASH_MAPPING["TkGeometryData"]
                geometry_data = TkGeometryData.read(f)

        if geometry_data.Indices16Bit:
            self.mesh_indexes = []
            for idx_val in geometry_data.IndexBuffer:
                self.mesh_indexes.extend((idx_val & 0xFFFF, idx_val >> 16))
        else:
            self.mesh_indexes = geometry_data.IndexBuffer
        self.CollisionIndexCount = geometry_data.CollisionIndexCount
        self.Indices16Bit = geometry_data.Indices16Bit
        self.vert_pos_count = geometry_data.PositionVertexLayout.ElementCount
        self.vert_pos_stride = geometry_data.PositionVertexLayout.Stride
        self.vert_extras_count = geometry_data.VertexLayout.ElementCount
        self.vert_extras_stride = geometry_data.VertexLayout.Stride
        for ve in geometry_data.PositionVertexLayout.VertexElements:
            self.position_vertex_elements.append(
                {
                    "semID": ve.SemanticID,
                    "size": ve.Size,
                    "type": ve.Type,
                    "offset": ve.Offset,
                }
            )
        for ve in geometry_data.VertexLayout.VertexElements:
            self.vertex_elements.append(
                {
                    "semID": ve.SemanticID,
                    "size": ve.Size,
                    "type": ve.Type,
                    "offset": ve.Offset,
                }
            )

        self.mesh_binding_data = {
            "JointBindings": geometry_data.JointBindings,
            "SkinMatrixLayout": geometry_data.SkinMatrixLayout,
            "MeshBaseSkinMat": geometry_data.MeshBaseSkinMat,
        }

        self.scn.nmsdk_anim_data.has_bound_mesh = len(geometry_data.JointBindings) == 0

        # load all the bounded hull data
        self.bh_data = geometry_data.BoundHullVerts

        # load all the mesh metadata
        self.mesh_metadata = {
            x.IdString.upper(): gstream_info(
                x.VertexDataSize,
                x.VertexDataOffset,
                x.IndexDataSize,
                x.IndexDataOffset,
                x.VertexPositionDataSize,
                x.VertexPositionDataOffset,
            )
            for x in geometry_data.StreamMetaDataArray
        }

# region public methods

    def load_animations(self, import_idle_anims: bool):
        """ Handle the loading of the animations. """
        # TODO: Fixme! This needs to read from the pak files too...

        _loadable_anim_data = self.scn.nmsdk_anim_data.loadable_anim_data
        # If there are no entities, there is no animation data. (Even implicit
        # animations have an entity associated.)
        if len(self.entities) == 0:
            print("Error: Could not find any associated entity files.")
            return
        # Iterate over the entity files to collate all the animation data
        animation_data: dict[str, TkAnimationData] = {}
        ctx_nonignored_namehashes.set({0x6E59DA5E})
        for entity in self.entities:
            with load_file(entity, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                MBINHeader.read(f)
                entity_data = TkAttachmentData.read(f)
                anim_data: list[TkAnimationComponentData] = [att for att in entity_data.iter_attachments(TkAnimationComponentData)]
                if anim_data:
                    print(f"{entity} has {len(entity_data.Components)} components which contains {len(anim_data)} TkAnimationComponentData's")
                    for anim in anim_data:
                        # Special case the idle data since there can also be an "IDLE" animation which is
                        # different (ie. an actual animation).
                        animation_data["__idle__"] = anim.Idle
                        for _anim in anim.Anims:
                            animation_data[_anim.Anim] = _anim
        if len(animation_data) == 0:
            # If there are no animations added by this scene just return to
            # save time.
            return
        # Find out how many animations have been found in this scene.
        # If the total number is greater than 10 then we don't want to render
        # them all as it gets too slow to import a scene then.
        print(f"Found {len(animation_data)} animations to be loaded")

        # Update the global animation data dictionary
        # _loadable_anim_data.update(local_anims)

        max_anims = self.settings.get('max_anims', 10)
        if max_anims == 0:
            load_anims = False
        elif max_anims != -1:
            if len(_loadable_anim_data) < max_anims:
                load_anims = True
            else:
                print('Warning! Too many animations detected!')
                load_anims = False
        else:
            load_anims = True

        if self.settings.get("import_idle_anims", False):
            # We can import just the idle animation data... Should be fairly quick...
            if (_idle_anim_data := animation_data.get("__idle__")) is not None:
                if _idle_anim_data.Filename:
                    with load_file(
                        _idle_anim_data.Filename, self.root_dir, self.from_pak, self.pak_data_mapping
                    ) as f:
                        MBINHeader.read(f)
                        idle_anim_data = TkAnimMetadata.read(f)
                    add_animation_to_scene(bpy.context.scene, "", idle_anim_data, True)
        return

        # self._fix_anim_data(local_anims, self.root_dir)

        if not self.scn.nmsdk_anim_data.anims_loaded:
            # Only update the value if going from False -> True
            self.scn.nmsdk_anim_data.anims_loaded = load_anims

        if load_anims:
            for anim_name, anim_data in local_anims.items():
                print(anim_name, anim_data)
                fpath = anim_data['Filename']
                # Call the animation loading operator with the info
                if anim_name not in self.scn.nmsdk_anim_data.loaded_anims:
                    if op.exists(fpath):
                        bpy.ops.nmsdk.animation_handler(
                            anim_name=anim_name,
                            anim_path=fpath)

        # Ensure the animation starts on frame 0
        self.scn.frame_start = 0
        self.scn.frame_current = 0

    def load_mesh(self, mesh_node: SceneNodeData):
        """ Load the mesh.
        This will load the mesh data into memory then deserialize the actual
        vertex and index data from the gstream mbin.
        """
        self._deserialize_gstream_data(mesh_node)
        mesh_node._generate_bounded_hull(self.bh_data)

    def load_collision_mesh(self, mesh_node: SceneNodeData):
        """ Load the collision mesh data.
        This only needs the bounded hull data and the index buffer with the
        VERTRSTART value subtracted off.
        """
        idx_start = int(mesh_node.Attribute('BATCHSTART'))
        idx_count = int(mesh_node.Attribute('BATCHCOUNT'))
        idxs = self.mesh_indexes[idx_start: idx_start + idx_count]
        mesh_node.idxs.extend([idx - int(mesh_node.Attribute('VERTRSTART')) for idx in idxs])
        mesh_node._generate_geometry(from_bh=True)
        mesh_node._generate_bounded_hull(self.bh_data)

    def render_mesh(self, mesh_ID: str):
        """Render the specified mesh in the blender view. """
        obj = self.scene_node_data.get(mesh_ID)
        if obj.Type == 'MESH':
            obj.metadata = self._handle_duplicate_mesh_names(mesh_ID.upper())
            self.load_mesh(obj)
            self._add_mesh_to_scene(obj, standalone=True)
        elif obj.Type == 'LOCATOR' or obj.Type == 'JOINT':
            self._add_empty_to_scene(obj, standalone=True)
        self.state = {'FINISHED'}

    @witch.section("render_scene")
    def render_scene(self):
        """ Render the scene in the blender view. """
        # First, add the empty root object that everything will be a
        # child of.
        print('rendering {0}'.format(self.scene_name))
        if self.parent_obj is None:
            # First, remove everything else in the scene
            if self.settings.get('clear_scene', True):
                self._clear_prev_scene()
            self._add_empty_to_scene(self.scene_node_data)
        # Get all the joints in the scene
        for obj in self.scene_node_data.iter():
            if obj.Type == 'JOINT':
                self.joints.append(obj)
                self.scn.nmsdk_anim_data.joints.append(obj.Name)
        t1 = time.perf_counter()

        try:
            self.geometry_stream_data = load_file_unsafe(
                self.geometry_stream_file,
                self.root_dir,
                self.from_pak,
                self.pak_data_mapping,
            )

            for i, obj in enumerate(self.scene_node_data.iter()):
                added_obj = None
                if obj.Type == 'MESH':
                    if obj.Name.upper() in self.mesh_metadata:
                        obj.metadata = self._handle_duplicate_mesh_names(
                            obj.Name.upper())
                    else:
                        print('Failed to load {0}. Please make sure your scene '
                            'file and geometry data are the same '
                            'versions.'.format(obj.Name))
                        continue
                    try:
                        with witch.section("load_mesh"):
                            self.load_mesh(obj)
                        with witch.section("add_mesh_to_scene"):
                            added_obj = self._add_mesh_to_scene(obj)

                    except MeshError:
                        # In the case of a mesh error, we will pass and leave the
                        # `added_obj` as None to handle later.
                        pass
                elif obj.Type in ('LOCATOR', 'JOINT', 'REFERENCE'):
                    added_obj = self._add_empty_to_scene(obj)
                elif obj.Type == 'COLLISION':
                    if self.settings.get('import_collisions', True):
                        if obj.Attribute('TYPE') == 'Mesh':
                            self.load_collision_mesh(obj)
                            added_obj = self._add_mesh_collision_to_scene(obj)
                        else:
                            added_obj = self._add_primitive_collision_to_scene(obj)
                elif obj.Type == 'LIGHT':
                    added_obj = self._add_light_to_scene(obj)
                # Get the added object and give it its scene node data so that it
                # can be rexported in a more faithful way.
                # if added_obj:
                #     added_obj['scene_node'] = {'idx': i, 'data': asdict(obj.info)}
        except Exception:
            print(f"An exception ocurred while rendering {self.scene_path}:")
            print(traceback.format_exc())
            if not self.from_pak:
                self.geometry_stream_data.close()

        # We will add an armature to the scene irrespective of whether we have
        # any animations, only if we are asked to import bones.
        import_bones = (self.settings.get("import_bones", False) or
                        self.settings.get('import_anims', False))
        import_anims = self.settings.get('import_anims', False)
        if import_bones and self.joints:
            armature = self._add_armature_to_scene()
            for joint in self.joints:
                self._add_bone_to_scene(joint, armature)
            # Now that we have the armature set up, apply modifiers to each of
            # the meshes to bind them.
            for mesh_obj in self.skinned_meshes:
                mod = mesh_obj.modifiers.new('Armature', 'ARMATURE')
                mod.object = bpy.data.objects['Armature']
        if import_anims and self.settings.get('max_anims', 10) != 0:
            self.load_animations(self.settings.get('import_idle_anims', True))
            bpy.ops.nmsdk._change_animation(anim_names='None')

        # If the loaded scene is a proc-gen scene, load the info in.
        if self.scn['scene_node'].NMSReference_props.is_proc:
            self._apply_proc_gen_info()

        t2 = time.perf_counter()
        print(f"Took {t2 - t1:.05f}s to fully render {self.scene_path}")

        self.state = {'FINISHED'}

# region private methods

    def _add_armature_to_scene(self) -> Armature:
        """ Each joint will be added as an armature. """
        armature = bpy.data.armatures.new(self.scene_basename)
        obj = bpy.data.objects.new('Armature', armature)
        obj.NMSNode_props.node_types = 'None'
        self.scene_ctx.link_object(obj)
        if self.parent_obj is None:
            obj.parent = self.local_objects[self.scene_basename]
        else:
            obj.parent = self.local_objects[self.parent_obj]
        return obj

    def _add_bone_to_scene(self, scene_node: SceneNodeData,
                           armature: Armature):
        # Let's get all the data collection out of the way
        if self.scn.nmsdk_anim_data.has_bound_mesh:
            joint_index = scene_node.Attribute('JOINTINDEX', int)
            joint_binding_data: TkJointBindingData = self.mesh_binding_data['JointBindings'][joint_index]
            inv_bind_matrix = joint_binding_data.InvBindMatrix
            inv_bind_matrix = Matrix([inv_bind_matrix[:4],
                                      inv_bind_matrix[4:8],
                                      inv_bind_matrix[8:12],
                                      inv_bind_matrix[12:]])
            inv_bind_matrix.transpose()
            bind_trans = joint_binding_data.BindTranslate
            bind_rot = joint_binding_data.BindRotate
            bind_sca = joint_binding_data.BindScale

            # Assign the bind matrix so we can do easy lookup of it later for
            # applying animations.
            # Ironically, the inverse bind matrix is strored uninverted, and
            # the bind matrix is stored inverted...
            self.inv_bind_matrices[scene_node.Name] = inv_bind_matrix

            # Let's create the bone now
            # All changes to Bones have to be in EDIT mode or _bad things
            # happen_
            with edit_object(armature) as data:
                bone = data.edit_bones.new(scene_node.Name)
                bone.use_inherit_rotation = True
                bone.inherit_scale = "FIX_SHEAR"

                self.scn.objects[scene_node.Name]['bind_data'] = (
                    Vector(bind_trans[:3]),
                    Quaternion((bind_rot[3],
                                bind_rot[0],
                                bind_rot[1],
                                bind_rot[2])),
                    Vector(bind_sca[:3]))
                """
                self.bind_matrices[scene_node.Name] = (Vector(bind_trans[:3]),
                                                    Quaternion((bind_rot[3],
                                                            bind_rot[0],
                                                            bind_rot[1],
                                                            bind_rot[2])),
                                                    Vector(bind_sca[:3]))
                """

                if scene_node.parent.Type == 'JOINT':
                    bone.matrix = self.inv_bind_matrices[
                        scene_node.parent.Name]

                bone.tail = inv_bind_matrix.inverted().to_translation()

                if bone.length == 0:
                    bone.tail = bone.head + Vector([0, 10 ** (-4), 0])

                if scene_node.parent.Type == 'JOINT':
                    bone.parent = armature.data.edit_bones[
                        scene_node.parent.Name]

                bone.use_connect = True

                # NMS defines some bones used in animations with 0 transform,
                # eg. Toy Cube.
                # This causes bone creation to fail, we need to move the tail
                # slightly.
                # Note that MMD Tools would have to deal with this too.
                while scene_node:
                    if scene_node.Transform['Trans'] != (0.0, 0.0, 0.0):
                        break
                    bone.tail += Vector([0, 0, 10 ** (-4)])
                    scene_node = scene_node.parent
        else:
            # Add bones but based on their associated joint data.
            # Hopefully the above chunk can be merged into this if it ends up
            # working correctly...
            with edit_object(armature) as data:
                if scene_node.parent.Type != 'JOINT':
                    return
                bone = data.edit_bones.new(scene_node.Name)
                bone.use_inherit_rotation = True
                bone.inherit_scale = "FIX_SHEAR"  # TODO: Investigate the other options...
                bone.use_local_location = True
                bone.use_connect = True
                if scene_node.parent.Name in armature.data.edit_bones:
                    bone.parent = armature.data.edit_bones[
                        scene_node.parent.Name]

                # Not sure whether to use:
                bone.matrix = scene_node.parent.matrix_local
                bone.tail = scene_node.matrix_local.decompose()[0]
                # or something using
                # bone.transform(scene_node.matrix_local)

    def _add_bounds_to_scene(self, scene_node: SceneNodeData):
        x = (scene_node.Attribute("AABBMINX", float),
             scene_node.Attribute("AABBMAXX", float))
        y = (scene_node.Attribute("AABBMINY", float),
             scene_node.Attribute("AABBMAXY", float))
        z = (scene_node.Attribute("AABBMINZ", float),
             scene_node.Attribute("AABBMAXZ", float))
        name = op.basename(scene_node.Name) + '_BBOX'
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0,
                              matrix=BB_transform_matrix(x, y, z))
        bm.to_mesh(mesh)
        bm.free()
        del bm
        bbox_obj = bpy.data.objects.new(name, mesh)
        bbox_obj.NMSNode_props.node_types = 'None'
        self.scene_ctx.link_object(bbox_obj)

    def _add_empty_to_scene(self, scene_node: SceneNodeData, standalone: bool = False):
        """ Adds the given scene node data to the Blender scene.

        Parameters
        ----------
        scene_node
            The scene node object which contains the attributes and children
            nodes.
        standalone
            Whether or not the scene_node is provided by itself and not part
            of a complete scene. This is used to indicate that a single mesh
            part is being rendered.
        """
        # We can determine if a scene is the root scene by whether it has a
        # 'GEOMETRY' key in the attributes.
        if (scene_node.Attribute('GEOMETRY') is not None
                and self.parent_obj is None):
            empty_mesh = bpy.data.meshes.new(self.scene_basename)
            empty_obj = bpy.data.objects.new(self.scene_basename,
                                             empty_mesh)
            empty_obj.NMSNode_props.node_types = 'Reference'
            empty_obj.NMSReference_props.reference_path = self.scene_name + '.SCENE.MBIN'
            empty_obj.matrix_world = ROT_MATRIX
            self.scene_ctx.link_object(empty_obj)
            select_object(empty_obj)

            # Determine if the scene has LOD info
            if scene_node.Attribute('NUMLODS', int) > 1:
                lods = []
                for i in range(1, scene_node.Attribute('NUMLODS', int)):
                    lods.append(scene_node.Attribute(f'LODDIST{i}', float))
                empty_obj.NMSReference_props.num_lods = len(lods)
                # TODO: make this more robust... What if there are 4 LOD's?
                if empty_obj.NMSReference_props.num_lods < 3:
                    # pad it with 0's until it is 3
                    j = 3 - empty_obj.NMSReference_props.num_lods
                    for _ in range(j):
                        lods.append(0)
                empty_obj.NMSReference_props.lod_levels = lods[:3]
                empty_obj.NMSReference_props.has_lods = True

            # Add a custom property so that if it is exported with the
            # 'preserve node info' option selected then it can use this info.
            empty_obj['imported_from'] = self.scene_name
            # Also add this object to the scene in a sneaky way so that we can
            # always find this node easily.
            self.scn['scene_node'] = empty_obj
            # check if the scene is proc-gen
            descriptor_path = normalise_path(self.scene_name + '.DESCRIPTOR.MBIN').lower()
            if self.from_pak:
                # See if the descriptor exists.
                if descriptor_path not in self.pak_data_mapping:
                    descriptor_path = None
            else:
                if op.exists(op.join(self.local_directory, op.basename(descriptor_path))):
                    descriptor_path = op.join(self.local_directory, op.basename(descriptor_path))
                elif op.exists(op.join(self.root_dir, descriptor_path)):
                    descriptor_path = op.join(self.root_dir, descriptor_path)
                else:
                    descriptor_path = None

            if descriptor_path is not None:
                empty_obj.NMSReference_props.is_proc = True
                with load_file(descriptor_path, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                    MBINHeader.read(f)
                    self.descriptor_data = TkModelDescriptorList.read(f)
            else:
                pass
            print(f"Adding {self.scene_basename} empty obj to local_objects")
            self.local_objects[self.scene_basename] = empty_obj
            return empty_obj

        # Otherwise just assign everything as usual...
        name = scene_node.Name

        # add the objects entity file if it has one
        if scene_node.Attribute('ATTACHMENT') is not None:
            self.entities.add(scene_node.Attribute('ATTACHMENT'))

        # create a new empty instance
        empty_mesh = bpy.data.meshes.new(name)
        empty_obj = bpy.data.objects.new(name, empty_mesh)
        empty_obj.NMSNode_props.node_types = TYPE_MAP[scene_node.Type]

        self.local_objects[scene_node] = empty_obj

        # Set the rotation mode to be in quaternions so that anims work
        # correctly
        empty_obj.rotation_mode = 'QUATERNION'

        if not standalone:
            if self.parent_obj is not None and scene_node.parent.Name is None:
                # Direct child of the reference node
                empty_obj.parent = self.parent_obj
                self.ref_scenes[self.scene_path].append(empty_obj)
            elif scene_node.parent.Name is not None:
                # Other child
                if scene_node.parent in self.local_objects:
                    empty_obj.parent = self.local_objects[scene_node.parent]
                else:
                    # In this case the parent object doesn't exist (maybe it is
                    # corrupt?). Skip this object.
                    return
            else:
                # Direct child of loaded scene
                empty_obj.parent = self.local_objects[self.scene_basename]
            # Apply the transform
            empty_obj.matrix_local = scene_node.matrix_local
        else:
            empty_obj.matrix_world = ROT_MATRIX * empty_obj.matrix_world

        # link the object then update the scene so that the above transforms
        # can be applied before we do the NMS -> blender scene rotation
        self.scene_ctx.link_object(empty_obj)
        self.dep_graph.update()

        # Check to see if the empty node has an associated entity
        if scene_node.Type == 'LOCATOR':
            entity_path = scene_node.Attribute('ATTACHMENT')
            if entity_path != '' and entity_path is not None:
                empty_obj.NMSLocator_props.has_entity = True
                empty_obj.NMSEntity_props.name_or_path = entity_path

        if scene_node.Type == 'JOINT':
            empty_obj.NMSJoint_props.joint_id = scene_node.Attribute('JOINTINDEX', int)

        if scene_node.Type == 'REFERENCE':
            print(f"Reference node name: {scene_node.Name}")
            empty_obj.NMSReference_props.reference_path = scene_node.Attribute('SCENEGRAPH')
            if self.from_pak:
                ref_scene_path = scene_node.Attribute('SCENEGRAPH')
            else:
                ref_scene_path = op.join(self.root_dir, scene_node.Attribute('SCENEGRAPH'))
            if self.from_pak or op.exists(ref_scene_path):
                if self.settings.get('import_recursively', True):
                    print(f'loading referenced scene: {ref_scene_path}')
                    with witch.section("import_referenced"):
                        sub_scene = ImportScene(
                            ref_scene_path,
                            empty_obj,
                            self.ref_scenes,
                            self.settings,
                            self.from_pak,
                        )
                        if sub_scene.requires_render:
                            sub_scene.render_scene()
            else:
                print(
                    f"The reference node {name} has a reference to a path "
                    f"that doesn't exist ({ref_scene_path})"
                )

        return empty_obj

    def _add_light_to_scene(self, scene_node: SceneNodeData,
                            standalone: bool = False):
        """ Adds the given light node to the Blender scene. """
        name = scene_node.Name

        # Create a new light instance
        light = bpy.data.lights.new(name, 'POINT')

        # Apply a number of settings relating to the light
        # light.color = Color((float(scene_node.Attribute('COL_R')),
        #                      float(scene_node.Attribute('COL_G')),
        #                      float(scene_node.Attribute('COL_B'))))
        light.color = (float(scene_node.Attribute('COL_R')),
                       float(scene_node.Attribute('COL_G')),
                       float(scene_node.Attribute('COL_B')))
        light.use_nodes = True
        # Divide by some arbitary amount... This will need to be played with...
        light_intensity = float(scene_node.Attribute('INTENSITY'))
        intensity = light_intensity / 100
        light.node_tree.nodes['Emission'].inputs[1].default_value = intensity
        light_obj = bpy.data.objects.new(name, light)
        light_obj.NMSNode_props.node_types = TYPE_MAP[scene_node.Type]
        # This is pretty much just a hack until I can get the value directly
        # from the node. This is just easier really...
        light_obj.NMSLight_props.intensity_value = light_intensity

        self.local_objects[scene_node] = light_obj

        if not standalone:
            if self.parent_obj is not None and scene_node.parent.Name is None:
                # Direct child of the reference node
                light_obj.parent = self.parent_obj
                self.ref_scenes[self.scene_path].append(light_obj)
            elif scene_node.parent.Name is not None:
                # Other child
                if scene_node.parent in self.local_objects:
                    light_obj.parent = self.local_objects[scene_node.parent]
                else:
                    # In this case the parent object doesn't exist (maybe it is
                    # corrupt?). Skip this object.
                    return
            else:
                # Direct child of loaded scene
                light_obj.parent = self.local_objects[self.scene_basename]
            light_obj.matrix_local = scene_node.matrix_local
        else:
            light_obj.matrix_world = ROT_MATRIX * light_obj.matrix_world

        # Set the rotation mode to be in quaternions so that anims work
        # correctly
        light_obj.rotation_mode = 'QUATERNION'

        self.scene_ctx.link_object(light_obj)
        self.dep_graph.update()

        return light_obj

    def _add_mesh_collision_to_scene(self, scene_node: SceneNodeData):
        """ Adds the given collision node to the Blender scene. """
        name = op.basename(scene_node.Name)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([x[0:3] for x in scene_node.bounded_hull],
                         [],
                         scene_node.faces)
        bh_obj = bpy.data.objects.new(name, mesh)

        bh_obj.NMSNode_props.node_types = 'Collision'
        bh_obj.NMSCollision_props.collision_types = 'Mesh'

        if self.parent_obj is not None and scene_node.parent.Name is None:
            # Direct child of reference node
            bh_obj.parent = self.parent_obj
            self.ref_scenes[self.scene_path].append(bh_obj)
        elif scene_node.parent.Name is not None:
            # Other child
            if scene_node.parent in self.local_objects:
                bh_obj.parent = self.local_objects[scene_node.parent]
            else:
                # In this case the parent object doesn't exist (maybe it is
                # corrupt?). Skip this object.
                return
        else:
            # Direct child of loaded scene
            bh_obj.parent = self.local_objects[self.scene_basename]

        bh_obj.matrix_local = scene_node.matrix_local

        self.scene_ctx.link_object(bh_obj)
        self.local_objects[scene_node] = bh_obj

        # Set the rotation mode to be in quaternions so that anims work
        # correctly
        bh_obj.rotation_mode = 'QUATERNION'

        if not self.settings.get('show_collisions', False):
            # Only draw the collisions if they are wanted
            bh_obj.hide_set(True)
        # Never show the object in the render.
        bh_obj.hide_render = True

        return bh_obj

    def _add_primitive_collision_to_scene(self, scene_node: SceneNodeData):
        name = op.basename(scene_node.Name) + '_COLL'
        mesh = bpy.data.meshes.new(name)
        coll_type = scene_node.Attribute('TYPE')
        bm = bmesh.new()
        if coll_type == 'Box':
            bmesh.ops.create_cube(bm, size=1.0)
            scale_mult = [float(scene_node.Attribute('WIDTH')),
                          float(scene_node.Attribute('HEIGHT')),
                          float(scene_node.Attribute('DEPTH'))]
        elif coll_type == 'Sphere':
            bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
            scale_mult = [float(scene_node.Attribute('RADIUS')),
                          float(scene_node.Attribute('RADIUS')),
                          float(scene_node.Attribute('RADIUS'))]
        elif coll_type == 'Cylinder':
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True,
                                  radius1=1, radius2=1, depth=1.0,
                                  segments=20, matrix=ROT_MATRIX)
            scale_mult = [float(scene_node.Attribute('RADIUS')),
                          float(scene_node.Attribute('HEIGHT')),
                          float(scene_node.Attribute('RADIUS'))]
        elif coll_type == 'Capsule':
            capsule = bmesh.ops.create_icosphere(
                bm, subdivisions=4, radius=1,
                matrix=Matrix.Scale(0.25, 4, Vector((0, 1, 0))))
            # select the top set of verts
            for bmvert in capsule['verts']:
                if bmvert.co[1] > 0:
                    bmvert.co[1] += 0.25
                elif bmvert.co[1] < 0:
                    bmvert.co[1] -= 0.25

            scale_mult = [float(scene_node.Attribute('RADIUS')),
                          float(scene_node.Attribute('HEIGHT')),
                          float(scene_node.Attribute('RADIUS'))]
        else:
            print('Skipping unsupported coll_type: {0}'.format(coll_type))
            bm.free()
            del bm
            return
        # Convert the bmesh back to the mesh
        bm.to_mesh(mesh)
        bm.free()
        del bm

        coll_obj = bpy.data.objects.new(name, mesh)
        coll_obj.NMSNode_props.node_types = 'Collision'
        coll_obj.NMSCollision_props.collision_types = coll_type

        # get transform and apply
        transform = scene_node.Transform['Trans']
        coll_obj.location = Vector(transform)
        # get rotation and apply
        rotation = scene_node.Transform['Rot']
        coll_obj.rotation_mode = 'ZXY'
        coll_obj.rotation_euler = rotation
        # get scale and apply
        scale = scene_node.Transform['Scale']
        mod_scale = tuple(scale_mult[i] * scale[i] for i in range(3))
        coll_obj.scale = Vector(mod_scale)

        # TODO: make its own function
        if self.parent_obj is not None and scene_node.parent.Name is None:
            # Direct child of reference node
            coll_obj.parent = self.parent_obj
            self.ref_scenes[self.scene_path].append(coll_obj)
        elif scene_node.parent.Name is not None:
            # Other child
            if scene_node.parent in self.local_objects:
                coll_obj.parent = self.local_objects[scene_node.parent]
            else:
                # In this case the parent object doesn't exist (maybe it is
                # corrupt?). Skip this object.
                return
        else:
            # Direct child of loaded scene
            coll_obj.parent = self.local_objects[self.scene_basename]

        self.scene_ctx.link_object(coll_obj)
        self.local_objects[scene_node] = coll_obj

        # Set the rotation mode to be in quaternions so that anims work
        # correctly
        coll_obj.rotation_mode = 'QUATERNION'

        if not self.settings.get('show_collisions', False):
            # Only draw the collisions if they are wanted
            coll_obj.hide_set(True)
        # never show the object in the render
        coll_obj.hide_render = True

        return coll_obj

    def _add_existing_to_scene(self):
        # For each object under the existing scene path, copy and reparent.
        for obj in self.ref_scenes[self.scene_path]:
            new_obj = obj.copy()
            new_obj.parent = self.parent_obj
            self.scn.collection.objects.link(new_obj)

    def _add_mesh_to_scene(self, scene_node: SceneNodeData, standalone: bool = False):
        """ Adds the given scene node data to the Blender scene.

        Parameters
        ----------
        standalone : bool
            Whether or not the scene_node is provided by itself and not part
            of a complete scene. This is used to indicate that a single mesh
            part is being rendered.
        """
        name = scene_node.Name
        mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
        vert_count = len(scene_node.np_verts) // 3
        idx_count = len(scene_node.np_idxs)
        face_count = idx_count // 3
        mesh.vertices.add(vert_count)
        mesh.loops.add(idx_count)
        mesh.polygons.add(face_count)

        mesh.vertices.foreach_set("co", scene_node.np_verts)
        if scene_node.np_norms is not None:
            # Flatten the normals in "Fortran" order (ie. down columns, then across rows) because of the
            # format of the normal data. It's done this way to avoid a reshape earlier on...
            mesh.vertices.foreach_set("normal", scene_node.np_norms.flatten(order="F"))

        mesh.polygons.foreach_set("loop_start", range(0, idx_count, 3))
        mesh.loops.foreach_set("vertex_index", scene_node.np_idxs)

        mesh.uv_layers.new(name=f"{name}_UVMap")
        uvs_new = np.take(scene_node.np_uvs, scene_node.np_idxs, axis=0)
        mesh.uv_layers.active.data.foreach_set("uv", uvs_new.flatten())

        mesh.validate()
        mesh.update()

        # add the objects entity file if it has one
        if scene_node.Attribute('ATTACHMENT') is not None:
            self.entities.add(scene_node.Attribute('ATTACHMENT'))

        mesh_obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
        mesh_obj.NMSNode_props.node_types = 'Mesh'

        self.local_objects[scene_node] = mesh_obj

        # give object correct parent
        if not standalone:
            if self.parent_obj is not None and scene_node.parent.Name is None:
                # Direct child of reference node
                mesh_obj.parent = self.parent_obj
                self.ref_scenes[self.scene_path].append(mesh_obj)
            elif scene_node.parent.Name is not None:
                # Other child
                if scene_node.parent in self.local_objects:
                    mesh_obj.parent = self.local_objects[scene_node.parent]
                else:
                    # In this case the parent object doesn't exist (maybe it is
                    # corrupt?). Skip this object.
                    print(f"Warning: Couldn't find the appropriate parent for {scene_node.Name}")
                    return
            else:
                # Direct child of loaded scene
                mesh_obj.parent = self.local_objects[self.scene_basename]
            mesh_obj.matrix_local = scene_node.matrix_local
        else:
            mesh_obj.matrix_world = ROT_MATRIX @ mesh_obj.matrix_world

        # Set the rotation mode to be in quaternions so that anims work
        # correctly
        mesh_obj.rotation_mode = 'QUATERNION'

        # link the object then update the scene so that the above transforms
        # can be applied before we do the NMS -> blender scene rotation
        self.scene_ctx.link_object(mesh_obj)
        self.dep_graph.update()

        # Add vertex colour
        if (colours := scene_node.np_colours) is not None:
            colour_layer_name = f"{name}_colour"
            if (colour_attribute := mesh.color_attributes.get(colour_layer_name)) is None:
                colour_attribute = mesh.color_attributes.new(f"{name}_colour", "FLOAT_COLOR", "CORNER")
            for loop in mesh_obj.data.loops:
                colour = colours[loop.vertex_index] / 255.0
                colour_attribute.data[loop.index].color = colour

        # Add vertexes to mesh groups
        if self.mesh_binding_data is not None:
            first_skin_mat = int(scene_node.Attribute('FIRSTSKINMAT'))
            last_skin_mat = int(scene_node.Attribute('LASTSKINMAT'))
            skin_mats = self.mesh_binding_data['SkinMatrixLayout'][first_skin_mat: last_skin_mat]
            for skin_mat in skin_mats:
                joint = self._find_joint(skin_mat)
                mesh_obj.vertex_groups.new(name=joint.Name)
            if len(skin_mats) != 0:
                for i, vert in enumerate(mesh_obj.data.vertices):
                    blend_indices = scene_node.np_blendIndex[i]
                    blend_weights = scene_node.np_blendWeight[i][0: 3]
                    for j, bw in enumerate(blend_weights):
                        if bw != 0:
                            mesh_obj.vertex_groups[blend_indices[j]].add(
                                index=[vert.index], weight=bw, type='ADD')
            self.skinned_meshes.append(mesh_obj)

        # sort out materials
        mat_path = self._get_material_path(scene_node)
        material = None
        if mat_path is not None:
            if mat_path not in self.materials:
                if self.from_pak:
                    root_folder = self.root_dir
                else:
                    root_folder = self.local_root_folder
                material = create_material_node(
                    mat_path,
                    root_folder,
                    self.from_pak,
                    self.pak_data_mapping,
                )
                if material:
                    self.materials[mat_path] = material
            else:
                material = self.materials[mat_path]
            mesh_obj.NMSMesh_props.material_path = scene_node.Attribute(
                'MATERIAL')
        if material is not None:
            mesh_obj.data.materials.append(material)
            mesh_obj.active_material = material

        # Check to see if the mesh has an associated entity
        entity_path = scene_node.Attribute('ATTACHMENT')
        if entity_path != '' and entity_path is not None:
            mesh_obj.NMSMesh_props.has_entity = True
            mesh_obj.NMSEntity_props.name_or_path = entity_path

        if self.settings.get('draw_hulls', False):
            # create child object for bounded hull
            name = 'BH' + name
            mesh = bpy.data.meshes.new(name)
            bm = bmesh.new()
            # First, add all the verts
            for vert in scene_node.bounded_hull:
                v = bm.verts.new(vert)
            bm.verts.ensure_lookup_table()
            bmesh.ops.convex_hull(bm, input=bm.verts)
            bm.to_mesh(mesh)
            bm.free()

            bh_obj = bpy.data.objects.new(name, mesh)
            bh_obj.NMSNode_props.node_types = 'None'
            bh_obj.parent = mesh_obj
            self.scene_ctx.link_object(bh_obj)
            # Don't show the bounded hull
            bh_obj.hide_set(True)
            bh_obj.hide_render = True
            bh_obj['_dont_export'] = True

        if self.settings.get('draw_bounding_box', False):
            self._add_bounds_to_scene(scene_node)

        return mesh_obj

    def _apply_proc_gen_info(self):
        """ Go over the data in the descriptor and add it to the scene. """
        # We'll create a function here to apply recursively
        def apply_recursively(data: TkModelDescriptorList, parent_collection):
            for resource_descriptor_list in data.List:
                key = resource_descriptor_list.TypeId
                coll = bpy.data.collections.new(key)
                parent_collection.children.link(coll)
                for node in resource_descriptor_list.Descriptors:
                    obj = bpy.data.objects.get(node.Name)
                    if obj:
                        obj.NMSDescriptor_props.choice_types = "Random"
                        obj.NMSDescriptor_props.proc_prefix = key
                        coll.objects.link(obj)
                    for child in node.Children:
                        apply_recursively(child, coll)

        # Let's add a collection for all the proc-gen object's to be linked in
        # so that they can be toggled easily.

        # First, add the root collection
        if not bpy.data.collections.get('Descriptor'):
            desc_coll = bpy.data.collections.new('Descriptor')
            self.scn.collection.children.link(desc_coll)
        else:
            desc_coll = bpy.data.collections['Descriptor']

        # Now, when we apply the above function recursively it will add the
        # objects to the collection.
        apply_recursively(self.descriptor_data, desc_coll)

    def _clear_prev_scene(self):
        """ Remove any existing data in the blender scene. """
        for obj in bpy.data.objects:
            # Don't remove the camera or lamp objects
            if obj.name not in ['Camera', 'Light']:
                bpy.data.objects.remove(obj)
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)
        for mat in bpy.data.materials:
            bpy.data.materials.remove(mat)
        for img in bpy.data.images:
            bpy.data.images.remove(img)
        # Remove any previously existing actions:
        for act in bpy.data.actions:
            bpy.data.actions.remove(act)
        self.scn.nmsdk_anim_data.reset()

    def _deserialize_index_data(self, mesh: SceneNodeData):
        """ Take the raw index data and generate a list of actual index data.

        Parameters
        ----------
        mesh
            SceneNodeData of type MESH to get the vertex data of.
        """
        idx_count = mesh.Attribute('BATCHCOUNT', int)
        face_count = idx_count // 3
        size = mesh.metadata.idx_size // face_count
        if size // 3 == 4:
            dtype = np.uint32
        elif size // 3 == 2:
            dtype = np.uint16
        else:
            err = ("An error has ocurred. Here is the object information:\n"
                   + "Mesh name: {0}\n".format(mesh.Name)
                   + "Mesh indexes: {0}\n".format(face_count * 3)
                   + "Mesh metadata: {0}\n".format(mesh.metadata)
                   + "In geometry file: {0}".format(self.geometry_fname))
            raise MeshError(err)
        
        metadata = cast(gstream_info, mesh.metadata)

        if self.from_pak:
            with load_file(self.geometry_stream_file, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                mesh.np_idxs = np.frombuffer(f.getvalue(), dtype=dtype, count=idx_count, offset=metadata.idx_off + metadata.vert_off)
        else:
            with load_file(self.geometry_stream_file, self.root_dir, self.from_pak, self.pak_data_mapping) as f:
                mesh.np_idxs = np.fromfile(f, dtype=dtype, count=idx_count, offset=metadata.idx_off + metadata.vert_off)

    def _deserialize_gstream_data(self, mesh: SceneNodeData):
        """ Take the raw vertex data and generate a list of actual vertex data.

        Parameters
        ----------
        mesh
            SceneNodeData of type MESH to get the vertex data of.
        """
        # Vertex data
        names: list[str] = []
        pos_names: list[str] = []
        np_fmts: list[str] = []
        np_pos_fmts: list[str] = []
        for ve in self.position_vertex_elements:
            _size = ve['size'] * VERT_TYPE_MAP[ve['type']]['size']
            np_fmt = VERT_TYPE_MAP[ve['type']]['np_fmt']
            if np_fmt is not None:
                np_pos_fmts.append(np_fmt)
            else:
                np_pos_fmts.append(f"S{_size}")
            pos_names.append(REV_SEMANTICS[ve['semID']])
        for ve in self.vertex_elements:
            _size = ve['size'] * VERT_TYPE_MAP[ve['type']]['size']
            np_fmt = VERT_TYPE_MAP[ve['type']]['np_fmt']
            if np_fmt is not None:
                np_fmts.append(np_fmt)
            else:
                np_fmts.append(f"S{_size}")
            names.append(REV_SEMANTICS[ve['semID']])

        # Index data
        idx_count = mesh.Attribute('BATCHCOUNT', int)
        face_count = idx_count // 3
        size = mesh.metadata.idx_size // face_count
        if size // 3 == 4:
            _dtype = np.uint32
        elif size // 3 == 2:
            _dtype = np.uint16
        else:
            err = ("An error has ocurred. Here is the object information:\n"
                   + "Mesh name: {0}\n".format(mesh.Name)
                   + "Mesh indexes: {0}\n".format(face_count * 3)
                   + "Mesh metadata: {0}\n".format(mesh.metadata)
                   + "In geometry file: {0}".format(self.geometry_fname))
            raise MeshError(err)
        idx_dtype = np.dtype({"names": ["index"], "formats": [_dtype]})

        metadata = cast(gstream_info, mesh.metadata)

        num_verts = metadata.vert_size / self.vert_extras_stride
        np_dtype = np.dtype({"names": names, "formats": np_fmts})
        np_pos_dtype = np.dtype({"names": pos_names, "formats": np_pos_fmts})
        if not num_verts % 1 == 0:
            raise ValueError(f'Error with {mesh.Name}: # of verts '
                             f'({metadata.vert_size}) isn\'t consistent '
                             'with the stride value.')

        # Ensure we're always going from the start for each mesh metadata.
        self.geometry_stream_data.seek(metadata.vert_off)
        vert_data = np.rec.fromfile(
            self.geometry_stream_data,
            np_dtype,
            int(num_verts),
        )

        # Load the index data now since it will be immediately after the vertex data.
        mesh.np_idxs = np.rec.fromfile(self.geometry_stream_data, idx_dtype, idx_count).index

        self.geometry_stream_data.seek(metadata.vert_pos_off)
        pos_vert_data = np.rec.fromfile(
            self.geometry_stream_data,
            np_pos_dtype,
            int(num_verts),
        )
        if "Vertices" in pos_names:
            mesh.np_verts = pos_vert_data.Vertices[:, :3].flatten()
        if "UVs" in pos_names:
            pos_vert_data.UVs[..., 1] = 1 - pos_vert_data.UVs[..., 1]
            mesh.np_uvs = pos_vert_data.UVs[:, :2]
        if "Normals" in names:
            mesh.np_norms = np_read_int_2_10_10_10_rev(vert_data.Normals)
        if "BlendIndex" in names:
            mesh.np_blendIndex = vert_data.BlendIndex
        if "BlendWeight" in names:
            mesh.np_blendWeight = vert_data.BlendWeight
        if "Colours" in names:
            mesh.np_colours = vert_data.Colours / 255.0  # divide by 255 to convert to floats

    def _find_joint(self, index=None, name=None):
        """ Return the joint with the specified index. """
        for joint in self.joints:
            if index is not None:
                if int(joint.Attribute('JOINTINDEX')) == index:
                    return joint
            elif name is not None:
                if joint.Name == name:
                    return joint
        return None

    def _fix_anim_data(self, local_anims: dict, mod_dir: str):
        """ Replace an implicitly named animation with a name and a path.
        This modifies the local_anims dictionary in-place.
        """
        _loadable_anim_data = self.scn.nmsdk_anim_data.loadable_anim_data
        # Make a copy of the dictionary to avoid modifying it while iterating
        # over its values.
        local_anims_copy = local_anims.copy()
        for anim_name, anim_data in local_anims_copy.items():
            if anim_data['Filename'] == '':
                # In this case we are using the implicit animation data
                fpath = self.geometry_fname.replace('geometry.mbin.pc', 'anim.mbin')
                # If the anim name is empty, replace it with a new one called
                # "_DEFAULT"
                if anim_name == '':
                    del _loadable_anim_data['']
                    del local_anims['']
                    anim_name = '_DEFAULT'
                # Update the loadable anim data dictionary with the new
                # name. We only want to do this if the animation file
                # actually exists.
                if op.exists(fpath):
                    anim_data['Filename'] = fpath
                    _loadable_anim_data.update({anim_name: anim_data})
                    local_anims.update({anim_name: anim_data})
                else:
                    # If the path to the animation doesn't actually exist,
                    # remove it from the list so that it isn't loaded
                    if anim_name in _loadable_anim_data:
                        del _loadable_anim_data[anim_name]
                        if anim_name in local_anims:
                            del local_anims[anim_name]
            else:
                fpath = op.join(mod_dir, anim_data['Filename'])
                _loadable_anim_data[anim_name]['Filename'] = fpath
                local_anims[anim_name]['Filename'] = fpath

    def _get_material_path(self, scene_node: SceneNodeData):
        raw_path = scene_node.Attribute('MATERIAL')
        if raw_path is not None and not self.from_pak:
            return self._get_path(raw_path)
        return raw_path

    def _get_path(self, fpath):
        # First, try and find the file locally:
        local_path = op.join(self.local_root_folder, fpath)
        if op.exists(local_path):
            return local_path
        # Otherwise, fallback to returning the filepath relative to the PCBANKS
        # folder.
        try:
            return op.join(self.root_dir, fpath)
        except ValueError:
            return None

    def _handle_duplicate_mesh_names(self, node_name):
        """ Very rarely, multiple nodes in a scene can have the same name
        differing only by case. In this case we cannot simply do a look up
        of the mesh metadata as there will be multiple values for the metadata.
        We have to crossreference the metadata to the SceneNodeData and see
        which matches.

        Parameters:
        -----------
        node_name : str
            The UPPER-ified node name.

        Returns:
        --------
        mesh_metadata : namedTuple
            The appropriate mesh metadata for the scene node.
        """
        mesh_metadata = self.mesh_metadata.get(node_name)
        if isinstance(mesh_metadata, list):
            if node_name not in self.name_clash_orders:
                self.name_clash_orders[node_name] = 0
            else:
                self.name_clash_orders[node_name] += 1
            return mesh_metadata[self.name_clash_orders[node_name]]
        else:
            return mesh_metadata
