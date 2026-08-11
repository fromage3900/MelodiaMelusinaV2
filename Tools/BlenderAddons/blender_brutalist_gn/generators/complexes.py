"""Brutalist Complex Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import BrutalistGNBase, register_generator


@register_generator
class BrutalistHousingEstateGN(BrutalistGNBase):
    """Mass Housing Estate Complex."""
    category = "complexes"
    generator_id = "brutalist_housing_estate_gn"
    generator_name = "Housing Estate"
    description = "Large-scale brutalist housing complex"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Building Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Building Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Building Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Spacing', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Building Count': socket.default_value = 6
            elif socket.name == 'Building Width': socket.default_value = 10.0
            elif socket.name == 'Building Height': socket.default_value = 25.0
            elif socket.name == 'Spacing': socket.default_value = 15.0
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Single building block
        building = nodes.new('GeometryNodeMeshCube')
        building.location = (-400, 0)
        building.inputs['Size'].default_value = (10.0, 8.0, 25.0)
        links.new(input_node.outputs['Building Width'], building.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Building Height'], building.inputs['Size'].sockets[2])
        
        links.new(building.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistCivicCenterGN(BrutalistGNBase):
    """Monumental Civic Center Complex."""
    category = "complexes"
    generator_id = "brutalist_civic_center_gn"
    generator_name = "Civic Center"
    description = "Brutalist government/civic building"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Main Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Main Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Wing Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Plaza Size', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Main Width': socket.default_value = 20.0
            elif socket.name == 'Main Height': socket.default_value = 15.0
            elif socket.name == 'Wing Width': socket.default_value = 12.0
            elif socket.name == 'Plaza Size': socket.default_value = 30.0
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Main building
        main = nodes.new('GeometryNodeMeshCube')
        main.location = (-400, 0)
        main.inputs['Size'].default_value = (20.0, 15.0, 15.0)
        links.new(input_node.outputs['Main Width'], main.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Main Height'], main.inputs['Size'].sockets[2])
        
        links.new(main.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
