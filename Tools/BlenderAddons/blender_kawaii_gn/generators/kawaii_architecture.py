"""
Kawaii Architecture Geometry Nodes Generators
==============================================
Procedural kawaii architectural elements using Geometry Nodes:
- Cute bricks with rounded edges
- Kawaii walls with expressive faces
- Adorable pillars and columns
- Cute foundations and bases

All generators are fully non-destructive and parameterized.
"""

import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import (
    link_from_input,
    kindchenschema_from_input,
    link_cube_size,
    link_to_vector_input,
)


@register_generator
class KawaiiBricksGN(KawaiiGNBase):
    """Kawaii Bricks with rounded edges and pastel colors."""
    
    category = "architecture"
    generator_id = "kawaii_bricks_gn"
    generator_name = "Kawaii Bricks"
    description = "Cute rounded bricks with adjustable proportions"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        """Add brick parameters."""
        # Width
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        # Height  
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        # Depth
        tree.interface.new_socket('Depth', in_out='INPUT', socket_type='NodeSocketFloat')
        # Roundness (Kindchenschema puffiness)
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        # Rows
        tree.interface.new_socket('Rows', in_out='INPUT', socket_type='NodeSocketInt')
        # Columns
        tree.interface.new_socket('Columns', in_out='INPUT', socket_type='NodeSocketInt')
        
        # Set defaults
        for socket in tree.interface.items_tree:
            if socket.name == 'Width':
                socket.default_value = 2.0
            elif socket.name == 'Height':
                socket.default_value = 1.0
            elif socket.name == 'Depth':
                socket.default_value = 1.0
            elif socket.name == 'Roundness':
                socket.default_value = 0.7
            elif socket.name == 'Rows':
                socket.default_value = 3
            elif socket.name == 'Columns':
                socket.default_value = 5
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build kawaii bricks geometry."""
        nodes = tree.nodes
        links = tree.links

        puff_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Mesh to Points for instancing
        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-200, 200)

        height_mul = nodes.new('ShaderNodeMath')
        height_mul.operation = 'MULTIPLY'
        height_mul.location = (-400, 100)
        height_mul.inputs[1].default_value = 1.0
        links.new(body_scale_sock, height_mul.inputs[0])
        link_from_input(links, input_node, 'Height', height_mul.inputs[1])
        link_cube_size(
            links, tree, cube,
            x_sock=get_input_socket(input_node, 'Width'),
            y_sock=height_mul.outputs[0],
            z_sock=get_input_socket(input_node, 'Depth'),
            location=(-300, 200),
        )
        
        # Subdivide for rounded edges
        subdivide = nodes.new('GeometryNodeSubdivideMesh')
        subdivide.location = (0, 200)
        subdivide.inputs['Selection'].default_value = True
        subdivide.inputs['Cuts'].default_value = 3
        
        links.new(cube.outputs['Mesh'], subdivide.inputs['Mesh'])
        
        # Kindchenschema puff — inflate corners when Roundness is high
        puff_mul = nodes.new('ShaderNodeMath')
        puff_mul.operation = 'MULTIPLY'
        puff_mul.location = (100, 320)
        puff_mul.inputs[1].default_value = 0.04
        links.new(puff_scale_sock, puff_mul.inputs[0])

        set_pos = nodes.new('GeometryNodeSetPosition')
        set_pos.location = (200, 200)
        
        links.new(subdivide.outputs['Mesh'], set_pos.inputs['Mesh'])
        link_to_vector_input(
            links, tree, set_pos.inputs['Offset'],
            x_sock=puff_mul.outputs[0], default_y=0.0, default_z=0.0,
            location=(150, 320),
        )
        
        # Instance on Points for brick pattern
        instance = nodes.new('GeometryNodeInstanceOnPoints')
        instance.location = (400, 0)
        
        links.new(set_pos.outputs['Mesh'], instance.inputs['Points'])
        links.new(cube.outputs['Mesh'], instance.inputs['Instance'])
        
        # Realize Instances
        realize = nodes.new('GeometryNodeRealizeInstances')
        realize.location = (600, 0)
        
        links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
        
        # Output
        links.new(realize.outputs['Geometry'], output_node.inputs['Geometry'])


@register_generator
class KawaiiWallGN(KawaiiGNBase):
    """Kawaii Wall with cute proportions and optional face."""
    
    category = "architecture"
    generator_id = "kawaii_wall_gn"
    generator_name = "Kawaii Wall"
    description = "Cute wall — Roundness bulges width/height vs thickness (Kindchenschema)"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        """Add wall parameters."""
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Has Face', in_out='INPUT', socket_type='NodeSocketBool')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width':
                socket.default_value = 4.0
            elif socket.name == 'Height':
                socket.default_value = 3.0
            elif socket.name == 'Thickness':
                socket.default_value = 0.5
            elif socket.name == 'Roundness':
                socket.default_value = 0.5
            elif socket.name == 'Has Face':
                socket.default_value = True
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build kawaii wall geometry."""
        nodes = tree.nodes
        links = tree.links

        face_scale_sock, depth_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-200, 0)

        wall_w = nodes.new('ShaderNodeMath')
        wall_w.operation = 'MULTIPLY'
        wall_w.location = (-400, 250)
        links.new(face_scale_sock, wall_w.inputs[0])
        link_from_input(links, input_node, 'Width', wall_w.inputs[1])

        wall_h = nodes.new('ShaderNodeMath')
        wall_h.operation = 'MULTIPLY'
        wall_h.location = (-400, 150)
        links.new(face_scale_sock, wall_h.inputs[0])
        link_from_input(links, input_node, 'Height', wall_h.inputs[1])

        wall_t = nodes.new('ShaderNodeMath')
        wall_t.operation = 'MULTIPLY'
        wall_t.location = (-400, 50)
        links.new(depth_scale_sock, wall_t.inputs[0])
        link_from_input(links, input_node, 'Thickness', wall_t.inputs[1])

        link_cube_size(
            links, tree, cube,
            x_sock=wall_w.outputs[0], y_sock=wall_h.outputs[0], z_sock=wall_t.outputs[0],
            location=(-300, 0),
        )

        links.new(cube.outputs['Mesh'], output_node.inputs['Geometry'])


def register():
    """Register kawaii architecture generators."""
    pass


def unregister():
    """Unregister kawaii architecture generators."""
    pass
