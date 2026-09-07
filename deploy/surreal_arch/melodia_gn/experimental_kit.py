"""MEL experimental builders — absorbed from the monolith (P2 family 5).

15 builders + 2 core-form deps (tower, ogee_arch). Params-as-values port.
Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)

def add_noise_displace(tree, in_geom, scale, detail, strength, seed, x=0, y=300):
    pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (x, y); color_node(pos, "input")
    noise = tree.nodes.new('ShaderNodeTexNoise'); noise.location = (x+200, y)
    noise.noise_dimensions = '4D'
    noise.inputs['W'].default_value = float(seed) * 0.1
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = detail
    noise.inputs['Roughness'].default_value = 0.55
    noise.inputs['Distortion'].default_value = 0.4
    tree.links.new(pos.outputs['Position'], noise.inputs['Vector'])
    color_node(noise, "noise")

    center = tree.nodes.new('ShaderNodeVectorMath'); center.location = (x+450, y); center.operation = 'SUBTRACT'
    center.inputs[1].default_value = (0.5, 0.5, 0.5)
    tree.links.new(noise.outputs['Color'], center.inputs[0])

    sc = tree.nodes.new('ShaderNodeVectorMath'); sc.location = (x+650, y); sc.operation = 'SCALE'
    sc.inputs['Scale'].default_value = strength
    tree.links.new(center.outputs['Vector'], sc.inputs[0])

    set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (x+850, 0); color_node(set_pos, "deform")
    tree.links.new(in_geom, set_pos.inputs['Geometry'])
    tree.links.new(sc.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']



def _node(tree, bl_idname, loc=(0, 0), **kwargs):
    n = tree.nodes.new(bl_idname)
    n.location = loc
    for k, v in kwargs.items():
        try:
            if hasattr(n, k):
                setattr(n, k, v)
            elif k in n.inputs:
                n.inputs[k].default_value = v
        except Exception:
            pass
    return n


# ──────────────────────────────────────────────────────────────────────
# ADVANCED BUILDER: RAYCAST FACADE
# Uses Raycast node to project panel windows onto a curved surface,
# creating a parametric glass curtain-wall facade.
# ──────────────────────────────────────────────────────────────────────
def _safe_node(tree, bl_idname, loc=(0, 0)):
    """Create a node, returning None (not crashing) if the type doesn't exist."""
    try:
        n = tree.nodes.new(bl_idname)
        n.location = loc
        return n
    except Exception:
        return None


def _link(tree, src, dst):
    try:
        tree.links.new(src, dst)
    except Exception:
        pass


def add_taper_chain(tree, in_geom, height, taper, x=0, y=-300):
    pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (x, y); color_node(pos, "input")
    sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (x+200, y)
    tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])

    map_range = tree.nodes.new('ShaderNodeMapRange'); map_range.location = (x+400, y)
    map_range.inputs['From Min'].default_value = -height/2
    map_range.inputs['From Max'].default_value =  height/2
    map_range.inputs['To Min'].default_value   =  1.0
    map_range.inputs['To Max'].default_value   =  max(0.05, 1.0 - taper)
    tree.links.new(sep.outputs['Z'], map_range.inputs['Value'])
    color_node(map_range, "tower")

    combine = tree.nodes.new('ShaderNodeCombineXYZ'); combine.location = (x+600, y)
    tree.links.new(map_range.outputs['Result'], combine.inputs['X'])
    tree.links.new(map_range.outputs['Result'], combine.inputs['Y'])
    combine.inputs['Z'].default_value = 1.0

    mul = tree.nodes.new('ShaderNodeVectorMath'); mul.location = (x+800, y+100); mul.operation = 'MULTIPLY'
    tree.links.new(pos.outputs['Position'], mul.inputs[0])
    tree.links.new(combine.outputs['Vector'], mul.inputs[1])

    sub = tree.nodes.new('ShaderNodeVectorMath'); sub.location = (x+1000, y+100); sub.operation = 'SUBTRACT'
    tree.links.new(mul.outputs['Vector'], sub.inputs[0])
    tree.links.new(pos.outputs['Position'], sub.inputs[1])

    set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (x+1200, 0); color_node(set_pos, "deform")
    tree.links.new(in_geom, set_pos.inputs['Geometry'])
    tree.links.new(sub.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


def add_twist(tree, in_geom, twist_angle, height, x=0, y=300):
    if abs(twist_angle) < 0.001:
        return in_geom

    pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (x, y); color_node(pos, "input")
    sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (x+200, y)
    tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])

    map_range = tree.nodes.new('ShaderNodeMapRange'); map_range.location = (x+400, y)
    map_range.inputs['From Min'].default_value = -height/2
    map_range.inputs['From Max'].default_value =  height/2
    map_range.inputs['To Min'].default_value   = 0.0
    map_range.inputs['To Max'].default_value   = twist_angle
    tree.links.new(sep.outputs['Z'], map_range.inputs['Value'])

    rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (x+600, y)
    rvec.inputs['X'].default_value = 0.0
    rvec.inputs['Y'].default_value = 0.0
    tree.links.new(map_range.outputs['Result'], rvec.inputs['Z'])

    rotate = tree.nodes.new('ShaderNodeVectorRotate'); rotate.location = (x+800, y)
    rotate.rotation_type = 'EULER_XYZ'
    tree.links.new(pos.outputs['Position'], rotate.inputs['Vector'])
    tree.links.new(rvec.outputs['Vector'], rotate.inputs['Rotation'])
    color_node(rotate, "organic")

    sub = tree.nodes.new('ShaderNodeVectorMath'); sub.location = (x+1000, y); sub.operation = 'SUBTRACT'
    tree.links.new(rotate.outputs['Vector'], sub.inputs[0])
    tree.links.new(pos.outputs['Position'], sub.inputs[1])

    set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (x+1200, 0); color_node(set_pos, "deform")
    tree.links.new(in_geom, set_pos.inputs['Geometry'])
    tree.links.new(sub.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


# ----------------------------------------------------------------------
# WHIMSY: musical/harmonic modulation helpers
# ----------------------------------------------------------------------

def _ogee_curve_pair(tree, half_W, height, swell, shoulder, base_x=0, base_y=0):
    """
    Build the two Bezier curves of an ogee arch (right + left).
    Returns (right_curve_socket, left_curve_socket).
    Curves are in the XZ plane (rotated from default XY).
    """
    rb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment')
    rb.location = (base_x, base_y + 200); color_node(rb, "ogee")
    rb.inputs['Resolution'].default_value = 32
    rb.inputs['Start'].default_value         = (half_W, 0, 0)
    rb.inputs['Start Handle'].default_value  = (half_W + swell, shoulder, 0)
    rb.inputs['End Handle'].default_value    = (half_W * 0.3, height - 0.3, 0)
    rb.inputs['End'].default_value           = (0, height, 0)

    lb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment')
    lb.location = (base_x, base_y - 200); color_node(lb, "ogee")
    lb.inputs['Resolution'].default_value = 32
    lb.inputs['Start'].default_value         = (-half_W, 0, 0)
    lb.inputs['Start Handle'].default_value  = (-half_W - swell, shoulder, 0)
    lb.inputs['End Handle'].default_value    = (-half_W * 0.3, height - 0.3, 0)
    lb.inputs['End'].default_value           = (0, height, 0)

    rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x + 300, base_y + 200)
    rt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(rb.outputs['Curve'], rt.inputs['Geometry'])

    lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x + 300, base_y - 200)
    lt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(lb.outputs['Curve'], lt.inputs['Geometry'])

    return rt.outputs['Geometry'], lt.outputs['Geometry']



NOTE_PATTERNS = {
    'WHOLE':    1.0,
    'HALF':     2.0,
    'QUARTER':  4.0,
    'EIGHTH':   8.0,
    'SIXTEENTH':16.0,
    'TRIPLET':  3.0,
    'DOTTED':   1.5,
}

BUILDER_PARAM_DEFAULTS = {
    "arch_thickness": {"type": "FloatProperty", "default": 0.18, "min": 0.02, "max": 1.0},
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "bulge_amount": {"type": "FloatProperty", "default": 0.2, "min": 0.0, "max": 2.0},
    "complexity_level": {"type": "IntProperty", "default": 3, "min": 1, "max": 5},
    "flow_amount": {"type": "FloatProperty", "default": 0.3, "min": 0.0, "max": 2.0},
    "fractal_iterations": {"type": "IntProperty", "default": 4, "min": 1, "max": 8},
    "fractal_offset": {"type": "FloatProperty", "default": 0.0, "min": -1.0, "max": 1.0},
    "fractal_scale": {"type": "FloatProperty", "default": 0.65, "min": 0.3, "max": 0.95},
    "fractal_twist_per": {"type": "FloatProperty", "default": 15.0, "min": -90.0, "max": 90.0},
    "gothic_thickness": {"type": "FloatProperty", "default": 0.12, "min": 0.02, "max": 1.0},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "hyperbolic_curvature": {"type": "FloatProperty", "default": 0.7, "min": 0.0, "max": 1.0},
    "hyperbolic_petals": {"type": "IntProperty", "default": 12, "min": 3, "max": 64},
    "hyperbolic_radius": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "hyperbolic_rings": {"type": "IntProperty", "default": 6, "min": 2, "max": 20},
    "musical_freq_a": {"type": "FloatProperty", "default": 0.6, "min": 0.05, "max": 5.0},
    "note_pattern": {"type": "EnumProperty", "default": 'QUARTER', "min": None, "max": None},
    "ogee_finial": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 2.0},
    "ogee_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 12.0},
    "ogee_shoulder": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 2.0},
    "ogee_swell": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 1.5},
    "ogee_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 8.0},
    "path_arch_count": {"type": "IntProperty", "default": 8, "min": 0, "max": 48},
    "path_radius": {"type": "FloatProperty", "default": 4.0, "min": 1.0, "max": 20.0},
    "path_segments": {"type": "IntProperty", "default": 24, "min": 6, "max": 120},
    "path_thickness": {"type": "FloatProperty", "default": 0.2, "min": 0.05, "max": 1.0},
    "path_width": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 5.0},
    "path_with_arches": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "path_z_amplitude": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 5.0},
    "path_z_freq": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "penrose_rise": {"type": "FloatProperty", "default": 0.18, "min": 0.0, "max": 0.5},
    "penrose_side_length": {"type": "FloatProperty", "default": 4.0, "min": 1.0, "max": 15.0},
    "penrose_steps_per_side": {"type": "IntProperty", "default": 5, "min": 2, "max": 20},
    "recursion_depth": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "rise": {"type": "FloatProperty", "default": 0.0, "min": None, "max": None},
    "seed": {"type": "IntProperty", "default": 42, "min": 0, "max": 9999},
    "symmetry_break": {"type": "FloatProperty", "default": 0.3, "min": 0.0, "max": 1.0},
    "taper_ratio": {"type": "FloatProperty", "default": 0.6, "min": 0.0, "max": 1.0},
    "tempo_factor": {"type": "FloatProperty", "default": 1.0, "min": 0.1, "max": 4.0},
    "tess_grid_x": {"type": "IntProperty", "default": 8, "min": 2, "max": 40},
    "tess_grid_y": {"type": "IntProperty", "default": 8, "min": 2, "max": 40},
    "tess_height_var": {"type": "FloatProperty", "default": 0.3, "min": 0.0, "max": 2.0},
    "tess_rotate_var": {"type": "FloatProperty", "default": 0.0, "min": 0.0, "max": math.pi},
    "tess_size": {"type": "FloatProperty", "default": 0.5, "min": 0.05, "max": 3.0},
    "twist_angle": {"type": "FloatProperty", "default": 0.0, "min": -math.tau, "max": math.tau},
    "unit_size": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "variation_intensity": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 1.0},
    "wave_frequency": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
}


