"""Kawaii Nature GN Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, mesh_input

@register_generator
class KawaiiTreeGN(KawaiiGNBase):
    category = "nature"
    generator_id = "kawaii_tree_gn"
    generator_name = "Kawaii Tree"
    description = "Cute rounded tree"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Trunk Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Canopy Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Trunk Height': socket.default_value = 2.0
            elif socket.name == 'Canopy Size': socket.default_value = 1.5
            elif socket.name == 'Roundness': socket.default_value = 0.8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        trunk = nodes.new('GeometryNodeMeshCylinder')
        trunk.location = (-200, -100)
        trunk.inputs['Radius'].default_value = 0.2
        mesh_input(trunk, 'Height').default_value = 2.0
        link_from_input(links, input_node, 'Trunk Height', mesh_input(trunk, 'Height'))
        
        canopy = nodes.new('GeometryNodeMeshUVSphere')
        canopy.location = (-200, 100)
        canopy.inputs['Radius'].default_value = 1.0
        link_from_input(links, input_node, 'Canopy Size', canopy.inputs['Radius'])
        
        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (0, 0)
        links.new(trunk.outputs['Mesh'], join.inputs['Geometry'])
        links.new(canopy.outputs['Mesh'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])

def register(): pass
def unregister(): pass
