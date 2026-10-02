"""MEL_horn_dangler_row — a row of danglers along a host curve (v4).

═══════════════════════════════════════════════════════════════════════════
HOW THE HORN LANE FEEDS THIS ROW (measured, 2026-10-01)
═══════════════════════════════════════════════════════════════════════════

The host curve for the sheep's horns is NOT the horn's centreline. It is a
baked SURFACE LOCUS + SOLVED HANG ANCHOR: `Tools/wardrobe_pipeline/horn_spine_snap.py`
snaps the horn's true centreline out of its own mesh (chord-midpoint snap; 1.0
inside fraction on both horns), then per station solves the drop that puts the
dangler clear of the horn while its loop stays near the surface, and bakes that
anchor into the curve's point positions. It also writes the solved
loop-to-surface GAP into each point's `radius`, which is what the chain stage
(P5) reads as its length.

Why the placement is baked instead of computed in the row:
  * `Curve to Points`' own `Normal` frame TWISTS on a helix — offsetting along
    it buried pearls (vertex-inside fractions up to 0.92 measured).
  * A legacy Curve datablock has NO `attributes` API in 5.2
    ("'Curve' object has no attribute 'attributes'"), so a true outward vector
    cannot ride along with the curve. Per-point values must be baked into the
    points (or the scalar `radius`, which does work).
  * A straight -Z drop does NOT leave a coil: the coil's cross-section plane
    contains the coil axis, so "down" from the rim walks around the tube.

So: Host Offset and Hang Drop stay 0 for the horn (the snapper carries the
placement) and remain useful for plain hosts.

═══════════════════════════════════════════════════════════════════════════
v1 -> v2 history (kept: it is why the gates below exist)
═══════════════════════════════════════════════════════════════════════════

v1 built cleanly, linked "cleanly", passed 17/18 gates, and emitted zero
renderable geometry:

  * The killer was a branch wired through TWO cross-domain links
    (`Mesh Line.Mesh -> Vector Math.Vector`, `Vector Math.Vector -> Mesh to
    Curve.Mesh`). Blender ACCEPTS those links at creation (so
    `core.link_failures()` stayed empty) and evaluates them as EMPTY.
  * The only live branch was a bare POINTS cloud — no faces, renders nothing,
    reads 0 through `to_mesh()`. "0 verts" was invisibility, not absence.
  * "Curve to Points is dead in 5.2" was a MEASUREMENT ARTIFACT: c2p(Count=9)
    instanced and realized emits exactly 9 x 482 = 4,338 verts.

v2 shape (proven): host curve -> CurveToPoints(Count) -> SetPosition(Offset =
Normal * Host Offset - Z * Hang Drop) -> Instance terminus -> Realize.
Proven numbers: terminus 1,322 verts; Count x terminus exactly (12 on a
2-spline spine -> 15,864).

v4 adds (all gated in horn_dangl_proof.py):
  * `Terminus` 0..3 — pearl / star / lace / bead house danglers (switch chain)
  * `Pearl Material` / `Trim Material` — MATERIAL sockets; with a terminus that
    exposes the per-part split they drive pearl vs cap+loop, otherwise the row
    falls back to ONE SetMaterial on the whole dangler
  * `Pearl Smooth` — subdivision level 1 on the terminus before instancing
  * `Chain Links` — a short chain segment instanced per host point, its length
    read from the host curve's baked `radius` (the solved loop-to-surface gap)
  * `Variation` + `Seed` — per-point size jitter (0 = off, seed-reproducible)
  * music passthrough: the row's house `Musical Amplitude` x `Music Influence`
    sockets modulate the uniform scale (E6)

Dials (neutral — defaults sit the dangler exactly on the host point):
    Count         int    danglers per host spline (CurveToPoints counts PER SPLINE)
    Host Offset   float  push along Normal — leave 0 for helix hosts (twist!)
    Hang Drop     float  drop below the host point (world -Z)
    Terminal Size float  uniform scale (1.0 = authored 33 mm terminus)
    Terminus      int    0 pearl, 1 star, 2 lace, 3 bead
    Chain Links   int    rings per dangler along the baked gap (0 = off)
    Pearl Smooth  bool   subdivide the terminus once before instancing
    Variation     float  per-point size jitter (+-Variation)
    Seed          int    jitter seed

Traps this module is written against:
  * GeometryNodeInputNormal is EMPTY on curve points — use CurveToPoints' OWN
    `Normal`.
  * Never wire a GEOMETRY socket into a VECTOR socket (or back): accepted,
    no failure recorded, evaluates EMPTY.
  * An unlinked Geometry input is a SILENT no-op, not an error.
  * ShaderNodeMath inputs[0] AND [1] both default to 0.5 — write BOTH operands.
  * A fresh CombineXYZ is (0,0,0) — every axis the dial affects must be written.

TERMINI ARE REUSED, NEVER REBUILT (all four come from `cute_decor`).
"""
from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)
from . import cute_decor

