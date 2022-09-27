# Add some right click options

# stdlib imports
from copy import copy
import math

# Local imports
from ..utils.misc import get_root_node, clone_node
from ..ModelExporter.utils import get_children

# Blender imports
import bmesh
import bpy
from bpy.types import Menu, Operator
from mathutils import Matrix


CONE_ROTATION_MAT = Matrix.Rotation(math.radians(90), 4, 'X')


class AddReferenceNode(Operator):
    """Add a new NMS reference node"""
    bl_idname = "nmsdk.add_reference_node"
    bl_label = "Reference Node"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to add a child node to')
            return {'FINISHED'}
        # Create a new empty reference node.
        for obj in selected_objs:
            empty_mesh = bpy.data.meshes.new('ref')
            empty_obj = bpy.data.objects.new('ref', empty_mesh)
            empty_obj.NMSNode_props.node_types = 'Reference'
            empty_obj.matrix_world = Matrix()
            empty_obj.parent = obj
            empty_obj.rotation_mode = 'QUATERNION'
            bpy.context.scene.collection.objects.link(empty_obj)

        return {'FINISHED'}


class AddLocatorNode(Operator):
    """Add a new NMS reference node"""
    bl_idname = "nmsdk.add_locator_node"
    bl_label = "Locator Node"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to add a child node to')
            return {'FINISHED'}
        # Create a new empty reference node.
        for obj in selected_objs:
            empty_mesh = bpy.data.meshes.new('loc')
            empty_obj = bpy.data.objects.new('loc', empty_mesh)
            empty_obj.NMSNode_props.node_types = 'Locator'
            empty_obj.matrix_world = Matrix()
            empty_obj.parent = obj
            empty_obj.rotation_mode = 'QUATERNION'
            bpy.context.scene.collection.objects.link(empty_obj)

        return {'FINISHED'}


class AddBoxCollisionNode(Operator):
    """Add a new NMS box collision node"""
    bl_idname = "nmsdk.add_box_collision_node"
    bl_label = "Box collision node"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to add a child node to')
            return {'FINISHED'}
        # Create a new empty reference node.
        for obj in selected_objs:
            # Create a new cube for collisions
            mesh = bpy.data.meshes.new('cube')
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bm.to_mesh(mesh)
            bm.free()
            cube = bpy.data.objects.new('cube', mesh)
            cube.NMSNode_props.node_types = 'Collision'
            cube.NMSCollision_props.collision_types = 'Box'
            cube.matrix_world = Matrix()
            cube.parent = obj
            bpy.context.scene.collection.objects.link(cube)
            cube.rotation_mode = 'QUATERNION'

        return {'FINISHED'}


class AddSphereCollisionNode(Operator):
    """Add a new NMS sphere collision node"""
    bl_idname = "nmsdk.add_sphere_collision_node"
    bl_label = "Sphere collision node"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to add a child node to')
            return {'FINISHED'}
        # Create a new empty reference node.
        for obj in selected_objs:
            # Create a new sphere for collisions
            mesh = bpy.data.meshes.new('sphere')
            bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=4, radius=0.5)
            bm.to_mesh(mesh)
            bm.free()
            sphere = bpy.data.objects.new('sphere', mesh)
            sphere.NMSNode_props.node_types = 'Collision'
            sphere.NMSCollision_props.collision_types = 'Sphere'
            sphere.matrix_world = Matrix()
            sphere.parent = obj
            bpy.context.scene.collection.objects.link(sphere)
            sphere.rotation_mode = 'QUATERNION'

        return {'FINISHED'}


class AddCylinderCollisionNode(Operator):
    """Add a new NMS cylinder collision node"""
    bl_idname = "nmsdk.add_cylinder_collision_node"
    bl_label = "Cylinder collision node"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to add a child node to')
            return {'FINISHED'}
        # Create a new empty reference node.
        for obj in selected_objs:
            # Create a new cylinder for collisions
            mesh = bpy.data.meshes.new('cylinder')
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True,
                                  radius1=0.5, radius2=0.5, depth=1.0,
                                  segments=20, matrix=CONE_ROTATION_MAT)
            bm.to_mesh(mesh)
            bm.free()
            cylinder = bpy.data.objects.new('cylinder', mesh)
            cylinder.NMSNode_props.node_types = 'Collision'
            cylinder.NMSCollision_props.collision_types = 'Cylinder'
            cylinder.matrix_world = Matrix()
            cylinder.parent = obj
            bpy.context.scene.collection.objects.link(cylinder)
            cylinder.rotation_mode = 'QUATERNION'

        return {'FINISHED'}


class CloneNodes(Operator):
    """Clone the selcted node(s)"""
    bl_idname = "nmsdk.clone_nodes"
    bl_label = "Clone node(s)"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to clone')
            return {'FINISHED'}
        # Make a copy of each of the selected nodes.
        for obj in selected_objs:
            clone_node(obj)
        return {'FINISHED'}


