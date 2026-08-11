"""Advanced Kawaii Plushie Geometry Nodes Generators."""
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import link_from_input, kindchenschema_from_input, mesh_input, create_mesh_capsule


@register_generator
class KawaiiBearPlushGN(KawaiiGNBase):
    """Kawaii Bear Plushie with round body."""
    category = "plushies"
    generator_id = "kawaii_bear_plush_gn"
    generator_name = "Bear Plushie"
    description = "Round bear plushie with tiny ears and stubby limbs"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Body Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Head Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Ear Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Arm Length', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Leg Length', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Squishiness', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Body Size': socket.default_value = 1.0
            elif socket.name == 'Head Size': socket.default_value = 0.7
            elif socket.name == 'Ear Size': socket.default_value = 0.2
            elif socket.name == 'Arm Length': socket.default_value = 0.5
            elif socket.name == 'Leg Length': socket.default_value = 0.4
            elif socket.name == 'Squishiness': socket.default_value = 0.6
            elif socket.name == 'Roundness': socket.default_value = 0.8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        head_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Body (round sphere)
        body = nodes.new('GeometryNodeMeshUVSphere')
        body.location = (-800, 0)
        body.inputs['Segments'].default_value = 32
        body.inputs['Rings'].default_value = 16

        body_ks = nodes.new('ShaderNodeMath')
        body_ks.operation = 'MULTIPLY'
        body_ks.location = (-900, -50)
        links.new(body_scale_sock, body_ks.inputs[0])
        links.new(get_input_socket(input_node, 'Body Size'), body_ks.inputs[1])
        links.new(body_ks.outputs[0], body.inputs['Radius'])
        
        # Head (larger sphere for chibi)
        head = nodes.new('GeometryNodeMeshUVSphere')
        head.location = (-800, 200)
        head.inputs['Segments'].default_value = 32

        head_ks = nodes.new('ShaderNodeMath')
        head_ks.operation = 'MULTIPLY'
        head_ks.location = (-900, 150)
        links.new(head_scale_sock, head_ks.inputs[0])
        links.new(get_input_socket(input_node, 'Head Size'), head_ks.inputs[1])
        links.new(head_ks.outputs[0], head.inputs['Radius'])
        
        # Position head on top
        head_pos = nodes.new('GeometryNodeTransform')
        head_pos.location = (-600, 200)
        head_pos.inputs['Translation'].default_value = (0, 0, 1.0)
        links.new(head.outputs['Mesh'], head_pos.inputs['Geometry'])
        
        # Left ear
        ear_l = nodes.new('GeometryNodeMeshUVSphere')
        ear_l.location = (-800, 400)
        ear_l.inputs['Radius'].default_value = 0.15
        links.new(get_input_socket(input_node, 'Ear Size'), ear_l.inputs['Radius'])
        
        ear_l_pos = nodes.new('GeometryNodeTransform')
        ear_l_pos.location = (-600, 400)
        ear_l_pos.inputs['Translation'].default_value = (-0.35, 0, 1.3)
        links.new(ear_l.outputs['Mesh'], ear_l_pos.inputs['Geometry'])
        
        # Right ear
        ear_r = nodes.new('GeometryNodeMeshUVSphere')
        ear_r.location = (-800, 600)
        ear_r.inputs['Radius'].default_value = 0.15
        links.new(get_input_socket(input_node, 'Ear Size'), ear_r.inputs['Radius'])
        
        ear_r_pos = nodes.new('GeometryNodeTransform')
        ear_r_pos.location = (-600, 600)
        ear_r_pos.inputs['Translation'].default_value = (0.35, 0, 1.3)
        links.new(ear_r.outputs['Mesh'], ear_r_pos.inputs['Geometry'])
        
        # Left arm
        arm_l = create_mesh_capsule(nodes, (-800, 800), radius=0.12, height=0.4)
        links.new(get_input_socket(input_node, 'Arm Length'), mesh_input(arm_l, 'Height'))
        
        arm_l_pos = nodes.new('GeometryNodeTransform')
        arm_l_pos.location = (-600, 800)
        arm_l_pos.inputs['Translation'].default_value = (-0.65, 0, 0.2)
        arm_l_pos.inputs['Rotation'].default_value = (0, 0, 0.4)
        links.new(arm_l.outputs['Mesh'], arm_l_pos.inputs['Geometry'])
        
        # Right arm
        arm_r = create_mesh_capsule(nodes, (-800, 1000), radius=0.12, height=0.4)
        links.new(get_input_socket(input_node, 'Arm Length'), mesh_input(arm_r, 'Height'))
        
        arm_r_pos = nodes.new('GeometryNodeTransform')
        arm_r_pos.location = (-600, 1000)
        arm_r_pos.inputs['Translation'].default_value = (0.65, 0, 0.2)
        arm_r_pos.inputs['Rotation'].default_value = (0, 0, -0.4)
        links.new(arm_r.outputs['Mesh'], arm_r_pos.inputs['Geometry'])
        
        # Join all parts progressively
        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-400, 100)
        links.new(body.outputs['Mesh'], j1.inputs['Geometry'])
        links.new(head_pos.outputs['Geometry'], j1.inputs['Geometry'])
        
        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (-400, 300)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(ear_l_pos.outputs['Geometry'], j2.inputs['Geometry'])
        
        j3 = nodes.new('GeometryNodeJoinGeometry')
        j3.location = (-400, 500)
        links.new(j2.outputs['Geometry'], j3.inputs['Geometry'])
        links.new(ear_r_pos.outputs['Geometry'], j3.inputs['Geometry'])
        
        j4 = nodes.new('GeometryNodeJoinGeometry')
        j4.location = (-200, 700)
        links.new(j3.outputs['Geometry'], j4.inputs['Geometry'])
        links.new(arm_l_pos.outputs['Geometry'], j4.inputs['Geometry'])
        
        j5 = nodes.new('GeometryNodeJoinGeometry')
        j5.location = (0, 0)
        links.new(j4.outputs['Geometry'], j5.inputs['Geometry'])
        links.new(arm_r_pos.outputs['Geometry'], j5.inputs['Geometry'])
        
        # Subdivision for roundness
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (200, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j5.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


@register_generator
class KawaiiPenguinPlushGN(KawaiiGNBase):
    """Kawaii Penguin Plushie."""
    category = "plushies"
    generator_id = "kawaii_penguin_plush_gn"
    generator_name = "Penguin Plushie"
    description = "Chubby penguin with tiny flippers"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Body Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Belly Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Beak Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Flipper Size', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Body Size': socket.default_value = 1.0
            elif socket.name == 'Belly Size': socket.default_value = 0.6
            elif socket.name == 'Beak Size': socket.default_value = 0.15
            elif socket.name == 'Flipper Size': socket.default_value = 0.3
            elif socket.name == 'Roundness': socket.default_value = 0.8
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links

        head_scale_sock, body_scale_sock = kindchenschema_from_input(
            tree, links, input_node, 'Roundness',
        )
        
        # Body (elongated sphere)
        body = nodes.new('GeometryNodeMeshUVSphere')
        body.location = (-600, 0)
        body.inputs['Segments'].default_value = 32

        body_ks = nodes.new('ShaderNodeMath')
        body_ks.operation = 'MULTIPLY'
        body_ks.location = (-700, -50)
        links.new(body_scale_sock, body_ks.inputs[0])
        links.new(get_input_socket(input_node, 'Body Size'), body_ks.inputs[1])
        links.new(body_ks.outputs[0], body.inputs['Radius'])
        
        body_scale = nodes.new('GeometryNodeTransform')
        body_scale.location = (-400, 0)
        body_scale.inputs['Scale'].default_value = (1.0, 1.0, 1.4)
        links.new(body.outputs['Mesh'], body_scale.inputs['Geometry'])
        
        # Belly (white sphere in front)
        belly = nodes.new('GeometryNodeMeshUVSphere')
        belly.location = (-600, 200)
        belly.inputs['Segments'].default_value = 32

        belly_ks = nodes.new('ShaderNodeMath')
        belly_ks.operation = 'MULTIPLY'
        belly_ks.location = (-700, 150)
        links.new(head_scale_sock, belly_ks.inputs[0])
        links.new(get_input_socket(input_node, 'Belly Size'), belly_ks.inputs[1])
        links.new(belly_ks.outputs[0], belly.inputs['Radius'])
        
        belly_pos = nodes.new('GeometryNodeTransform')
        belly_pos.location = (-400, 200)
        belly_pos.inputs['Translation'].default_value = (0, 0.35, -0.1)
        links.new(belly.outputs['Mesh'], belly_pos.inputs['Geometry'])
        
        # Beak (cone)
        beak = nodes.new('GeometryNodeMeshCone')
        beak.location = (-600, 400)
        beak.inputs['Radius'].default_value = 0.08
        beak.inputs['Depth'].default_value = 0.2
        links.new(get_input_socket(input_node, 'Beak Size'), beak.inputs['Depth'])
        
        beak_pos = nodes.new('GeometryNodeTransform')
        beak_pos.location = (-400, 400)
        beak_pos.inputs['Translation'].default_value = (0, 0.5, 0.35)
        beak_pos.inputs['Rotation'].default_value = (1.57, 0, 0)
        links.new(beak.outputs['Mesh'], beak_pos.inputs['Geometry'])
        
        # Left flipper
        flip_l = create_mesh_capsule(nodes, (-600, 600), radius=0.08, height=0.4)
        links.new(get_input_socket(input_node, 'Flipper Size'), mesh_input(flip_l, 'Height'))
        
        flip_l_pos = nodes.new('GeometryNodeTransform')
        flip_l_pos.location = (-400, 600)
        flip_l_pos.inputs['Translation'].default_value = (-0.55, 0, 0.1)
        flip_l_pos.inputs['Rotation'].default_value = (0, 0, 0.3)
        links.new(flip_l.outputs['Mesh'], flip_l_pos.inputs['Geometry'])
        
        # Right flipper
        flip_r = create_mesh_capsule(nodes, (-600, 800), radius=0.08, height=0.4)
        links.new(get_input_socket(input_node, 'Flipper Size'), mesh_input(flip_r, 'Height'))
        
        flip_r_pos = nodes.new('GeometryNodeTransform')
        flip_r_pos.location = (-400, 800)
        flip_r_pos.inputs['Translation'].default_value = (0.55, 0, 0.1)
        flip_r_pos.inputs['Rotation'].default_value = (0, 0, -0.3)
        links.new(flip_r.outputs['Mesh'], flip_r_pos.inputs['Geometry'])
        
        # Join all
        j1 = nodes.new('GeometryNodeJoinGeometry')
        j1.location = (-200, 100)
        links.new(body_scale.outputs['Geometry'], j1.inputs['Geometry'])
        links.new(belly_pos.outputs['Geometry'], j1.inputs['Geometry'])
        
        j2 = nodes.new('GeometryNodeJoinGeometry')
        j2.location = (0, 300)
        links.new(j1.outputs['Geometry'], j2.inputs['Geometry'])
        links.new(beak_pos.outputs['Geometry'], j2.inputs['Geometry'])
        
        j3 = nodes.new('GeometryNodeJoinGeometry')
        j3.location = (200, 500)
        links.new(j2.outputs['Geometry'], j3.inputs['Geometry'])
        links.new(flip_l_pos.outputs['Geometry'], j3.inputs['Geometry'])
        
        j4 = nodes.new('GeometryNodeJoinGeometry')
        j4.location = (400, 0)
        links.new(j3.outputs['Geometry'], j4.inputs['Geometry'])
        links.new(flip_r_pos.outputs['Geometry'], j4.inputs['Geometry'])
        
        subdiv = nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.location = (600, 0)
        subdiv.inputs['Level'].default_value = 2
        links.new(j4.outputs['Geometry'], subdiv.inputs['Mesh'])
        
        links.new(subdiv.outputs['Mesh'], output_node.inputs['Geometry'])


def register(): pass
def unregister(): pass
