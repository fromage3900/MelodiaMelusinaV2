"""
Kawaii Advanced Decorations Geometry Nodes Generators
=====================================================
15+ kawaii decorative elements.
"""

import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input, mesh_input


@register_generator
class KawaiiBowGN(KawaiiGNBase):
    """Kawaii Bow/Ribbon."""
    category = "decorations"
    generator_id = "kawaii_bow_gn"
    generator_name = "Kawaii Bow"
    description = "Cute ribbon bow"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Loop Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Tail Length', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 1.0
            elif socket.name == 'Loop Size': socket.default_value = 0.5
            elif socket.name == 'Tail Length': socket.default_value = 0.8
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        loop_scale_sock, tail_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Center knot (fixed fraction of Size)
        knot = nodes.new('GeometryNodeMeshUVSphere')
        knot.location = (-600, 0)
        knot.inputs['Segments'].default_value = 16
        knot.inputs['Rings'].default_value = 8

        knot_radius = nodes.new('ShaderNodeMath')
        knot_radius.operation = 'MULTIPLY'
        knot_radius.location = (-800, 0)
        knot_radius.inputs[1].default_value = 0.2
        link_from_input(links, input_node, 'Size', knot_radius.inputs[0])
        links.new(knot_radius.outputs[0], knot.inputs['Radius'])

        # Ribbon loops (Kindchenschema head scale -> puffier loops when cute)
        loop = nodes.new('GeometryNodeMeshUVSphere')
        loop.location = (-600, 200)
        loop.inputs['Segments'].default_value = 24
        loop.inputs['Rings'].default_value = 12

        loop_radius = nodes.new('ShaderNodeMath')
        loop_radius.operation = 'MULTIPLY'
        loop_radius.location = (-800, 250)
        links.new(loop_scale_sock, loop_radius.inputs[0])
        link_from_input(links, input_node, 'Loop Size', loop_radius.inputs[1])

        loop_size = nodes.new('ShaderNodeMath')
        loop_size.operation = 'MULTIPLY'
        loop_size.location = (-800, 200)
        link_from_input(links, input_node, 'Size', loop_size.inputs[0])
        links.new(loop_radius.outputs[0], loop_size.inputs[1])
        links.new(loop_size.outputs[0], loop.inputs['Radius'])

        loop_left = nodes.new('GeometryNodeTransform')
        loop_left.location = (-400, 250)
        loop_left.inputs['Translation'].default_value = (-0.6, 0, 0)
        links.new(loop.outputs['Mesh'], loop_left.inputs['Geometry'])

        loop_right = nodes.new('GeometryNodeTransform')
        loop_right.location = (-400, 150)
        loop_right.inputs['Translation'].default_value = (0.6, 0, 0)
        links.new(loop.outputs['Mesh'], loop_right.inputs['Geometry'])

        # Ribbon tails (Kindchenschema body scale -> shorter tails when cute)
        tail = nodes.new('GeometryNodeMeshCylinder')
        tail.location = (-600, -200)
        tail.inputs['Radius'].default_value = 0.08
        tail.inputs['Vertices'].default_value = 12

        tail_height = nodes.new('ShaderNodeMath')
        tail_height.operation = 'MULTIPLY'
        tail_height.location = (-800, -150)
        links.new(tail_scale_sock, tail_height.inputs[0])
        link_from_input(links, input_node, 'Tail Length', tail_height.inputs[1])

        tail_size = nodes.new('ShaderNodeMath')
        tail_size.operation = 'MULTIPLY'
        tail_size.location = (-800, -200)
        link_from_input(links, input_node, 'Size', tail_size.inputs[0])
        links.new(tail_height.outputs[0], tail_size.inputs[1])
        links.new(tail_size.outputs[0], mesh_input(tail, 'Height'))

        tail_left = nodes.new('GeometryNodeTransform')
        tail_left.location = (-400, -250)
        tail_left.inputs['Translation'].default_value = (-0.15, 0, -0.5)
        links.new(tail.outputs['Mesh'], tail_left.inputs['Geometry'])

        tail_right = nodes.new('GeometryNodeTransform')
        tail_right.location = (-400, -150)
        tail_right.inputs['Translation'].default_value = (0.15, 0, -0.5)
        links.new(tail.outputs['Mesh'], tail_right.inputs['Geometry'])

        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (-200, 0)
        links.new(knot.outputs['Mesh'], join.inputs['Geometry'])
        links.new(loop_left.outputs['Geometry'], join.inputs['Geometry'])
        links.new(loop_right.outputs['Geometry'], join.inputs['Geometry'])
        links.new(tail_left.outputs['Geometry'], join.inputs['Geometry'])
        links.new(tail_right.outputs['Geometry'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])


