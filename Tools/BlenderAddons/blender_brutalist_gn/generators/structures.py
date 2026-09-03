"""Brutalist Structure Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import BrutalistGNBase, register_generator


@register_generator
class BrutalistTowerBlockGN(BrutalistGNBase):
    """Massive Tower Block with repetitive windows."""
    category = "structures"
    generator_id = "brutalist_tower_block_gn"
    generator_name = "Tower Block"
    description = "Monolithic residential tower"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Depth', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Floors', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Floor Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Window Spacing', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 12.0
            elif socket.name == 'Depth': socket.default_value = 8.0
            elif socket.name == 'Floors': socket.default_value = 20
            elif socket.name == 'Floor Height': socket.default_value = 3.0
            elif socket.name == 'Window Spacing': socket.default_value = 2.5
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Main tower
        tower = nodes.new('GeometryNodeMeshCube')
        tower.location = (-400, 0)
        tower.inputs['Size'].default_value = (12.0, 8.0, 60.0)
        links.new(input_node.outputs['Width'], tower.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Depth'], tower.inputs['Size'].sockets[1])
        links.new(input_node.outputs['Floors'], tower.inputs['Size'].sockets[2])
        links.new(input_node.outputs['Floor Height'], tower.inputs['Size'].sockets[2])
        
        links.new(tower.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistMonumentGN(BrutalistGNBase):
    """Monumental Civic Structure."""
    category = "structures"
    generator_id = "brutalist_monument_gn"
    generator_name = "Monument"
    description = "Oversized brutalist monument"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Base Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Taper', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Base Width': socket.default_value = 8.0
            elif socket.name == 'Height': socket.default_value = 15.0
            elif socket.name == 'Taper': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Monument base
        base = nodes.new('GeometryNodeMeshCube')
        base.location = (-400, 0)
        base.inputs['Size'].default_value = (8.0, 8.0, 15.0)
        links.new(input_node.outputs['Base Width'], base.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Height'], base.inputs['Size'].sockets[2])
        
        links.new(base.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistHabitatGN(BrutalistGNBase):
    """Habitat-style Stepped Structure."""
    category = "structures"
    generator_id = "brutalist_habitat_gn"
    generator_name = "Habitat"
    description = "Stepped modular housing complex"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Module Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Module Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Steps', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Modules Per Step', in_out='INPUT', socket_type='NodeSocketInt')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Module Width': socket.default_value = 4.0
            elif socket.name == 'Module Height': socket.default_value = 3.0
            elif socket.name == 'Steps': socket.default_value = 5
            elif socket.name == 'Modules Per Step': socket.default_value = 3
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Base module
        module = nodes.new('GeometryNodeMeshCube')
        module.location = (-400, 0)
        module.inputs['Size'].default_value = (4.0, 4.0, 3.0)
        links.new(input_node.outputs['Module Width'], module.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Module Height'], module.inputs['Size'].sockets[2])
        
        links.new(module.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
