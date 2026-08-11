"""Kawaii Characters GN Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input

@register_generator
class KawaiiChibiGN(KawaiiGNBase):
    category = "characters"
    generator_id = "kawaii_chibi_gn"
    generator_name = "Chibi Character Base"
    description = "Chibi proportioned character base"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Head Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Body Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Height': socket.default_value = 2.0
            elif socket.name == 'Head Size': socket.default_value = 0.6
            elif socket.name == 'Body Size': socket.default_value = 0.4
            elif socket.name == 'Roundness': socket.default_value = 0.8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        head_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        head = nodes.new('GeometryNodeMeshUVSphere')
        head.location = (-200, 100)
        head.inputs['Radius'].default_value = 0.5

        head_radius = nodes.new('ShaderNodeMath')
        head_radius.operation = 'MULTIPLY'
        head_radius.location = (-400, 200)
        links.new(head_scale_sock, head_radius.inputs[0])
        link_from_input(links, input_node, 'Head Size', head_radius.inputs[1])
        links.new(head_radius.outputs[0], head.inputs['Radius'])
        
        body = nodes.new('GeometryNodeMeshUVSphere')
        body.location = (-200, -100)
        body.inputs['Radius'].default_value = 0.4

        body_radius = nodes.new('ShaderNodeMath')
        body_radius.operation = 'MULTIPLY'
        body_radius.location = (-400, -100)
        links.new(body_scale_sock, body_radius.inputs[0])
        link_from_input(links, input_node, 'Body Size', body_radius.inputs[1])
        links.new(body_radius.outputs[0], body.inputs['Radius'])
        
        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (0, 0)
        links.new(head.outputs['Mesh'], join.inputs['Geometry'])
        links.new(body.outputs['Mesh'], join.inputs['Geometry'])
        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])

def register(): pass
def unregister(): pass
