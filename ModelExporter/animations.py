import bpy

# Internal imports
from .utils import transform_to_NMS_coords, get_actions_with_name
from ..NMS.classes import (TkAnimMetadata, TkAnimNodeData, TkAnimNodeFrameData)
from ..NMS.classes import List, Vector4f, Quaternion


def process_anims(anim_node_data):
    """ Get all the data for all animations in the global scene, and sort them.

    Parameters
    ----------
    anim_node_data : dict
        key: name of NMS scene
        value: list of child objects in this scene that need to be included in
               the animation data.

    Returns
    -------
    anim_data : dict
        key: name of the NMS scene
        value: dict
            key: name of the animation
            value: TkAnimMetadata object containing all the information which
                   can be written to an animation file.
    """
    anim_data = dict()

    for anim_name in bpy.context.scene.nmsdk_anim_data.loaded_anims:
        # Ignore the 'None' action.
        if anim_name == 'None':
            continue
        # Get the list of all the actions with the base name.
        actions = get_actions_with_name(anim_name)

        print('Processing animation {0}'.format(anim_name))

        action_frames = None

        # Apply the current animation to any object that uses it.
        bpy.ops.nmsdk._change_animation(anim_names=anim_name)

        objs_in_action = list()
        varying_components = dict()

        for action in actions:
            # Ensure that the name of the action is valid.
            try:
                obj_name = action.name.split('.', 1)[1]
            except IndexError:
                raise ValueError(
                    'The action {0} has an invalid name. Please fix it '
                    'manually or by running the fix actions tool in the '
                    'NMSDK settings panel.'.format(action.name))
            # Add the name of the object to the list of objects that are
            # animated in this action
            objs_in_action.append(obj_name)
            # Get the set of which components in the action change.
            _varying = set()
            for fcurve in action.fcurves:
                _varying.add(fcurve.data_path)
            # Make sure that there is only one kind of rotation applied
            if ('rotation_euler' in _varying and
                    'rotation_quaternion' in _varying):
                raise ValueError(
                    'Action {0} contains two different types of rotations.'
                    'Please only use one.'.format(action.name))
            # Sanitize the set a little to homogenise the 'rotation_euler'
            # and 'rotation_quaternion' values if they exist.
            if 'rotation_euler' in _varying:
                _varying.remove('rotation_euler')
                _varying.add('rotation')
            if 'rotation_quaternion' in _varying:
                _varying.remove('rotation_quaternion')
                _varying.add('rotation')

            # Get the number of frames and ensure that it is the same as
            # all the other actions in the same animation.
            if action_frames is None:
                action_frames = int(action.frame_range[1])
            else:
                if int(action.frame_range[1]) != action_frames:
                    raise ValueError(
                        'Action {0} has a different number of frames to '
                        'the other actions in the animation. Please ensure'
                        ' that all actions with the same name have the '
                        'same number of frames.'.format(action.name))

            # Assign the components that vary to the dictionary
            varying_components[obj_name] = _varying

        # Determine the indexes of the rotation, translation and scales
        anim_rot, still_rot = (0, 0)
        anim_loc, still_loc = (0, 0)
        anim_sca, still_sca = (0, 0)
        rot_index, loc_index, sca_index = (0, 0, 0)
        indexes = dict()
        NodeData = List()
        # Go over each of the objects and assign the indexes.
        # The index for animated objects will be real, but the one for
        # still types will not be. They will need the `anim_<~>` variable
        # added to them
        for scene_name, animated_objs in anim_node_data.items():
            if not set(objs_in_action).issubset(set(animated_objs)):
                # We only want to generate data for animations that are
                # actually in this scene
                continue
            scene_anim_data = dict()

            for obj_name in animated_objs:
                varying = varying_components.get(obj_name, set())
                if 'rotation' in varying:
                    rot_index = anim_rot
                    anim_rot += 1
                else:
                    rot_index = still_rot
                    still_rot += 1
                if 'location' in varying:
                    loc_index = anim_loc
                    anim_loc += 1
                else:
                    loc_index = still_loc
                    still_loc += 1
                if 'scale' in varying:
                    sca_index = anim_sca
                    anim_sca += 1
                else:
                    sca_index = still_sca
                    still_sca += 1
                indexes[obj_name] = (rot_index, loc_index, sca_index)

            # Rectify the indexes of any still frame data
            for obj_name in animated_objs:
                varying = varying_components.get(obj_name, set())
                rot_index, loc_index, sca_index = indexes[obj_name]
                if 'rotation' not in varying:
                    rot_index += anim_rot
                if 'location' not in varying:
                    loc_index += anim_loc
                if 'scale' not in varying:
                    sca_index += anim_sca
                # add the anim node data
                NodeData.append(TkAnimNodeData(Node=obj_name.upper(),
                                               RotIndex=str(rot_index),
                                               TransIndex=str(loc_index),
                                               ScaleIndex=str(sca_index)))

            AnimFrameData = List()
            stillTranslations = List()
            stillRotations = List()
            stillScales = List()

            # Finally, we want to run the animation and get all the frame
            # data.
            for frame in range(action_frames + 1):
                # need to change the frame of the scene to appropriate one.
                bpy.context.scene.frame_set(frame)

                Translations = List()
                Rotations = List()
                Scales = List()

                for obj_name in animated_objs:
                    obj = bpy.data.objects[obj_name]
                    # TODO: is it better to just get the data directly from
                    # the fcurve.co??
                    trans, rot_q, scale = transform_to_NMS_coords(obj)

                    # Add the location data
                    if 'location' in varying_components.get(obj_name,
                                                            set()):
                        Translations.append(Vector4f(x=trans.x,
                                                     y=trans.y,
                                                     z=trans.z,
                                                     t=1.0))
                    else:
                        if frame == 0:
                            stillTranslations.append(Vector4f(x=trans.x,
                                                              y=trans.y,
                                                              z=trans.z,
                                                              t=1.0))
                    # Add the rotation data
                    if 'rotation' in varying_components.get(obj_name,
                                                            set()):
                        Rotations.append(Quaternion(x=rot_q.x,
                                                    y=rot_q.y,
                                                    z=rot_q.z,
                                                    w=rot_q.w))
                    else:
                        if frame == 0:
                            stillRotations.append(Quaternion(x=rot_q.x,
                                                             y=rot_q.y,
                                                             z=rot_q.z,
                                                             w=rot_q.w))
                    # Add the scale data
                    if 'scale' in varying_components.get(obj_name, set()):
                        Scales.append(Vector4f(x=scale.x,
                                               y=scale.y,
                                               z=scale.z,
                                               t=1.0))
                    else:
                        if frame == 0:
                            stillScales.append(Vector4f(x=scale.x,
                                                        y=scale.y,
                                                        z=scale.z,
                                                        t=1.0))
                FrameData = TkAnimNodeFrameData(Rotations=Rotations,
                                                Translations=Translations,
                                                Scales=Scales)
                AnimFrameData.append(FrameData)

            # Assign the still frame data
            StillFrameData = TkAnimNodeFrameData(
                Rotations=stillRotations,
                Translations=stillTranslations,
                Scales=stillScales)

            scene_anim_data[anim_name] = TkAnimMetadata(
                FrameCount=str(action_frames + 1),
                NodeCount=str(len(animated_objs)),
                NodeData=NodeData,
                AnimFrameData=AnimFrameData,
                StillFrameData=StillFrameData)
            if scene_name in anim_data:
                anim_data[scene_name].update(scene_anim_data)
            else:
                anim_data[scene_name] = scene_anim_data

    return anim_data
