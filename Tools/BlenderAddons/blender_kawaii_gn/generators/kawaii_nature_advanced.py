"""Kawaii Nature Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import link_from_input, kindchenschema_from_input, mesh_input


@register_generator
class KawaiiTreeGN(KawaiiGNBase):
    """Kawaii Tree with round canopy."""
    category = "nature"
    generator_id = "kawaii_tree_gn"
    generator_name = "Kawaii Tree"
    description = "Cute tree with round fluffy canopy"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Trunk Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Trunk Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Canopy Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Canopy Fluffiness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Trunk Height': socket.default_value = 2.0
            elif socket.name == 'Trunk Radius': socket.default_value = 0.15
            elif socket.name == 'Canopy Size': socket.default_value = 1.5
            elif socket.name == 'Canopy Fluffiness': socket.default_value = 0.8
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        canopy_scale_sock, trunk_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Trunk (cylinder)
        trunk = nodes.new('GeometryNodeMeshCylinder')
        trunk.location = (-600, 0)
        trunk.inputs['Radius'].default_value = 0.15
        mesh_input(trunk, 'Height').default_value = 2.0
        trunk.inputs['Vertices'].default_value = 16

        trunk_radius = nodes.new('ShaderNodeMath')
        trunk_radius.operation = 'MULTIPLY'
        trunk_radius.location = (-800, 50)
        links.new(trunk_scale_sock, trunk_radius.inputs[0])
        link_from_input(links, input_node, 'Trunk Radius', trunk_radius.inputs[1])
        links.new(trunk_radius.outputs[0], trunk.inputs['Radius'])

        trunk_height = nodes.new('ShaderNodeMath')
        trunk_height.operation = 'MULTIPLY'
        trunk_height.location = (-800, -50)
        links.new(trunk_scale_sock, trunk_height.inputs[0])
        link_from_input(links, input_node, 'Trunk Height', trunk_height.inputs[1])
        links.new(trunk_height.outputs[0], mesh_input(trunk, 'Height'))
        
        # Canopy (large sphere)
        canopy = nodes.new('GeometryNodeMeshUVSphere')
        canopy.location = (-600, 200)
        canopy.inputs['Radius'].default_value = 1.0
        canopy.inputs['Segments'].default_value = 32
        canopy.inputs['Rings'].default_value = 16

        canopy_radius = nodes.new('ShaderNodeMath')
        canopy_radius.operation = 'MULTIPLY'
        canopy_radius.location = (-800, 250)
        links.new(canopy_scale_sock, canopy_radius.inputs[0])
        link_from_input(links, input_node, 'Canopy Size', canopy_radius.inputs[1])
        links.new(canopy_radius.outputs[0], canopy.inputs['Radius'])
        
        # Position canopy on top
        canopy_pos = nodes.new('GeometryNodeTransform')
        canopy_pos.location = (-400, 200)
        canopy_pos.inputs['Translation'].default_value = (0, 0, 2.0)
        links.new(canopy.outputs['Mesh'], canopy_pos.inputs['Geometry'])
        
        # Extra fluff spheres around canopy
        fluff1 = nodes.new('GeometryNodeMeshUVSphere')
        fluff1.location = (-600, 400)
        fluff1.inputs['Radius'].default_value = 0.6
        fluff1.inputs['Segments'].default_value = 16

        fluff1_radius = nodes.new('ShaderNodeMath')
        fluff1_radius.operation = 'MULTIPLY'
        fluff1_radius.location = (-800, 450)
        links.new(canopy_scale_sock, fluff1_radius.inputs[0])
        link_from_input(links, input_node, 'Canopy Fluffiness', fluff1_radius.inputs[1])
        links.new(fluff1_radius.outputs[0], fluff1.inputs['Radius'])
        
        fluff1_pos = nodes.new('GeometryNodeTransform')
        fluff1_pos.location = (-400, 400)
        fluff1_pos.inputs['Translation'].default_value = (0.7, 0, 2.2)
        links.new(fluff1.outputs['Mesh'], fluff1_pos.inputs['Geometry'])
        
        fluff2 = nodes.new('GeometryNodeMeshUVSphere')
        fluff2.location = (-600, 600)
        fluff2.inputs['Radius'].default_value = 0.6
        fluff2.inputs['Segments'].default_value = 16

        fluff2_radius = nodes.new('ShaderNodeMath')
        fluff2_radius.operation = 'MULTIPLY'
        fluff2_radius.location = (-800, 650)
        links.new(canopy_scale_sock, fluff2_radius.inputs[0])
        link_from_input(links, input_node, 'Canopy Fluffiness', fluff2_radius.inputs[1])
        links.new(fluff2_radius.outputs[0], fluff2.inputs['Radius'])
        
        fluff2_pos = nodes.new('GeometryNodeTransform')
        fluff2_pos.location = (-400, 600)
        fluff2_pos.inputs['Translation'].default_value = (-0.7, 0, 2.2)
        links.new(fluff2.outputs['Mesh'], fluff2_pos.inputs['Geometry'])
        
        # Join all parts
        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-200, 100)
        links.new(trunk.outputs['Mesh'], j1.inputs['Geometry'])
        links.new(canopy_pos.outputs['Geometry'], j1.inputs['Geometry'])
        
        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (0, 300)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(fluff1_pos.outputs['Geometry'], j2.inputs['Geometry'])
        
        j3 = nodes.new('GeometryNodeJoinGeometry')
        j3.location = (200, 0)
        links.new(j2.outputs['Geometry'], j3.inputs['Geometry'])
        links.new(fluff2_pos.outputs['Geometry'], j3.inputs['Geometry'])
        
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (400, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j3.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class KawaiiFlowerGN(KawaiiGNBase):
    """Kawaii Flower with petals."""
    category = "nature"
    generator_id = "kawaii_flower_gn"
    generator_name = "Kawaii Flower"
    description = "Cute flower with round petals"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Stem Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Petal Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Petal Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Center Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Stem Height': socket.default_value = 1.5
            elif socket.name == 'Petal Count': socket.default_value = 6
            elif socket.name == 'Petal Size': socket.default_value = 0.3
            elif socket.name == 'Center Size': socket.default_value = 0.2
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        blossom_scale_sock, stem_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Stem (thin cylinder)
        stem = nodes.new('GeometryNodeMeshCylinder')
        stem.location = (-600, 0)
        stem.inputs['Radius'].default_value = 0.05
        mesh_input(stem, 'Height').default_value = 1.5
        stem.inputs['Vertices'].default_value = 8

        stem_height = nodes.new('ShaderNodeMath')
        stem_height.operation = 'MULTIPLY'
        stem_height.location = (-800, -50)
        links.new(stem_scale_sock, stem_height.inputs[0])
        link_from_input(links, input_node, 'Stem Height', stem_height.inputs[1])
        links.new(stem_height.outputs[0], mesh_input(stem, 'Height'))

        stem_radius = nodes.new('ShaderNodeMath')
        stem_radius.operation = 'MULTIPLY'
        stem_radius.location = (-800, -150)
        stem_radius.inputs[1].default_value = 0.05
        links.new(stem_scale_sock, stem_radius.inputs[0])
        links.new(stem_radius.outputs[0], stem.inputs['Radius'])
        
        # Flower center (sphere)
        center = nodes.new('GeometryNodeMeshUVSphere')
        center.location = (-600, 200)
        center.inputs['Radius'].default_value = 0.2
        center.inputs['Segments'].default_value = 16

        center_radius = nodes.new('ShaderNodeMath')
        center_radius.operation = 'MULTIPLY'
        center_radius.location = (-800, 250)
        links.new(blossom_scale_sock, center_radius.inputs[0])
        link_from_input(links, input_node, 'Center Size', center_radius.inputs[1])
        links.new(center_radius.outputs[0], center.inputs['Radius'])
        
        center_pos = nodes.new('GeometryNodeTransform')
        center_pos.location = (-400, 200)
        center_pos.inputs['Translation'].default_value = (0, 0, 1.5)
        links.new(center.outputs['Mesh'], center_pos.inputs['Geometry'])
        
        # Petals (spheres arranged in circle)
        petal1 = nodes.new('GeometryNodeMeshUVSphere')
        petal1.location = (-600, 400)
        petal1.inputs['Radius'].default_value = 0.3
        petal1.inputs['Segments'].default_value = 16

        petal1_radius = nodes.new('ShaderNodeMath')
        petal1_radius.operation = 'MULTIPLY'
        petal1_radius.location = (-800, 450)
        links.new(blossom_scale_sock, petal1_radius.inputs[0])
        link_from_input(links, input_node, 'Petal Size', petal1_radius.inputs[1])
        links.new(petal1_radius.outputs[0], petal1.inputs['Radius'])
        
        p1_pos = nodes.new('GeometryNodeTransform')
        p1_pos.location = (-400, 400)
        p1_pos.inputs['Translation'].default_value = (0.4, 0, 1.5)
        links.new(petal1.outputs['Mesh'], p1_pos.inputs['Geometry'])
        
        petal2 = nodes.new('GeometryNodeMeshUVSphere')
        petal2.location = (-600, 600)
        petal2.inputs['Radius'].default_value = 0.3
        petal2.inputs['Segments'].default_value = 16

        petal2_radius = nodes.new('ShaderNodeMath')
        petal2_radius.operation = 'MULTIPLY'
        petal2_radius.location = (-800, 650)
        links.new(blossom_scale_sock, petal2_radius.inputs[0])
        link_from_input(links, input_node, 'Petal Size', petal2_radius.inputs[1])
        links.new(petal2_radius.outputs[0], petal2.inputs['Radius'])
        
        p2_pos = nodes.new('GeometryNodeTransform')
        p2_pos.location = (-400, 600)
        p2_pos.inputs['Translation'].default_value = (-0.4, 0, 1.5)
        links.new(petal2.outputs['Mesh'], p2_pos.inputs['Geometry'])
        
        petal3 = nodes.new('GeometryNodeMeshUVSphere')
        petal3.location = (-600, 800)
        petal3.inputs['Radius'].default_value = 0.3
        petal3.inputs['Segments'].default_value = 16

        petal3_radius = nodes.new('ShaderNodeMath')
        petal3_radius.operation = 'MULTIPLY'
        petal3_radius.location = (-800, 850)
        links.new(blossom_scale_sock, petal3_radius.inputs[0])
        link_from_input(links, input_node, 'Petal Size', petal3_radius.inputs[1])
        links.new(petal3_radius.outputs[0], petal3.inputs['Radius'])
        
        p3_pos = nodes.new('GeometryNodeTransform')
        p3_pos.location = (-400, 800)
        p3_pos.inputs['Translation'].default_value = (0, 0.4, 1.5)
        links.new(petal3.outputs['Mesh'], p3_pos.inputs['Geometry'])
        
        petal4 = nodes.new('GeometryNodeMeshUVSphere')
        petal4.location = (-600, 1000)
        petal4.inputs['Radius'].default_value = 0.3
        petal4.inputs['Segments'].default_value = 16

        petal4_radius = nodes.new('ShaderNodeMath')
        petal4_radius.operation = 'MULTIPLY'
        petal4_radius.location = (-800, 1050)
        links.new(blossom_scale_sock, petal4_radius.inputs[0])
        link_from_input(links, input_node, 'Petal Size', petal4_radius.inputs[1])
        links.new(petal4_radius.outputs[0], petal4.inputs['Radius'])
        
        p4_pos = nodes.new('GeometryNodeTransform')
        p4_pos.location = (-400, 1000)
        p4_pos.inputs['Translation'].default_value = (0, -0.4, 1.5)
        links.new(petal4.outputs['Mesh'], p4_pos.inputs['Geometry'])
        
        # Join all
        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-200, 100)
        links.new(stem.outputs['Mesh'], j1.inputs['Geometry'])
        links.new(center_pos.outputs['Geometry'], j1.inputs['Geometry'])
        
        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (0, 300)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(p1_pos.outputs['Geometry'], j2.inputs['Geometry'])
        
        j3 = nodes.new('GeometryNodeJoinGeometry')
        j3.location = (200, 500)
        links.new(j2.outputs['Geometry'], j3.inputs['Geometry'])
        links.new(p2_pos.outputs['Geometry'], j3.inputs['Geometry'])
        
        j4 = nodes.new('GeometryNodeJoinGeometry')
        j4.location = (400, 700)
        links.new(j3.outputs['Geometry'], j4.inputs['Geometry'])
        links.new(p3_pos.outputs['Geometry'], j4.inputs['Geometry'])
        
        j5 = nodes.new('GeometryNodeJoinGeometry')
        j5.location = (600, 0)
        links.new(j4.outputs['Geometry'], j5.inputs['Geometry'])
        links.new(p4_pos.outputs['Geometry'], j5.inputs['Geometry'])
        
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (800, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j5.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
