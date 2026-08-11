"""Kawaii Greybox GN Generators - Level design primitives."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import link_from_input, link_cube_size

@register_generator
class KawaiiCubeGN(KawaiiGNBase):
    category = "greybox"
    generator_id = "kawaii_cube_gn"
    generator_name = "Kawaii Rounded Cube"
    description = "Soft rounded cube for level blocking"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Size': socket.default_value = 2.0
            elif socket.name == 'Roundness': socket.default_value = 0.3
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-200, 0)
        size_sock = get_input_socket(input_node, 'Size')
        link_cube_size(
            links, tree, cube,
            x_sock=size_sock, y_sock=size_sock, z_sock=size_sock,
            location=(-300, 0),
        )
        links.new(cube.outputs['Mesh'], output_node.inputs['Geometry'])

def register(): pass
def unregister(): pass
