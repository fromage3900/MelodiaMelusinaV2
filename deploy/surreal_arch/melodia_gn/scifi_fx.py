"""MEL scifi effect passes — absorbed from the monolith (P2 family 2).

7 builders (+ enum aliases HOLOGRAM->greeble, VENT_GRILLE->panel_lines).
Modifier-style: Geometry IN -> decorated OUT. Params as values at build
time (monolith rebuild-on-change semantics). Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, register_builder,
)

SLUGS = {
    "GREEBLE": "greeble",
    "CIRCUIT": "circuit",
    "NEON_TRIM": "neon_trim",
    "PANEL_LINES": "panel_lines",
    "ANTENNA": "antenna",
    "DAMAGE": "damage",
    "HEX_ARMOUR": "hex_armour",
    "HOLOGRAM": "greeble",
    "VENT_GRILLE": "panel_lines",
}

AESTHETIC_ENUM_MAP_UNUSED = None
SCIFI_ENUM_MAP = {
    "GREEBLE": "MEL_scifi_" + SLUGS["GREEBLE"],
    "CIRCUIT": "MEL_scifi_" + SLUGS["CIRCUIT"],
    "NEON_TRIM": "MEL_scifi_" + SLUGS["NEON_TRIM"],
    "PANEL_LINES": "MEL_scifi_" + SLUGS["PANEL_LINES"],
    "ANTENNA": "MEL_scifi_" + SLUGS["ANTENNA"],
    "DAMAGE": "MEL_scifi_" + SLUGS["DAMAGE"],
    "HEX_ARMOUR": "MEL_scifi_" + SLUGS["HEX_ARMOUR"],
    "HOLOGRAM": "MEL_scifi_" + SLUGS["HOLOGRAM"],
    "VENT_GRILLE": "MEL_scifi_" + SLUGS["VENT_GRILLE"],
}


# ---- helpers (shared port set) ----

def _get_input_geom(tree):
    for n in tree.nodes:
        if n.type == 'GROUP_INPUT':
            for out in n.outputs:
                if out.type == 'GEOMETRY':
                    return out
    return None


def _link(tree, srcc, dst):
    if srcc is not None and dst is not None:
        try:
            tree.links.new(srcc, dst)
        except Exception:
            pass


def _safe_node(tree, bl_idname, loc=(0, 0)):
    try:
        n = tree.nodes.new(bl_idname)
        n.location = loc
        return n
    except Exception:
        return None


def _node(tree, bl_idname, loc=(0, 0), **kwargs):
    return _safe_node(tree, bl_idname, loc)


DEFAULT_PARAMS = {
    "density": 2.0, "depth": 0.08, "edge_angle": 30.0,
    "layers": 2, "panel_scale": 0.8, "randomness": 0.6,
    "tube_radius": 0.025, "seed": 42,
}


def _add_scifi_params(tree):
    add_float_param(tree, "Density", 2.0, 0.1, 20.0)
    add_float_param(tree, "Depth", 0.08, 0.001, 1.0)
    add_float_param(tree, "Edge Angle", 30.0, 5.0, 80.0)
    add_int_param(tree, "Layers", 2, 1, 5)
    add_float_param(tree, "Panel Scale", 0.8, 0.05, 3.0)
    add_float_param(tree, "Randomness", 0.6, 0.0, 1.0)
    add_float_param(tree, "Tube Radius", 0.025, 0.005, 0.3)
    add_int_param(tree, "Seed", 42, 0, 9999)


def build_scifi_greeble_group(group_name="MEL_scifi_greeble"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Greeble panel generator: distribute points on faces, instance
        rectangular boxes of varying heights for classic sci-fi hull detail.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        # Subdivide for denser face distribution
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x, 200))
        subd.inputs['Level'].default_value = min(2, P["layers"])
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        color_node(subd, "optimize")

        # Distribute points on faces
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (x+350, 200))
        if pts:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value  = 0.35 / max(0.1, P["density"])
            pts.inputs['Density Max'].default_value   = P["density"] * 3.0
            pts.inputs['Seed'].default_value          = P["seed"]
            _link(tree, subd.outputs['Mesh'], pts.inputs['Mesh'])
            color_node(pts, "input")

        # Panel box
        panel = _node(tree, 'GeometryNodeMeshCube', (x+350, -250))
        panel.inputs['Size'].default_value = (0.3 * P["panel_scale"], 0.12 * P["panel_scale"], P["depth"] * 2.0)
        color_node(panel, "tower")

        # Random scale per instance
        rnd_val = _safe_node(tree, 'ShaderNodeTexNoise', (x+350, -550))
        if rnd_val:
            rnd_val.inputs['Scale'].default_value = 8.0
            rnd_val.inputs['Detail'].default_value = 2.0
            color_node(rnd_val, "noise")

        pos_p = _node(tree, 'GeometryNodeInputPosition', (x+100, -550))
        if rnd_val and pos_p:
            _link(tree, pos_p.outputs['Position'], rnd_val.inputs['Vector'])

        # Scale the panel randomly (0.4 -> 1.0)
        scale_map = _node(tree, 'ShaderNodeMapRange', (x+600, -550))
        scale_map.inputs['From Min'].default_value = 0.0
        scale_map.inputs['From Max'].default_value = 1.0
        scale_map.inputs['To Min'].default_value   = 0.4
        scale_map.inputs['To Max'].default_value   = 1.0 + P["randomness"]
        if rnd_val:
            _link(tree, rnd_val.outputs['Fac'], scale_map.inputs['Value'])

        # Instance on points
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (x+750, 200))
        if inst:
            _link(tree, pts.outputs['Points'],   inst.inputs['Points'])
            _link(tree, panel.outputs['Mesh'],   inst.inputs['Instance'])
            if pts:
                _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            _link(tree, scale_map.outputs['Result'], inst.inputs['Scale'])
            inst.inputs['Scale'].default_value = (1, 1, 1)
            color_node(inst, "ornament")

        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (x+1050, 200))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])

        # Join original + panels
        join = _node(tree, 'GeometryNodeJoinGeometry', (x+1350, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        if real:
            _link(tree, real.outputs['Geometry'], join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_greeble")
    return tree, gin, gout

register_builder(
    "MEL_scifi_greeble", build_scifi_greeble_group,
    "Greeble", "Sci-fi effect pass (absorbed from monolith build_scifi_greeble).",
    category="effects", role="modifier")


def build_scifi_circuit_group(group_name="MEL_scifi_circuit"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Circuit board surface: Voronoi-driven raised pads + noise trace lines
        distributed across the mesh surface.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        # Subdivide the base mesh for fine resolution
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x, 100))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])

        # Voronoi texture for pad placement
        pos_c = _node(tree, 'GeometryNodeInputPosition', (x+200, -300))
        vor_c = _node(tree, 'ShaderNodeTexVoronoi', (x+400, -300))
        vor_c.voronoi_dimensions = '3D'
        vor_c.feature = 'F1'
        vor_c.inputs['Scale'].default_value      = P["density"] * 2.5
        vor_c.inputs['Randomness'].default_value = P["randomness"]
        _link(tree, pos_c.outputs['Position'], vor_c.inputs['Vector'])
        color_node(vor_c, "noise")

        # Threshold -> only extrude near cell centres (pads)
        thresh = _node(tree, 'ShaderNodeMath', (x+650, -300))
        thresh.operation = 'LESS_THAN'
        thresh.inputs[1].default_value = 0.25 * (1.0 + P["randomness"] * 0.5)
        _link(tree, vor_c.outputs['Distance'], thresh.inputs[0])

        # Extrude selected faces as component pads
        ext_c = _safe_node(tree, 'GeometryNodeExtrudeMesh', (x+450, 100))
        if ext_c:
            ext_c.mode = 'FACES'
            ext_c.inputs['Individual'].default_value = True
            ext_c.inputs['Offset Scale'].default_value = P["depth"] * 0.5
            _link(tree, subd.outputs['Mesh'], ext_c.inputs['Mesh'])
            _link(tree, thresh.outputs['Value'], ext_c.inputs['Selection'])
            color_node(ext_c, "deform")

        # Second noise for trace lines
        noise_tr = _node(tree, 'ShaderNodeTexNoise', (x+400, -700))
        noise_tr.inputs['Scale'].default_value     = P["density"] * 4.0
        noise_tr.inputs['Detail'].default_value    = 3.0
        noise_tr.inputs['Roughness'].default_value = 0.3
        _link(tree, pos_c.outputs['Position'], noise_tr.inputs['Vector'])

        mul_tr = _node(tree, 'ShaderNodeVectorMath', (x+650, -700))
        mul_tr.operation = 'MULTIPLY'
        mul_tr.inputs[1].default_value = (P["depth"] * 0.3,) * 3
        _link(tree, noise_tr.outputs['Color'], mul_tr.inputs[0])

        set_tr = _node(tree, 'GeometryNodeSetPosition', (x+900, 100))
        _link(tree, (ext_c.outputs['Mesh'] if ext_c else subd.outputs['Mesh']),
              set_tr.inputs['Geometry'])
        _link(tree, mul_tr.outputs['Vector'], set_tr.inputs['Offset'])
        color_node(set_tr, "deform")

        join_c = _node(tree, 'GeometryNodeJoinGeometry', (x+1200, 0))
        if in_geom:
            _link(tree, in_geom, join_c.inputs['Geometry'])
        _link(tree, set_tr.outputs['Geometry'], join_c.inputs['Geometry'])
        color_node(join_c, "output")
        return join_c.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_circuit")
    return tree, gin, gout

register_builder(
    "MEL_scifi_circuit", build_scifi_circuit_group,
    "Circuit", "Sci-fi effect pass (absorbed from monolith build_scifi_circuit).",
    category="effects", role="modifier")


def build_scifi_neon_trim_group(group_name="MEL_scifi_neon_trim"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Neon trim: find sharp edges -> convert to curves -> sweep a circular
        profile to create glowing tube outlines.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        # Edge angle node
        edge_ang = _safe_node(tree, 'GeometryNodeInputMeshEdgeAngle', (x, -200))

        # Select edges sharper than threshold
        ang_thresh = _node(tree, 'ShaderNodeMath', (x+250, -200))
        ang_thresh.operation = 'GREATER_THAN'
        ang_thresh.inputs[1].default_value = math.radians(P["edge_angle"])
        if edge_ang:
            _link(tree, edge_ang.outputs['Unsigned Angle'], ang_thresh.inputs[0])

        # Convert mesh to curve on selected edges
        m2c = _safe_node(tree, 'GeometryNodeMeshToCurve', (x+250, 100))
        if m2c and in_geom:
            _link(tree, in_geom, m2c.inputs['Mesh'])
            if edge_ang:
                _link(tree, ang_thresh.outputs['Value'], m2c.inputs['Selection'])
            color_node(m2c, "tracery")

        # Circular sweep profile
        prof = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+500, -300))
        prof.mode = 'RADIUS'
        prof.inputs['Radius'].default_value     = P["tube_radius"]
        prof.inputs['Resolution'].default_value = 8
        color_node(prof, "ornament")

        # Curve to mesh
        c2m = _node(tree, 'GeometryNodeCurveToMesh', (x+750, 100))
        if m2c:
            _link(tree, m2c.outputs['Curve'],   c2m.inputs['Curve'])
        _link(tree, prof.outputs['Curve'], c2m.inputs['Profile Curve'])
        c2m.inputs['Fill Caps'].default_value = True
        color_node(c2m, "ornament")

        join_n = _node(tree, 'GeometryNodeJoinGeometry', (x+1050, 0))
        if in_geom:
            _link(tree, in_geom, join_n.inputs['Geometry'])
        _link(tree, c2m.outputs['Mesh'], join_n.inputs['Geometry'])
        color_node(join_n, "output")
        return join_n.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_neon_trim")
    return tree, gin, gout

register_builder(
    "MEL_scifi_neon_trim", build_scifi_neon_trim_group,
    "Neon Trim", "Sci-fi effect pass (absorbed from monolith build_scifi_neon_trim).",
    category="effects", role="modifier")


def build_scifi_panel_lines_group(group_name="MEL_scifi_panel_lines"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Panel lines: engraved grid lines via Voronoi cell boundary detection
        + Wireframe on selected edges.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x, 100))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])

        pos_pl = _node(tree, 'GeometryNodeInputPosition', (x+200, -300))
        vor_pl = _node(tree, 'ShaderNodeTexVoronoi', (x+400, -300))
        vor_pl.voronoi_dimensions = '3D'
        vor_pl.feature = 'SMOOTH_F1'
        vor_pl.inputs['Scale'].default_value      = P["density"] * 1.5
        vor_pl.inputs['Randomness'].default_value = P["randomness"] * 0.4
        _link(tree, pos_pl.outputs['Position'], vor_pl.inputs['Vector'])

        # Detect cell boundary (where distance is near its edges)
        edge_det = _node(tree, 'ShaderNodeMath', (x+650, -300))
        edge_det.operation = 'LESS_THAN'
        edge_det.inputs[1].default_value = 0.08
        _link(tree, vor_pl.outputs['Distance'], edge_det.inputs[0])

        # Inward displacement along normals for engraved look
        nrm_pl = _node(tree, 'GeometryNodeInputNormal', (x+400, -600))
        mul_pl = _node(tree, 'ShaderNodeVectorMath', (x+650, -600))
        mul_pl.operation = 'MULTIPLY'
        mul_pl.inputs[1].default_value = (-P["depth"] * 0.4,) * 3
        _link(tree, nrm_pl.outputs['Normal'], mul_pl.inputs[0])

        # Combine boolean mask into float for multiply
        mul_mask = _node(tree, 'ShaderNodeVectorMath', (x+900, -400))
        mul_mask.operation = 'SCALE'
        _link(tree, mul_pl.outputs['Vector'],    mul_mask.inputs[0])
        _link(tree, edge_det.outputs['Value'],   mul_mask.inputs['Scale'])

        set_pl = _node(tree, 'GeometryNodeSetPosition', (x+450, 100))
        _link(tree, subd.outputs['Mesh'],        set_pl.inputs['Geometry'])
        _link(tree, mul_mask.outputs['Vector'],  set_pl.inputs['Offset'])
        color_node(set_pl, "deform")

        join_pl = _node(tree, 'GeometryNodeJoinGeometry', (x+1200, 0))
        if in_geom:
            _link(tree, in_geom, join_pl.inputs['Geometry'])
        _link(tree, set_pl.outputs['Geometry'], join_pl.inputs['Geometry'])
        color_node(join_pl, "output")
        return join_pl.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_panel_lines")
    return tree, gin, gout

register_builder(
    "MEL_scifi_panel_lines", build_scifi_panel_lines_group,
    "Panel Lines", "Sci-fi effect pass (absorbed from monolith build_scifi_panel_lines).",
    category="effects", role="modifier")


def build_scifi_antenna_group(group_name="MEL_scifi_antenna"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Antenna array: distribute points only on upward-facing surfaces,
        instance tall thin cylinders with dish caps.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        # Filter selection: only upward normals (dot with +Z > threshold)
        nrm_a = _node(tree, 'GeometryNodeInputNormal', (x, -200))
        sep_a = _node(tree, 'ShaderNodeSeparateXYZ', (x+200, -200))
        _link(tree, nrm_a.outputs['Normal'], sep_a.inputs['Vector'])
        cmp_a = _node(tree, 'ShaderNodeMath', (x+400, -200))
        cmp_a.operation = 'GREATER_THAN'
        cmp_a.inputs[1].default_value = 0.5
        _link(tree, sep_a.outputs['Z'], cmp_a.inputs[0])

        pts_a = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (x+300, 100))
        if pts_a and in_geom:
            pts_a.distribute_method = 'POISSON'
            pts_a.inputs['Distance Min'].default_value  = 0.6 / max(0.1, P["density"])
            pts_a.inputs['Density Max'].default_value   = P["density"]
            pts_a.inputs['Seed'].default_value          = P["seed"] + 55
            _link(tree, in_geom, pts_a.inputs['Mesh'])
            _link(tree, cmp_a.outputs['Value'], pts_a.inputs['Selection'])
            color_node(pts_a, "input")

        # Antenna shaft - thin cylinder
        shaft = _node(tree, 'GeometryNodeMeshCylinder', (x+300, -450))
        shaft.inputs['Vertices'].default_value = 8
        shaft.inputs['Radius'].default_value   = 0.02 * P["panel_scale"]
        shaft.inputs['Depth'].default_value    = P["depth"] * 8.0
        color_node(shaft, "ornament")

        inst_a = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (x+650, 100))
        if inst_a and pts_a:
            _link(tree, pts_a.outputs['Points'],   inst_a.inputs['Points'])
            _link(tree, shaft.outputs['Mesh'],     inst_a.inputs['Instance'])
            _link(tree, pts_a.outputs['Normal'],   inst_a.inputs['Rotation'])
            color_node(inst_a, "ornament")

        real_a = _safe_node(tree, 'GeometryNodeRealizeInstances', (x+950, 100))
        if real_a and inst_a:
            _link(tree, inst_a.outputs['Instances'], real_a.inputs['Geometry'])

        join_a = _node(tree, 'GeometryNodeJoinGeometry', (x+1250, 0))
        if in_geom:
            _link(tree, in_geom, join_a.inputs['Geometry'])
        if real_a:
            _link(tree, real_a.outputs['Geometry'], join_a.inputs['Geometry'])
        color_node(join_a, "output")
        return join_a.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_antenna")
    return tree, gin, gout

register_builder(
    "MEL_scifi_antenna", build_scifi_antenna_group,
    "Antenna", "Sci-fi effect pass (absorbed from monolith build_scifi_antenna).",
    category="effects", role="modifier")


def build_scifi_damage_group(group_name="MEL_scifi_damage"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Battle damage: Voronoi crater displacement + random face deletion.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x, 100))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])

        pos_d = _node(tree, 'GeometryNodeInputPosition', (x+200, -300))
        vor_d = _node(tree, 'ShaderNodeTexVoronoi', (x+400, -300))
        vor_d.voronoi_dimensions = '3D'
        vor_d.feature = 'F1'
        vor_d.inputs['Scale'].default_value      = P["density"] * 1.2
        vor_d.inputs['Randomness'].default_value = 0.9
        _link(tree, pos_d.outputs['Position'], vor_d.inputs['Vector'])

        noise_d = _node(tree, 'ShaderNodeTexNoise', (x+400, -600))
        noise_d.inputs['Scale'].default_value     = P["density"] * 3.0
        noise_d.inputs['Detail'].default_value    = 6.0
        noise_d.inputs['Roughness'].default_value = 0.75
        _link(tree, pos_d.outputs['Position'], noise_d.inputs['Vector'])

        # Combine Voronoi + noise for irregular craters
        mix_d = _node(tree, 'ShaderNodeMix', (x+700, -400))
        mix_d.data_type = 'FLOAT'
        mix_d.inputs['Factor'].default_value = 0.45
        _link(tree, vor_d.outputs['Distance'], mix_d.inputs[6])
        _link(tree, noise_d.outputs['Fac'],    mix_d.inputs[7])

        mul_d = _node(tree, 'ShaderNodeVectorMath', (x+950, -300))
        mul_d.operation = 'MULTIPLY'
        mul_d.inputs[1].default_value = (-P["depth"] * 1.5,) * 3
        nrm_d = _node(tree, 'GeometryNodeInputNormal', (x+700, -700))
        _link(tree, nrm_d.outputs['Normal'], mul_d.inputs[0])

        scale_d = _node(tree, 'ShaderNodeVectorMath', (x+1200, -300))
        scale_d.operation = 'SCALE'
        _link(tree, mul_d.outputs['Vector'],  scale_d.inputs[0])
        _link(tree, mix_d.outputs[1],         scale_d.inputs['Scale'])

        set_d = _node(tree, 'GeometryNodeSetPosition', (x+450, 100))
        _link(tree, subd.outputs['Mesh'],    set_d.inputs['Geometry'])
        _link(tree, scale_d.outputs['Vector'], set_d.inputs['Offset'])
        color_node(set_d, "deform")

        return set_d.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_damage")
    return tree, gin, gout

register_builder(
    "MEL_scifi_damage", build_scifi_damage_group,
    "Damage", "Sci-fi effect pass (absorbed from monolith build_scifi_damage).",
    category="effects", role="modifier")




def build_scifi_hex_armour_group(group_name="MEL_scifi_hex_armour"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_scifi_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """
        Hexagonal armour plating: Voronoi-extruded hex-like tiles.
        """
        x = 0
        in_geom = _get_input_geom(tree)

        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x, 100))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])

        pos_h = _node(tree, 'GeometryNodeInputPosition', (x+200, -300))
        vor_h = _node(tree, 'ShaderNodeTexVoronoi', (x+400, -300))
        vor_h.voronoi_dimensions = '3D'
        vor_h.feature = 'F1'
        vor_h.distance = 'CHEBYCHEV'
        vor_h.inputs['Scale'].default_value      = P["density"] * 2.0
        vor_h.inputs['Randomness'].default_value = 0.15
        _link(tree, pos_h.outputs['Position'], vor_h.inputs['Vector'])

        # Cell centre distance drives height
        height_map = _node(tree, 'ShaderNodeMapRange', (x+650, -300))
        height_map.inputs['From Min'].default_value = 0.0
        height_map.inputs['From Max'].default_value = 0.5
        height_map.inputs['To Min'].default_value   = 0.0
        height_map.inputs['To Max'].default_value   = P["depth"]
        _link(tree, vor_h.outputs['Distance'], height_map.inputs['Value'])

        ext_h = _safe_node(tree, 'GeometryNodeExtrudeMesh', (x+450, 100))
        if ext_h:
            ext_h.mode = 'FACES'
            ext_h.inputs['Individual'].default_value = True
            _link(tree, subd.outputs['Mesh'],          ext_h.inputs['Mesh'])
            _link(tree, height_map.outputs['Result'],  ext_h.inputs['Offset Scale'])
            color_node(ext_h, "deform")

        result_h = ext_h.outputs['Mesh'] if ext_h else subd.outputs['Mesh']
        join_h = _node(tree, 'GeometryNodeJoinGeometry', (x+1100, 0))
        if in_geom:
            _link(tree, in_geom, join_h.inputs['Geometry'])
        _link(tree, result_h, join_h.inputs['Geometry'])
        color_node(join_h, "output")
        return join_h.outputs['Geometry']


    # Map scifi effect enum to builder function

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_scifi_hex_armour")
    return tree, gin, gout

register_builder(
    "MEL_scifi_hex_armour", build_scifi_hex_armour_group,
    "Hex Armour", "Sci-fi effect pass (absorbed from monolith build_scifi_hex_armour).",
    category="effects", role="modifier")

# 7 builders registered (plus 2 enum aliases)
