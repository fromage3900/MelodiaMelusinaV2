"""Kawaii Food GN Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input

@register_generator
class KawaiiCupcakeGN(KawaiiGNBase):
    category = "food"
    generator_id = "kawaii_cupcake_gn"
    generator_name = "Kawaii Cupcake"
    description = "Cute cupcake with frosting"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Frosting Height', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 1.0
            elif socket.name == 'Frosting Height': socket.default_value = 0.5
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        cylinder = nodes.new('GeometryNodeMeshCylinder')
        cylinder.location = (-200, 0)
        link_from_input(links, input_node, 'Size', cylinder.inputs['Radius'])
        links.new(cylinder.outputs['Mesh'], output_node.inputs['Geometry'])

def register(): pass
def unregister(): pass
