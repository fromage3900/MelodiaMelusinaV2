"""
Kawaii Effects Geometry Nodes Generators
========================================
Procedural magical effects:
- Sparkle particles
- Rainbow arcs
- Cloud formations
- Magic circles
- Heart explosions
"""

import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input, link_to_vector_input


@register_generator
class KawaiiSparklesGN(KawaiiGNBase):
    """Sparkle particle effect."""
    
    category = "effects"
    generator_id = "kawaii_sparkles_gn"
    generator_name = "Sparkle Effect"
    description = "Magical sparkle particles"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Spread', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Twinkle Speed', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Count':
                socket.default_value = 50
            elif socket.name == 'Spread':
                socket.default_value = 2.0
            elif socket.name == 'Size':
                socket.default_value = 0.1
            elif socket.name == 'Twinkle Speed':
                socket.default_value = 1.0
            elif socket.name == 'Roundness':
                socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build sparkle effect."""
        nodes = tree.nodes
        links = tree.links

        point_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Distribute points
        distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
        distribute.location = (-200, 0)
        distribute.inputs['Count'].default_value = 50
        
        # Start with a sphere
        sphere = nodes.new('GeometryNodeMeshUVSphere')
        sphere.location = (-400, 0)
        sphere.inputs['Radius'].default_value = 1.0
        
        links.new(sphere.outputs['Mesh'], distribute.inputs['Mesh'])
        link_from_input(links, input_node, 'Count', distribute.inputs['Count'])
        
        # Instance 4-point stars (Kindchenschema -> puffier points when cute)
        star = nodes.new('GeometryNodeCurveStar')
        star.location = (-400, 200)
        star.inputs['Vertices'].default_value = 4

        outer_radius = nodes.new('ShaderNodeMath')
        outer_radius.operation = 'MULTIPLY'
        outer_radius.location = (-600, 250)
        outer_radius.inputs[1].default_value = 0.5
        links.new(point_scale_sock, outer_radius.inputs[0])
        link_from_input(links, input_node, 'Size', outer_radius.inputs[1])
        links.new(outer_radius.outputs[0], star.inputs['Outer Radius'])

        inner_ratio = nodes.new('ShaderNodeMath')
        inner_ratio.operation = 'MULTIPLY'
        inner_ratio.location = (-600, 100)
        inner_ratio.inputs[1].default_value = 0.3
        links.new(body_scale_sock, inner_ratio.inputs[0])
        link_from_input(links, input_node, 'Size', inner_ratio.inputs[1])
        links.new(inner_ratio.outputs[0], star.inputs['Inner Radius'])
        
        # Curve to mesh
        star_mesh = nodes.new('GeometryNodeCurveToMesh')
        star_mesh.location = (-200, 200)
        
        links.new(star.outputs['Curve'], star_mesh.inputs['Curve'])
        
        # Instance on points
        instance = nodes.new('GeometryNodeInstanceOnPoints')
        instance.location = (0, 0)
        
        links.new(distribute.outputs['Points'], instance.inputs['Points'])
        links.new(star_mesh.outputs['Mesh'], instance.inputs['Instance'])

        size_scaled = nodes.new('ShaderNodeMath')
        size_scaled.operation = 'MULTIPLY'
        size_scaled.location = (-200, -120)
        links.new(point_scale_sock, size_scaled.inputs[0])
        link_from_input(links, input_node, 'Size', size_scaled.inputs[1])
        link_to_vector_input(
            links, tree, instance.inputs['Scale'],
            x_sock=size_scaled.outputs[0],
            y_sock=size_scaled.outputs[0],
            z_sock=size_scaled.outputs[0],
            default_x=1.0, default_y=1.0, default_z=1.0,
            location=(-100, -120),
        )
        
        # Realize
        realize = nodes.new('GeometryNodeRealizeInstances')
        realize.location = (200, 0)
        
        links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
        links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])


@register_generator
class KawaiiRainbowGN(KawaiiGNBase):
    """Rainbow arc effect."""
    
    category = "effects"
    generator_id = "kawaii_rainbow_gn"
    generator_name = "Rainbow Arc"
    description = "Cute rainbow with color bands"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Bands', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Arc Angle', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Radius':
                socket.default_value = 2.0
            elif socket.name == 'Bands':
                socket.default_value = 7
            elif socket.name == 'Thickness':
                socket.default_value = 0.3
            elif socket.name == 'Arc Angle':
                socket.default_value = 3.14
            elif socket.name == 'Roundness':
                socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build rainbow."""
        nodes = tree.nodes
        links = tree.links

        arc_scale_sock, _ = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Circle curve (Kindchenschema -> wider arc when cute)
        circle = nodes.new('GeometryNodeCurveCircle')
        circle.location = (-200, 0)
        circle.inputs['Radius'].default_value = 2.0

        radius_scale = nodes.new('ShaderNodeMath')
        radius_scale.operation = 'MULTIPLY'
        radius_scale.location = (-400, 0)
        links.new(arc_scale_sock, radius_scale.inputs[0])
        link_from_input(links, input_node, 'Radius', radius_scale.inputs[1])
        links.new(radius_scale.outputs[0], circle.inputs['Radius'])
        
        # Trim to arc
        trim = nodes.new('GeometryNodeTrimCurve')
        trim.location = (0, 0)
        trim.inputs['Start'].default_value = 0.0
        trim.inputs['End'].default_value = 0.5
        
        links.new(circle.outputs['Curve'], trim.inputs['Curve'])
        
        # Curve to mesh (thick)
        profile = nodes.new('GeometryNodeCurveCircle')
        profile.location = (-200, 200)
        profile.inputs['Radius'].default_value = 0.15
        
        link_from_input(links, input_node, 'Thickness', profile.inputs['Radius'])
        
        curve_mesh = nodes.new('GeometryNodeCurveToMesh')
        curve_mesh.location = (200, 0)
        
        links.new(trim.outputs['Curve'], curve_mesh.inputs['Curve'])
        links.new(profile.outputs['Curve'], curve_mesh.inputs['Profile Curve'])
        
        links.new(curve_mesh.outputs['Mesh'], output_node.inputs['Geometry'])


def register():
    pass

def unregister():
    pass