@register_generator
class KawaiiStarDecorGN(KawaiiGNBase):
    """Kawaii Hanging Star Decoration."""
    category = "decorations"
    generator_id = "kawaii_star_decor_gn"
    generator_name = "Hanging Star"
    description = "Decorative hanging star"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('String Length', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 0.5
            elif socket.name == 'String Length': socket.default_value = 1.0
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        point_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Star points (Kindchenschema head scale -> puffier outer radius when cute)
        star = nodes.new('GeometryNodeCurveStar')
        star.location = (-200, 0)
        star.inputs['Points'].default_value = 5

        outer_radius = nodes.new('ShaderNodeMath')
        outer_radius.operation = 'MULTIPLY'
        outer_radius.location = (-400, 50)
        links.new(point_scale_sock, outer_radius.inputs[0])
        link_from_input(links, input_node, 'Size', outer_radius.inputs[1])
        links.new(outer_radius.outputs[0], star.inputs['Outer Radius'])

        # Star body (Kindchenschema body scale -> smaller inner core when cute)
        inner_ratio = nodes.new('ShaderNodeMath')
        inner_ratio.operation = 'MULTIPLY'
        inner_ratio.location = (-400, -100)
        inner_ratio.inputs[1].default_value = 0.42
        links.new(body_scale_sock, inner_ratio.inputs[0])
        link_from_input(links, input_node, 'Size', inner_ratio.inputs[1])
        links.new(inner_ratio.outputs[0], star.inputs['Inner Radius'])

        links.new(star.outputs['Curve'], output_node.inputs['Geometry'])


@register_generator
class KawaiiHeartDecorGN(KawaiiGNBase):
    """Kawaii Heart Decoration."""
    category = "decorations"
    generator_id = "kawaii_heart_decor_gn"
    generator_name = "Heart Decoration"
    description = "3D heart ornament"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Depth', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 0.8
            elif socket.name == 'Depth': socket.default_value = 0.3
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        lobe_scale_sock, depth_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Heart lobes (Kindchenschema head scale -> puffier lobes when cute)
        lobe = nodes.new('GeometryNodeMeshUVSphere')
        lobe.location = (-600, 200)
        lobe.inputs['Segments'].default_value = 24
        lobe.inputs['Rings'].default_value = 16

        lobe_radius = nodes.new('ShaderNodeMath')
        lobe_radius.operation = 'MULTIPLY'
        lobe_radius.location = (-800, 250)
        links.new(lobe_scale_sock, lobe_radius.inputs[0])
        link_from_input(links, input_node, 'Size', lobe_radius.inputs[1])
        links.new(lobe_radius.outputs[0], lobe.inputs['Radius'])

        lobe_left = nodes.new('GeometryNodeTransform')
        lobe_left.location = (-400, 250)
        lobe_left.inputs['Translation'].default_value = (-0.35, 0, 0.15)
        links.new(lobe.outputs['Mesh'], lobe_left.inputs['Geometry'])

        lobe_right = nodes.new('GeometryNodeTransform')
        lobe_right.location = (-400, 150)
        lobe_right.inputs['Translation'].default_value = (0.35, 0, 0.15)
        links.new(lobe.outputs['Mesh'], lobe_right.inputs['Geometry'])

        # Heart point (Kindchenschema body scale -> shallower depth when cute)
        point = nodes.new('GeometryNodeMeshCone')
        point.location = (-600, -100)
        point.inputs['Radius'].default_value = 0.35
        point.inputs['Vertices'].default_value = 24

        point_radius = nodes.new('ShaderNodeMath')
        point_radius.operation = 'MULTIPLY'
        point_radius.location = (-800, -50)
        links.new(depth_scale_sock, point_radius.inputs[0])
        link_from_input(links, input_node, 'Size', point_radius.inputs[1])
        links.new(point_radius.outputs[0], point.inputs['Radius'])

        point_depth = nodes.new('ShaderNodeMath')
        point_depth.operation = 'MULTIPLY'
        point_depth.location = (-800, -150)
        links.new(depth_scale_sock, point_depth.inputs[0])
        link_from_input(links, input_node, 'Depth', point_depth.inputs[1])
        links.new(point_depth.outputs[0], point.inputs['Depth'])

        point_xform = nodes.new('GeometryNodeTransform')
        point_xform.location = (-400, -100)
        point_xform.inputs['Rotation'].default_value = (3.14159, 0, 0)
        point_xform.inputs['Translation'].default_value = (0, 0, -0.1)
        links.new(point.outputs['Mesh'], point_xform.inputs['Geometry'])

        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (-200, 0)
        links.new(lobe_left.outputs['Geometry'], join.inputs['Geometry'])
        links.new(lobe_right.outputs['Geometry'], join.inputs['Geometry'])
        links.new(point_xform.outputs['Geometry'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
