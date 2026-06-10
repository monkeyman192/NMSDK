# -*- coding: utf-8 -*-

""" Courtesy of mmd_tools (https://github.com/powroupi/blender_mmd_tools)
This code is distrubted under a GPLv3 licence and has been modified to remove
some un-needed functions, to apply some proper linting to the code and to
streamline the code to be applicable to blender 2.8x only
"""

import bpy


class __EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        self.__obj = obj
        self.__obj_select = obj.select_get()
        with select_object(obj) as _:
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self.__obj.data

    def __exit__(self, type, value, traceback):
        if self.__prevMode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')  # update edited data
        bpy.ops.object.mode_set(mode=self.__prevMode)
        self.__obj.select_set(self.__obj_select)


class __SelectObjects:
    def __init__(self, active_object, selected_objects=[]):
        if not isinstance(active_object, bpy.types.Object):
            raise ValueError
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for i in bpy.context.selected_objects:
            i.select_set(False)

        self.__active_object = active_object
        self.__selected_objects = [active_object] + selected_objects

        self.__hides = []
        scene = SceneOp(bpy.context)
        for i in self.__selected_objects:
            self.__hides.append(i.hide_get())
            scene.select_object(i)
        scene.active_object = active_object

    def __enter__(self):
        return self.__active_object

    def __exit__(self, type, value, traceback):
        for i, j in zip(self.__selected_objects, self.__hides):
            i.hide_set(j)


def edit_object(obj):
    """ Set the object interaction mode to 'EDIT'

    It is recommended to use 'edit_object' with 'with' statement like the
    following code.

        with edit_object:
            some functions...
    """
    return __EditMode(obj)


def select_object(obj, objects=[]):
    """ Select objects.

    It is recommended to use 'select_object' with 'with' statement like the
    following code.
    This function can select "hidden" objects safely.

        with select_object(obj):
            some functions...
    """
    return __SelectObjects(obj, objects)


def createObject(name='Object', object_data=None, target_scene=None):
    target_scene = SceneOp(target_scene)
    obj = bpy.data.objects.new(name=name, object_data=object_data)
    target_scene.link_object(obj)
    target_scene.active_object = obj
    obj.select = True
    return obj


class SceneOp():
    def __init__(self, context):
        self.__context = context or bpy.context
        self.__collection = self.__context.collection
        self.__view_layer = self.__context.view_layer

    def select_object(self, obj):
        obj.hide_set(False)
        obj.select_set(True)

    def link_object(self, obj):
        self.__collection.objects.link(obj)

    @property
    def active_object(self):
        return self.__view_layer.objects.active

    @active_object.setter
    def active_object(self, obj):
        self.__view_layer.objects.active = obj

    @property
    def id_scene(self):
        return self.__view_layer

    @property
    def id_objects(self):
        return self.__view_layer.objects
