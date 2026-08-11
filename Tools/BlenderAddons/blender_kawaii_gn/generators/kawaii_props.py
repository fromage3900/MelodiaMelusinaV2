"""
Kawaii Props Geometry Nodes Generators
=======================================
Cute props and decorative items.
"""

import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input, mesh_input


@register_generator
class KawaiiVaseGN(KawaiiGNBase):
    category = "props"
    generator_id = "kawaii_vase_gn"
    generator_name = "Kawaii Vase"
    description = "Cute rounded vase"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Height':
                socket.default_value = 1.5
            elif socket.name == 'Width':
                socket.default_value = 0.8
            elif socket.name == 'Roundness':
                socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        belly_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Belly (main rounded body — scales up with cuteness)
        belly = nodes.new('GeometryNodeMeshCylinder')
        belly.location = (-400, 0)
        belly.inputs['Vertices'].default_value = 32

        belly_radius = nodes.new('ShaderNodeMath')
        belly_radius.operation = 'MULTIPLY'
        belly_radius.location = (-600, 50)
        links.new(belly_scale_sock, belly_radius.inputs[0])
        link_from_input(links, input_node, 'Width', belly_radius.inputs[1])
        links.new(belly_radius.outputs[0], belly.inputs['Radius'])

        belly_height = nodes.new('ShaderNodeMath')
        belly_height.operation = 'MULTIPLY'
        belly_height.location = (-600, -50)
        belly_height.inputs[1].default_value = 0.55
        links.new(belly_scale_sock, belly_height.inputs[0])
        link_from_input(links, input_node, 'Height', belly_height.inputs[1])
        links.new(belly_height.outputs[0], mesh_input(belly, 'Height'))

        # Neck (narrow top — scales down with cuteness)
        neck = nodes.new('GeometryNodeMeshCylinder')
        neck.location = (-400, 200)
        neck.inputs['Vertices'].default_value = 24

        neck_radius = nodes.new('ShaderNodeMath')
        neck_radius.operation = 'MULTIPLY'
        neck_radius.location = (-800, 250)
        neck_radius.inputs[1].default_value = 0.4
        links.new(body_scale_sock, neck_radius.inputs[0])
        link_from_input(links, input_node, 'Width', neck_radius.inputs[1])
        links.new(neck_radius.outputs[0], neck.inputs['Radius'])

        neck_height = nodes.new('ShaderNodeMath')
        neck_height.operation = 'MULTIPLY'
        neck_height.location = (-800, 150)
        neck_height.inputs[1].default_value = 0.35
        links.new(body_scale_sock, neck_height.inputs[0])
        link_from_input(links, input_node, 'Height', neck_height.inputs[1])
        links.new(neck_height.outputs[0], mesh_input(neck, 'Height'))

        neck_pos = nodes.new('GeometryNodeTransform')
        neck_pos.location = (-200, 200)
        neck_pos.inputs['Translation'].default_value = (0, 0, 0.675)
        links.new(neck.outputs['Mesh'], neck_pos.inputs['Geometry'])

        # Base (narrow foot — scales down with cuteness)
        base = nodes.new('GeometryNodeMeshCylinder')
        base.location = (-400, -200)
        base.inputs['Vertices'].default_value = 24

        base_radius = nodes.new('ShaderNodeMath')
        base_radius.operation = 'MULTIPLY'
        base_radius.location = (-800, -150)
        base_radius.inputs[1].default_value = 0.5
        links.new(body_scale_sock, base_radius.inputs[0])
        link_from_input(links, input_node, 'Width', base_radius.inputs[1])
        links.new(base_radius.outputs[0], base.inputs['Radius'])

        base_height = nodes.new('ShaderNodeMath')
        base_height.operation = 'MULTIPLY'
        base_height.location = (-800, -250)
        base_height.inputs[1].default_value = 0.15
        links.new(body_scale_sock, base_height.inputs[0])
        link_from_input(links, input_node, 'Height', base_height.inputs[1])
        links.new(base_height.outputs[0], mesh_input(base, 'Height'))

        base_pos = nodes.new('GeometryNodeTransform')
        base_pos.location = (-200, -200)
        base_pos.inputs['Translation'].default_value = (0, 0, -0.675)
        links.new(base.outputs['Mesh'], base_pos.inputs['Geometry'])

        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (0, 0)
        links.new(belly.outputs['Mesh'], join.inputs['Geometry'])
        links.new(neck_pos.outputs['Geometry'], join.inputs['Geometry'])
        links.new(base_pos.outputs['Geometry'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])


def register():
    pass
def unregister():
    pass
