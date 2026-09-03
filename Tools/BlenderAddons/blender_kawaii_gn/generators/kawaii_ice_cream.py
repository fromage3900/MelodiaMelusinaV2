"""Kawaii Ice Cream Generator."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input


@register_generator
class KawaiiIceCreamGN(KawaiiGNBase):
    """Kawaii Ice Cream Cone with scoops."""
    category = "food"
    generator_id = "kawaii_ice_cream_gn"
    generator_name = "Kawaii Ice Cream"
    description = "Ice cream cone with multiple scoops"

    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Cone Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Cone Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Scoop Count', in_out='INPUT', socket_type='NodeSocketInt')
        tree.interface.new_socket('Scoop Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')

        for socket in tree.interface.items_tree:
            if socket.name == 'Cone Height':
                socket.default_value = 1.2
            elif socket.name == 'Cone Radius':
                socket.default_value = 0.3
            elif socket.name == 'Scoop Count':
                socket.default_value = 3
            elif socket.name == 'Scoop Size':
                socket.default_value = 0.4
            elif socket.name == 'Roundness':
                socket.default_value = 0.7

    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        scoop_scale_sock, cone_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        cone = nodes.new('GeometryNodeMeshCone')
        cone.location = (-600, 0)
        cone.inputs['Radius'].default_value = 0.3
        cone.inputs['Depth'].default_value = 1.2
        cone.inputs['Vertices'].default_value = 16

        cone_radius = nodes.new('ShaderNodeMath')
        cone_radius.operation = 'MULTIPLY'
        cone_radius.location = (-800, 50)
        links.new(cone_scale_sock, cone_radius.inputs[0])
        link_from_input(links, input_node, 'Cone Radius', cone_radius.inputs[1])
        links.new(cone_radius.outputs[0], cone.inputs['Radius'])

        cone_height = nodes.new('ShaderNodeMath')
        cone_height.operation = 'MULTIPLY'
        cone_height.location = (-800, -50)
        links.new(cone_scale_sock, cone_height.inputs[0])
        link_from_input(links, input_node, 'Cone Height', cone_height.inputs[1])
        links.new(cone_height.outputs[0], cone.inputs['Depth'])

        scoop1 = nodes.new('GeometryNodeMeshUVSphere')
        scoop1.location = (-600, 200)
        scoop1.inputs['Radius'].default_value = 0.4
        scoop1.inputs['Segments'].default_value = 32

        scoop1_radius = nodes.new('ShaderNodeMath')
        scoop1_radius.operation = 'MULTIPLY'
        scoop1_radius.location = (-800, 250)
        links.new(scoop_scale_sock, scoop1_radius.inputs[0])
        link_from_input(links, input_node, 'Scoop Size', scoop1_radius.inputs[1])
        links.new(scoop1_radius.outputs[0], scoop1.inputs['Radius'])

        scoop1_pos = nodes.new('GeometryNodeTransform')
        scoop1_pos.location = (-400, 200)
        scoop1_pos.inputs['Translation'].default_value = (0, 0, 1.0)
        links.new(scoop1.outputs['Mesh'], scoop1_pos.inputs['Geometry'])

        scoop2 = nodes.new('GeometryNodeMeshUVSphere')
        scoop2.location = (-600, 400)
        scoop2.inputs['Radius'].default_value = 0.4
        scoop2.inputs['Segments'].default_value = 32

        scoop2_radius = nodes.new('ShaderNodeMath')
        scoop2_radius.operation = 'MULTIPLY'
        scoop2_radius.location = (-800, 450)
        links.new(scoop_scale_sock, scoop2_radius.inputs[0])
        link_from_input(links, input_node, 'Scoop Size', scoop2_radius.inputs[1])
        links.new(scoop2_radius.outputs[0], scoop2.inputs['Radius'])

        scoop2_pos = nodes.new('GeometryNodeTransform')
        scoop2_pos.location = (-400, 400)
        scoop2_pos.inputs['Translation'].default_value = (0, 0, 1.6)
        links.new(scoop2.outputs['Mesh'], scoop2_pos.inputs['Geometry'])

        scoop3 = nodes.new('GeometryNodeMeshUVSphere')
        scoop3.location = (-600, 600)
        scoop3.inputs['Radius'].default_value = 0.35
        scoop3.inputs['Segments'].default_value = 32

        scoop3_radius = nodes.new('ShaderNodeMath')
        scoop3_radius.operation = 'MULTIPLY'
        scoop3_radius.location = (-800, 650)
        links.new(scoop_scale_sock, scoop3_radius.inputs[0])
        link_from_input(links, input_node, 'Scoop Size', scoop3_radius.inputs[1])
        links.new(scoop3_radius.outputs[0], scoop3.inputs['Radius'])

        scoop3_pos = nodes.new('GeometryNodeTransform')
        scoop3_pos.location = (-400, 600)
        scoop3_pos.inputs['Translation'].default_value = (0, 0, 2.1)
        links.new(scoop3.outputs['Mesh'], scoop3_pos.inputs['Geometry'])

        cherry = nodes.new('GeometryNodeMeshUVSphere')
        cherry.location = (-600, 800)
        cherry.inputs['Radius'].default_value = 0.1
        cherry.inputs['Segments'].default_value = 16

        cherry_pos = nodes.new('GeometryNodeTransform')
        cherry_pos.location = (-400, 800)
        cherry_pos.inputs['Translation'].default_value = (0, 0, 2.5)
        links.new(cherry.outputs['Mesh'], cherry_pos.inputs['Geometry'])

        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-200, 100)
        links.new(cone.outputs['Mesh'], j1.inputs['Geometry'])
        links.new(scoop1_pos.outputs['Geometry'], j1.inputs['Geometry'])

        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (0, 300)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(scoop2_pos.outputs['Geometry'], j2.inputs['Geometry'])

        j3 = nodes.new('GeometryNodeJoinGeometry')
        j3.location = (200, 500)
        links.new(j2.outputs['Geometry'], j3.inputs['Geometry'])
        links.new(scoop3_pos.outputs['Geometry'], j3.inputs['Geometry'])

        j4 = nodes.new('GeometryNodeJoinGeometry')
        j4.location = (400, 0)
        links.new(j3.outputs['Geometry'], j4.inputs['Geometry'])
        links.new(cherry_pos.outputs['Geometry'], j4.inputs['Geometry'])

        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (600, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j4.outputs['Geometry'], subdiv.inputs['Mesh'])

        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


def register():
    pass


def unregister():
    pass
