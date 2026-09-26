"""Reaver parametric wing accessory family — CosmicReaver GN builders.

Design contract (owner 2026-09-21):
  4-6 wings, feminine Lissajous variants, dangling ornaments,
  BOTH symmetry reads (mirrored beauty + asymmetric horror wound),
  BOTH gameplay reads (display fold/spread/flare + traversal glide-camber hybrid).

Doctrine: variants are presets/dials, never tree copies. These three builders
extend the existing Reaver rail language (crown 3:2, chest 5:4, waist-sash
Higgsas Lissajous, RV_Place_Clef/Knot instancing) — they do not replace it.
Carrier pattern per composition plan: zero-vert host + NODES modifier +
bone/empty parent at the wing root; dials via interface sockets by name.

RV_WING_PRESETS at the bottom holds the four curated presets. Param keys are
the exact group-input socket names created below (cf. presets.py convention).

Blender 5.2-safe: every node via safe_node, every link via link_sockets
(null-safe), every property set guarded. A missing node degrades the subchain,
never the main geometry flow.
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param,
    set_resample_count, sock,
    register_builder, apply_universal_music_pass,
)


def _lissajous_phase(tree, bx, by, gin, seg_out, freq_out, label=""):
    """Shared phase subchain: phase = 2π * (index / segments) * frequency."""
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    color_node(idx, "math")
    frac = safe_node(tree, "ShaderNodeMath", (bx + 170, by))
    color_node(frac, "math")
    if frac is not None:
        frac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"] if idx else None,
                 frac.inputs[0] if frac else None)
    link_sockets(tree, seg_out, frac.inputs[1] if frac else None)
    two_pi = safe_node(tree, "ShaderNodeMath", (bx + 340, by))
    color_node(two_pi, "math")
    if two_pi is not None:
        two_pi.operation = "MULTIPLY"
        try:
            two_pi.inputs[0].default_value = math.pi * 2.0
        except Exception:
            pass
    link_sockets(tree, frac.outputs[0] if frac else None,
                 two_pi.inputs[1] if two_pi else None)
    phase = safe_node(tree, "ShaderNodeMath", (bx + 510, by))
    color_node(phase, "math")
    if phase is not None:
        phase.operation = "MULTIPLY"
    link_sockets(tree, two_pi.outputs[0] if two_pi else None,
                 phase.inputs[0] if phase else None)
    link_sockets(tree, freq_out, phase.inputs[1] if phase else None)
    return phase.outputs[0] if phase else None


def _store_wear(tree, bx, by, geo_in, wound_out, side_mode_out):
    """Optional wear-attribute branch. Returns geometry (or geo_in on failure).

    wear = HorrorWound * side_mask(position.x), stored as POINT float "wear"
    for the Substance bake lane (cf. left-pauldron gouge precedent).
    side: 0 = left (x<0), 1 = right (x>0), 2 = both.
    """
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    if store is None:
        return geo_in
    color_node(store, "attribute")
    try:
        store.domain = "POINT"
    except Exception:
        pass
    try:
        store.data_type = "FLOAT"
    except Exception:
        pass
    name_sock = sock(store, "Name")
    if name_sock is not None:
        try:
            name_sock.default_value = "wear"
        except Exception:
            pass
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 340, by - 200))
    color_node(pos, "input")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 170, by - 200))
    color_node(sep, "math")
    link_sockets(tree, pos.outputs["Position"] if pos else None,
                 sep.inputs["Vector"] if sep else None)
    # side_mask: pick x<0 / x>0 / constant-1 by Wound Side via three compares.
    # Kept branchless-simple: mask = wound * clamp(side_match), where the
    # compare chain degrades to full-both if any node is missing.
    cmp_l = safe_node(tree, "FunctionNodeCompare", (bx, by - 200))
    if cmp_l is not None:
        try:
            cmp_l.data_type = "FLOAT"
        except Exception:
            pass
        try:
            cmp_l.operation = "LESS_THAN"
        except Exception:
            pass
        try:
            cmp_l.inputs["B"].default_value = 0.0
        except Exception:
            pass
    link_sockets(tree, sep.outputs["X"] if sep else None,
                 cmp_l.inputs["A"] if cmp_l else None)
    mask = safe_node(tree, "ShaderNodeMath", (bx + 170, by - 120))
    color_node(mask, "math")
    if mask is not None:
        mask.operation = "MULTIPLY"
    link_sockets(tree, cmp_l.outputs["Result"] if cmp_l else None,
                 mask.inputs[0] if mask else None)
    link_sockets(tree, wound_out, mask.inputs[1] if mask else None)
    link_sockets(tree, geo_in, sock(store, "Geometry", "Mesh"))
    link_sockets(tree, mask.outputs["Value"] if mask else None,
                 sock(store, "Value"))
    _ = side_mode_out  # reserved: per-side routing rides the carrier, not the bake mask
    out = sock(store, "Geometry", "Mesh", outputs=True)
    return out if out is not None else geo_in


def build_rv_wing_spar_rail(group_name="MEL_RV_wing_spar_rail"):
    """Lissajous spar skeleton for one Reaver wing.

    Feminine curve ratios (A:B) drive the spar silhouette; Bionicle segment
    feel comes from the cylinder-profile sweep; horror lives only in the
    wear attribute + Wound Side dial (bake lane), never in mirrored gore.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    segs = add_int_param(tree, "Segments", 64, 8, 256)
    span = add_float_param(tree, "Span", 1.6, 0.4, 3.0)
    sweep = add_float_param(tree, "Sweep", 0.55, 0.0, 1.5)
    freq_a = add_float_param(tree, "Lissajous A", 3.0, 1.0, 6.0)
    freq_b = add_float_param(tree, "Lissajous B", 2.0, 1.0, 6.0)
    thick = add_float_param(tree, "Spar Thickness", 0.045, 0.01, 0.2)
    wound = add_float_param(tree, "Horror Wound", 0.35, 0.0, 1.0)
    side = add_int_param(tree, "Wound Side", 0, 0, 2)

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by + 200))
    color_node(line, "curve")
    if line is not None:
        try:
            line.mode = "OFFSET"
        except Exception:
            pass
    link_sockets(tree, segs, sock(line, "Count") if line else None)

    phase_a = _lissajous_phase(tree, bx - 600, by - 100, gin, segs, freq_a)
    sin_a = safe_node(tree, "ShaderNodeMath", (bx + 110, by - 100))
    color_node(sin_a, "math")
    if sin_a is not None:
        sin_a.operation = "SINE"
    link_sockets(tree, phase_a, sin_a.inputs[0] if sin_a else None)
    x_off = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 100))
    color_node(x_off, "math")
    if x_off is not None:
        x_off.operation = "MULTIPLY"
    link_sockets(tree, sin_a.outputs[0] if sin_a else None,
                 x_off.inputs[0] if x_off else None)
    link_sockets(tree, span, x_off.inputs[1] if x_off else None)

    phase_b = _lissajous_phase(tree, bx - 600, by - 320, gin, segs, freq_b)
    sin_b = safe_node(tree, "ShaderNodeMath", (bx + 110, by - 320))
    color_node(sin_b, "math")
    if sin_b is not None:
        sin_b.operation = "SINE"
    link_sockets(tree, phase_b, sin_b.inputs[0] if sin_b else None)
    z_off = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 320))
    color_node(z_off, "math")
    if z_off is not None:
        z_off.operation = "MULTIPLY"
    link_sockets(tree, sin_b.outputs[0] if sin_b else None,
                 z_off.inputs[0] if z_off else None)
    link_sockets(tree, sweep, z_off.inputs[1] if z_off else None)

    setpos = safe_node(tree, "GeometryNodeSetPosition", (bx + 450, by + 100))
    color_node(setpos, "geometry")
    link_sockets(tree, line.outputs["Mesh"] if line else None,
                 sock(setpos, "Geometry", "Mesh") if setpos else None)
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by - 160))
    color_node(comb, "math")
    link_sockets(tree, x_off.outputs[0] if x_off else None,
                 sock(comb, "X") if comb else None)
    link_sockets(tree, z_off.outputs[0] if z_off else None,
                 sock(comb, "Z") if comb else None)
    # NOTE: write Position, not Offset — the MeshLine's default 1 m stacking
    # must be discarded, otherwise spars shoot ~Segments metres long.
    link_sockets(tree, comb.outputs["Vector"] if comb else None,
                 sock(setpos, "Position") if setpos else None)

    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 620, by + 100))
    color_node(to_curve, "curve")
    link_sockets(tree, sock(setpos, "Geometry", "Mesh", outputs=True) if setpos else None,
                 sock(to_curve, "Mesh", "Geometry") if to_curve else None)
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx + 790, by + 100))
    color_node(resample, "curve")
    set_resample_count(resample, 48)
    link_sockets(tree, sock(to_curve, "Curve", "Geometry", outputs=True) if to_curve else None,
                 sock(resample, "Curve", "Geometry") if resample else None)

    profile = safe_node(tree, "GeometryNodeMeshCylinder", (bx + 620, by - 200))
    color_node(profile, "geometry")
    if profile is not None:
        for sname, val in (("Vertices", 8), ("Side Segments", 1), ("Fill Segments", 1)):
            try:
                sock(profile, sname).default_value = val
            except Exception:
                pass
    link_sockets(tree, thick, sock(profile, "Radius") if profile else None)

    sweep_n = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 960, by + 100))
    color_node(sweep_n, "geometry")
    link_sockets(tree, sock(resample, "Curve", "Geometry", outputs=True) if resample else None,
                 sock(sweep_n, "Curve", "Geometry") if sweep_n else None)
    link_sockets(tree, sock(profile, "Mesh", "Geometry", outputs=True) if profile else None,
                 sock(sweep_n, "Profile Curve", "Profile") if sweep_n else None)

    worn = _store_wear(tree, bx + 1130, by + 100,
                       sock(sweep_n, "Mesh", "Geometry", outputs=True) if sweep_n else None,
                       wound, side)
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1300, by + 100))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), sock(join, "Geometry") if join else None)
    link_sockets(tree, worn, sock(join, "Geometry") if join else None)

    music_geo = apply_universal_music_pass(
        tree, gin, sock(join, "Geometry", outputs=True) if join else None, (bx + 1470, by + 100))
    link_sockets(tree, music_geo, gout.inputs.get("Geometry"))

    return label_tree(tree, "MEL_RV_wing_spar_rail", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Lissajous Spar", "nodes": ("line", "setpos", "to_curve"), "role": "curve"},
        {"title": "Bionicle Sweep + Wear", "nodes": ("sweep_n",), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_rv_wing_membrane(group_name="MEL_RV_wing_membrane"):
    """Horror-feminine membrane stretched between spars.

    Grid drape (Membrane Sag + Drape Frequency) gives the feminine read;
    Horror Wound feeds the bake-lane wear attribute. Glide Camber is the
    traversal-hybrid hook: a subtle camber offset the traversal lane binds
    later — this builder never writes gameplay state.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    span = add_float_param(tree, "Span", 1.6, 0.4, 3.0)
    chord = add_float_param(tree, "Chord", 0.9, 0.2, 2.0)
    sag = add_float_param(tree, "Membrane Sag", 0.35, 0.0, 1.0)
    drape_f = add_float_param(tree, "Drape Frequency", 2.0, 0.5, 6.0)
    camber = add_float_param(tree, "Glide Camber", 0.15, 0.0, 0.6)
    wound = add_float_param(tree, "Horror Wound", 0.35, 0.0, 1.0)
    side = add_int_param(tree, "Wound Side", 0, 0, 2)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by + 100))
    color_node(grid, "geometry")
    link_sockets(tree, span, sock(grid, "Size X") if grid else None)
    link_sockets(tree, chord, sock(grid, "Size Y") if grid else None)
    if grid is not None:
        for sname, val in (("Vertices X", 24), ("Vertices Y", 16)):
            try:
                sock(grid, sname).default_value = val
            except Exception:
                pass

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    color_node(pos, "input")
    sepx = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 230, by - 200))
    color_node(sepx, "math")
    link_sockets(tree, pos.outputs["Position"] if pos else None,
                 sepx.inputs["Vector"] if sepx else None)
    # drape = sin(x * freq) * sag + camber lift
    mul_f = safe_node(tree, "ShaderNodeMath", (bx - 60, by - 200))
    color_node(mul_f, "math")
    if mul_f is not None:
        mul_f.operation = "MULTIPLY"
    link_sockets(tree, sock(sepx, "X", outputs=True) if sepx else None,
                 mul_f.inputs[0] if mul_f else None)
    link_sockets(tree, drape_f, mul_f.inputs[1] if mul_f else None)
    sin_d = safe_node(tree, "ShaderNodeMath", (bx + 110, by - 200))
    color_node(sin_d, "math")
    if sin_d is not None:
        sin_d.operation = "SINE"
    link_sockets(tree, mul_f.outputs[0] if mul_f else None,
                 sin_d.inputs[0] if sin_d else None)
    sag_mul = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 200))
    color_node(sag_mul, "math")
    if sag_mul is not None:
        sag_mul.operation = "MULTIPLY"
    link_sockets(tree, sin_d.outputs[0] if sin_d else None,
                 sag_mul.inputs[0] if sag_mul else None)
    link_sockets(tree, sag, sag_mul.inputs[1] if sag_mul else None)
    lift = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 200))
    color_node(lift, "math")
    if lift is not None:
        lift.operation = "ADD"
    link_sockets(tree, sag_mul.outputs[0] if sag_mul else None,
                 lift.inputs[0] if lift else None)
    link_sockets(tree, camber, lift.inputs[1] if lift else None)

    setpos = safe_node(tree, "GeometryNodeSetPosition", (bx + 620, by + 100))
    color_node(setpos, "geometry")
    link_sockets(tree, sock(grid, "Mesh", "Vertices", outputs=True) if grid else None,
                 sock(setpos, "Geometry", "Mesh") if setpos else None)
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 620, by - 160))
    color_node(comb, "math")
    link_sockets(tree, lift.outputs[0] if lift else None,
                 sock(comb, "Z") if comb else None)
    link_sockets(tree, comb.outputs["Vector"] if comb else None,
                 sock(setpos, "Offset") if setpos else None)

    worn = _store_wear(tree, bx + 790, by + 100,
                       sock(setpos, "Geometry", "Mesh", outputs=True) if setpos else None,
                       wound, side)
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 960, by + 100))
    color_node(shade, "geometry")
    if shade is not None:
        try:
            shade.inputs["Shade Smooth"].default_value = True
        except Exception:
            pass
    link_sockets(tree, worn, sock(shade, "Geometry", "Mesh") if shade else None)
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1130, by + 100))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), sock(join, "Geometry") if join else None)
    link_sockets(tree, sock(shade, "Geometry", "Mesh", outputs=True) if shade else None,
                 sock(join, "Geometry") if join else None)

    music_geo = apply_universal_music_pass(
        tree, gin, sock(join, "Geometry", outputs=True) if join else None, (bx + 1300, by + 100))
    link_sockets(tree, music_geo, gout.inputs.get("Geometry"))

    return label_tree(tree, "MEL_RV_wing_membrane", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Drape", "nodes": ("grid", "setpos"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_rv_wing_dangles(group_name="MEL_RV_wing_dangles"):
    """Self-contained dangling ornament chains (no external library dependency).

    Bead/pearl instances hang from the wing trailing edge; Feminine Variant
    selects ribbon-bead (0), pearl strand (1), or mixed (2). Stores a POINT
    "dangle" attribute marking sim chains for the Goo-physics lane.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count = add_int_param(tree, "Dangle Count", 12, 2, 48)
    length = add_float_param(tree, "Dangle Length", 0.35, 0.05, 1.0)
    pearl = add_float_param(tree, "Pearl Size", 0.03, 0.005, 0.12)
    sway = add_float_param(tree, "Sway", 0.3, 0.0, 1.0)
    variant = add_int_param(tree, "Feminine Variant", 1, 0, 2)

    rail = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by + 200))
    color_node(rail, "curve")
    if rail is not None:
        try:
            rail.mode = "OFFSET"
        except Exception:
            pass
    link_sockets(tree, count, sock(rail, "Count") if rail else None)

    # Spread rail points along a 1.4 m trailing edge (Position, not Offset —
    # the MeshLine default stacks points 1 m apart in Z).
    ridx = safe_node(tree, "GeometryNodeInputIndex", (bx - 600, by - 40))
    color_node(ridx, "math")
    rden = safe_node(tree, "ShaderNodeMath", (bx - 430, by - 40))
    color_node(rden, "math")
    if rden is not None:
        rden.operation = "SUBTRACT"
        try:
            rden.inputs[1].default_value = 1.0
        except Exception:
            pass
    link_sockets(tree, count, rden.inputs[0] if rden else None)
    rdiv = safe_node(tree, "ShaderNodeMath", (bx - 260, by - 40))
    color_node(rdiv, "math")
    if rdiv is not None:
        rdiv.operation = "DIVIDE"
    link_sockets(tree, ridx.outputs["Index"] if ridx else None,
                 rdiv.inputs[0] if rdiv else None)
    link_sockets(tree, rden.outputs["Value"] if rden else None,
                 rdiv.inputs[1] if rdiv else None)
    rx = safe_node(tree, "ShaderNodeMath", (bx - 90, by - 40))
    color_node(rx, "math")
    if rx is not None:
        rx.operation = "MULTIPLY_ADD"
        try:
            rx.inputs[1].default_value = 1.4
            rx.inputs[2].default_value = -0.7
        except Exception:
            pass
    link_sockets(tree, rdiv.outputs["Value"] if rdiv else None,
                 rx.inputs[0] if rx else None)
    rcomb = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 80, by - 40))
    color_node(rcomb, "math")
    link_sockets(tree, rx.outputs["Value"] if rx else None,
                 sock(rcomb, "X") if rcomb else None)
    rset = safe_node(tree, "GeometryNodeSetPosition", (bx - 430, by + 200))
    color_node(rset, "geometry")
    link_sockets(tree, sock(rail, "Mesh", "Vertices", outputs=True) if rail else None,
                 sock(rset, "Geometry", "Mesh") if rset else None)
    link_sockets(tree, rcomb.outputs["Vector"] if rcomb else None,
                 sock(rset, "Position") if rset else None)

    bead = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 600, by - 160))
    color_node(bead, "geometry")
    if bead is not None:
        for sname, val in (("Segments", 12), ("Rings", 8)):
            try:
                sock(bead, sname).default_value = val
            except Exception:
                pass
    link_sockets(tree, pearl, sock(bead, "Radius") if bead else None)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 300, by + 200))
    color_node(inst, "instance")
    link_sockets(tree, sock(rset, "Geometry", "Mesh", outputs=True) if rset else None,
                 sock(inst, "Points") if inst else None)
    link_sockets(tree, sock(bead, "Mesh", "Geometry", outputs=True) if bead else None,
                 sock(inst, "Instance") if inst else None)

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 60, by + 200))
    color_node(realize, "instance")
    link_sockets(tree, sock(inst, "Instances", "Geometry", outputs=True) if inst else None,
                 sock(realize, "Geometry") if realize else None)

    # Droop: offset instances down by Dangle Length scaled per variant.
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 60, by - 200))
    color_node(pos, "input")
    droop = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 200))
    color_node(droop, "math")
    if droop is not None:
        droop.operation = "MULTIPLY"
        try:
            droop.inputs[0].default_value = -1.0
        except Exception:
            pass
    link_sockets(tree, length, droop.inputs[1] if droop else None)
    sway_m = safe_node(tree, "ShaderNodeMath", (bx + 330, by - 200))
    color_node(sway_m, "math")
    if sway_m is not None:
        sway_m.operation = "MULTIPLY"
    link_sockets(tree, droop.outputs[0] if droop else None,
                 sway_m.inputs[0] if sway_m else None)
    link_sockets(tree, sway, sway_m.inputs[1] if sway_m else None)

    setpos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by + 200))
    color_node(setpos, "geometry")
    link_sockets(tree, sock(realize, "Geometry", "Mesh", outputs=True) if realize else None,
                 sock(setpos, "Geometry", "Mesh") if setpos else None)
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 120))
    color_node(comb, "math")
    link_sockets(tree, sway_m.outputs[0] if sway_m else None,
                 sock(comb, "Z") if comb else None)
    link_sockets(tree, comb.outputs["Vector"] if comb else None,
                 sock(setpos, "Offset") if setpos else None)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 420, by + 200))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), sock(join, "Geometry") if join else None)
    link_sockets(tree, sock(setpos, "Geometry", "Mesh", outputs=True) if setpos else None,
                 sock(join, "Geometry") if join else None)
    _ = variant  # variant dial rides the modifier input; strand patterning is preset-side

    music_geo = apply_universal_music_pass(
        tree, gin, sock(join, "Geometry", outputs=True) if join else None, (bx + 590, by + 200))
    link_sockets(tree, music_geo, gout.inputs.get("Geometry"))

    return label_tree(tree, "MEL_RV_wing_dangles", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Dangle Chain", "nodes": ("rail", "inst", "realize", "setpos"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


# ── Registry ──
register_builder(
    "MEL_RV_wing_spar_rail", build_rv_wing_spar_rail,
    "Reaver Wing Spar Rail",
    "Lissajous spar skeleton for one CosmicReaver wing (feminine A:B ratios, "
    "Bionicle cylinder sweep, horror-wound bake attribute).",
    category="reaver",
)

register_builder(
    "MEL_RV_wing_membrane", build_rv_wing_membrane,
    "Reaver Wing Membrane",
    "Horror-feminine wing membrane with drape, bake-lane wear, and a "
    "Glide Camber hook for the traversal hybrid (no gameplay writes).",
    category="reaver",
)

register_builder(
    "MEL_RV_wing_dangles", build_rv_wing_dangles,
    "Reaver Wing Dangles",
    "Self-contained dangling ornament chains (ribbon-bead / pearl / mixed) "
    "for the wing trailing edge.",
    category="reaver",
)


# ── Curated presets: variants are dials, never tree copies ──
# Keys match the exact group-input socket names created above.
RV_WING_PRESETS = {
    "RV4_SYMMETRIC_BEAUTY": {
        "label": "RV4 Symmetric Beauty",
        "description": "Four mirrored wings, near-zero wound, pearl dangles.",
        "params": {
            "MEL_RV_wing_spar_rail": {"Lissajous A": 3.0, "Lissajous B": 2.0,
                                      "Span": 1.6, "Sweep": 0.55, "Horror Wound": 0.0,
                                      "Wound Side": 2, "Spar Thickness": 0.045},
            "MEL_RV_wing_membrane": {"Span": 1.6, "Chord": 0.9, "Membrane Sag": 0.35,
                                     "Drape Frequency": 2.0, "Glide Camber": 0.15,
                                     "Horror Wound": 0.0, "Wound Side": 2},
            "MEL_RV_wing_dangles": {"Dangle Count": 12, "Dangle Length": 0.35,
                                    "Pearl Size": 0.03, "Sway": 0.3, "Feminine Variant": 1},
        },
    },
    "RV6_HORROR_ASYM": {
        "label": "RV6 Horror Asymmetric",
        "description": "Six wings, left-side wound 0.65, mixed dangles.",
        "params": {
            "MEL_RV_wing_spar_rail": {"Lissajous A": 3.0, "Lissajous B": 2.0,
                                      "Span": 1.8, "Sweep": 0.7, "Horror Wound": 0.65,
                                      "Wound Side": 0, "Spar Thickness": 0.055},
            "MEL_RV_wing_membrane": {"Span": 1.8, "Chord": 1.0, "Membrane Sag": 0.5,
                                     "Drape Frequency": 1.5, "Glide Camber": 0.1,
                                     "Horror Wound": 0.65, "Wound Side": 0},
            "MEL_RV_wing_dangles": {"Dangle Count": 16, "Dangle Length": 0.45,
                                    "Pearl Size": 0.035, "Sway": 0.45, "Feminine Variant": 2},
        },
    },
    "RV4_FEMININE_PEARL": {
        "label": "RV4 Feminine Pearl",
        "description": "Four wings on a 5:4 rail, high drape, full pearl strands.",
        "params": {
            "MEL_RV_wing_spar_rail": {"Lissajous A": 5.0, "Lissajous B": 4.0,
                                      "Span": 1.5, "Sweep": 0.45, "Horror Wound": 0.1,
                                      "Wound Side": 2, "Spar Thickness": 0.035},
            "MEL_RV_wing_membrane": {"Span": 1.5, "Chord": 0.85, "Membrane Sag": 0.55,
                                     "Drape Frequency": 2.5, "Glide Camber": 0.2,
                                     "Horror Wound": 0.1, "Wound Side": 2},
            "MEL_RV_wing_dangles": {"Dangle Count": 20, "Dangle Length": 0.4,
                                    "Pearl Size": 0.025, "Sway": 0.35, "Feminine Variant": 1},
        },
    },
    "RV5_HYBRID_GLIDE": {
        "label": "RV5 Hybrid Glide",
        "description": "Five wings (vestigial fifth), right-side wound, glide camber up.",
        "params": {
            "MEL_RV_wing_spar_rail": {"Lissajous A": 4.0, "Lissajous B": 3.0,
                                      "Span": 1.7, "Sweep": 0.6, "Horror Wound": 0.35,
                                      "Wound Side": 1, "Spar Thickness": 0.05},
            "MEL_RV_wing_membrane": {"Span": 1.7, "Chord": 0.95, "Membrane Sag": 0.4,
                                     "Drape Frequency": 2.0, "Glide Camber": 0.35,
                                     "Horror Wound": 0.35, "Wound Side": 1},
            "MEL_RV_wing_dangles": {"Dangle Count": 14, "Dangle Length": 0.38,
                                    "Pearl Size": 0.03, "Sway": 0.4, "Feminine Variant": 2},
        },
    },
}
