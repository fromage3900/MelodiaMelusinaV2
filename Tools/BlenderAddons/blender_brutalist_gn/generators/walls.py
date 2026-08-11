"""Brutalist Wall Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import BrutalistGNBase, register_generator


@register_generator
class BrutalistConcreteWallGN(BrutalistGNBase):
    """Raw Concrete Wall with form marks."""
    category = "walls"
    generator_id = "brutalist_concrete_wall_gn"
    generator_name = "Concrete Wall"
    description = "Raw board-formed concrete wall"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Form Marks', in_out='INPUT', socket_type='NodeSocketInt')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 6.0
            elif socket.name == 'Height': socket.default_value = 4.0
            elif socket.name == 'Thickness': socket.default_value = 0.3
            elif socket.name == 'Form Marks': socket.default_value = 8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Main wall
        wall = nodes.new('GeometryNodeMeshCube')
        wall.location = (-400, 0)
        wall.inputs['Size'].default_value = (6.0, 0.3, 4.0)
        links.new(input_node.outputs['Width'], wall.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Thickness'], wall.inputs['Size'].sockets[1])
        links.new(input_node.outputs['Height'], wall.inputs['Size'].sockets[2])
        
        links.new(wall.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistModularWallGN(BrutalistGNBase):
    """Modular Repetitive Wall System."""
    category = "walls"
    generator_id = "brutalist_modular_wall_gn"
    generator_name = "Modular Wall"
    description = "Grid-based modular wall panels"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Panel Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Panel Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Panel Count X', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Panel Count Y', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Spacing', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Panel Width': socket.default_value = 2.0
            elif socket.name == 'Panel Height': socket.default_value = 2.0
            elif socket.name == 'Panel Count X': socket.default_value = 5
            elif socket.name == 'Panel Count Y': socket.default_value = 3
            elif socket.name == 'Spacing': socket.default_value = 0.1
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Single panel
        panel = nodes.new('GeometryNodeMeshCube')
        panel.location = (-400, 0)
        panel.inputs['Size'].default_value = (2.0, 0.3, 2.0)
        links.new(input_node.outputs['Panel Width'], panel.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Panel Height'], panel.inputs['Size'].sockets[2])
        
        links.new(panel.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
