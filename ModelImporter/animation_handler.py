# stdlib imports
from collections import OrderedDict as odict
from collections import namedtuple
from typing import Optional

# Blender imports
import bpy
from bpy.props import StringProperty
from mathutils import Vector, Quaternion

# Internal imports
from .readers import read_anim  # pylint: disable=relative-beyond-top-level


DATA_PATH_MAP = {'Rotation': 'rotation_quaternion',
                 'Translation': 'location',
                 'Scale': 'scale'}

# Named tuples which are used to simplify the creation of animation channels.
location = namedtuple('location', ['x', 'y', 'z'])
rotation = namedtuple('rotation', ['x', 'y', 'z', 'w'])
scale = namedtuple('scale', ['x', 'y', 'z'])


class AnimationHandler(bpy.types.Operator):
    """ Animation handler class

    Parameters
    ----------
    context : ImportScene object
        The class that is used to load a particular scene.
        Because this object contains so much information regarding the loaded
        scene it is easiest to just store a reference to this class and
        retrieve the properties required when needed.
    """

    bl_idname = "nmsdk.animation_handler"
    bl_label = "Main operator to handle loading of animations for NMSDK"

    anim_name: StringProperty(default="")
    anim_path: StringProperty(default="")

    def execute(self, context):
        print(f'Adding animation: {self.anim_name}')
        self.scn = bpy.context.scene
        self.anim_data = read_anim(self.anim_path)
        self._add_animation_to_scene(self.anim_name, self.anim_data)
        self.scn.nmsdk_anim_data.loaded_anims.append(self.anim_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    # TODO: Add the ability to add the 'None' animation. This will back in an
    # action which is the rest pose so that it can actually be set correctly
    # from the animation selection menu.

    def _add_animation_to_scene(self, anim_name, anim_data):
        # First, let's find out what animation data each object has
        # We do this by looking at the indexes of the rotation, translation and
        # scale data and see whether that lies within the AnimNodeData or the
        # StillFrameData
        node_data_map = odict()
        rot_anim_len = len(anim_data['AnimFrameData'][0]['Rotation'])
        trans_anim_len = len(anim_data['AnimFrameData'][0]['Translation'])
        scale_anim_len = len(anim_data['AnimFrameData'][0]['Scale'])
        for node_data in anim_data['NodeData']:
            data = {'anim': dict(), 'still': dict()}
            # For each node, check to see if the data is in the animation data
            # or in the still frame data
            rotIndex = int(node_data['RotIndex'])
            if rotIndex >= rot_anim_len:
                rotIndex -= rot_anim_len
                data['still']['Rotation'] = rotIndex
            else:
                data['anim']['Rotation'] = rotIndex
            transIndex = int(node_data['TransIndex'])
            if transIndex >= trans_anim_len:
                transIndex -= trans_anim_len
                data['still']['Translation'] = transIndex
            else:
                data['anim']['Translation'] = transIndex
            scaleIndex = int(node_data['ScaleIndex'])
            if scaleIndex >= scale_anim_len:
                scaleIndex -= scale_anim_len
                data['still']['Scale'] = scaleIndex
            else:
                data['anim']['Scale'] = scaleIndex
            node_data_map[node_data['Node']] = data

        # Now that we have all the indexes sorted out, for each node, we create
        # a new action and give it all the information it requires.
        for name, data in node_data_map.items():
            try:
                obj = self.scn.objects[name]
            except KeyError:
                # Skip this object and move on to the next
                continue

            # The animation data for non-joints is the globals values. It will
            # be determined by the transforms of the joints, so we don't want to
            # actually animate it.
            if not obj.NMSNode_props.node_types == 'Joint':
                continue

            obj.animation_data_create()
            action_name = "{0}.{1}".format(anim_name, name)
            obj.animation_data.action = bpy.data.actions.new(
                name=action_name)
            # set the action to have a fake user
            obj.animation_data.action.use_fake_user = True
            animated_props = list(data['anim'].keys())
            fcurves = self._create_anim_channels(
                obj, action_name, animated_props
            )
            self._apply_animdata_to_fcurves(fcurves, data, anim_data)

        # If we have a mesh with joint bindings, also animate the armature
        # TODO: Fix this...
        if self.scn.nmsdk_anim_data.has_bound_mesh:
            armature = bpy.data.objects['Armature']
            armature.animation_data_create()
            action_name = "{0}_Armature".format(anim_name)
            armature.animation_data.action = bpy.data.actions.new(
                name=action_name)
            # set the action to have a fake user
            armature.animation_data.action.use_fake_user = True
            num_frames = anim_data['FrameCount']
            for name, node_data in node_data_map.items():
                # we only care about animating the joints
                if name not in self.scn.nmsdk_anim_data.joints:
                    continue
                print('-- adding {0} --'.format(name))

                bone = armature.pose.bones[name]

                still_data = node_data['still']
                animated_data = node_data['anim']

                location = None
                rotation = None
                scale = None

                # Apply the transforms as required
                for key, value in still_data.items():
                    data = anim_data['StillFrameData'][key][value]
                    if key == 'Translation':
                        location = Vector(data[:3])
                    elif key == 'Rotation':
                        # move the w value to the start to initialize the
                        # quaternion
                        rotation = Quaternion([data[3], data[0], data[1],
                                               data[2]])
                    elif key == 'Scale':
                        scale = Vector(data[:3])

                # Apply the proper animated data
                # bone_ref_mat = bone.matrix.copy()
                for i, frame in enumerate(anim_data['AnimFrameData']):
                    # First apply the required transforms
                    for key, value in animated_data.items():
                        data = frame[key][value]
                        if key == 'Translation':
                            location = Vector(data[:3])
                        elif key == 'Rotation':
                            # move the w value to the start to initialize the
                            # quaternion
                            rotation = Quaternion([data[3], data[0], data[1],
                                                   data[2]])
                        elif key == 'Scale':
                            scale = Vector(data[:3])

                    bind_data = self.scn.objects[name]['bind_data']
                    delta_loc = location - Vector(bind_data[0].to_list())
                    delta_rot = rotation.rotation_difference(
                        Quaternion(bind_data[1].to_list()))
                    ref_scale = Vector(bind_data[2].to_list())
                    delta_sca = Vector((scale[0] / ref_scale[0],
                                        scale[1] / ref_scale[1],
                                        scale[2] / ref_scale[2]))

                    bone.location = delta_loc
                    bone.rotation_quaternion = delta_rot
                    bone.scale = delta_sca
                    # For each transform applied, add a keyframe
                    for key in ['Translation', 'Rotation', 'Scale']:
                        if key in still_data:
                            if i == 0 or i == num_frames - 1:
                                self._apply_pose_data(bone, DATA_PATH_MAP[key],
                                                      i, action_name)
                        elif key in animated_data:
                            self._apply_pose_data(bone, DATA_PATH_MAP[key],
                                                  i, action_name)

    def _apply_animdata_to_fcurves(self, fcurves, mapping, anim_data):
        """ Apply the supplied animation data to the fcurves.

        Parameters
        ----------
        fcurves
            A Tuple containing the location, rotation and scaling nameduples.
        mapping
            Information describing what components are still frame and which
            are animated.
        anim_data
            The actual animation data
        """
        loc, rot, sca = fcurves
        num_frames = anim_data['FrameCount']
        animated_data = mapping['anim']
        for key, value in animated_data.items():
            if key == 'Translation':
                loc.x.keyframe_points.add(num_frames)
                loc.y.keyframe_points.add(num_frames)
                loc.z.keyframe_points.add(num_frames)
            elif key == 'Rotation':
                rot.x.keyframe_points.add(num_frames)
                rot.y.keyframe_points.add(num_frames)
                rot.z.keyframe_points.add(num_frames)
                rot.w.keyframe_points.add(num_frames)
            elif key == 'Scale':
                sca.x.keyframe_points.add(num_frames)
                sca.y.keyframe_points.add(num_frames)
                sca.z.keyframe_points.add(num_frames)
            for i, frame in enumerate(anim_data['AnimFrameData']):
                data = frame[key][value]
                if key == 'Translation':
                    self._apply_animframe_data(loc.x, data[0], i)
                    self._apply_animframe_data(loc.y, data[1], i)
                    self._apply_animframe_data(loc.z, data[2], i)
                elif key == 'Rotation':
                    self._apply_animframe_data(rot.x, data[0], i)
                    self._apply_animframe_data(rot.y, data[1], i)
                    self._apply_animframe_data(rot.z, data[2], i)
                    self._apply_animframe_data(rot.w, data[3], i)
                elif key == 'Scale':
                    self._apply_animframe_data(sca.x, data[0], i)
                    self._apply_animframe_data(sca.y, data[1], i)
                    self._apply_animframe_data(sca.z, data[2], i)

    def _apply_animframe_data(self, fcurve, data, frame):
        fcurve.keyframe_points[int(frame)].co = float(frame), float(data)

    def _apply_pose_data(self, bone, _type, frame, name):
        bone.keyframe_insert(data_path=_type, frame=frame, group=name)

    def _create_anim_channels(
        self,
        obj,
        anim_name: str,
        animated_props: list[str]
    ) -> tuple[
        Optional[namedtuple],
        Optional[namedtuple],
        Optional[namedtuple]
    ]:
        """ Generate all the channels required for the animation.

        Parameters
        ----------
        obj : Blender object
            The object to create the anim channels on.
        anim_name
            Name of the animation so that all fcurves are in the same group.
        animated_props
            A list of the keys in DATA_PATH_MAP which are actually animated.

        Returns
        -------
        Tuple of collections.namedtuple's:
            (location, rotation, scale)
        """
        # Set defaults
        loc = None
        rot = None
        sca = None
        if 'Translation' in animated_props:
            loc_x = obj.animation_data.action.fcurves.new(data_path='location',
                                                        index=0,
                                                        action_group=anim_name)
            loc_y = obj.animation_data.action.fcurves.new(data_path='location',
                                                        index=1,
                                                        action_group=anim_name)
            loc_z = obj.animation_data.action.fcurves.new(data_path='location',
                                                        index=2,
                                                        action_group=anim_name)
            loc = location(loc_x, loc_y, loc_z)
        if 'Rotation' in animated_props:
            rot_w = obj.animation_data.action.fcurves.new(
                data_path='rotation_quaternion',
                index=0,
                action_group=anim_name)
            rot_x = obj.animation_data.action.fcurves.new(
                data_path='rotation_quaternion',
                index=1,
                action_group=anim_name)
            rot_y = obj.animation_data.action.fcurves.new(
                data_path='rotation_quaternion',
                index=2,
                action_group=anim_name)
            rot_z = obj.animation_data.action.fcurves.new(
                data_path='rotation_quaternion',
                index=3,
                action_group=anim_name)
            rot = rotation(rot_x, rot_y, rot_z, rot_w)
        if 'Scale' in animated_props:
            sca_x = obj.animation_data.action.fcurves.new(data_path='scale',
                                                        index=0,
                                                        action_group=anim_name)
            sca_y = obj.animation_data.action.fcurves.new(data_path='scale',
                                                        index=1,
                                                        action_group=anim_name)
            sca_z = obj.animation_data.action.fcurves.new(data_path='scale',
                                                        index=2,
                                                        action_group=anim_name)
            sca = scale(sca_x, sca_y, sca_z)
        return (loc, rot, sca)
