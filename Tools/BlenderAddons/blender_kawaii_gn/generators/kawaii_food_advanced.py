"""Kawaii Food Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket, get_output_socket
from ..core.node_builder import (
    link_from_input,
    kindchenschema_from_input,
    create_mesh_torus,
    mesh_input,
)


@register_generator
class KawaiiDonutGN(KawaiiGNBase):
    """Kawaii Donut with frosting."""
    category = "food"
    generator_id = "kawaii_donut_gn"
    generator_name = "Kawaii Donut"
    description = "Cute donut - Roundness scales icing ring, height, and lift"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Frosting Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Sprinkle Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Radius': socket.default_value = 0.8
            elif socket.name == 'Thickness': socket.default_value = 0.4
            elif socket.name == 'Frosting Height': socket.default_value = 0.15
            elif socket.name == 'Sprinkle Count': socket.default_value = 30
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        icing_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Donut base (torus via curve sweep - MeshTorus removed in Blender 5.1)
        donut_ctm, donut_circle, donut_profile = create_mesh_torus(
            nodes, links, (-600, 0), major_radius=0.8, minor_radius=0.3,
        )
        links.new(get_input_socket(input_node, 'Radius'), donut_circle.inputs['Radius'])

        body_thickness = nodes.new('ShaderNodeMath')
        body_thickness.operation = 'MULTIPLY'
        body_thickness.location = (-800, -50)
        links.new(body_scale_sock, body_thickness.inputs[0])
        link_from_input(links, input_node, 'Thickness', body_thickness.inputs[1])
        links.new(body_thickness.outputs[0], donut_profile.inputs['Radius'])
        
        # Frosting (slightly larger torus on top) - Roundness scales icing ring + height
        frost_ctm, frost_circle, frost_profile = create_mesh_torus(
            nodes, links, (-600, 200), major_radius=0.8, minor_radius=0.35,
        )

        frost_radius = nodes.new('ShaderNodeMath')
        frost_radius.operation = 'MULTIPLY'
        frost_radius.location = (-800, 250)
        links.new(icing_scale_sock, frost_radius.inputs[0])
        link_from_input(links, input_node, 'Radius', frost_radius.inputs[1])
        links.new(frost_radius.outputs[0], frost_circle.inputs['Radius'])

        icing_height = nodes.new('ShaderNodeMath')
        icing_height.operation = 'MULTIPLY'
        icing_height.location = (-800, 150)
        links.new(icing_scale_sock, icing_height.inputs[0])
        link_from_input(links, input_node, 'Frosting Height', icing_height.inputs[1])
        links.new(icing_height.outputs[0], frost_profile.inputs['Radius'])

        frost_z = nodes.new('ShaderNodeMath')
        frost_z.operation = 'MULTIPLY'
        frost_z.location = (-600, 100)
        frost_z.inputs[1].default_value = 0.35
        links.new(body_thickness.outputs[0], frost_z.inputs[0])

        frost_lift = nodes.new('ShaderNodeCombineXYZ')
        frost_lift.location = (-400, 100)
        frost_lift.inputs['X'].default_value = 0.0
        frost_lift.inputs['Y'].default_value = 0.0
        links.new(frost_z.outputs[0], frost_lift.inputs['Z'])

        frosting_pos = nodes.new('GeometryNodeTransform')
        frosting_pos.location = (-200, 200)
        links.new(frost_lift.outputs['Vector'], frosting_pos.inputs['Translation'])
        links.new(frost_ctm.outputs['Mesh'], frosting_pos.inputs['Geometry'])
        
        # Join and subdivide
        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (-200, 0)
        links.new(donut_ctm.outputs['Mesh'], join.inputs['Geometry'])
        links.new(frosting_pos.outputs['Geometry'], join.inputs['Geometry'])
        
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (0, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(join.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], get_output_socket(output_node, 'Geometry'))


@register_generator
class KawaiiCupcakeGN(KawaiiGNBase):
    """Kawaii Cupcake with frosting swirl."""
    category = "food"
    generator_id = "kawaii_cupcake_gn"
    generator_name = "Kawaii Cupcake"
    description = "Cute cupcake with swirled frosting"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Base Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Base Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Frosting Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Frosting Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Fluting', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Base Radius': socket.default_value = 0.5
            elif socket.name == 'Base Height': socket.default_value = 0.6
            elif socket.name == 'Frosting Radius': socket.default_value = 0.45
            elif socket.name == 'Frosting Height': socket.default_value = 0.5
            elif socket.name == 'Fluting': socket.default_value = 12
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        icing_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Cupcake base (cylinder, wider at top)
        base = nodes.new('GeometryNodeMeshCylinder')
        base.location = (-600, 0)
        base.inputs['Radius'].default_value = 0.5
        mesh_input(base, 'Height').default_value = 0.6
        base.inputs['Vertices'].default_value = 32

        base_radius = nodes.new('ShaderNodeMath')
        base_radius.operation = 'MULTIPLY'
        base_radius.location = (-800, 50)
        links.new(body_scale_sock, base_radius.inputs[0])
        link_from_input(links, input_node, 'Base Radius', base_radius.inputs[1])
        links.new(base_radius.outputs[0], base.inputs['Radius'])

        base_height = nodes.new('ShaderNodeMath')
        base_height.operation = 'MULTIPLY'
        base_height.location = (-800, -50)
        links.new(body_scale_sock, base_height.inputs[0])
        link_from_input(links, input_node, 'Base Height', base_height.inputs[1])
        links.new(base_height.outputs[0], mesh_input(base, 'Height'))
        
        # Frosting (sphere on top)
        frosting = nodes.new('GeometryNodeMeshUVSphere')
        frosting.location = (-600, 200)
        frosting.inputs['Radius'].default_value = 0.45
        frosting.inputs['Segments'].default_value = 32
        frosting.inputs['Rings'].default_value = 16

        frost_radius = nodes.new('ShaderNodeMath')
        frost_radius.operation = 'MULTIPLY'
        frost_radius.location = (-800, 250)
        links.new(icing_scale_sock, frost_radius.inputs[0])
        link_from_input(links, input_node, 'Frosting Radius', frost_radius.inputs[1])
        links.new(frost_radius.outputs[0], frosting.inputs['Radius'])
        
        frosting_pos = nodes.new('GeometryNodeTransform')
        frosting_pos.location = (-400, 200)
        frosting_pos.inputs['Translation'].default_value = (0, 0, 0.5)
        links.new(frosting.outputs['Mesh'], frosting_pos.inputs['Geometry'])
        
        # Cherry on top (small sphere)
        cherry = nodes.new('GeometryNodeMeshUVSphere')
        cherry.location = (-600, 400)
        cherry.inputs['Radius'].default_value = 0.1
        cherry.inputs['Segments'].default_value = 16
        
        cherry_pos = nodes.new('GeometryNodeTransform')
        cherry_pos.location = (-400, 400)
        cherry_pos.inputs['Translation'].default_value = (0, 0, 0.95)
        links.new(cherry.outputs['Mesh'], cherry_pos.inputs['Geometry'])
        
        # Join all
        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-200, 100)
        links.new(base.outputs['Mesh'], j1.inputs['Geometry'])
        links.new(frosting_pos.outputs['Geometry'], j1.inputs['Geometry'])
        
        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (0, 0)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(cherry_pos.outputs['Geometry'], j2.inputs['Geometry'])
        
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (200, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j2.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
