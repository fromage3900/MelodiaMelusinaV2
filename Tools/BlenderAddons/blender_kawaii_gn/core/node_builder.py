"""Node builder utilities for Kawaii GN generators (Blender 4.2-5.1)."""
from .gn_framework import get_input_socket, get_output_socket


def safe_link(links, from_socket, to_socket):
    """Create a node link; return False instead of raising on Blender API errors."""
    try:
        links.new(from_socket, to_socket)
        return True
    except (RuntimeError, TypeError, ValueError):
        return False


def mesh_input(node, name: str):
    """Resolve mesh-primitive socket names changed in Blender 5.1."""
    if name in node.inputs:
        return node.inputs[name]
    if name == 'Height':
        if 'Depth' in node.inputs:
            return node.inputs['Depth']
    raise KeyError(f"Mesh primitive input not found: {name}")


def new_combine_xyz(tree, location=(0, 0), x=0.0, y=0.0, z=0.0):
    comb = tree.nodes.new('ShaderNodeCombineXYZ')
    comb.location = location
    comb.inputs['X'].default_value = x
    comb.inputs['Y'].default_value = y
    comb.inputs['Z'].default_value = z
    return comb


def link_to_vector_input(links, tree, vector_input, x_sock=None, y_sock=None, z_sock=None,
                         default_x=0.0, default_y=0.0, default_z=0.0, location=(0, 0), combine=None):
    """Link up to three float sockets into a VECTOR node input via Combine XYZ."""
    comb = combine or new_combine_xyz(
        tree, location, x=default_x, y=default_y, z=default_z,
    )
    if x_sock is not None:
        safe_link(links, x_sock, comb.inputs['X'])
    if y_sock is not None:
        safe_link(links, y_sock, comb.inputs['Y'])
    if z_sock is not None:
        safe_link(links, z_sock, comb.inputs['Z'])
    safe_link(links, comb.outputs['Vector'], vector_input)
    return comb


def link_cube_size(links, tree, cube_node, x_sock=None, y_sock=None, z_sock=None,
                   default_x=1.0, default_y=1.0, default_z=1.0, location=(0, 0), combine=None):
    return link_to_vector_input(
        links, tree, cube_node.inputs['Size'],
        x_sock=x_sock, y_sock=y_sock, z_sock=z_sock,
        default_x=default_x, default_y=default_y, default_z=default_z,
        location=location, combine=combine,
    )


def link_translation(links, tree, xf_node, x_sock=None, y_sock=None, z_sock=None,
                     default_x=0.0, default_y=0.0, default_z=0.0, location=(0, 0), combine=None):
    return link_to_vector_input(
        links, tree, xf_node.inputs['Translation'],
        x_sock=x_sock, y_sock=y_sock, z_sock=z_sock,
        default_x=default_x, default_y=default_y, default_z=default_z,
        location=location, combine=combine,
    )


def link_scale_z(links, tree, xf_node, z_sock, location=(0, 0), combine=None):
    return link_to_vector_input(
        links, tree, xf_node.inputs['Scale'],
        z_sock=z_sock, default_x=1.0, default_y=1.0, default_z=1.0,
        location=location, combine=combine,
    )


def link_rotation_x(links, tree, xf_node, x_sock, location=(0, 0)):
    """Drive X euler on a transform Rotation socket from a float socket."""
    comb = new_combine_xyz(tree, location)
    safe_link(links, x_sock, comb.inputs['X'])
    rot = tree.nodes.new('FunctionNodeRotateEuler')
    rot.location = (location[0] + 150, location[1])
    safe_link(links, comb.outputs['Vector'], rot.inputs['Rotate By'])
    safe_link(links, rot.outputs['Rotation'], xf_node.inputs['Rotation'])
    return rot


def create_mesh_torus(nodes, links, location, major_radius=0.8, minor_radius=0.3):
    """Build a torus mesh (Blender 5.1 removed GeometryNodeMeshTorus)."""
    circle = nodes.new('GeometryNodeCurvePrimitiveCircle')
    circle.location = (location[0] - 200, location[1])
    circle.inputs['Radius'].default_value = major_radius

    profile = nodes.new('GeometryNodeCurvePrimitiveCircle')
    profile.location = (location[0] - 200, location[1] - 150)
    profile.inputs['Radius'].default_value = minor_radius

    ctm = nodes.new('GeometryNodeCurveToMesh')
    ctm.location = location
    safe_link(links, circle.outputs['Curve'], ctm.inputs['Curve'])
    safe_link(links, profile.outputs['Curve'], ctm.inputs['Profile Curve'])
    return ctm, circle, profile


def create_mesh_capsule(nodes, location, radius=0.12, height=0.4):
    """Capsule substitute - Blender 5.1 removed GeometryNodeMeshCapsule."""
    cyl = nodes.new('GeometryNodeMeshCylinder')
    cyl.location = location
    cyl.inputs['Radius'].default_value = radius
    mesh_input(cyl, 'Height').default_value = height
    return cyl


def link_from_input(links, input_node, param_name, target_input):
    """Link a Group Input parameter to a target node input socket."""
    return safe_link(links, get_input_socket(input_node, param_name), target_input)


def kindchenschema_from_input(tree, links, input_node, cuteness_param='Roundness'):
    """Build GN math nodes for head/body scale from 0-1 cuteness (Kindchenschema)."""
    nodes = tree.nodes
    cuteness = get_input_socket(input_node, cuteness_param)

    head_mul = nodes.new('ShaderNodeMath')
    head_mul.operation = 'MULTIPLY'
    head_mul.inputs[1].default_value = 0.35
    links.new(cuteness, head_mul.inputs[0])

    head_add = nodes.new('ShaderNodeMath')
    head_add.operation = 'ADD'
    head_add.inputs[1].default_value = 1.0
    links.new(head_mul.outputs[0], head_add.inputs[0])

    body_mul = nodes.new('ShaderNodeMath')
    body_mul.operation = 'MULTIPLY'
    body_mul.inputs[1].default_value = 0.15
    links.new(cuteness, body_mul.inputs[0])

    body_sub = nodes.new('ShaderNodeMath')
    body_sub.operation = 'SUBTRACT'
    body_sub.inputs[0].default_value = 1.0
    links.new(body_mul.outputs[0], body_sub.inputs[1])

    return head_add.outputs[0], body_sub.outputs[0]


def join_geometry_input(join_node):
    """Blender 5.1 Join Geometry uses one multi-input Geometry socket."""
    if 'Geometry' in join_node.inputs:
        return join_node.inputs['Geometry']
    return join_node.inputs[0]


def new_node(tree, node_type, location=(0, 0), label=None):
    """Create a geometry node with optional label."""
    node = tree.nodes.new(node_type)
    node.location = location
    if label:
        node.label = label
    return node
