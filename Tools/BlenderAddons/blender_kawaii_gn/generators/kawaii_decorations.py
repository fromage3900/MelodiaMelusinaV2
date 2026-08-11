"""Kawaii Decorations GN Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input

@register_generator
class KawaiiHeartGN(KawaiiGNBase):
    category = "decorations"
    generator_id = "kawaii_heart_gn"
    generator_name = "Kawaii Heart"
    description = "Cute heart shape"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Depth', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 1.0
            elif socket.name == 'Depth': socket.default_value = 0.3
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Create heart from two spheres and inverted cone
        sphere_l = nodes.new('GeometryNodeMeshUVSphere')
        sphere_l.location = (-600, 200)
        sphere_l.inputs['Radius'].default_value = 0.5
        sphere_l.inputs['Segments'].default_value = 32
        link_from_input(links, input_node, 'Size', sphere_l.inputs['Radius'])
        
        sphere_r = nodes.new('GeometryNodeMeshUVSphere')
        sphere_r.location = (-600, -200)
        sphere_r.inputs['Radius'].default_value = 0.5
        sphere_r.inputs['Segments'].default_value = 32
        link_from_input(links, input_node, 'Size', sphere_r.inputs['Radius'])
        
        # Position left sphere
        pos_l = nodes.new('GeometryNodeTransform')
        pos_l.location = (-400, 200)
        pos_l.inputs['Translation'].default_value = (-0.35, 0, 0.2)
        links.new(sphere_l.outputs['Mesh'], pos_l.inputs['Geometry'])
        
        # Position right sphere
        pos_r = nodes.new('GeometryNodeTransform')
        pos_r.location = (-400, -200)
        pos_r.inputs['Translation'].default_value = (0.35, 0, 0.2)
        links.new(sphere_r.outputs['Mesh'], pos_r.inputs['Geometry'])
        
        # Bottom point (inverted cone)
        cone = nodes.new('GeometryNodeMeshCone')
        cone.location = (-600, 0)
        cone.inputs['Radius'].default_value = 0.7
        cone.inputs['Depth'].default_value = 1.2
        cone.inputs['Vertices'].default_value = 32
        
        pos_cone = nodes.new('GeometryNodeTransform')
        pos_cone.location = (-400, 0)
        pos_cone.inputs['Translation'].default_value = (0, 0, -0.5)
        pos_cone.inputs['Rotation'].default_value = (3.14159, 0, 0)  # Flip upside down
        links.new(cone.outputs['Mesh'], pos_cone.inputs['Geometry'])
        
        # Join all parts
        join1 = nodes.new('GeometryNodeJoinGeometry')
        join1.location = (-200, 100)
        links.new(pos_l.outputs['Geometry'], join1.inputs['Geometry'])
        links.new(pos_r.outputs['Geometry'], join1.inputs['Geometry'])
        
        join2 = nodes.new('GeometryNodeJoinGeometry')
        join2.location = (0, 0)
        links.new(join1.outputs['Geometry'], join2.inputs['Geometry'])
        links.new(pos_cone.outputs['Geometry'], join2.inputs['Geometry'])
        
        # Smooth with subdivision
        subdivide = nodes.new('GeometryNodeSubdivisionSurface')
        subdivide.location = (200, 0)
        subdivide.inputs['Level'].default_value = 2
        links.new(join2.outputs['Geometry'], subdivide.inputs['Mesh'])
        
        links.new(subdivide.outputs['Mesh'], output_node.inputs['Geometry'])

def register(): pass
def unregister(): pass