# The house pearl terminus's top loop sits at this local z (the pearl centre is
# the terminus origin). Measured: terminus z-span 0.033 = -0.012 (pearl bottom)
# .. +0.021 (loop top).
LOOP_TOP_Z = 0.019

# The chain segment is authored at this unit length and scaled to the baked gap.
CHAIN_UNIT = 0.006

# Terminus menu: index -> (key, cute_decor builder, tree name)
_TERMINI = (
    ("pearl", "build_pearl_dangl", "MEL_horn_dangle_terminus"),
    ("star", "build_star_dangl", "MEL_horn_dangle_star"),
    ("lace", "build_lace_dangl", "MEL_horn_dangle_lace"),
    ("bead", "build_bead_tassel", "MEL_horn_dangle_bead"),
)


def _const(tree, loc, value, label=""):
    n = safe_node(tree, "ShaderNodeValue", loc)
    color_node(n, "value")
    n.outputs[0].default_value = float(value)
    if label:
        n.label = label
    return n.outputs[0]


def _math(tree, op, loc, in0=None, in1=None, label=""):
    """Binary Math node — BOTH operands are always written explicitly.

    A bare constant in a Math node silently computes 0.5 * K (both inputs
    default to 0.5); every call site passes both operands on purpose.
    """
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = op
    color_node(n, "math")
    if in0 is not None:
        link_sockets(tree, in0, n.inputs[0])
    if in1 is not None:
        link_sockets(tree, in1, n.inputs[1])
    if label:
        n.label = label
    return n.outputs[0]


def _switch(tree, loc, kind, in_false, in_true, switch, label=""):
    """Switch node — both branches are wired by the caller, never left default."""
    n = safe_node(tree, "GeometryNodeSwitch", loc)
    n.input_type = kind
    color_node(n, "geometry" if kind == "GEOMETRY" else "math")
    if in_false is not None:
        link_sockets(tree, in_false, n.inputs["False"])
    if in_true is not None:
        link_sockets(tree, in_true, n.inputs["True"])
    link_sockets(tree, switch, n.inputs["Switch"])
    if label:
        n.label = label
    return n.outputs[0]


def _mat_param(tree, name, gin, default=None):
    """Add a MATERIAL interface input (the house helpers cover float/int/bool).

    Returns the Group Input node's matching output socket, or None if the API
    refuses — the caller must handle None rather than pretend the dial works.
    """
    try:
        tree.interface.new_socket(name=name, in_out="INPUT",
                                  socket_type="NodeSocketMaterial")
    except Exception:
        return None
    sock = gin.outputs.get(name)
    if sock is not None and default is not None:
        try:
            sock.default_value = default
        except Exception:
            pass
    return sock


def _ring_mesh(tree, x, y, radius_socket):
    """A small ring: a circle swept with a thin profile.

    Measured: `GeometryNodeMeshTorus` does NOT exist in 5.2 (node type
    undefined), so the sweep is the only path — do not re-add a torus attempt.
    """
    circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x, y))
    color_node(circle, "curve")
    try:
        circle.inputs["Resolution"].default_value = 12
    except Exception:
        pass
    link_sockets(tree, radius_socket, circle.inputs["Radius"])
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x, y - 140))
    color_node(prof, "curve")
    try:
        prof.inputs["Resolution"].default_value = 6
        prof.inputs["Radius"].default_value = 0.0009
    except Exception:
        pass
    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (x + 200, y))
    color_node(c2m, "geometry")
    link_sockets(tree, circle.outputs["Curve"], c2m.inputs["Curve"])
    link_sockets(tree, prof.outputs["Curve"], c2m.inputs["Profile Curve"])
    return c2m.outputs["Mesh"]


