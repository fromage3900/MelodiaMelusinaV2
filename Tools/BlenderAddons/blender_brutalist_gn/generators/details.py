"""Brutalist Detail Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import BrutalistGNBase, register_generator


@register_generator
class BrutalistBalconyGN(BrutalistGNBase):
    """Cantilevered Concrete Balcony."""
    category = "details"
    generator_id = "brutalist_balcony_gn"
    generator_name = "Balcony"
    description = "Raw concrete cantilevered balcony"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Depth', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Railing Height', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 4.0
            elif socket.name == 'Depth': socket.default_value = 2.0
            elif socket.name == 'Thickness': socket.default_value = 0.2
            elif socket.name == 'Railing Height': socket.default_value = 1.1
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Balcony slab
        slab = nodes.new('GeometryNodeMeshCube')
        slab.location = (-400, 0)
        slab.inputs['Size'].default_value = (4.0, 2.0, 0.2)
        links.new(input_node.outputs['Width'], slab.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Depth'], slab.inputs['Size'].sockets[1])
        links.new(input_node.outputs['Thickness'], slab.inputs['Size'].sockets[2])
        
        links.new(slab.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistBreezeBlockGN(BrutalistGNBase):
    """Decorative Breeze Block Screen."""
    category = "details"
    generator_id = "brutalist_breeze_block_gn"
    generator_name = "Breeze Block"
    description = "Perforated concrete screen block"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Pattern', in_out='INPUT', socket_type='NodeSocketInt')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 1.0
            elif socket.name == 'Height': socket.default_value = 1.0
            elif socket.name == 'Thickness': socket.default_value = 0.15
            elif socket.name == 'Pattern': socket.default_value = 0
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Screen panel
        panel = nodes.new('GeometryNodeMeshCube')
        panel.location = (-400, 0)
        panel.inputs['Size'].default_value = (1.0, 0.15, 1.0)
        links.new(input_node.outputs['Width'], panel.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Thickness'], panel.inputs['Size'].sockets[1])
        links.new(input_node.outputs['Height'], panel.inputs['Size'].sockets[2])
        
        links.new(panel.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class BrutalistPilotisGN(BrutalistGNBase):
    """Reinforced Concrete Pilotis (Support Columns)."""
    category = "details"
    generator_id = "brutalist_pilotis_gn"
    generator_name = "Pilotis"
    description = "Structural support columns"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Spacing', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Height': socket.default_value = 5.0
            elif socket.name == 'Width': socket.default_value = 0.6
            elif socket.name == 'Count': socket.default_value = 4
            elif socket.name == 'Spacing': socket.default_value = 3.0
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        # Single pilotis column
        column = nodes.new('GeometryNodeMeshCube')
        column.location = (-400, 0)
        column.inputs['Size'].default_value = (0.6, 0.6, 5.0)
        links.new(input_node.outputs['Width'], column.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Height'], column.inputs['Size'].sockets[2])
        
        links.new(column.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
