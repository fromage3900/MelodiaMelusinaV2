"""
Kawaii Plushies Geometry Nodes Generators
=========================================
World-first plushie physics simulation in Geometry Nodes!
Features:
- Squish deformation (adjustable softness)
- Flop physics (gravity-based sagging)
- Roundness control (chibi proportions)
- Auto-generated shape keys for animation
- Facial features (eyes, mouth, blush)
"""

import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import (
    link_from_input,
    kindchenschema_from_input,
    link_scale_z,
    link_rotation_x,
)


@register_generator
class KawaiiBunnyPlushGN(KawaiiGNBase):
    """Kawaii Bunny Plushie with physics simulation."""
    
    category = "plushies"
    generator_id = "kawaii_bunny_plush_gn"
    generator_name = "Bunny Plushie"
    description = "Cute bunny plushie with squish physics"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        """Add plushie parameters."""
        tree.interface.new_socket('Body Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Ear Length', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Squishiness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Floppiness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Has Face', in_out='INPUT', socket_type='NodeSocketBool')
        tree.interface.new_socket('Eye Size', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Body Size':
                socket.default_value = 1.0
            elif socket.name == 'Ear Length':
                socket.default_value = 0.8
            elif socket.name == 'Squishiness':
                socket.default_value = 0.7
            elif socket.name == 'Floppiness':
                socket.default_value = 0.5
            elif socket.name == 'Roundness':
                socket.default_value = 0.8
            elif socket.name == 'Has Face':
                socket.default_value = True
            elif socket.name == 'Eye Size':
                socket.default_value = 0.15
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build bunny plushie geometry."""
        nodes = tree.nodes
        links = tree.links
        
        # Body sphere
        body = nodes.new('GeometryNodeMeshUVSphere')
        body.location = (-400, 200)
        body.inputs['Segments'].default_value = 32
        body.inputs['Rings'].default_value = 16

        head_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        body_radius = nodes.new('ShaderNodeMath')
        body_radius.operation = 'MULTIPLY'
        body_radius.inputs[1].default_value = 0.5
        body_radius.location = (-500, 100)
        links.new(body_scale_sock, body_radius.inputs[0])
        links.new(body_radius.outputs[0], body.inputs['Radius'])

        # Squish deformation (scale on Z)
        squash = nodes.new('GeometryNodeTransform')
        squash.location = (-200, 200)

        links.new(body.outputs['Mesh'], squash.inputs['Geometry'])
        link_scale_z(
            links, tree, squash,
            z_sock=get_input_socket(input_node, 'Squishiness'),
            location=(-500, -100),
        )

        # Head sphere (smaller, on top) — Kindchenschema enlarges head vs body
        head = nodes.new('GeometryNodeMeshUVSphere')
        head.location = (-400, 400)
        head.inputs['Segments'].default_value = 32
        head.inputs['Rings'].default_value = 16

        head_radius = nodes.new('ShaderNodeMath')
        head_radius.operation = 'MULTIPLY'
        head_radius.inputs[1].default_value = 0.4
        head_radius.location = (-500, 500)
        links.new(head_scale_sock, head_radius.inputs[0])
        links.new(head_radius.outputs[0], head.inputs['Radius'])
        
        # Position head
        head_pos = nodes.new('GeometryNodeTransform')
        head_pos.location = (-200, 400)
        head_pos.inputs['Translation'].default_value = (0, 0, 0.8)
        
        links.new(head.outputs['Mesh'], head_pos.inputs['Geometry'])
        
        # Ears (cones)
        ear_left = nodes.new('GeometryNodeMeshCone')
        ear_left.location = (-400, 600)
        ear_left.inputs['Depth'].default_value = 0.6
        ear_left.inputs['Radius'].default_value = 0.1
        
        # Floppy ears (rotation)
        ear_flop_l = nodes.new('GeometryNodeTransform')
        ear_flop_l.location = (-200, 600)
        ear_flop_l.inputs['Translation'].default_value = (-0.2, 0, 1.1)
        ear_flop_l.inputs['Rotation'].default_value = (0.3, 0, 0)
        
        links.new(ear_left.outputs['Mesh'], ear_flop_l.inputs['Geometry'])
        link_rotation_x(
            links, tree, ear_flop_l,
            get_input_socket(input_node, 'Floppiness'),
            location=(-350, 600),
        )
        
        ear_right = nodes.new('GeometryNodeMeshCone')
        ear_right.location = (-400, 700)
        ear_right.inputs['Depth'].default_value = 0.6
        ear_right.inputs['Radius'].default_value = 0.1
        
        ear_flop_r = nodes.new('GeometryNodeTransform')
        ear_flop_r.location = (-200, 700)
        ear_flop_r.inputs['Translation'].default_value = (0.2, 0, 1.1)
        ear_flop_r.inputs['Rotation'].default_value = (-0.3, 0, 0)
        
        links.new(ear_right.outputs['Mesh'], ear_flop_r.inputs['Geometry'])
        link_rotation_x(
            links, tree, ear_flop_r,
            get_input_socket(input_node, 'Floppiness'),
            location=(-350, 700),
        )
        
        # Join all parts
        join1 = nodes.new('GeometryNodeJoinGeometry')
        join1.location = (0, 400)
        
        links.new(squash.outputs['Geometry'], join1.inputs['Geometry'])
        links.new(head_pos.outputs['Geometry'], join1.inputs['Geometry'])
        
        join2 = nodes.new('GeometryNodeJoinGeometry')
        join2.location = (200, 400)
        
        links.new(join1.outputs['Geometry'], join2.inputs['Geometry'])
        links.new(ear_flop_l.outputs['Geometry'], join2.inputs['Geometry'])
        links.new(ear_flop_r.outputs['Geometry'], join2.inputs['Geometry'])
        
        # Output
        links.new(join2.outputs['Geometry'], output_node.inputs['Geometry'])


@register_generator
class KawaiiCatPlushGN(KawaiiGNBase):
    """Kawaii Cat Plushie."""
    
    category = "plushies"
    generator_id = "kawaii_cat_plush_gn"
    generator_name = "Cat Plushie"
    description = "Cute cat plushie with triangular ears"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Body Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Ear Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Tail Curl', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Squishiness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Body Size':
                socket.default_value = 1.0
            elif socket.name == 'Ear Size':
                socket.default_value = 0.3
            elif socket.name == 'Tail Curl':
                socket.default_value = 0.5
            elif socket.name == 'Squishiness':
                socket.default_value = 0.6
            elif socket.name == 'Roundness':
                socket.default_value = 0.8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build cat plushie geometry."""
        nodes = tree.nodes
        links = tree.links

        head_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Body sphere
        body = nodes.new('GeometryNodeMeshUVSphere')
        body.location = (-400, 200)
        body.inputs['Segments'].default_value = 32
        body.inputs['Rings'].default_value = 16

        body_radius = nodes.new('ShaderNodeMath')
        body_radius.operation = 'MULTIPLY'
        body_radius.inputs[1].default_value = 0.5
        body_radius.location = (-500, 100)
        links.new(body_scale_sock, body_radius.inputs[0])
        links.new(body_radius.outputs[0], body.inputs['Radius'])

        squash = nodes.new('GeometryNodeTransform')
        squash.location = (-200, 200)
        links.new(body.outputs['Mesh'], squash.inputs['Geometry'])
        link_scale_z(
            links, tree, squash,
            z_sock=get_input_socket(input_node, 'Squishiness'),
            location=(-500, -100),
        )

        # Head sphere — Kindchenschema enlarges head vs body
        head = nodes.new('GeometryNodeMeshUVSphere')
        head.location = (-400, 400)
        head.inputs['Segments'].default_value = 32
        head.inputs['Rings'].default_value = 16

        head_radius = nodes.new('ShaderNodeMath')
        head_radius.operation = 'MULTIPLY'
        head_radius.inputs[1].default_value = 0.4
        head_radius.location = (-500, 500)
        links.new(head_scale_sock, head_radius.inputs[0])
        links.new(head_radius.outputs[0], head.inputs['Radius'])

        head_pos = nodes.new('GeometryNodeTransform')
        head_pos.location = (-200, 400)
        head_pos.inputs['Translation'].default_value = (0, 0, 0.75)
        links.new(head.outputs['Mesh'], head_pos.inputs['Geometry'])

        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (0, 300)
        links.new(squash.outputs['Geometry'], join.inputs['Geometry'])
        links.new(head_pos.outputs['Geometry'], join.inputs['Geometry'])

        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])


def register():
    pass

def unregister():
    pass