def build_horn_dangle_chain(group_name="MEL_horn_dangle_chain"):
    """One dangler's chain segment: `Links` rings from the terminus's loop top
    upward by `Chain Length` (local units — the row scales it).

    Instanced PER HOST POINT by the row. `Links` 0 is handled by the row's
    switch (the chain branch is discarded, not evaluated into the output).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    links = add_int_param(tree, "Links", 3, 1, 12)
    length = add_float_param(tree, "Chain Length", 0.006, 0.0, 0.1)
    link_r = add_float_param(tree, "Link Radius", 0.0035, 0.001, 0.02)

    # Mesh Line in its DEFAULT (OFFSET) mode: "Start Location" + "Offset".
    # Measured: switching `mode` to END_POINTS silently failed and the socket
    # names differ per mode (KeyError 'End Location'). OFFSET needs no switch.
    # The segment starts at LOCAL 0 — the row places it at the loop top and
    # scales z to the baked gap (a group input is not a per-point field).
    z0 = _const(tree, (-1180, 300), 0.0, "segment base")

    s_vec = safe_node(tree, "GeometryNodeCombineXYZ", (-1180, 160))
    color_node(s_vec, "vector")
    link_sockets(tree, z0, s_vec.inputs["Z"])
    o_vec = safe_node(tree, "GeometryNodeCombineXYZ", (-1040, 160))
    color_node(o_vec, "vector")
    link_sockets(tree, length, o_vec.inputs["Z"])

    line = safe_node(tree, "GeometryNodeMeshLine", (-1180, 0))
    color_node(line, "curve")
    link_sockets(tree, s_vec.outputs[0], line.inputs["Start Location"])
    link_sockets(tree, o_vec.outputs[0], line.inputs["Offset"])
    link_sockets(tree, links, line.inputs["Count"])

    pts = safe_node(tree, "GeometryNodeMeshToPoints", (-900, 0))
    color_node(pts, "geometry")
    link_sockets(tree, line.outputs["Mesh"], pts.inputs["Mesh"])

    ring = _ring_mesh(tree, -1000, -260, link_r)
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-560, -120))
    color_node(inst, "instance")
    link_sockets(tree, pts.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, ring, inst.inputs["Instance"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (-320, -120))
    color_node(real, "geometry")
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
    link_sockets(tree, real.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("group input",), "role": "input"},
        {"title": "Chain", "nodes": ("mesh line", "mesh to points", "torus",
                                     "circle", "curve to mesh", "combine xyz",
                                     "math", "value"), "role": "curve"},
        {"title": "Links", "nodes": ("instance on points", "realize"),
         "role": "instance"},
        {"title": "Output", "nodes": ("group output",), "role": "output"},
    ])


def build_horn_dangler_row(group_name="MEL_horn_dangler_row"):
    """Dangler row along a host curve (pearl-first; terminus selectable)."""
    tree, gin, gout = new_geometry_tree(group_name)

    # ── Dials ───────────────────────────────────────────────────────────────
    count = add_int_param(tree, "Count", 7, 1, 512)
    host_offset = add_float_param(tree, "Host Offset", 0.0, -0.5, 0.5)
    hang_drop = add_float_param(tree, "Hang Drop", 0.0, 0.0, 0.5)
    terminal_size = add_float_param(tree, "Terminal Size", 1.0, 0.1, 8.0)
    terminus_sel = add_int_param(tree, "Terminus", 0, 0, 3,
                                 "0 pearl, 1 star, 2 lace, 3 bead")
    chain_links = add_int_param(tree, "Chain Links", 0, 0, 8)
    smooth_on = add_bool_param(tree, "Pearl Smooth", False)
    variation = add_float_param(tree, "Variation", 0.0, 0.0, 0.5)
    seed = add_int_param(tree, "Seed", 0, 0, 9999)
    pearl_mat = _mat_param(tree, "Pearl Material", gin)

    host = gin.outputs.get("Geometry")
    if host is None:
        raise RuntimeError(
            "MEL_horn_dangler_row: Group Input has no 'Geometry' socket - "
            "the host curve has nowhere to land")
    music_influence = gin.outputs.get("Music Influence")
    music_amp = gin.outputs.get("Musical Amplitude")

    # ── 1. Host curve -> exact Count points PER SPLINE ─────────────────────
    # Curve to Points measured WORKING in 5.2 (9 points -> 4,338 realised
    # sphere verts) and it counts PER SPLINE (12 on two splines -> 11,568).
    c2p = safe_node(tree, "GeometryNodeCurveToPoints", (-1600, 200))
    color_node(c2p, "curve")
    c2p.label = "Host Points"
    link_sockets(tree, host, c2p.inputs["Curve"])
    link_sockets(tree, count, c2p.inputs["Count"])

    # ── 2. Offset = Normal * Host Offset + (0, 0, -Hang Drop) ──────────────
    # Radial push uses CurveToPoints' OWN Normal (never InputNormal, which is
    # empty on curve points and no-ops silently). CAVEAT (measured): on a
    # HELIX that frame twists, so a large radial offset can BURY instances;
    # the horn lane therefore feeds a pre-baked surface locus (the snapper) and
    # leaves Host Offset at 0.
    push = safe_node(tree, "ShaderNodeVectorMath", (-1400, 300))
    push.operation = "SCALE"
    color_node(push, "vector")
    link_sockets(tree, c2p.outputs["Normal"], push.inputs[0])
    link_sockets(tree, host_offset, push.inputs["Scale"])

    neg = _math(tree, "MULTIPLY", (-1600, 60), hang_drop,
                _const(tree, (-1780, 60), -1.0), label="hang down")
    zvec = safe_node(tree, "GeometryNodeCombineXYZ", (-1400, 80))
    color_node(zvec, "vector")
    link_sockets(tree, neg, zvec.inputs["Z"])

    addv = safe_node(tree, "ShaderNodeVectorMath", (-1220, 180))
    addv.operation = "ADD"
    color_node(addv, "vector")
    link_sockets(tree, push.outputs["Vector"], addv.inputs[0])
    link_sockets(tree, zvec.outputs[0], addv.inputs[1])

    setp = safe_node(tree, "GeometryNodeSetPosition", (-1050, 200))
    color_node(setp, "geometry")
    link_sockets(tree, c2p.outputs["Points"], setp.inputs["Geometry"])
    link_sockets(tree, addv.outputs["Vector"], setp.inputs["Offset"])

    # ── 3. Terminus menu (E1) — all four house builders, switch-selected ────
    tnodes = {}
    for idx, (kind, fn_name, tree_name) in enumerate(_TERMINI):
        fn = getattr(cute_decor, fn_name, None)
        if fn is None:
            raise AttributeError(
                f"cute_decor.{fn_name} is missing - the {kind} branch would be a "
                f"SILENT no-op that still passes every gate")
        tnodes[kind] = safe_node(tree, "GeometryNodeGroup", (-1600 + idx * 30,
                                                            -520 - idx * 260))
        color_node(tnodes[kind], "instance")
        tnodes[kind].node_tree = fn(tree_name)
        tnodes[kind].name = f"Terminus_{kind}"

    ge1 = _math(tree, "GREATER_THAN", (-1900, -560), terminus_sel,
                _const(tree, (-2040, -560), 0.5), ">0")
    ge2 = _math(tree, "GREATER_THAN", (-1900, -640), terminus_sel,
                _const(tree, (-2040, -640), 1.5), ">1")
    ge3 = _math(tree, "GREATER_THAN", (-1900, -720), terminus_sel,
                _const(tree, (-2040, -720), 2.5), ">2")
    sel1 = _switch(tree, (-1740, -520), "GEOMETRY",
                   tnodes["pearl"].outputs["Geometry"],
                   tnodes["star"].outputs["Geometry"], ge1, "star?")
    sel2 = _switch(tree, (-1560, -520), "GEOMETRY", sel1,
                   tnodes["lace"].outputs["Geometry"], ge2, "lace?")
    sel3 = _switch(tree, (-1380, -520), "GEOMETRY", sel2,
                   tnodes["bead"].outputs["Geometry"], ge3, "bead?")

    # ── 4. Pearl Smooth (P4) — subdivide the terminus once, before instancing
    sub = safe_node(tree, "GeometryNodeSubdivisionSurface", (-1200, -760))
    color_node(sub, "geometry")
    link_sockets(tree, sel3, sub.inputs["Mesh"])
    try:
        sub.inputs["Level"].default_value = 1
    except Exception:
        pass
    try:
        sub.subdivision_type = "CATMULL_CLARK"
    except Exception:
        pass
    term_geo = _switch(tree, (-1040, -560), "GEOMETRY", sel3,
                       sub.outputs["Mesh"], smooth_on, "smooth?")

    # ── 5. Materials (P1a / P1c) ───────────────────────────────────────────
    # Split mode requires EVERY terminus in the menu to expose the per-part
    # material sockets — otherwise a material dial would be silently inert for
    # some menu values. Today only the pearl builder has them, so the row
    # correctly uses ONE SetMaterial over the whole dangler; extend the other
    # three builders and this flips to split by itself.
    split_ok = bool(tnodes) and all("Pearl Material" in n.inputs for n in tnodes.values())
    if split_ok and pearl_mat is not None:
        trim_mat = _mat_param(tree, "Trim Material", gin)
        for _kind, n in tnodes.items():
            link_sockets(tree, pearl_mat, n.inputs["Pearl Material"])
            if trim_mat is not None and "Trim Material" in n.inputs:
                link_sockets(tree, trim_mat, n.inputs["Trim Material"])
        geo_out = term_geo
        mat_mode = "split"
    else:
        sm = safe_node(tree, "GeometryNodeSetMaterial", (-880, -560))
        color_node(sm, "geometry")
        link_sockets(tree, term_geo, sm.inputs["Geometry"])
        if pearl_mat is not None:
            link_sockets(tree, pearl_mat, sm.inputs["Material"])
        geo_out = sm.outputs["Geometry"]
        mat_mode = "single"

    # ── 6. Scale = Terminal Size x music (E6) x per-point variation (E5) ────
    if music_amp is not None and music_influence is not None:
        mu1 = _math(tree, "MULTIPLY", (-1600, -900), music_amp, music_influence,
                    "amp x influence")
        mu2 = _math(tree, "ADD", (-1440, -900), mu1,
                    _const(tree, (-1600, -960), 1.0), "1 + music")
    else:
        mu2 = _const(tree, (-1440, -900), 1.0, "no music sockets")
    base = _math(tree, "MULTIPLY", (-1280, -900), terminal_size, mu2,
                 "terminal x music")

    rv = safe_node(tree, "FunctionNodeRandomValue", (-1440, -1060))
    color_node(rv, "math")
    try:
        rv.data_type = "FLOAT"
    except Exception:
        pass
    lo = _math(tree, "SUBTRACT", (-1600, -1060),
               _const(tree, (-1760, -1060), 1.0), variation, "1 - var")
    hi = _math(tree, "ADD", (-1600, -1140),
               _const(tree, (-1760, -1140), 1.0), variation, "1 + var")
    link_sockets(tree, lo, rv.inputs["Min"])
    link_sockets(tree, hi, rv.inputs["Max"])
    link_sockets(tree, seed, rv.inputs["Seed"])
    scl_f = _math(tree, "MULTIPLY", (-1120, -980), base, rv.outputs["Value"],
                  "final scale")
    scl = safe_node(tree, "GeometryNodeCombineXYZ", (-960, -980))
    color_node(scl, "vector")
    for axis in ("X", "Y", "Z"):
        link_sockets(tree, scl_f, scl.inputs[axis])

    # ── 7. Instance + realize ──────────────────────────────────────────────
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-640, -300))
    color_node(inst, "instance")
    link_sockets(tree, setp.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, geo_out, inst.inputs["Instance"])
    link_sockets(tree, scl.outputs[0], inst.inputs["Scale"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (-420, -300))
    color_node(real, "geometry")
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])

    # ── 8. Chain (P5) — length from the host curve's baked `radius` ─────────
    cnode = safe_node(tree, "GeometryNodeGroup", (-640, -640))
    color_node(cnode, "instance")
    cnode.node_tree = build_horn_dangle_chain()
    cnode.name = "Chain"
    link_sockets(tree, chain_links, cnode.inputs["Links"])

    nattr = safe_node(tree, "GeometryNodeInputNamedAttribute", (-880, -700))
    color_node(nattr, "attribute")
    try:
        nattr.data_type = "FLOAT"
        nattr.inputs["Name"].default_value = "radius"
    except Exception:
        pass
    if "Chain Length" in cnode.inputs:
        # The segment is authored at UNIT length here; the row scales it to the
        # baked gap per point. (Linking the per-point attribute into this GROUP
        # INPUT silently evaluated to 0 — a group input is not a field.)
        try:
            cnode.inputs["Chain Length"].default_value = CHAIN_UNIT
        except Exception:
            pass

    # chain base = the terminus's loop top, scaled with the dangler
    lt = _const(tree, (-1180, -560), LOOP_TOP_Z, "loop top")
    lts = _math(tree, "MULTIPLY", (-1040, -560), lt, scl_f, "loop top x scale")
    ltv = safe_node(tree, "GeometryNodeCombineXYZ", (-900, -560))
    color_node(ltv, "vector")
    link_sockets(tree, lts, ltv.inputs["Z"])
    csetp = safe_node(tree, "GeometryNodeSetPosition", (-760, -560))
    color_node(csetp, "geometry")
    link_sockets(tree, setp.outputs["Geometry"], csetp.inputs["Geometry"])
    link_sockets(tree, ltv.outputs[0], csetp.inputs["Offset"])

    # chain length = baked gap / unit, clamped so a missing attribute is harmless
    ratio = _math(tree, "DIVIDE", (-1040, -700), nattr.outputs[0],
                  _const(tree, (-1180, -700), CHAIN_UNIT), "gap / unit")
    ratio = _math(tree, "MAXIMUM", (-900, -700), ratio,
                  _const(tree, (-1040, -760), 0.05), "clamp")
    zscale = _math(tree, "MULTIPLY", (-760, -700), scl_f, ratio, "z scale")
    cscale = safe_node(tree, "GeometryNodeCombineXYZ", (-620, -700))
    color_node(cscale, "vector")
    link_sockets(tree, scl_f, cscale.inputs["X"])
    link_sockets(tree, scl_f, cscale.inputs["Y"])
    link_sockets(tree, zscale, cscale.inputs["Z"])

    cinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-440, -440))
    color_node(cinst, "instance")
    link_sockets(tree, csetp.outputs["Geometry"], cinst.inputs["Points"])
    link_sockets(tree, cnode.outputs["Geometry"], cinst.inputs["Instance"])
    link_sockets(tree, cscale.outputs[0], cinst.inputs["Scale"])

    creal = safe_node(tree, "GeometryNodeRealizeInstances", (-260, -440))
    color_node(creal, "geometry")
    link_sockets(tree, cinst.outputs["Instances"], creal.inputs["Geometry"])

    both = safe_node(tree, "GeometryNodeJoinGeometry", (-220, -380))
    color_node(both, "geometry")
    link_sockets(tree, real.outputs["Geometry"], both.inputs["Geometry"])
    link_sockets(tree, creal.outputs["Geometry"], both.inputs["Geometry"])

    c_on = _math(tree, "GREATER_THAN", (-420, -760), chain_links,
                 _const(tree, (-580, -760), 0.5), "links > 0")
    final = _switch(tree, (-40, -300), "GEOMETRY", real.outputs["Geometry"],
                    both.outputs["Geometry"], c_on, "chain on?")
    link_sockets(tree, final, gout.inputs["Geometry"])

    tree["terminus_material_mode"] = mat_mode
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("group input",), "role": "input"},
        {"title": "Host Points", "nodes": ("curve to points", "set position",
                                           "vector math", "combine xyz", "math",
                                           "value"), "role": "curve"},
        {"title": "Terminus Menu", "nodes": ("terminus_", "switch"),
         "role": "instance"},
        {"title": "Material + Scale", "nodes": ("subdivision surface",
                                                "set material", "random value",
                                                "group output"), "role": "output"},
        {"title": "Rows", "nodes": ("instance on points", "realize", "chain",
                                    "named attribute", "join geometry"),
         "role": "instance"},
    ])


register_builder(
    "MEL_horn_dangler_row", build_horn_dangler_row,
    "Horn Dangler Row",
    "Dangler row along a host curve: terminus menu, materials, chain, jitter.",
    category="ornament",
)

register_builder(
    "MEL_horn_dangle_chain", build_horn_dangle_chain,
    "Horn Dangle Chain",
    "Short chain segment (ring row) for one dangler; instanced per host point.",
    category="ornament",
)
