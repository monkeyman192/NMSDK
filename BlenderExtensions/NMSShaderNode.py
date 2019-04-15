# Code inspired by https://blender.stackexchange.com/a/99003

import bpy
from bpy.props import BoolProperty
from nodeitems_utils import (NodeItem, register_node_categories,
                             unregister_node_categories)
from nodeitems_builtins import ShaderNewNodeCategory


FLAGS = [('_F01_DIFFUSEMAP', 'Diffuse Map', 'Diffuse Map'),
         ('_F03_NORMALMAP', 'Normal Map', 'Normal Map'),
         ('_F25_ROUGHNESS_MASK', 'Roughness Mask', 'Roughness Mask')]


class NMSShader(bpy.types.NodeCustomGroup):

    bl_idname = 'NMSShader'
    bl_label = "No Man's Sky Uber Shader"

    # Return the list of valid operators
    def operators(self, context):
        _ = context.space_data.edit_tree
        list = [('_F01_DIFFUSEMAP', 'Diffuse Map', 'Diffuse Map'),
                ('_F03_NORMALMAP', 'Normal Map', 'Normal Map'),
                ('_F25_ROUGHNESS_MASK', 'Roughness Mask', 'Roughness Mask')]
        return list

    # Manage the node's sockets, adding additional ones when needed and
    # removing those no longer required
    def __nodeinterface_setup__(self):

        # No operators --> no inpout or output sockets
        if self.inputSockets < 1:
            self.node_tree.inputs.clear()
            self.node_tree.outputs.clear()

            return

        # Look for input sockets that are no longer required and remove them
        for i in range(len(self.node_tree.inputs), 0, -1):
            if i > self.inputSockets:
                self.node_tree.inputs.remove(self.node_tree.inputs[-1])

        # Add any additional input sockets that are now required
        for i in range(0, self.inputSockets):
            if i > len(self.node_tree.inputs):
                self.node_tree.inputs.new("NodeSocketFloat", "Value")

        # Add the output socket
        if len(self.node_tree.outputs) < 1:
            self.node_tree.outputs.new("NodeSocketFloat", "Value")

    # Manage the internal nodes to perform the chained operation - clear all
    # the nodes and build from scratch each time.
    def __nodetree_setup__(self):

        # Remove all links and all nodes that aren't "Group Input" or
        # "Group Output"
        self.node_tree.links.clear()
        for node in self.node_tree.nodes:
            if node.name not in ['Group Input', 'Group Output']:
                self.node_tree.nodes.remove(node)

        # Start from Group Input and add nodes as required, chaining each new
        # one to the previous level and the next input
        groupinput = self.node_tree.nodes['Group Input']
        previousnode = groupinput
        if self.inputSockets <= 1:
            # Special case <= 1 input --> link input directly to output
            self.node_tree.links.new(
                previousnode.outputs[0],
                self.node_tree.nodes['Group Output'].inputs[0])
        else:
            # Create one node for each input socket > 1
            for i in range(1, self.inputSockets):
                newnode = self.node_tree.nodes.new('ShaderNodeMath')
                newnode.operation = self.selectOperator
                self.node_tree.links.new(previousnode.outputs[0],
                                         newnode.inputs[0])
                self.node_tree.links.new(groupinput.outputs[i],
                                         newnode.inputs[1])
                previousnode = newnode

            # Connect the last one to the output
            self.node_tree.links.new(
                previousnode.outputs[0],
                self.node_tree.nodes['Group Output'].inputs[0])

    # Chosen operator has changed - update the nodes and links
    def update_operator(self, context):
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

    # Number of inputs has changed - update the nodes and links
    def update_inpSockets(self, context):
        self.__nodeinterface_setup__()
        self.__nodetree_setup__()

    # The node properties - Operator (Add, Subtract, etc.) and number of input
    # sockets
    F01_DIFFUSEMAP_choice = BoolProperty(
        name='Has diffuse map',
        description='Whether material has a diffuse map.',
        default=True)
    F03_NORMALMAP_choice = BoolProperty(
        name='Has normal map',
        description='Whether material has a normal map.',
        default=True)
    F25_ROUGHNESS_MASK_choice = BoolProperty(
        name='Has roughness mask',
        description='Whether material has a roughness mask.',
        default=False)

    # Setup the node - setup the node tree and add the group Input and Output
    # nodes
    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(self.bl_name,
                                                  'ShaderNodeTree')
        if hasattr(self.node_tree, 'is_hidden'):
            self.node_tree.is_hidden = True
        self.node_tree.nodes.new('NodeGroupInput')
        self.node_tree.nodes.new('NodeGroupOutput')

    # Draw the node components
    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'F01_DIFFUSEMAP_choice', text='')
        row = layout.row()
        row.prop(self, 'F03_NORMALMAP_choice', text='')
        row = layout.row()
        row.prop(self, 'F25_ROUGHNESS_MASK_choice', text='')

    # Copy
    def copy(self, node):
        self.node_tree = node.node_tree.copy()

    # Free (when node is deleted)
    def free(self):
        bpy.data.node_groups.remove(self.node_tree, do_unlink=True)


def register():
    bpy.utils.register_class(NMSShader)
    newcatlist = [ShaderNewNodeCategory("SH_NEW_CUSTOM", "NMS Shader",
                                        items=[NodeItem("NMSShader")])]
    register_node_categories("NMS_SHADER", newcatlist)


def unregister():
    unregister_node_categories("NMS_SHADER")
    bpy.utils.unregister_class(NMSShader)