class CloneNodesRecursively(Operator):
    """Clone the selcted node(s) and all attached children"""
    bl_idname = "nmsdk.clone_nodes_recursively"
    bl_label = "Clone node(s) recursively"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", None)
        if not selected_objs:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select an object to clone')
            return {'FINISHED'}
        # Make a copy of each of the selected nodes.
        for obj in selected_objs:
            clone_node(obj, True)
        return {'FINISHED'}


class NMSDK_OT_move_to_parent(Operator):
    """Set the selected object(s) to be a child node of the selected parent"""
    bl_idname = "nmsdk.add_to_parent"
    bl_label = "Set object(s) as child of selected parent"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objs = getattr(context, "selected_objects", [])
        parent_obj = getattr(context, "active_object", None)

        # First, make sure we have, a) enough objects selected, and b) the
        # correct set of objects to iterate over so that it doesn't include the
        # parent object.
        if len(selected_objs) < 2:
            self.report({'ERROR_INVALID_INPUT'},
                        'Please select 2 or more objects')
            return {'FINISHED'}
        child_objs = set(selected_objs) - {parent_obj}
        root_obj = get_root_node(parent_obj)
        for obj in child_objs:
            # There are two possibilities for moving an object under a parent.
            # 1. It can already be inside the imported scene, in which case we
            # don't want to apply any kind of transforms, but simply set the
            # parent and local transform.
            # 2. The object exists outside of the scene, so we need to do a few
            # extra things detailed within the code block.
            if get_root_node(obj) == root_obj:
                # Copy the local transform.
                trans = copy(obj.matrix_local)
                # set the parent.
                obj.parent = parent_obj
                # Set the local transform as before
                obj.matrix_local = trans
                del trans
            else:
                trans = copy(obj.matrix_world)
                bpy.ops.object.parent_set()
                obj.matrix_world = trans
                del trans

                # Go over all the children nodes, and if any don't have data
                # then they are empty. We'll set these as Locators.
                # Also check the obj itself while we are here...
                for child in [obj] + get_children(obj):
                    if not child.data:
                        child.NMSNode_props.node_types = 'Locator'

        return {'FINISHED'}


class NMSDK_MT_add_NMS_Scenenodes(Menu):
    bl_label = "Add new Scene Node objects"
    bl_idname = "NMSDK_MT_add_NMS_Scenenodes"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('nmsdk.add_reference_node')
        row = layout.row()
        row.operator('nmsdk.add_locator_node')
        layout.separator()
        row = layout.row()
        row.operator('nmsdk.add_box_collision_node')
        row = layout.row()
        row.operator('nmsdk.add_sphere_collision_node')
        row = layout.row()
        row.operator('nmsdk.add_cylinder_collision_node')


class NMSDK_MT_clone_NMS_Scenenodes(Menu):
    bl_label = "Clone NMS Scenenode objects"
    bl_idname = "NMSDK_MT_clone_NMS_Scenenodes"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('nmsdk.clone_nodes')
        row = layout.row()
        row.operator('nmsdk.clone_nodes_recursively')
        row = layout.row()


# Functions to modify blenders' menu items


def add_empty_root_node(self, context):
    """ Add an option to the 'add' menu in the 3D view to add an empty root
    NMS SceneNode reference for exporting. """
    layout = self.layout
    layout.separator()
    layout.operator('nmsdk.create_root_scene')


def parent_menu_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator('nmsdk.add_to_parent')


def add_obj_menu_func(self, context):
    """ Add the sub-menu to the context menu. """
    layout = self.layout
    if get_root_node(context.active_object) is not None:
        layout.separator()
        row = layout.row()
        row.menu("NMSDK_MT_add_NMS_Scenenodes")
        row = layout.row()
        row.menu("NMSDK_MT_clone_NMS_Scenenodes")


classes = (NMSDK_OT_move_to_parent,
           AddReferenceNode,
           AddBoxCollisionNode,
           AddSphereCollisionNode,
           AddCylinderCollisionNode,
           AddLocatorNode,
           NMSDK_MT_add_NMS_Scenenodes,
           NMSDK_MT_clone_NMS_Scenenodes,
           CloneNodes,
           CloneNodesRecursively)


class ContextMenus():
    @staticmethod
    def register():
        # Register classes to be used.
        for cls_ in classes:
            bpy.utils.register_class(cls_)
        # Add the functions to the menus they need to be in.
        bpy.types.VIEW3D_MT_add.append(add_empty_root_node)
        bpy.types.VIEW3D_MT_object_parent.append(parent_menu_func)
        bpy.types.VIEW3D_MT_object_context_menu.append(add_obj_menu_func)

    @staticmethod
    def unregister():
        # Unregister classes used.
        for cls_ in classes:
            bpy.utils.unregister_class(cls_)
        # Remove the functions from the menus they were in.
        bpy.types.VIEW3D_MT_add.remove(add_empty_root_node)
        bpy.types.VIEW3D_MT_object_parent.remove(parent_menu_func)
        bpy.types.VIEW3D_MT_object_context_menu.remove(add_obj_menu_func)
