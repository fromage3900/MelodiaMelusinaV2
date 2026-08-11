"""Kawaii Furniture GN Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator
from ..core.node_builder import link_from_input, kindchenschema_from_input, link_cube_size, link_translation


@register_generator
class KawaiiTableGN(KawaiiGNBase):
    category = "furniture"
    generator_id = "kawaii_table_gn"
    generator_name = "Kawaii Table"
    description = "Cute chibi table with Kindchenschema proportions"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Leg Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width':
                socket.default_value = 2.0
            elif socket.name == 'Height':
                socket.default_value = 1.0
            elif socket.name == 'Leg Thickness':
                socket.default_value = 0.15
            elif socket.name == 'Roundness':
                socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        top_scale_sock, leg_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )

        # Tabletop — chunky top scales up with cuteness
        top = nodes.new('GeometryNodeMeshCube')
        top.location = (-400, 200)

        top_w = nodes.new('ShaderNodeMath')
        top_w.operation = 'MULTIPLY'
        top_w.location = (-600, 250)
        links.new(top_scale_sock, top_w.inputs[0])
        link_from_input(links, input_node, 'Width', top_w.inputs[1])

        top_d = nodes.new('ShaderNodeMath')
        top_d.operation = 'MULTIPLY'
        top_d.location = (-600, 150)
        top_d.inputs[1].default_value = 0.85
        links.new(top_scale_sock, top_d.inputs[0])
        link_from_input(links, input_node, 'Width', top_d.inputs[1])

        top_thickness = nodes.new('ShaderNodeMath')
        top_thickness.operation = 'MULTIPLY'
        top_thickness.location = (-600, 50)
        top_thickness.inputs[1].default_value = 0.12
        links.new(top_scale_sock, top_thickness.inputs[0])
        link_from_input(links, input_node, 'Height', top_thickness.inputs[1])
        link_cube_size(
            links, tree, top,
            x_sock=top_w.outputs[0], y_sock=top_d.outputs[0], z_sock=top_thickness.outputs[0],
            location=(-500, 200),
        )

        top_pos = nodes.new('GeometryNodeTransform')
        top_pos.location = (-200, 200)
        top_pos.inputs['Translation'].default_value = (0, 0, 0.95)
        links.new(top.outputs['Mesh'], top_pos.inputs['Geometry'])

        # Legs — stubbier/shorter when cute
        leg_h = nodes.new('ShaderNodeMath')
        leg_h.operation = 'MULTIPLY'
        leg_h.location = (-800, -150)
        leg_h.inputs[1].default_value = 0.85
        links.new(leg_scale_sock, leg_h.inputs[0])
        link_from_input(links, input_node, 'Height', leg_h.inputs[1])

        leg_th = nodes.new('ShaderNodeMath')
        leg_th.operation = 'MULTIPLY'
        leg_th.location = (-800, -250)
        links.new(leg_scale_sock, leg_th.inputs[0])
        link_from_input(links, input_node, 'Leg Thickness', leg_th.inputs[1])

        join = nodes.new('GeometryNodeJoinGeometry')
        join.location = (0, 0)
        links.new(top_pos.outputs['Geometry'], join.inputs['Geometry'])

        leg_offsets = (
            (0.85, 0.85),
            (0.85, -0.85),
            (-0.85, 0.85),
            (-0.85, -0.85),
        )
        for idx, (ox, oy) in enumerate(leg_offsets):
            leg = nodes.new('GeometryNodeMeshCube')
            leg.location = (-400, -200 - idx * 120)

            leg_w = nodes.new('ShaderNodeMath')
            leg_w.operation = 'MULTIPLY'
            leg_w.location = (-600, -180 - idx * 120)
            links.new(leg_th.outputs[0], leg_w.inputs[0])
            leg_w.inputs[1].default_value = 1.0

            leg_d = nodes.new('ShaderNodeMath')
            leg_d.operation = 'MULTIPLY'
            leg_d.location = (-600, -220 - idx * 120)
            links.new(leg_th.outputs[0], leg_d.inputs[0])
            leg_d.inputs[1].default_value = 1.0

            link_cube_size(
                links, tree, leg,
                x_sock=leg_w.outputs[0], y_sock=leg_d.outputs[0], z_sock=leg_h.outputs[0],
                location=(-500, -200 - idx * 120),
            )

            spread_x = nodes.new('ShaderNodeMath')
            spread_x.operation = 'MULTIPLY'
            spread_x.location = (-800, -100 - idx * 120)
            spread_x.inputs[1].default_value = ox
            link_from_input(links, input_node, 'Width', spread_x.inputs[0])

            spread_y = nodes.new('ShaderNodeMath')
            spread_y.operation = 'MULTIPLY'
            spread_y.location = (-800, -130 - idx * 120)
            spread_y.inputs[1].default_value = oy
            link_from_input(links, input_node, 'Width', spread_y.inputs[0])

            leg_z = nodes.new('ShaderNodeMath')
            leg_z.operation = 'MULTIPLY'
            leg_z.location = (-800, -160 - idx * 120)
            leg_z.inputs[1].default_value = 0.5
            links.new(leg_h.outputs[0], leg_z.inputs[0])

            leg_pos = nodes.new('GeometryNodeTransform')
            leg_pos.location = (-200, -200 - idx * 120)
            links.new(leg.outputs['Mesh'], leg_pos.inputs['Geometry'])
            link_translation(
                links, tree, leg_pos,
                x_sock=spread_x.outputs[0], y_sock=spread_y.outputs[0], z_sock=leg_z.outputs[0],
                location=(-350, -200 - idx * 120),
            )

            links.new(leg_pos.outputs['Geometry'], join.inputs['Geometry'])

        links.new(join.outputs['Geometry'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
