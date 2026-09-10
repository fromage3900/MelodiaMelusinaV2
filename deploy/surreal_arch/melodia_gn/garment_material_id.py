"""Garment material ID — assigns integer material IDs by region (fabric, trim, hem, neckline).

Infinity Nikki style material assignment via Geometry Nodes.
Blender 5.2 compatible.
"""

from __future__ import annotations

import bpy  # noqa: F401

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param,
    register_builder, sock,
)


def build_garment_material_id(group_name='MEL_garment_material_id'):
    """Assign integer material IDs to garment faces by region.

    ID 1 = Fabric body (default)
    ID 2 = Trim border (near mesh boundary)
    ID 3 = Hem (bottom Y% of bounding box)
    ID 4 = Neckline/Top (top Y% of bounding box)
    """
    tree, gin, gout = new_geometry_tree(group_name)

    # Parameters
    add_float_param(tree, 'Border Width', 0.05, 0.001, 1.0)
    add_float_param(tree, 'Hem Height', 0.15, 0.0, 1.0)
    add_float_param(tree, 'Neck Height', 0.1, 0.0, 1.0)

    bx, by = 0, 0

    # === Face position ===
    pos = safe_node(tree, 'GeometryNodeInputPosition', (bx, by))
    sep = safe_node(tree, 'ShaderNodeSeparateXYZ', (bx + 200, by))
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])

    # === Bounding box ===
    bbox = safe_node(tree, 'GeometryNodeBoundBox', (bx, by - 200))
    link_sockets(tree, gin.outputs['Geometry'], bbox.inputs['Geometry'])
    sep_min = safe_node(tree, 'ShaderNodeSeparateXYZ', (bx + 200, by - 150))
    link_sockets(tree, bbox.outputs['Min'], sep_min.inputs['Vector'])
    sep_max = safe_node(tree, 'ShaderNodeSeparateXYZ', (bx + 200, by - 250))
    link_sockets(tree, bbox.outputs['Max'], sep_max.inputs['Vector'])

    # bbox_height = max_y - min_y
    bbox_height = safe_node(tree, 'ShaderNodeMath', (bx + 400, by - 200))
    bbox_height.operation = 'SUBTRACT'
    link_sockets(tree, sep_max.outputs['Y'], bbox_height.inputs[0])
    link_sockets(tree, sep_min.outputs['Y'], bbox_height.inputs[1])

    # hem_threshold = min_y + bbox_height * Hem Height
    hem_mul = safe_node(tree, 'ShaderNodeMath', (bx + 600, by - 150))
    hem_mul.operation = 'MULTIPLY'
    link_sockets(tree, bbox_height.outputs[0], hem_mul.inputs[0])
    link_sockets(tree, gin.outputs['Hem Height'], hem_mul.inputs[1])
    hem_thresh = safe_node(tree, 'ShaderNodeMath', (bx + 800, by - 150))
    hem_thresh.operation = 'ADD'
    link_sockets(tree, sep_min.outputs['Y'], hem_thresh.inputs[0])
    link_sockets(tree, hem_mul.outputs[0], hem_thresh.inputs[1])

    # neck_threshold = max_y - bbox_height * Neck Height
    neck_mul = safe_node(tree, 'ShaderNodeMath', (bx + 600, by - 300))
    neck_mul.operation = 'MULTIPLY'
    link_sockets(tree, bbox_height.outputs[0], neck_mul.inputs[0])
    link_sockets(tree, gin.outputs['Neck Height'], neck_mul.inputs[1])
    neck_thresh = safe_node(tree, 'ShaderNodeMath', (bx + 800, by - 300))
    neck_thresh.operation = 'SUBTRACT'
    link_sockets(tree, sep_max.outputs['Y'], neck_thresh.inputs[0])
    link_sockets(tree, neck_mul.outputs[0], neck_thresh.inputs[1])

    # === Compare face Y to thresholds ===
    # is_hem = face_y < hem_threshold
    cmp_hem = safe_node(tree, 'FunctionNodeCompare', (bx + 1000, by - 150))
    cmp_hem.data_type = 'FLOAT'
    cmp_hem.operation = 'LESS_THAN'
    link_sockets(tree, sep.outputs['Y'], cmp_hem.inputs['A'])
    link_sockets(tree, hem_thresh.outputs[0], cmp_hem.inputs['B'])

    # is_neck = face_y > neck_threshold
    cmp_neck = safe_node(tree, 'FunctionNodeCompare', (bx + 1000, by - 300))
    cmp_neck.data_type = 'FLOAT'
    cmp_neck.operation = 'GREATER_THAN'
    link_sockets(tree, sep.outputs['Y'], cmp_neck.inputs['A'])
    link_sockets(tree, neck_thresh.outputs[0], cmp_neck.inputs['B'])

    # === Border detection ===
    # 1. Identify boundary edges (edges with only 1 adjacent face)
    edge_neighbors = safe_node(tree, 'GeometryNodeInputMeshEdgeNeighbors', (bx, by + 200))
    # GeometryNodeInputMeshEdgeNeighbors is a pure field node - operates on current geometry

    # Boundary: face count == 1
    cmp_boundary = safe_node(tree, 'FunctionNodeCompare', (bx + 250, by + 200))
    cmp_boundary.data_type = 'INT'
    cmp_boundary.operation = 'EQUAL'
    face_count_sock = sock(edge_neighbors, 'Face Count', 'Faces', outputs=True)
    if face_count_sock is None:
        face_count_sock = edge_neighbors.outputs[2]
    link_sockets(tree, face_count_sock, cmp_boundary.inputs['A'])
    cmp_boundary.inputs['B'].default_value = 1

    # 2. Separate boundary edges from the mesh
    sep_boundary = safe_node(tree, 'GeometryNodeSeparateGeometry', (bx + 500, by + 200))
    sep_boundary.domain = 'EDGE'
    link_sockets(tree, gin.outputs['Geometry'], sep_boundary.inputs['Geometry'])
    link_sockets(tree, cmp_boundary.outputs['Result'], sep_boundary.inputs['Selection'])

    # 3. Proximity: distance from face centers to boundary edges
    proximity = safe_node(tree, 'GeometryNodeProximity', (bx + 750, by + 150))
    try:
        proximity.target_element = 'EDGES'
    except Exception:
        try:
            proximity.target_target = 'EDGES'
        except Exception:
            pass
    link_sockets(tree, gin.outputs['Geometry'], proximity.inputs['Geometry'])
    link_sockets(tree, sep_boundary.outputs['Selection'], proximity.inputs['Target'])

    # 4. Compare distance < Border Width
    cmp_border = safe_node(tree, 'FunctionNodeCompare', (bx + 1000, by + 150))
    cmp_border.data_type = 'FLOAT'
    cmp_border.operation = 'LESS_THAN'
    link_sockets(tree, proximity.outputs['Distance'], cmp_border.inputs['A'])
    link_sockets(tree, gin.outputs['Border Width'], cmp_border.inputs['B'])

    # === Combine material IDs ===
    # Start with fabric (1), then apply hem (3), neck (4), border (2)
    # Border has highest priority (overrides hem/neck when they overlap)

    # Mix for hem: if is_hem, ID=3, else ID=1
    mix_hem = safe_node(tree, 'ShaderNodeMix', (bx + 1300, by))
    mix_hem.data_type = 'FLOAT'
    mix_hem.inputs['A'].default_value = 1.0
    mix_hem.inputs['B'].default_value = 3.0
    link_sockets(tree, cmp_hem.outputs['Result'], mix_hem.inputs['Factor'])

    # Mix for neck: if is_neck, ID=4, else previous
    mix_neck = safe_node(tree, 'ShaderNodeMix', (bx + 1500, by - 50))
    mix_neck.data_type = 'FLOAT'
    link_sockets(tree, mix_hem.outputs[0], mix_neck.inputs['A'])
    mix_neck.inputs['B'].default_value = 4.0
    link_sockets(tree, cmp_neck.outputs['Result'], mix_neck.inputs['Factor'])

    # Mix for border: if is_border, ID=2, else previous
    mix_border = safe_node(tree, 'ShaderNodeMix', (bx + 1700, by - 100))
    mix_border.data_type = 'FLOAT'
    link_sockets(tree, mix_neck.outputs[0], mix_border.inputs['A'])
    mix_border.inputs['B'].default_value = 2.0
    link_sockets(tree, cmp_border.outputs['Result'], mix_border.inputs['Factor'])

    # Convert float mix result to INT for storage
    floor_id = safe_node(tree, 'ShaderNodeMath', (bx + 1850, by))
    floor_id.operation = 'FLOOR'
    link_sockets(tree, mix_border.outputs[0], floor_id.inputs[0])

    # === Store material_id attribute ===
    store = safe_node(tree, 'GeometryNodeStoreNamedAttribute', (bx + 1900, by))
    store.data_type = 'INT'
    store.domain = 'FACE'
    store.inputs['Name'].default_value = 'material_id'
    link_sockets(tree, gin.outputs['Geometry'], store.inputs['Geometry'])
    link_sockets(tree, floor_id.outputs[0], store.inputs['Value'])

    # === Output ===
    link_sockets(tree, store.outputs['Geometry'], gout.inputs['Geometry'])

    # Color nodes for clarity
    color_node(pos, 'input')
    color_node(bbox, 'input')
    color_node(proximity, 'attribute')
    color_node(store, 'attribute')
    color_node(mix_hem, 'material')
    color_node(mix_neck, 'material')
    color_node(mix_border, 'material')

    return label_tree(tree, group_name, [
        {'title': 'Inputs', 'nodes': ('Group Input',), 'role': 'input'},
        {'title': 'Position + Bounding Box', 'nodes': ('position', 'bounding box', 'separate'), 'role': 'input'},
        {'title': 'Region Detection', 'nodes': ('compare', 'proximity', 'boundary'), 'role': 'attribute'},
        {'title': 'Material ID Mix', 'nodes': ('mix',), 'role': 'material'},
        {'title': 'Output', 'nodes': ('Group Output',), 'role': 'output'},
    ])


register_builder('MEL_garment_material_id', build_garment_material_id,
                 'Garment Material ID',
                 'Assigns integer material IDs by region (fabric, trim, hem, neckline)',
                 'Garment')