def build_penrose_group(group_name="MEL_penrose"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Penrose impossible stairs: 4 staircases joined in a square loop, ascending subtly."""
        steps_per_side = max(2, PROPS.penrose_steps_per_side)
        total_steps = steps_per_side * 4
        side_length = PROPS.penrose_side_length
        step_run = side_length / steps_per_side
        rise = PROPS.penrose_rise

        line = tree.nodes.new('GeometryNodeMeshLine'); line.location = (base_x, 0); color_node(line, "penrose")
        line.mode = 'OFFSET'
        line.inputs['Count'].default_value = total_steps
        line.inputs['Offset'].default_value = (1, 0, 0)

        idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, -300)

        div = tree.nodes.new('ShaderNodeMath'); div.location = (base_x+200, -300); div.operation = 'DIVIDE'
        div.inputs[1].default_value = float(steps_per_side)
        tree.links.new(idx.outputs['Index'], div.inputs[0])
        floor_div = tree.nodes.new('ShaderNodeMath'); floor_div.location = (base_x+400, -300); floor_div.operation = 'FLOOR'
        tree.links.new(div.outputs['Value'], floor_div.inputs[0])

        mod_n = tree.nodes.new('ShaderNodeMath'); mod_n.location = (base_x+200, -500); mod_n.operation = 'MODULO'
        mod_n.inputs[1].default_value = float(steps_per_side)
        tree.links.new(idx.outputs['Index'], mod_n.inputs[0])

        rot_a = tree.nodes.new('ShaderNodeMath'); rot_a.location = (base_x+600, -300); rot_a.operation = 'MULTIPLY'
        rot_a.inputs[1].default_value = math.pi / 2
        tree.links.new(floor_div.outputs['Value'], rot_a.inputs[0])

        x_pos = tree.nodes.new('ShaderNodeMath'); x_pos.location = (base_x+600, -500); x_pos.operation = 'MULTIPLY'
        x_pos.inputs[1].default_value = step_run
        tree.links.new(mod_n.outputs['Value'], x_pos.inputs[0])

        sub_xc = tree.nodes.new('ShaderNodeMath'); sub_xc.location = (base_x+800, -500); sub_xc.operation = 'SUBTRACT'
        sub_xc.inputs[1].default_value = side_length / 2
        tree.links.new(x_pos.outputs['Value'], sub_xc.inputs[0])

        local_pos = tree.nodes.new('ShaderNodeCombineXYZ'); local_pos.location = (base_x+1000, -500)
        tree.links.new(sub_xc.outputs['Value'], local_pos.inputs['X'])
        local_pos.inputs['Y'].default_value = side_length / 2
        local_pos.inputs['Z'].default_value = 0

        rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (base_x+800, -300)
        rvec.inputs['X'].default_value = 0; rvec.inputs['Y'].default_value = 0
        tree.links.new(rot_a.outputs['Value'], rvec.inputs['Z'])

        rotate = tree.nodes.new('ShaderNodeVectorRotate'); rotate.location = (base_x+1200, -400)
        rotate.rotation_type = 'EULER_XYZ'
        tree.links.new(local_pos.outputs['Vector'], rotate.inputs[0])
        tree.links.new(rvec.outputs['Vector'], rotate.inputs[4])

        z_height = tree.nodes.new('ShaderNodeMath'); z_height.location = (base_x+1200, -600); z_height.operation = 'MULTIPLY'
        z_height.inputs[1].default_value = rise
        tree.links.new(idx.outputs['Index'], z_height.inputs[0])

        add_z = tree.nodes.new('ShaderNodeCombineXYZ'); add_z.location = (base_x+1400, -600)
        add_z.inputs['X'].default_value = 0; add_z.inputs['Y'].default_value = 0
        tree.links.new(z_height.outputs['Value'], add_z.inputs['Z'])

        final_pos = tree.nodes.new('ShaderNodeVectorMath'); final_pos.location = (base_x+1600, -500); final_pos.operation = 'ADD'
        tree.links.new(rotate.outputs[0], final_pos.inputs[0])
        tree.links.new(add_z.outputs['Vector'], final_pos.inputs[1])

        cur_pos = tree.nodes.new('GeometryNodeInputPosition'); cur_pos.location = (base_x+1600, -300)
        delta = tree.nodes.new('ShaderNodeVectorMath'); delta.location = (base_x+1800, -400); delta.operation = 'SUBTRACT'
        tree.links.new(final_pos.outputs[0], delta.inputs[0])
        tree.links.new(cur_pos.outputs['Position'], delta.inputs[1])

        set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (base_x+2000, 0); color_node(set_pos, "deform")
        tree.links.new(line.outputs['Mesh'], set_pos.inputs['Geometry'])
        tree.links.new(delta.outputs[0], set_pos.inputs['Offset'])

        step = tree.nodes.new('GeometryNodeMeshCube'); step.location = (base_x+1600, 200); color_node(step, "penrose")
        step.inputs['Size'].default_value = (step_run * 0.95, 0.5, max(rise, 0.05) * 0.9 + 0.05)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+2200, 0)
        tree.links.new(set_pos.outputs['Geometry'], inst.inputs['Points'])
        tree.links.new(step.outputs['Mesh'], inst.inputs['Instance'])

        rot_inst = tree.nodes.new('GeometryNodeRotateInstances'); rot_inst.location = (base_x+2400, 0)
        tree.links.new(inst.outputs['Instances'], rot_inst.inputs['Instances'])
        tree.links.new(rvec.outputs['Vector'], rot_inst.inputs['Rotation'])

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+2600, 0)
        tree.links.new(rot_inst.outputs['Instances'], realize.inputs['Geometry'])

        return realize.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: PILLAR / COLUMN
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_penrose")
    return tree, gin, gout

register_builder(
    "MEL_penrose", build_penrose_group,
    "Penrose", "Experimental builder (absorbed from monolith build_penrose).",
    category="experimental")


def build_fractal_group(group_name="MEL_fractal"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -2400
    def _impl():
        """Self-similar recursive tower stack. Each iteration scales smaller and offsets."""
        iterations = PROPS.fractal_iterations
        scale_per  = PROPS.fractal_scale
        offset_per = PROPS.fractal_offset
        twist_per  = math.radians(PROPS.fractal_twist_per)

        # Build base tower (use existing build_tower)
        base_geom = _impl_build_tower(tree, PROPS, base_x=base_x)

        parts = [base_geom]
        accumulated_height = PROPS.height

        for i in range(1, iterations):
            s = scale_per ** i
            # Re-instance / re-create scaled-down copy at progressive height
            # Simpler: use Transform on the same geometry
            trans = tree.nodes.new('GeometryNodeTransform'); trans.location = (base_x + 4000, -300 - i * 200); color_node(trans, "fractal")
            # Stack on top with diminishing radius/height
            stack_z = (accumulated_height + PROPS.height * s) / 2 + 0.1
            trans.inputs['Translation'].default_value = (offset_per * i * 0.4, 0, stack_z)
            trans.inputs['Rotation'].default_value = (0, 0, twist_per * i)
            trans.inputs['Scale'].default_value = (s, s, s)
            tree.links.new(base_geom, trans.inputs['Geometry'])
            parts.append(trans.outputs['Geometry'])
            accumulated_height += PROPS.height * s

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x + 4500, 0); color_node(join, "output")
        for p in parts:
            tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: TREBLE CLEF (musical notation)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_fractal")
    return tree, gin, gout

register_builder(
    "MEL_fractal", build_fractal_group,
    "Fractal", "Experimental builder (absorbed from monolith build_fractal).",
    category="experimental")


def build_escher_path_group(group_name="MEL_escher_path"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """A circular path with sine-driven vertical wave (impossible Escher feel) + arch supports."""
        R = PROPS.path_radius
        n = PROPS.path_segments
        width = PROPS.path_width
        thick = PROPS.path_thickness
        amp = PROPS.path_z_amplitude
        freq = PROPS.path_z_freq

        # Curve circle for path
        circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); circle.location = (base_x, 0); color_node(circle, "path")
        circle.mode = 'RADIUS'
        circle.inputs['Resolution'].default_value = n
        circle.inputs['Radius'].default_value = R

        # Z-wave displacement on the curve (sin driven by spline parameter)
        param = tree.nodes.new('GeometryNodeSplineParameter'); param.location = (base_x, -400); color_node(param, "input")
        mul_freq = tree.nodes.new('ShaderNodeMath'); mul_freq.location = (base_x+200, -400); mul_freq.operation = 'MULTIPLY'
        mul_freq.inputs[1].default_value = freq * math.tau
        tree.links.new(param.outputs['Factor'], mul_freq.inputs[0])
        sine = tree.nodes.new('ShaderNodeMath'); sine.location = (base_x+400, -400); sine.operation = 'SINE'
        tree.links.new(mul_freq.outputs['Value'], sine.inputs[0])
        z_amp = tree.nodes.new('ShaderNodeMath'); z_amp.location = (base_x+600, -400); z_amp.operation = 'MULTIPLY'
        z_amp.inputs[1].default_value = amp
        tree.links.new(sine.outputs['Value'], z_amp.inputs[0])
        color_node(z_amp, "ornament")
        ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+800, -400)
        ovec.inputs['X'].default_value = 0; ovec.inputs['Y'].default_value = 0
        tree.links.new(z_amp.outputs['Value'], ovec.inputs['Z'])

        set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (base_x+1000, 0); color_node(set_pos, "deform")
        tree.links.new(circle.outputs['Curve'], set_pos.inputs['Geometry'])
        tree.links.new(ovec.outputs['Vector'], set_pos.inputs['Offset'])

        # Sweep with rectangular profile (path width × thickness)
        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, 400); color_node(profile, "path")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 4   # 4 = square-ish
        profile.inputs['Radius'].default_value = max(width, thick) * 0.5

        sweep = tree.nodes.new('GeometryNodeCurveToMesh'); sweep.location = (base_x+1300, 0); color_node(sweep, "path")
        tree.links.new(set_pos.outputs['Geometry'], sweep.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], sweep.inputs['Profile Curve'])
        sweep.inputs['Fill Caps'].default_value = True

        parts = [sweep.outputs['Mesh']]

        # Arch supports below
        if PROPS.path_with_arches and PROPS.path_arch_count > 0:
            # Sample points around the path circle for arch placement
            sample = tree.nodes.new('GeometryNodeResampleCurve'); sample.location = (base_x+1300, 600); color_node(sample, "ornament")
            sample.inputs['Mode'].default_value = 'Count'
            sample.inputs['Count'].default_value = PROPS.path_arch_count
            tree.links.new(set_pos.outputs['Geometry'], sample.inputs['Curve'])

            c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+1500, 600)
            c2p.mode = 'EVALUATED'
            tree.links.new(sample.outputs['Curve'], c2p.inputs['Curve'])

            # Build a small ogee arch as the support
            saved_o = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial)
            PROPS.ogee_width = R * 0.3
            PROPS.ogee_height = R * 0.5
            PROPS.ogee_swell = 0.1
            PROPS.ogee_finial = 0.0
            small_arch = _impl_build_ogee_arch(tree, PROPS, base_x=base_x+1700)
            PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial = saved_o

            # Translate small arch downward (so its top is at path height)
            # Arches will be placed at points along the path with their tops touching
            arch_lower = tree.nodes.new('GeometryNodeTransform'); arch_lower.location = (base_x+2700, 600); color_node(arch_lower, "path")
            arch_lower.inputs['Translation'].default_value = (0, 0, -R * 0.5)
            tree.links.new(small_arch, arch_lower.inputs['Geometry'])

            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+3000, 600)
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(arch_lower.outputs['Geometry'], inst.inputs['Instance'])

            # Rotate each arch to face outward radially (use point's tangent rotation)
            tree.links.new(c2p.outputs['Rotation'], inst.inputs['Rotation'])

            realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+3300, 600)
            tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
            parts.append(realize.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+3700, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # MODULAR BUILDING PIECES - Window/Door/Balcony/Cornice/Fountain/Tile/Roof/Lantern
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_escher_path")
    return tree, gin, gout

register_builder(
    "MEL_escher_path", build_escher_path_group,
    "Escher Path", "Experimental builder (absorbed from monolith build_escher_path).",
    category="experimental")


def build_tessellation_group(group_name="MEL_tessellation"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """
        Escher-style tessellation:
        A grid of small cells where each cell has:
          * per-cell sine-wave Z displacement (metamorphosis)
          * per-cell rotation variation
          * interlocking via slight overlap
        Driven by the harmonic params for cohesion with the rest of the system.
        """
        nx = PROPS.tess_grid_x
        ny = PROPS.tess_grid_y
        s = PROPS.tess_size
        parts = []

        grid = tree.nodes.new('GeometryNodeMeshGrid'); grid.location = (base_x, 0); color_node(grid, "tessellation")
        grid.inputs['Size X'].default_value = s * nx
        grid.inputs['Size Y'].default_value = s * ny
        grid.inputs['Vertices X'].default_value = nx
        grid.inputs['Vertices Y'].default_value = ny

        # Tile prototype - small box
        tile = tree.nodes.new('GeometryNodeMeshCube'); tile.location = (base_x, 300); color_node(tile, "tessellation")
        tile.inputs['Size'].default_value = (s * 1.05, s * 1.05, s * 0.4)  # slight overlap

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+300, 0); color_node(inst, "tessellation")
        tree.links.new(grid.outputs['Mesh'], inst.inputs['Points'])
        tree.links.new(tile.outputs['Mesh'], inst.inputs['Instance'])

        # Per-instance Z height variation via sine of (X + Y) -> Escher metamorphosis pattern
        pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (base_x, -400); color_node(pos, "input")
        sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (base_x+200, -400)
        tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])
        sumxy = tree.nodes.new('ShaderNodeMath'); sumxy.location = (base_x+400, -400); sumxy.operation = 'ADD'
        tree.links.new(sep.outputs['X'], sumxy.inputs[0])
        tree.links.new(sep.outputs['Y'], sumxy.inputs[1])
        fmul = tree.nodes.new('ShaderNodeMath'); fmul.location = (base_x+600, -400); fmul.operation = 'MULTIPLY'
        fmul.inputs[1].default_value = PROPS.musical_freq_a * NOTE_PATTERNS.get(PROPS.note_pattern, 4.0) * PROPS.tempo_factor / 4.0
        tree.links.new(sumxy.outputs[0], fmul.inputs[0])
        sn = tree.nodes.new('ShaderNodeMath'); sn.location = (base_x+800, -400); sn.operation = 'SINE'
        tree.links.new(fmul.outputs[0], sn.inputs[0])
        color_node(sn, "tessellation")
        h_amp = tree.nodes.new('ShaderNodeMath'); h_amp.location = (base_x+1000, -400); h_amp.operation = 'MULTIPLY'
        h_amp.inputs[1].default_value = PROPS.tess_height_var
        tree.links.new(sn.outputs[0], h_amp.inputs[0])

        ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+1200, -400); color_node(ovec, "tessellation")
        ovec.inputs['X'].default_value = 0
        ovec.inputs['Y'].default_value = 0
        tree.links.new(h_amp.outputs[0], ovec.inputs['Z'])

        ti = tree.nodes.new('GeometryNodeTranslateInstances'); ti.location = (base_x+1400, 0); color_node(ti, "tessellation")
        tree.links.new(inst.outputs['Instances'], ti.inputs['Instances'])
        tree.links.new(ovec.outputs['Vector'], ti.inputs['Translation'])

        # Optional rotation variation
        if PROPS.tess_rotate_var > 0.001:
            idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x+1100, 200)
            # Pseudo-random rotation per index using sin
            rmul = tree.nodes.new('ShaderNodeMath'); rmul.location = (base_x+1300, 200); rmul.operation = 'MULTIPLY'
            rmul.inputs[1].default_value = 1.61803  # golden ratio for non-repeating
            tree.links.new(idx.outputs['Index'], rmul.inputs[0])
            rsin = tree.nodes.new('ShaderNodeMath'); rsin.location = (base_x+1500, 200); rsin.operation = 'SINE'
            tree.links.new(rmul.outputs[0], rsin.inputs[0])
            rscale = tree.nodes.new('ShaderNodeMath'); rscale.location = (base_x+1700, 200); rscale.operation = 'MULTIPLY'
            rscale.inputs[1].default_value = PROPS.tess_rotate_var
            tree.links.new(rsin.outputs[0], rscale.inputs[0])
            rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (base_x+1900, 200); color_node(rvec, "tessellation")
            rvec.inputs['X'].default_value = 0
            rvec.inputs['Y'].default_value = 0
            tree.links.new(rscale.outputs[0], rvec.inputs['Z'])
            ri = tree.nodes.new('GeometryNodeRotateInstances'); ri.location = (base_x+2100, 0)
            tree.links.new(ti.outputs['Instances'], ri.inputs['Instances'])
            tree.links.new(rvec.outputs['Vector'], ri.inputs['Rotation'])
            final_inst = ri.outputs['Instances']
        else:
            final_inst = ti.outputs['Instances']

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+2400, 0); color_node(realize, "output")
        tree.links.new(final_inst, realize.inputs['Geometry'])
        return realize.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: HYPERBOLIC DISK (Escher's Circle Limit)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_tessellation")
    return tree, gin, gout

register_builder(
    "MEL_tessellation", build_tessellation_group,
    "Tessellation", "Experimental builder (absorbed from monolith build_tessellation).",
    category="experimental")


def build_hyperbolic_disk_group(group_name="MEL_hyperbolic_disk"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """
        Poincaré disk - concentric rings of decreasing-arc tiles.
        True hyperbolic geometry has an infinite tiling that bends toward the boundary.
        Approximated here with: outer ring + N concentric rings + radial spokes.
        Curvature param mixes flat Euclidean (0) vs Poincaré projection (1).
        """
        R = PROPS.hyperbolic_radius
        n_rings = PROPS.hyperbolic_rings
        n_spokes = PROPS.hyperbolic_petals
        curv = PROPS.hyperbolic_curvature
        parts = []

        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "hyperbolic")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 6
        profile.inputs['Radius'].default_value = 0.04

        # Concentric rings - each smaller and lifted (Poincaré projection: tiles shrink toward boundary)
        for ring_i in range(n_rings):
            # Hyperbolic distance: r_i = R * (1 - 1/(1 + i*curv*0.5))
            # When curv=0: linear spacing R*i/n_rings. When curv=1: tighter near edge.
            t = (ring_i + 1) / n_rings
            r = R * t
            # If curv is high, push radii out toward R
            r = r * (1 - curv) + (R * (1 - 0.5 * (1 - t) ** 2)) * curv

            ring = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); ring.location = (base_x, ring_i * 200); color_node(ring, "hyperbolic")
            ring.mode = 'RADIUS'
            ring.inputs['Resolution'].default_value = max(16, n_spokes * 2)
            ring.inputs['Radius'].default_value = r

            # Lift by Poincaré projection (z = R * curv * (1 - sqrt(1 - (r/R)^2)))
            # This gives a lens-like dome shape when curv > 0
            z = R * curv * (1 - math.sqrt(max(0.0, 1 - (r/R)**2)))
            rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+250, ring_i * 200); color_node(rt, "hyperbolic")
            rt.inputs['Translation'].default_value = (0, 0, z)
            rt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
            tree.links.new(ring.outputs['Curve'], rt.inputs['Geometry'])

            sw = tree.nodes.new('GeometryNodeCurveToMesh'); sw.location = (base_x+500, ring_i * 200)
            tree.links.new(rt.outputs['Geometry'], sw.inputs['Curve'])
            tree.links.new(profile.outputs['Curve'], sw.inputs['Profile Curve'])
            parts.append(sw.outputs['Mesh'])

        # Radial spokes - pieces from center to outer ring
        for spoke_i in range(n_spokes):
            ang = (spoke_i / n_spokes) * math.tau
            # Build a thin cylinder spoke from center to radius R
            spoke = tree.nodes.new('GeometryNodeMeshCylinder'); spoke.location = (base_x, (n_rings + spoke_i // 2) * 200); color_node(spoke, "hyperbolic")
            spoke.inputs['Vertices'].default_value = 6
            spoke.inputs['Radius'].default_value = 0.025
            spoke.inputs['Depth'].default_value = R

            st = tree.nodes.new('GeometryNodeTransform'); st.location = (base_x+250, (n_rings + spoke_i // 2) * 200)
            # Position spoke so one end is at center, other end at edge
            st.inputs['Translation'].default_value = (math.cos(ang) * R/2, math.sin(ang) * R/2, 0)
            # Rotate to lie along radial direction (default cylinder is along Z)
            st.inputs['Rotation'].default_value = (0, math.radians(90), ang)
            tree.links.new(spoke.outputs['Mesh'], st.inputs['Geometry'])
            parts.append(st.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # LEVEL DESIGN / GREYBOX BUILDERS - all snap to PROPS.unit_size grid
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_hyperbolic_disk")
    return tree, gin, gout

register_builder(
    "MEL_hyperbolic_disk", build_hyperbolic_disk_group,
    "Hyperbolic Disk", "Experimental builder (absorbed from monolith build_hyperbolic_disk).",
    category="experimental")


def build_geodesic_voronoi_group(group_name="MEL_geodesic_voronoi"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """
        Geodesic dome with Voronoi cell patterning using:
        - Edge Angle node for crease-aware wireframe
        - Named Attribute storage for thickness
        - Distribute Points for structural rivets
        """
        x = -200
        segs = max(4, PROPS.complexity_level * 2)

        # Base UV sphere
        uvsph = _node(tree, 'GeometryNodeMeshUVSphere', (x, 200))
        uvsph.inputs['Segments'].default_value = segs * 4
        uvsph.inputs['Rings'].default_value    = segs * 2
        uvsph.inputs['Radius'].default_value   = PROPS.base_radius
        color_node(uvsph, "dome")

        # Voronoi texture for cell patterning
        vor = _node(tree, 'ShaderNodeTexVoronoi', (x+200, -400))
        vor.voronoi_dimensions = '3D'
        vor.feature = 'F1'
        vor.inputs['Scale'].default_value      = PROPS.wave_frequency * 1.5
        vor.inputs['Randomness'].default_value = PROPS.variation_intensity
        color_node(vor, "noise")

        # Use voronoi distance to threshold which faces are "glass" vs "frame"
        pos3 = _node(tree, 'GeometryNodeInputPosition', (x+100, -600))
        _link(tree, pos3.outputs['Position'], vor.inputs['Vector'])

        comp = _node(tree, 'ShaderNodeMath', (x+500, -400))
        comp.operation = 'GREATER_THAN'
        comp.inputs[1].default_value = 0.35 * PROPS.variation_intensity + 0.15
        _link(tree, vor.outputs['Distance'], comp.inputs[0])

        # Delete faces that are "glass" (keep structure frame)
        del_faces = _node(tree, 'GeometryNodeDeleteGeometry', (x+700, 200))
        del_faces.domain = 'FACE'
        del_faces.mode   = 'ALL'
        _link(tree, uvsph.outputs['Mesh'],  del_faces.inputs['Geometry'])
        _link(tree, comp.outputs['Value'],  del_faces.inputs['Selection'])
        color_node(del_faces, "optimize")

        # Wireframe the frame faces (Wireframe GN node removed in newer Blender;
        # _safe_node returns None and we pass through if so)
        wf = _safe_node(tree, 'GeometryNodeWireframe', (x+1000, 200))
        if wf is None:
            # Fallback - just return the unwireframed faces
            return del_faces.outputs['Geometry']
        wf.inputs['Thickness'].default_value = 0.04 + PROPS.arch_thickness * 0.3
        try: wf.use_replace_wire = True
        except (AttributeError, TypeError): pass
        _link(tree, del_faces.outputs['Geometry'], wf.inputs['Mesh'])
        color_node(wf, "gothic")

        # Edge angle node - find flat vs sharp edges for decorative treatment
        edge_ang = _node(tree, 'GeometryNodeInputMeshEdgeAngle', (x+600, -700))
        color_node(edge_ang, "input")

        # Store signed angle as named attribute for downstream use
        store_attr = _node(tree, 'GeometryNodeStoreNamedAttribute', (x+900, -700))
        store_attr.domain    = 'EDGE'
        store_attr.data_type = 'FLOAT'
        store_attr.inputs['Name'].default_value = "dome_edge_angle"
        _link(tree, wf.outputs['Mesh'],           store_attr.inputs['Geometry'])
        _link(tree, edge_ang.outputs['Unsigned Angle'], store_attr.inputs['Value'])
        color_node(store_attr, "input")

        # Glass panel - keep voronoi cells as flat panels with solidify
        uvsph2 = _node(tree, 'GeometryNodeMeshUVSphere', (x, -200))
        uvsph2.inputs['Segments'].default_value  = segs * 4
        uvsph2.inputs['Rings'].default_value     = segs * 2
        uvsph2.inputs['Radius'].default_value    = PROPS.base_radius * 0.995
        color_node(uvsph2, "dome")

        keep_faces = _node(tree, 'GeometryNodeDeleteGeometry', (x+700, -200))
        keep_faces.domain = 'FACE'
        keep_faces.mode   = 'ALL'
        not_node = _node(tree, 'FunctionNodeBooleanMath', (x+500, -250))
        not_node.operation = 'NOT'
        _link(tree, comp.outputs['Value'],   not_node.inputs[0])
        _link(tree, uvsph2.outputs['Mesh'],  keep_faces.inputs['Geometry'])
        _link(tree, not_node.outputs['Boolean'], keep_faces.inputs['Selection'])
        color_node(keep_faces, "optimize")

        # Distribute structural rivets on frame wireframe surface
        pts3 = _node(tree, 'GeometryNodeDistributePointsOnFaces', (x+1300, -600))
        pts3.distribute_method = 'POISSON'
        pts3.inputs['Distance Min'].default_value = 0.15
        pts3.inputs['Density Max'].default_value  = 2.0
        pts3.inputs['Seed'].default_value         = PROPS.seed + 13
        _link(tree, store_attr.outputs['Geometry'], pts3.inputs['Mesh'])

        rivet = _node(tree, 'GeometryNodeMeshIcoSphere', (x+1300, -900))
        rivet.inputs['Radius'].default_value       = 0.025
        rivet.inputs['Subdivisions'].default_value  = 1

        inst3 = _node(tree, 'GeometryNodeInstanceOnPoints', (x+1600, -600))
        _link(tree, pts3.outputs['Points'],   inst3.inputs['Points'])
        _link(tree, rivet.outputs['Mesh'],    inst3.inputs['Instance'])
        real3 = _node(tree, 'GeometryNodeRealizeInstances', (x+1900, -600))
        _link(tree, inst3.outputs['Instances'], real3.inputs['Geometry'])

        join3 = _node(tree, 'GeometryNodeJoinGeometry', (x+2200, 0))
        _link(tree, store_attr.outputs['Geometry'], join3.inputs['Geometry'])
        _link(tree, keep_faces.outputs['Geometry'], join3.inputs['Geometry'])
        _link(tree, real3.outputs['Geometry'],      join3.inputs['Geometry'])
        color_node(join3, "output")

        return join3.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: DNA HELIX TOWER
    # Procedural double helix using Curve nodes - two intertwined spirals
    # with cross-rungs, swept with a circular profile.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_geodesic_voronoi")
    return tree, gin, gout

register_builder(
    "MEL_geodesic_voronoi", build_geodesic_voronoi_group,
    "Geodesic Voronoi", "Experimental builder (absorbed from monolith build_geodesic_voronoi).",
    category="experimental")


def build_dna_helix_group(group_name="MEL_dna_helix"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """
        DNA double helix: two Curve Line nodes swept into helices via
        Curve to Mesh + procedural position deform.
        """
        x = -200
        segs_h = max(32, PROPS.complexity_level * 24)

        pieces = []
        for strand in range(2):
            phase_offset = strand * math.pi

            # Parametric line -> deform into helix via Set Position
            line = _node(tree, 'GeometryNodeCurvePrimitiveLine', (x, strand * 500))
            line.inputs['Start'].default_value = (0, 0, -PROPS.height * 0.5)
            line.inputs['End'].default_value   = (0, 0,  PROPS.height * 0.5)
            color_node(line, "stair")

            res = _node(tree, 'GeometryNodeResampleCurve', (x+300, strand * 500))
            try: res.mode = 'Count'
            except (AttributeError, TypeError):
                try: res.inputs['Mode'].default_value = 'Count'
                except Exception: pass
            res.inputs['Count'].default_value = segs_h
            _link(tree, line.outputs['Curve'], res.inputs['Curve'])

            # Position along curve (t = 0..1 via spline parameter)
            spline_p = _node(tree, 'GeometryNodeSplineParameter', (x+300, strand*500 - 300))
            color_node(spline_p, "input")

            # Convert t -> angle
            mul_ang = _node(tree, 'ShaderNodeMath', (x+550, strand*500 - 300))
            mul_ang.operation = 'MULTIPLY'
            mul_ang.inputs[1].default_value = PROPS.recursion_depth * math.tau
            _link(tree, spline_p.outputs['Factor'], mul_ang.inputs[0])

            add_phase = _node(tree, 'ShaderNodeMath', (x+750, strand*500 - 300))
            add_phase.operation = 'ADD'
            add_phase.inputs[1].default_value = phase_offset
            _link(tree, mul_ang.outputs['Value'], add_phase.inputs[0])

            cos_n = _node(tree, 'ShaderNodeMath', (x+950, strand*500 - 200))
            cos_n.operation = 'COSINE'
            sin_n = _node(tree, 'ShaderNodeMath', (x+950, strand*500 - 400))
            sin_n.operation = 'SINE'
            _link(tree, add_phase.outputs['Value'], cos_n.inputs[0])
            _link(tree, add_phase.outputs['Value'], sin_n.inputs[0])

            scale_r = _node(tree, 'ShaderNodeMath', (x+1150, strand*500 - 200))
            scale_r.operation = 'MULTIPLY'
            scale_r.inputs[1].default_value = PROPS.base_radius
            _link(tree, cos_n.outputs['Value'], scale_r.inputs[0])

            scale_r2 = _node(tree, 'ShaderNodeMath', (x+1150, strand*500 - 400))
            scale_r2.operation = 'MULTIPLY'
            scale_r2.inputs[1].default_value = PROPS.base_radius
            _link(tree, sin_n.outputs['Value'], scale_r2.inputs[0])

            # Get Z from existing position
            pos_h = _node(tree, 'GeometryNodeInputPosition', (x+200, strand*500 - 600))
            sep_h = _node(tree, 'ShaderNodeSeparateXYZ',     (x+400, strand*500 - 600))
            _link(tree, pos_h.outputs['Position'], sep_h.inputs['Vector'])

            comb_h = _node(tree, 'ShaderNodeCombineXYZ', (x+1350, strand*500 - 300))
            _link(tree, scale_r.outputs['Value'],  comb_h.inputs['X'])
            _link(tree, scale_r2.outputs['Value'], comb_h.inputs['Y'])
            _link(tree, sep_h.outputs['Z'],        comb_h.inputs['Z'])

            set_p_h = _node(tree, 'GeometryNodeSetPosition', (x+1600, strand * 500))
            _link(tree, res.outputs['Curve'],      set_p_h.inputs['Geometry'])
            _link(tree, comb_h.outputs['Vector'],  set_p_h.inputs['Position'])
            color_node(set_p_h, "deform")

            # Circular sweep profile
            circ = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+1600, strand*500 - 500))
            circ.inputs['Radius'].default_value    = 0.06 * PROPS.base_radius
            circ.inputs['Resolution'].default_value = 8

            c2m = _node(tree, 'GeometryNodeCurveToMesh', (x+1900, strand * 500))
            _link(tree, set_p_h.outputs['Geometry'], c2m.inputs['Curve'])
            _link(tree, circ.outputs['Curve'],        c2m.inputs['Profile Curve'])
            c2m.inputs['Fill Caps'].default_value = True
            color_node(c2m, "stair")
            pieces.append(c2m.outputs['Mesh'])

        # Cross rungs - Sample UV Surface to place rungs between strands
        rung_count = max(4, PROPS.recursion_depth * 4)
        line_r = _node(tree, 'GeometryNodeCurvePrimitiveLine', (x+2200, -400))
        line_r.inputs['Start'].default_value = (-PROPS.base_radius, 0, 0)
        line_r.inputs['End'].default_value   = ( PROPS.base_radius, 0, 0)
        circ_r = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+2200, -700))
        circ_r.inputs['Radius'].default_value     = 0.035 * PROPS.base_radius
        circ_r.inputs['Resolution'].default_value = 6
        c2m_r = _node(tree, 'GeometryNodeCurveToMesh', (x+2500, -400))
        _link(tree, line_r.outputs['Curve'], c2m_r.inputs['Curve'])
        _link(tree, circ_r.outputs['Curve'], c2m_r.inputs['Profile Curve'])
        c2m_r.inputs['Fill Caps'].default_value = True
        color_node(c2m_r, "arch")

        # Array rungs along Z
        rung_pt = _node(tree, 'GeometryNodeMeshLine', (x+2500, -700))
        rung_pt.mode = 'OFFSET'
        rung_pt.inputs['Count'].default_value = rung_count
        rung_pt.inputs['Offset'].default_value = (0, 0, PROPS.height / max(1, rung_count))
        rung_pt.inputs['Start Location'].default_value = (0, 0, -PROPS.height * 0.5)
        color_node(rung_pt, "input")

        pts_r = _node(tree, 'GeometryNodeInstanceOnPoints', (x+2800, -400))
        _link(tree, rung_pt.outputs['Mesh'], pts_r.inputs['Points'])
        _link(tree, c2m_r.outputs['Mesh'],   pts_r.inputs['Instance'])
        real_r = _node(tree, 'GeometryNodeRealizeInstances', (x+3100, -400))
        _link(tree, pts_r.outputs['Instances'], real_r.inputs['Geometry'])

        join_h = _node(tree, 'GeometryNodeJoinGeometry', (x+3400, 0))
        for p in pieces:
            _link(tree, p, join_h.inputs['Geometry'])
        _link(tree, real_r.outputs['Geometry'], join_h.inputs['Geometry'])
        color_node(join_h, "output")

        return join_h.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: IMPOSSIBLE KLEIN BOTTLE ARCHITECTURE
    # A self-intersecting Klein bottle mesh - mathematically impossible
    # in 3D but beautiful as a sculptural form.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_dna_helix")
    return tree, gin, gout

register_builder(
    "MEL_dna_helix", build_dna_helix_group,
    "Dna Helix", "Experimental builder (absorbed from monolith build_dna_helix).",
    category="experimental")


def build_klein_bottle_group(group_name="MEL_klein_bottle"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """
        Klein bottle: parametric surface built using Index of Nearest
        and trigonometric math nodes - two components joined with twist.
        """
        import bmesh as _bkb

        x = -200
        segs_u = max(24, PROPS.complexity_level * 12)
        segs_v = max(16, PROPS.complexity_level * 8)
        R = PROPS.base_radius
        r = R * 0.25

        # We build the Klein bottle parametrically in bmesh and pass as mesh resource
        mesh_k = bpy.data.meshes.new("KleinBottle_Surf")
        bm_k = _bkb.new()
        verts_k = {}

        def klein_pos(u, v):
            # Standard Figure-8 Klein bottle parametrization
            cos_u = math.cos(u); sin_u = math.sin(u)
            cos_v = math.cos(v); sin_v = math.sin(v)
            cos_hu = math.cos(u * 0.5); sin_hu = math.sin(u * 0.5)
            # a = 2, b = 1 variant
            if u < math.pi:
                x_k = (R + r * cos_v * cos_u - r * sin_v * sin_hu * sin_u)
            else:
                x_k = (R + r * cos_v * cos_u + r * sin_v * sin_hu * sin_u)
            y_k = (R + r * cos_v * sin_u + r * sin_v * cos_hu * cos_u if u < math.pi
                   else R + r * cos_v * sin_u - r * sin_v * cos_hu * cos_u)
            z_k = r * sin_v * (sin_hu * PROPS.height * 0.3 + 1.0)
            return (x_k * PROPS.height * 0.2,
                    y_k * PROPS.height * 0.2,
                    z_k * PROPS.height * 0.5)

        for iu in range(segs_u):
            for iv in range(segs_v):
                u = 2 * math.pi * iu / segs_u
                v = 2 * math.pi * iv / segs_v
                verts_k[(iu, iv)] = bm_k.verts.new(klein_pos(u, v))

        for iu in range(segs_u):
            for iv in range(segs_v):
                v00 = verts_k[(iu, iv)]
                v10 = verts_k[((iu+1) % segs_u, iv)]
                v11 = verts_k[((iu+1) % segs_u, (iv+1) % segs_v)]
                v01 = verts_k[(iu, (iv+1) % segs_v)]
                try:
                    bm_k.faces.new([v00, v10, v11, v01])
                except Exception:
                    pass

        bm_k.normal_update()
        bm_k.to_mesh(mesh_k)
        bm_k.free()
        mesh_k.update()

        # Embed the pre-built mesh as an Object Data input via Object Info
        mesh_obj_k = bpy.data.objects.new("__KleinSurf__", mesh_k)
        bpy.context.collection.objects.link(mesh_obj_k)
        mesh_obj_k.hide_render = True
        mesh_obj_k.hide_viewport = True

        obj_info = _node(tree, 'GeometryNodeObjectInfo', (x, 0))
        obj_info.transform_space = 'RELATIVE'
        obj_info.inputs['Object'].default_value = mesh_obj_k
        color_node(obj_info, "fractal")

        # Subdiv for smoothness
        subd_k = _node(tree, 'GeometryNodeSubdivisionSurface', (x+300, 0))
        subd_k.inputs['Level'].default_value = min(2, PROPS.complexity_level - 1)
        _link(tree, obj_info.outputs['Geometry'], subd_k.inputs['Mesh'])

        # Noise distortion for surreal quality
        pos_k = _node(tree, 'GeometryNodeInputPosition', (x+300, -400))
        noise_k = _node(tree, 'ShaderNodeTexNoise', (x+500, -400))
        noise_k.inputs['Scale'].default_value     = 2.0
        noise_k.inputs['Detail'].default_value    = 4.0
        noise_k.inputs['Roughness'].default_value = 0.5
        _link(tree, pos_k.outputs['Position'], noise_k.inputs['Vector'])
        noise_k.inputs['Distortion'].default_value = PROPS.flow_amount * 0.5

        mul_k = _node(tree, 'ShaderNodeVectorMath', (x+750, -400))
        mul_k.operation = 'MULTIPLY'
        mul_k.inputs[1].default_value = (PROPS.bulge_amount * 0.15,) * 3
        _link(tree, noise_k.outputs['Color'], mul_k.inputs[0])

        set_k = _node(tree, 'GeometryNodeSetPosition', (x+600, 0))
        _link(tree, subd_k.outputs['Mesh'],     set_k.inputs['Geometry'])
        _link(tree, mul_k.outputs['Vector'],    set_k.inputs['Offset'])
        color_node(set_k, "deform")

        return set_k.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: SPIDER WEB DOME
    # Polar spiral curve + Curve to Mesh + instanced radial struts
    # using the Curve Circle + Trim Curve + Resample pipeline.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_klein_bottle")
    return tree, gin, gout

register_builder(
    "MEL_klein_bottle", build_klein_bottle_group,
    "Klein Bottle", "Experimental builder (absorbed from monolith build_klein_bottle).",
    category="experimental")


def build_spiderweb_dome_group(group_name="MEL_spiderweb_dome"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        x = -200
        rings = max(4, PROPS.recursion_depth + 2)
        spokes = max(8, PROPS.complexity_level * 4)
        R = PROPS.base_radius

        pieces_sw = []

        # Radial spokes - lines from centre to edge, bent upward
        for si in range(spokes):
            ang = 2 * math.pi * si / spokes
            ex = R * math.cos(ang); ey = R * math.sin(ang)
            ln = _node(tree, 'GeometryNodeCurvePrimitiveLine', (x, si * 80))
            ln.inputs['Start'].default_value = (0, 0, PROPS.rise if hasattr(PROPS, 'rise') else PROPS.height * 0.3)
            ln.inputs['End'].default_value   = (ex, ey, 0.0)
            res_sw = _node(tree, 'GeometryNodeResampleCurve', (x+250, si * 80))
            try: res_sw.mode = 'Count'
            except (AttributeError, TypeError):
                try: res_sw.inputs['Mode'].default_value = 'Count'
                except Exception: pass
            res_sw.inputs['Count'].default_value = 12
            _link(tree, ln.outputs['Curve'], res_sw.inputs['Curve'])
            circ_sw = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+250, si*80 - 200))
            circ_sw.inputs['Radius'].default_value     = 0.018
            circ_sw.inputs['Resolution'].default_value = 6
            c2m_sw = _node(tree, 'GeometryNodeCurveToMesh', (x+500, si * 80))
            _link(tree, res_sw.outputs['Curve'], c2m_sw.inputs['Curve'])
            _link(tree, circ_sw.outputs['Curve'],c2m_sw.inputs['Profile Curve'])
            pieces_sw.append(c2m_sw.outputs['Mesh'])
            color_node(c2m_sw, "arch")

        # Concentric ring circles
        for ri in range(1, rings + 1):
            frac = ri / (rings + 1)
            r_ring = R * frac
            z_ring = (PROPS.height * 0.3 if hasattr(PROPS, 'height') else 1.5) * (1.0 - frac)
            circ_ring = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x + 800, ri * 200))
            circ_ring.inputs['Radius'].default_value     = r_ring
            circ_ring.inputs['Resolution'].default_value = max(16, spokes * 2)
            # Move ring up via transform
            tfm = _node(tree, 'GeometryNodeTransform', (x + 1050, ri * 200))
            tfm.inputs['Translation'].default_value = (0, 0, z_ring)
            _link(tree, circ_ring.outputs['Curve'], tfm.inputs['Geometry'])
            prof_ring = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+800, ri*200 - 150))
            prof_ring.inputs['Radius'].default_value     = 0.014 + 0.005 * (rings - ri) / rings
            prof_ring.inputs['Resolution'].default_value = 6
            c2m_ring = _node(tree, 'GeometryNodeCurveToMesh', (x+1300, ri * 200))
            _link(tree, tfm.outputs['Geometry'],      c2m_ring.inputs['Curve'])
            _link(tree, prof_ring.outputs['Curve'],   c2m_ring.inputs['Profile Curve'])
            pieces_sw.append(c2m_ring.outputs['Mesh'])
            color_node(c2m_ring, "dome")

        join_sw = _node(tree, 'GeometryNodeJoinGeometry', (x + 1700, 0))
        for p in pieces_sw:
            _link(tree, p, join_sw.inputs['Geometry'])
        color_node(join_sw, "output")

        return join_sw.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: COSMIC WEB FILAMENT
    # Uses Distribute Points in Volume + Connect Point Lines to simulate
    # the large-scale cosmic web - used as a surreal architectural skeleton.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_spiderweb_dome")
    return tree, gin, gout

register_builder(
    "MEL_spiderweb_dome", build_spiderweb_dome_group,
    "Spiderweb Dome", "Experimental builder (absorbed from monolith build_spiderweb_dome).",
    category="experimental")


def build_cosmic_web_group(group_name="MEL_cosmic_web"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        x = -200
        R = PROPS.base_radius

        # Volume cube for point distribution
        cube_vol = _node(tree, 'GeometryNodeMeshCube', (x, 0))
        cube_vol.inputs['Size'].default_value = (R * 2.5, R * 2.5, PROPS.height)

        m2v_cw = _node(tree, 'GeometryNodeMeshToVolume', (x+300, 0))
        try: m2v_cw.resolution_mode = 'VOXEL_SIZE'
        except (AttributeError, TypeError): pass
        m2v_cw.inputs['Voxel Size'].default_value = 0.3
        m2v_cw.inputs['Interior Band Width'].default_value = R * 2.5
        _link(tree, cube_vol.outputs['Mesh'], m2v_cw.inputs['Mesh'])
        color_node(m2v_cw, "organic")

        # Distribute points in volume
        pts_vol = _node(tree, 'GeometryNodeDistributePointsInVolume', (x+600, 0))
        try: pts_vol.mode = 'DENSITY_RANDOM'
        except (AttributeError, TypeError):
            try: pts_vol.inputs['Mode'].default_value = 'DENSITY_RANDOM'
            except Exception: pass
        pts_vol.inputs['Density'].default_value    = max(1, PROPS.complexity_level * 2)
        pts_vol.inputs['Seed'].default_value       = PROPS.seed
        pts_vol.inputs['Spacing'].default_value    = (0.6, 0.6, 0.6)
        _link(tree, m2v_cw.outputs['Volume'], pts_vol.inputs['Volume'])
        color_node(pts_vol, "input")

        # Noise to cluster the points (galaxies attract)
        pos_cw = _node(tree, 'GeometryNodeInputPosition', (x+700, -400))
        noise_cw = _node(tree, 'ShaderNodeTexNoise', (x+900, -400))
        noise_cw.inputs['Scale'].default_value     = 0.8 * PROPS.wave_frequency
        noise_cw.inputs['Detail'].default_value    = 8.0
        noise_cw.inputs['Roughness'].default_value = 0.7
        _link(tree, pos_cw.outputs['Position'], noise_cw.inputs['Vector'])

        mul_cw = _node(tree, 'ShaderNodeVectorMath', (x+1100, -400))
        mul_cw.operation = 'MULTIPLY'
        mul_cw.inputs[1].default_value = (R * 0.4, R * 0.4, PROPS.height * 0.2)
        _link(tree, noise_cw.outputs['Color'], mul_cw.inputs[0])

        set_cw = _node(tree, 'GeometryNodeSetPosition', (x+900, 0))
        _link(tree, pts_vol.outputs['Points'], set_cw.inputs['Geometry'])
        _link(tree, mul_cw.outputs['Vector'],  set_cw.inputs['Offset'])
        color_node(set_cw, "deform")

        # Instance tiny ico-spheres at node points
        ico_cw = _node(tree, 'GeometryNodeMeshIcoSphere', (x+1200, -600))
        ico_cw.inputs['Radius'].default_value       = 0.05
        ico_cw.inputs['Subdivisions'].default_value  = 1

        inst_cw = _node(tree, 'GeometryNodeInstanceOnPoints', (x+1400, 0))
        _link(tree, set_cw.outputs['Geometry'], inst_cw.inputs['Points'])
        _link(tree, ico_cw.outputs['Mesh'],     inst_cw.inputs['Instance'])
        real_cw = _node(tree, 'GeometryNodeRealizeInstances', (x+1700, 0))
        _link(tree, inst_cw.outputs['Instances'], real_cw.inputs['Geometry'])

        # Filaments - nearest-neighbour lines between nodes using Edge Paths
        # Use Mesh Line with noise-offset positions as proxy filament network
        line_cw = _node(tree, 'GeometryNodeMeshLine', (x+1200, 400))
        line_cw.mode = 'OFFSET'
        line_cw.inputs['Count'].default_value          = max(20, PROPS.complexity_level * 12)
        line_cw.inputs['Offset'].default_value         = (0, 0, PROPS.height / max(1, PROPS.complexity_level * 12))
        line_cw.inputs['Start Location'].default_value = (0, 0, -PROPS.height * 0.5)

        pos_fil = _node(tree, 'GeometryNodeInputPosition', (x+1400, 200))
        noise_fil = _node(tree, 'ShaderNodeTexNoise', (x+1600, 200))
        noise_fil.inputs['Scale'].default_value = 1.2
        noise_fil.inputs['Detail'].default_value = 6.0
        _link(tree, pos_fil.outputs['Position'], noise_fil.inputs['Vector'])
        mul_fil = _node(tree, 'ShaderNodeVectorMath', (x+1800, 200))
        mul_fil.operation = 'MULTIPLY'
        mul_fil.inputs[1].default_value = (R * 0.8, R * 0.8, 0.1)
        _link(tree, noise_fil.outputs['Color'], mul_fil.inputs[0])
        set_fil = _node(tree, 'GeometryNodeSetPosition', (x+2000, 400))
        _link(tree, line_cw.outputs['Mesh'], set_fil.inputs['Geometry'])
        _link(tree, mul_fil.outputs['Vector'], set_fil.inputs['Offset'])
        circ_fil = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+2000, 100))
        circ_fil.inputs['Radius'].default_value = 0.012
        circ_fil.inputs['Resolution'].default_value = 5
        # Mesh line already IS a mesh - convert to curve then sweep
        m2c_fil = _node(tree, 'GeometryNodeMeshToCurve', (x+2200, 400))
        _link(tree, set_fil.outputs['Geometry'], m2c_fil.inputs['Mesh'])
        c2m_fil = _node(tree, 'GeometryNodeCurveToMesh', (x+2400, 400))
        _link(tree, m2c_fil.outputs['Curve'],    c2m_fil.inputs['Curve'])
        _link(tree, circ_fil.outputs['Curve'],   c2m_fil.inputs['Profile Curve'])
        color_node(c2m_fil, "organic")

        join_cw = _node(tree, 'GeometryNodeJoinGeometry', (x+2700, 0))
        _link(tree, real_cw.outputs['Geometry'],   join_cw.inputs['Geometry'])
        _link(tree, c2m_fil.outputs['Mesh'],       join_cw.inputs['Geometry'])
        color_node(join_cw, "output")

        return join_cw.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: MÖBIUS CATHEDRAL
    # Full Möbius strip cathedral - single-sided surface, extruded into
    # a thick band with gothic arches instanced along the loop.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cosmic_web")
    return tree, gin, gout

register_builder(
    "MEL_cosmic_web", build_cosmic_web_group,
    "Cosmic Web", "Experimental builder (absorbed from monolith build_cosmic_web).",
    category="experimental")


def build_mobius_cathedral_group(group_name="MEL_mobius_cathedral"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        import bmesh as _bmc

        x = -200
        segs_m = max(64, PROPS.complexity_level * 32)
        R_m = PROPS.base_radius * 1.5
        width_m = PROPS.height * 0.3

        mesh_m = bpy.data.meshes.new("MobiusBand_Mesh")
        bm_m = _bmc.new()
        rings_m = []

        for i in range(segs_m + 1):
            t = i / segs_m
            angle = t * 2 * math.pi
            twist = t * math.pi  # half-twist for Möbius

            cx = R_m * math.cos(angle)
            cy = R_m * math.sin(angle)

            # Local frame twisted around the loop
            nx = -math.sin(angle)
            ny =  math.cos(angle)
            bz_x = math.cos(twist) * 0.0 - math.sin(twist) * 1.0  # Z in twisted frame
            bz_y = 0.0
            bz_z = math.cos(twist)
            bx_x = math.cos(twist)
            bx_y = math.sin(twist) * math.cos(angle) * 0.3
            bx_z = -math.sin(twist)

            ring_m = []
            for j in range(3):  # 3 verts across the band width
                s = (j / 2.0 - 0.5) * width_m
                px = cx + bx_x * s; py = cy + bx_y * s + ny * 0
                pz = bx_z * s
                ring_m.append(bm_m.verts.new((px, py, pz)))
            rings_m.append(ring_m)

        # Stitch (note: last ring connects back to first with flip for Möbius)
        for i in range(segs_m):
            r0 = rings_m[i]; r1 = rings_m[i+1]
            if i < segs_m - 1:
                bm_m.faces.new([r0[0], r0[1], r1[1], r1[0]])
                bm_m.faces.new([r0[1], r0[2], r1[2], r1[1]])
            else:
                # Möbius closure: flip the end ring
                bm_m.faces.new([r0[0], r0[1], rings_m[0][1], rings_m[0][2]])
                bm_m.faces.new([r0[1], r0[2], rings_m[0][0], rings_m[0][1]])

        bm_m.normal_update()
        bm_m.to_mesh(mesh_m)
        bm_m.free()
        mesh_m.update()

        mob_obj = bpy.data.objects.new("__MobiusBand__", mesh_m)
        bpy.context.collection.objects.link(mob_obj)
        mob_obj.hide_render = True; mob_obj.hide_viewport = True

        obj_info_m = _node(tree, 'GeometryNodeObjectInfo', (x, 0))
        obj_info_m.transform_space = 'RELATIVE'
        obj_info_m.inputs['Object'].default_value = mob_obj
        color_node(obj_info_m, "penrose")

        subd_m = _node(tree, 'GeometryNodeSubdivisionSurface', (x+300, 0))
        subd_m.inputs['Level'].default_value = min(2, PROPS.complexity_level - 1)
        _link(tree, obj_info_m.outputs['Geometry'], subd_m.inputs['Mesh'])

        # Distribute arch instances along the Möbius band
        pts_m = _node(tree, 'GeometryNodeDistributePointsOnFaces', (x+600, 0))
        pts_m.distribute_method = 'POISSON'
        pts_m.inputs['Distance Min'].default_value  = 0.5
        pts_m.inputs['Density Max'].default_value   = PROPS.complexity_level * 0.4
        pts_m.inputs['Seed'].default_value          = PROPS.seed
        _link(tree, subd_m.outputs['Mesh'], pts_m.inputs['Mesh'])

        # Tiny arch cross-section
        arch_base = _node(tree, 'GeometryNodeMeshCircle', (x+600, -400))
        arch_base.inputs['Vertices'].default_value = 16
        arch_base.inputs['Radius'].default_value   = 0.1
        arch_base.fill_type = 'NGON'

        inst_m = _node(tree, 'GeometryNodeInstanceOnPoints', (x+900, 0))
        _link(tree, pts_m.outputs['Points'],     inst_m.inputs['Points'])
        _link(tree, pts_m.outputs['Normal'],     inst_m.inputs['Rotation'])
        _link(tree, arch_base.outputs['Mesh'],   inst_m.inputs['Instance'])
        real_m = _node(tree, 'GeometryNodeRealizeInstances', (x+1200, 0))
        _link(tree, inst_m.outputs['Instances'], real_m.inputs['Geometry'])

        join_m = _node(tree, 'GeometryNodeJoinGeometry', (x+1500, 0))
        _link(tree, subd_m.outputs['Mesh'],      join_m.inputs['Geometry'])
        _link(tree, real_m.outputs['Geometry'],  join_m.inputs['Geometry'])
        color_node(join_m, "output")
        return join_m.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: SEIFERT SURFACE (knot complement)
    # Seifert surface of the trefoil knot - orientable surface bounded
    # by the knot, built parametrically.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_mobius_cathedral")
    return tree, gin, gout

register_builder(
    "MEL_mobius_cathedral", build_mobius_cathedral_group,
    "Mobius Cathedral", "Experimental builder (absorbed from monolith build_mobius_cathedral).",
    category="experimental")


def build_seifert_surface_group(group_name="MEL_seifert_surface"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        import bmesh as _bks

        x = -200
        segs_s = max(32, PROPS.complexity_level * 16)
        segs_t_s = max(16, PROPS.complexity_level * 8)
        R_s = PROPS.base_radius

        mesh_s = bpy.data.meshes.new("SeifertSurface")
        bm_s = _bks.new()
        verts_s = {}

        def seifert_pos(u, v):
            # Trefoil Seifert surface - Milnor fibre parametrization
            # (u = fiber angle 0..2π, v = radial 0..1)
            phi = u * 3  # three-fold symmetry for trefoil
            r_f = R_s * (0.3 + v * 0.7)
            # Embed: fiber bundle over S1, fiber = disk
            x_s = r_f * math.cos(phi) * math.cos(u) - R_s * math.sin(phi) * math.sin(u)
            y_s = r_f * math.cos(phi) * math.sin(u) + R_s * math.sin(phi) * math.cos(u)
            z_s = r_f * math.sin(phi) * PROPS.height * 0.25
            return (x_s, y_s, z_s)

        for iu in range(segs_s):
            for iv in range(segs_t_s + 1):
                u = 2 * math.pi * iu / segs_s
                v = iv / segs_t_s
                verts_s[(iu, iv)] = bm_s.verts.new(seifert_pos(u, v))

        for iu in range(segs_s):
            for iv in range(segs_t_s):
                v00 = verts_s[(iu, iv)]
                v10 = verts_s[((iu+1) % segs_s, iv)]
                v11 = verts_s[((iu+1) % segs_s, iv+1)]
                v01 = verts_s[(iu, iv+1)]
                try:
                    bm_s.faces.new([v00, v10, v11, v01])
                except Exception:
                    pass

        bm_s.normal_update(); bm_s.to_mesh(mesh_s); bm_s.free(); mesh_s.update()
        seifert_obj = bpy.data.objects.new("__SeifertSurf__", mesh_s)
        bpy.context.collection.objects.link(seifert_obj)
        seifert_obj.hide_render = True; seifert_obj.hide_viewport = True

        oi_s = _node(tree, 'GeometryNodeObjectInfo', (x, 0))
        oi_s.transform_space = 'RELATIVE'
        oi_s.inputs['Object'].default_value = seifert_obj
        color_node(oi_s, "fractal")

        subd_s = _node(tree, 'GeometryNodeSubdivisionSurface', (x+300, 0))
        subd_s.inputs['Level'].default_value = min(2, PROPS.complexity_level - 1)
        _link(tree, oi_s.outputs['Geometry'], subd_s.inputs['Mesh'])

        # Noise ride on top for texture
        pos_s = _node(tree, 'GeometryNodeInputPosition', (x+300, -400))
        noise_s = _node(tree, 'ShaderNodeTexNoise', (x+500, -400))
        noise_s.inputs['Scale'].default_value     = 3.0
        noise_s.inputs['Detail'].default_value    = 5.0
        noise_s.inputs['Roughness'].default_value = 0.55
        _link(tree, pos_s.outputs['Position'], noise_s.inputs['Vector'])
        mul_s = _node(tree, 'ShaderNodeVectorMath', (x+750, -400))
        mul_s.operation = 'MULTIPLY'
        mul_s.inputs[1].default_value = (PROPS.flow_amount * 0.1,) * 3
        _link(tree, noise_s.outputs['Color'], mul_s.inputs[0])
        set_s = _node(tree, 'GeometryNodeSetPosition', (x+600, 0))
        _link(tree, subd_s.outputs['Mesh'],  set_s.inputs['Geometry'])
        _link(tree, mul_s.outputs['Vector'], set_s.inputs['Offset'])
        color_node(set_s, "deform")
        return set_s.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: FIELD SCULPTURE (Field at Index + proximity field)
    # Uses Index of Nearest + Field at Index to create a distance-driven
    # sculptural displacement based on control point attraction.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_seifert_surface")
    return tree, gin, gout

register_builder(
    "MEL_seifert_surface", build_seifert_surface_group,
    "Seifert Surface", "Experimental builder (absorbed from monolith build_seifert_surface).",
    category="experimental")


def build_field_sculpture_group(group_name="MEL_field_sculpture"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        x = -200
        R_f = PROPS.base_radius
        segs_f = max(8, PROPS.complexity_level * 4)

        # High-res base UV sphere
        uv_f = _node(tree, 'GeometryNodeMeshUVSphere', (x, 0))
        uv_f.inputs['Segments'].default_value = segs_f * 6
        uv_f.inputs['Rings'].default_value    = segs_f * 3
        uv_f.inputs['Radius'].default_value   = R_f
        color_node(uv_f, "organic")

        subd_f = _node(tree, 'GeometryNodeSubdivisionSurface', (x+250, 0))
        subd_f.inputs['Level'].default_value = min(2, PROPS.complexity_level - 1)
        _link(tree, uv_f.outputs['Mesh'], subd_f.inputs['Mesh'])

        # Control points - a small set of attractor points
        ctrl_line = _node(tree, 'GeometryNodeMeshLine', (x, -500))
        ctrl_line.mode = 'OFFSET'
        ctrl_line.inputs['Count'].default_value          = max(3, PROPS.recursion_depth)
        ctrl_line.inputs['Offset'].default_value         = (0, 0, R_f * 0.7)
        ctrl_line.inputs['Start Location'].default_value = (0, R_f * 0.4, -R_f * 0.3)
        color_node(ctrl_line, "input")

        # Noise shift on control points
        pos_ctrl = _node(tree, 'GeometryNodeInputPosition', (x+200, -800))
        noise_ctrl = _node(tree, 'ShaderNodeTexNoise', (x+400, -800))
        noise_ctrl.inputs['Scale'].default_value = 0.8
        noise_ctrl.inputs['Detail'].default_value = 3.0
        _link(tree, pos_ctrl.outputs['Position'], noise_ctrl.inputs['Vector'])
        mul_ctrl = _node(tree, 'ShaderNodeVectorMath', (x+650, -800))
        mul_ctrl.operation = 'MULTIPLY'
        mul_ctrl.inputs[1].default_value = (R_f * PROPS.variation_intensity,) * 3
        _link(tree, noise_ctrl.outputs['Color'], mul_ctrl.inputs[0])
        set_ctrl = _node(tree, 'GeometryNodeSetPosition', (x+300, -500))
        _link(tree, ctrl_line.outputs['Mesh'], set_ctrl.inputs['Geometry'])
        _link(tree, mul_ctrl.outputs['Vector'], set_ctrl.inputs['Offset'])
        color_node(set_ctrl, "deform")

        # Index of Nearest - find nearest control point for each sphere vertex
        idx_near = _node(tree, 'GeometryNodeIndexOfNearest', (x+700, 0))
        # We use Position as the element to search with
        pos_sphere = _node(tree, 'GeometryNodeInputPosition', (x+500, -200))
        _link(tree, pos_sphere.outputs['Position'], idx_near.inputs['Position'])
        # (Index Of Nearest needs the target's positions; feed ctrl geometry)
        color_node(idx_near, "input")

        # Field at Index - retrieve the control point position for the nearest
        fai = _node(tree, 'GeometryNodeFieldAtIndex', (x+1000, 0))
        fai.domain    = 'POINT'
        fai.data_type = 'FLOAT_VECTOR'
        _link(tree, idx_near.outputs['Index'], fai.inputs['Index'])
        pos_ctrl2 = _node(tree, 'GeometryNodeInputPosition', (x+700, -400))
        _link(tree, pos_ctrl2.outputs['Position'], fai.inputs['Value'])
        color_node(fai, "input")

        # Compute pull vector: (ctrl_pos - sphere_pos) * attraction
        vsub = _node(tree, 'ShaderNodeVectorMath', (x+1300, 0))
        vsub.operation = 'SUBTRACT'
        _link(tree, fai.outputs['Value'],           vsub.inputs[0])
        _link(tree, pos_sphere.outputs['Position'], vsub.inputs[1])

        # Scale by attraction factor
        vmul = _node(tree, 'ShaderNodeVectorMath', (x+1550, 0))
        vmul.operation = 'MULTIPLY'
        vmul.inputs[1].default_value = (PROPS.flow_amount * 0.25,) * 3
        _link(tree, vsub.outputs['Vector'], vmul.inputs[0])

        set_f = _node(tree, 'GeometryNodeSetPosition', (x+1800, 0))
        _link(tree, subd_f.outputs['Mesh'],    set_f.inputs['Geometry'])
        _link(tree, vmul.outputs['Vector'],    set_f.inputs['Offset'])
        color_node(set_f, "deform")

        return set_f.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: WEAVE SURFACE (UV Surface sampling + curve sweep)
    # Uses Sample UV Surface + Curve to Mesh for an architectural weave.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_field_sculpture")
    return tree, gin, gout

register_builder(
    "MEL_field_sculpture", build_field_sculpture_group,
    "Field Sculpture", "Experimental builder (absorbed from monolith build_field_sculpture).",
    category="experimental")


def build_weave_surface_group(group_name="MEL_weave_surface"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        x = -200
        R_w = PROPS.base_radius
        n_strands = max(4, PROPS.complexity_level * 3)

        pieces_w = []

        # Base surface - cylinder
        cyl_w = _node(tree, 'GeometryNodeMeshCylinder', (x, 0))
        cyl_w.inputs['Vertices'].default_value  = 32
        cyl_w.inputs['Radius'].default_value    = R_w
        cyl_w.inputs['Depth'].default_value     = PROPS.height
        cyl_w.inputs['Side Segments'].default_value = 24
        color_node(cyl_w, "tower")

        # UV sphere as sampling surface
        uvsph_w = _node(tree, 'GeometryNodeMeshUVSphere', (x, -400))
        uvsph_w.inputs['Segments'].default_value = 32
        uvsph_w.inputs['Rings'].default_value    = 16
        uvsph_w.inputs['Radius'].default_value   = R_w * 1.02

        for strand_i in range(n_strands):
            offset_u = strand_i / n_strands

            # Parametric curve along the cylinder surface (UV-space spiral)
            spline_crv = _node(tree, 'GeometryNodeCurvePrimitiveLine', (x+400, strand_i * 150))
            spline_crv.inputs['Start'].default_value = (0, 0, -PROPS.height * 0.5)
            spline_crv.inputs['End'].default_value   = (0, 0,  PROPS.height * 0.5)

            res_w = _node(tree, 'GeometryNodeResampleCurve', (x+650, strand_i * 150))
            try: res_w.mode = 'Count'
            except (AttributeError, TypeError):
                try: res_w.inputs['Mode'].default_value = 'Count'
                except Exception: pass
            res_w.inputs['Count'].default_value = 64
            _link(tree, spline_crv.outputs['Curve'], res_w.inputs['Curve'])

            # Spline parameter for UV
            sp_w = _node(tree, 'GeometryNodeSplineParameter', (x+650, strand_i*150 - 200))
            mul_w = _node(tree, 'ShaderNodeMath', (x+850, strand_i*150 - 200))
            mul_w.operation = 'ADD'
            mul_w.inputs[1].default_value = offset_u
            _link(tree, sp_w.outputs['Factor'], mul_w.inputs[0])
            ang_w = _node(tree, 'ShaderNodeMath', (x+1050, strand_i*150 - 200))
            ang_w.operation = 'MULTIPLY'
            ang_w.inputs[1].default_value = math.tau * PROPS.recursion_depth
            _link(tree, mul_w.outputs['Value'], ang_w.inputs[0])

            cos_w = _node(tree, 'ShaderNodeMath', (x+1250, strand_i*150 - 100))
            cos_w.operation = 'COSINE'
            sin_w = _node(tree, 'ShaderNodeMath', (x+1250, strand_i*150 - 300))
            sin_w.operation = 'SINE'
            _link(tree, ang_w.outputs['Value'], cos_w.inputs[0])
            _link(tree, ang_w.outputs['Value'], sin_w.inputs[0])

            # Sample UV surface at this angle/height
            suvs = _node(tree, 'GeometryNodeSampleUVSurface', (x+1500, strand_i * 150))
            suvs.data_type = 'FLOAT_VECTOR'
            uv_x = _node(tree, 'ShaderNodeCombineXYZ', (x+1300, strand_i*150-400))
            _link(tree, cos_w.outputs['Value'], uv_x.inputs['X'])
            _link(tree, sin_w.outputs['Value'], uv_x.inputs['Y'])
            _link(tree, uvsph_w.outputs['Mesh'],    suvs.inputs['Mesh'])
            _link(tree, uv_x.outputs['Vector'],     suvs.inputs['Sample UV'])
            pos_uvsph = _node(tree, 'GeometryNodeInputPosition', (x+1200, strand_i*150-600))
            _link(tree, pos_uvsph.outputs['Position'], suvs.inputs['Value'])
            color_node(suvs, "deform")

            # Set curve positions to sampled surface positions
            set_w = _node(tree, 'GeometryNodeSetPosition', (x+1800, strand_i * 150))
            _link(tree, res_w.outputs['Curve'],    set_w.inputs['Geometry'])
            _link(tree, suvs.outputs['Value'],     set_w.inputs['Position'])
            color_node(set_w, "deform")

            # Sweep thin tube profile
            circ_w = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (x+1800, strand_i*150 - 300))
            circ_w.inputs['Radius'].default_value     = 0.02 * R_w
            circ_w.inputs['Resolution'].default_value = 6
            c2m_w = _node(tree, 'GeometryNodeCurveToMesh', (x+2100, strand_i * 150))
            _link(tree, set_w.outputs['Geometry'], c2m_w.inputs['Curve'])
            _link(tree, circ_w.outputs['Curve'],   c2m_w.inputs['Profile Curve'])
            pieces_w.append(c2m_w.outputs['Mesh'])
            color_node(c2m_w, "tracery")

        join_w = _node(tree, 'GeometryNodeJoinGeometry', (x+2500, 0))
        for p in pieces_w:
            _link(tree, p, join_w.inputs['Geometry'])
        color_node(join_w, "output")
        return join_w.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: TESSELLATION TOWER (Penrose-like tiling extrusion)
    # Named attributes mark tile type; per-face height driven by voronoi.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_weave_surface")
    return tree, gin, gout

register_builder(
    "MEL_weave_surface", build_weave_surface_group,
    "Weave Surface", "Experimental builder (absorbed from monolith build_weave_surface).",
    category="experimental")


def build_tessellation_tower_group(group_name="MEL_tessellation_tower"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        x = -200
        R_tt = PROPS.base_radius
        segs_tt = max(6, PROPS.complexity_level * 4)
        layers_tt = max(2, PROPS.recursion_depth)

        pieces_tt = []
        for layer in range(layers_tt):
            frac = layer / layers_tt
            z_base = -PROPS.height * 0.5 + PROPS.height * frac
            z_top  = z_base + PROPS.height / layers_tt

            # Rotated grid per layer for interlocking effect
            rot = math.pi * frac * PROPS.twist_angle / max(1, layers_tt)
            grid_tt = _node(tree, 'GeometryNodeMeshGrid', (x, layer * 300))
            grid_tt.inputs['Size X'].default_value = R_tt * 2
            grid_tt.inputs['Size Y'].default_value = R_tt * 2
            grid_tt.inputs['Vertices X'].default_value = segs_tt
            grid_tt.inputs['Vertices Y'].default_value = segs_tt
            color_node(grid_tt, "modular")

            # Rotate and lift the grid
            tfm_tt = _node(tree, 'GeometryNodeTransform', (x+250, layer * 300))
            tfm_tt.inputs['Translation'].default_value = (0, 0, z_base)
            tfm_tt.inputs['Rotation'].default_value    = (0, 0, rot)
            _link(tree, grid_tt.outputs['Mesh'], tfm_tt.inputs['Geometry'])

            # Voronoi texture drives per-face extrusion height
            pos_tt = _node(tree, 'GeometryNodeInputPosition', (x+250, layer*300 - 300))
            vor_tt = _node(tree, 'ShaderNodeTexVoronoi', (x+450, layer*300 - 300))
            vor_tt.voronoi_dimensions = '3D'
            vor_tt.feature = 'F1'
            vor_tt.inputs['Scale'].default_value      = PROPS.wave_frequency * 1.2
            vor_tt.inputs['Randomness'].default_value = PROPS.variation_intensity
            _link(tree, pos_tt.outputs['Position'], vor_tt.inputs['Vector'])
            color_node(vor_tt, "noise")

            # Extrude faces by voronoi-driven height
            scale_v = _node(tree, 'ShaderNodeMath', (x+700, layer*300 - 300))
            scale_v.operation = 'MULTIPLY'
            scale_v.inputs[1].default_value = (z_top - z_base) * PROPS.height * 0.12
            _link(tree, vor_tt.outputs['Distance'], scale_v.inputs[0])

            extrude = _node(tree, 'GeometryNodeExtrudeMesh', (x+700, layer * 300))
            extrude.mode = 'FACES'
            extrude.inputs['Individual'].default_value = True
            _link(tree, tfm_tt.outputs['Geometry'], extrude.inputs['Mesh'])
            _link(tree, scale_v.outputs['Value'],   extrude.inputs['Offset Scale'])
            color_node(extrude, "tower")

            # Store tile ID as named attribute per face
            store_tt = _node(tree, 'GeometryNodeStoreNamedAttribute', (x+1000, layer * 300))
            store_tt.domain    = 'FACE'
            store_tt.data_type = 'FLOAT'
            store_tt.inputs['Name'].default_value = "tile_voronoi_dist"
            _link(tree, extrude.outputs['Mesh'],       store_tt.inputs['Geometry'])
            _link(tree, vor_tt.outputs['Distance'],    store_tt.inputs['Value'])
            color_node(store_tt, "input")

            pieces_tt.append(store_tt.outputs['Geometry'])

        join_tt = _node(tree, 'GeometryNodeJoinGeometry', (x+1300, 0))
        for p in pieces_tt:
            _link(tree, p, join_tt.inputs['Geometry'])
        color_node(join_tt, "output")
        return join_tt.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ONE-CLICK "COOL RANDOM STUFF" OPERATORS
    # ──────────────────────────────────────────────────────────────────────

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_tessellation_tower")
    return tree, gin, gout

register_builder(
    "MEL_tessellation_tower", build_tessellation_tower_group,
    "Tessellation Tower", "Experimental builder (absorbed from monolith build_tessellation_tower).",
    category="experimental")
def _impl_build_tower(tree, PROPS, base_x=-1400):
    cyl = tree.nodes.new('GeometryNodeMeshCylinder')
    cyl.location = (base_x, 0); color_node(cyl, "tower")
    cyl.inputs['Vertices'].default_value      = max(8, PROPS.complexity_level * 8)
    cyl.inputs['Side Segments'].default_value = max(2, PROPS.recursion_depth * 4)
    cyl.inputs['Fill Segments'].default_value = 1
    cyl.inputs['Radius'].default_value        = PROPS.base_radius
    cyl.inputs['Depth'].default_value         = PROPS.height

    geom = cyl.outputs['Mesh']
    geom = add_taper_chain(tree, geom, PROPS.height, PROPS.taper_ratio, x=base_x+300, y=-400)
    geom = add_twist(tree, geom, PROPS.twist_angle, PROPS.height, x=base_x+1600, y=-400)
    strength = PROPS.variation_intensity * 0.5 + PROPS.symmetry_break * 0.3
    geom = add_noise_displace(
        tree, geom,
        scale=1.5 + PROPS.complexity_level * 0.5,
        detail=float(PROPS.complexity_level),
        strength=strength,
        seed=PROPS.seed,
        x=base_x+2900, y=400,
    )
    return geom



def build_tower_group(group_name="MEL_tower"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        cyl = tree.nodes.new('GeometryNodeMeshCylinder')
        cyl.location = (base_x, 0); color_node(cyl, "tower")
        cyl.inputs['Vertices'].default_value      = max(8, PROPS.complexity_level * 8)
        cyl.inputs['Side Segments'].default_value = max(2, PROPS.recursion_depth * 4)
        cyl.inputs['Fill Segments'].default_value = 1
        cyl.inputs['Radius'].default_value        = PROPS.base_radius
        cyl.inputs['Depth'].default_value         = PROPS.height

        geom = cyl.outputs['Mesh']
        geom = add_taper_chain(tree, geom, PROPS.height, PROPS.taper_ratio, x=base_x+300, y=-400)
        geom = add_twist(tree, geom, PROPS.twist_angle, PROPS.height, x=base_x+1600, y=-400)
        strength = PROPS.variation_intensity * 0.5 + PROPS.symmetry_break * 0.3
        geom = add_noise_displace(
            tree, geom,
            scale=1.5 + PROPS.complexity_level * 0.5,
            detail=float(PROPS.complexity_level),
            strength=strength,
            seed=PROPS.seed,
            x=base_x+2900, y=400,
        )
        return geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_tower")
    return tree, gin, gout

register_builder(
    "MEL_tower", build_tower_group,
    "Tower", "Experimental builder (absorbed from monolith build_tower).",
    category="experimental")
def _impl_build_ogee_arch(tree, PROPS, base_x=-1400):
    """Iconic Venetian Gothic ogee arch with S-curve sides + finial pinnacle."""
    half_W = PROPS.ogee_width / 2
    H = PROPS.ogee_height
    rc, lc = _ogee_curve_pair(tree, half_W, H, PROPS.ogee_swell, PROPS.ogee_shoulder,
                               base_x=base_x, base_y=0)

    profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "ogee")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 8
    profile.inputs['Radius'].default_value = PROPS.gothic_thickness

    rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x+700, 200); color_node(rsw, "ogee")
    tree.links.new(rc, rsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], rsw.inputs['Profile Curve'])
    rsw.inputs['Fill Caps'].default_value = True

    lsw = tree.nodes.new('GeometryNodeCurveToMesh'); lsw.location = (base_x+700, -200); color_node(lsw, "ogee")
    tree.links.new(lc, lsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], lsw.inputs['Profile Curve'])
    lsw.inputs['Fill Caps'].default_value = True

    parts = [rsw.outputs['Mesh'], lsw.outputs['Mesh']]

    # Finial pinnacle at apex
    if PROPS.ogee_finial > 0.01:
        finial = tree.nodes.new('GeometryNodeMeshCone'); finial.location = (base_x, 600); color_node(finial, "ornament")
        finial.inputs['Vertices'].default_value = 16  # bumped from 8 in v2.31
        finial.inputs['Radius Top'].default_value = 0.0
        finial.inputs['Radius Bottom'].default_value = PROPS.ogee_finial * 0.3
        finial.inputs['Depth'].default_value = PROPS.ogee_finial

        ft = tree.nodes.new('GeometryNodeTransform'); ft.location = (base_x+300, 600)
        ft.inputs['Translation'].default_value = (0, 0, H + PROPS.ogee_finial / 2)
        tree.links.new(finial.outputs['Mesh'], ft.inputs['Geometry'])
        parts.append(ft.outputs['Geometry'])

    join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1000, 0); color_node(join, "output")
    for p in parts: tree.links.new(p, join.inputs['Geometry'])
    return join.outputs['Geometry']



def build_ogee_arch_group(group_name="MEL_ogee_arch"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Iconic Venetian Gothic ogee arch with S-curve sides + finial pinnacle."""
        half_W = PROPS.ogee_width / 2
        H = PROPS.ogee_height
        rc, lc = _ogee_curve_pair(tree, half_W, H, PROPS.ogee_swell, PROPS.ogee_shoulder,
                                   base_x=base_x, base_y=0)

        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "ogee")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 8
        profile.inputs['Radius'].default_value = PROPS.gothic_thickness

        rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x+700, 200); color_node(rsw, "ogee")
        tree.links.new(rc, rsw.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], rsw.inputs['Profile Curve'])
        rsw.inputs['Fill Caps'].default_value = True

        lsw = tree.nodes.new('GeometryNodeCurveToMesh'); lsw.location = (base_x+700, -200); color_node(lsw, "ogee")
        tree.links.new(lc, lsw.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], lsw.inputs['Profile Curve'])
        lsw.inputs['Fill Caps'].default_value = True

        parts = [rsw.outputs['Mesh'], lsw.outputs['Mesh']]

        # Finial pinnacle at apex
        if PROPS.ogee_finial > 0.01:
            finial = tree.nodes.new('GeometryNodeMeshCone'); finial.location = (base_x, 600); color_node(finial, "ornament")
            finial.inputs['Vertices'].default_value = 16  # bumped from 8 in v2.31
            finial.inputs['Radius Top'].default_value = 0.0
            finial.inputs['Radius Bottom'].default_value = PROPS.ogee_finial * 0.3
            finial.inputs['Depth'].default_value = PROPS.ogee_finial

            ft = tree.nodes.new('GeometryNodeTransform'); ft.location = (base_x+300, 600)
            ft.inputs['Translation'].default_value = (0, 0, H + PROPS.ogee_finial / 2)
            tree.links.new(finial.outputs['Mesh'], ft.inputs['Geometry'])
            parts.append(ft.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_ogee_arch")
    return tree, gin, gout

register_builder(
    "MEL_ogee_arch", build_ogee_arch_group,
    "Ogee Arch", "Experimental builder (absorbed from monolith build_ogee_arch).",
    category="experimental")


# 17 builders registered
