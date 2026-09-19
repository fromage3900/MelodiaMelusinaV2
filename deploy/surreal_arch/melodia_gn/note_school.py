"""Note Fish School - "Melody Aquarium" GN builders.

A note-creature: the canonical note head as the body, a swept flag tail, side
fins, bead eyes. Two authored UV channels (FLOAT2 / CORNER) carry the show:

  UVMap   analytic cylindrical wrap around the swim axis (static).
  UVFlow  UVMap + (0, flow) where
          flow = MODULO((Frame-1) * FlowCycles / LoopFrames + Phase, 1)

  Integer FlowCycles => at frame N+1 the offset wraps to exactly the frame-1
  value (MODULO(2.0, 1.0) == 0.0), so any integer-frequency pattern in v
  repeats with an EXACT loop seam. The sawtooth wrap reads as continuous flow
  because the pattern is periodic. Materials read Attribute("UVFlow").

Builders (registered, category "music"):
  MEL_music_note_fish - one note fish (template for the school)

Design units: metres. Nose = +X, tail = -X. Body-to-lobe-tip ~2.9 u.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, sock, make_group_input,
)
from .music import build_music_note_head

TAU = math.tau

# ---------------------------------------------------------------------------
# Local helpers (mirroring the chimes_gn private style)
# ---------------------------------------------------------------------------


def _math(tree, operation, loc, a=None, b=None):
    node = safe_node(tree, "ShaderNodeMath", loc)
    if node:
        try:
            node.operation = operation
        except Exception:
            pass
        for idx, val in ((0, a), (1, b)):
            if val is None:
                continue
            if isinstance(val, (int, float)):
                node.inputs[idx].default_value = float(val)
            else:
                link_sockets(tree, val, node.inputs[idx])
    return node


def _combine(tree, loc, x=None, y=None, z=None):
    node = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None or node is None:
            continue
        if isinstance(val, (int, float)):
            try:
                node.inputs[name].default_value = float(val)
            except Exception:
                pass
        else:
            link_sockets(tree, val, node.inputs[name])
    return node


def _true_socket(n):
    return n.inputs.get("True") or n.inputs.get("A")


def _false_socket(n):
    return n.inputs.get("False") or n.inputs.get("B")


def _out_socket(n):
    return n.outputs.get("Output") or (n.outputs[0] if n and n.outputs else None)


def _replace_output(tree, gout, geom):
    geo_in = gout.inputs.get("Geometry")
    if geo_in is not None:
        for lk in list(tree.links):
            if lk.to_socket == geo_in:
                tree.links.remove(lk)
    link_sockets(tree, geom, gout.inputs["Geometry"])


def _export_tail(tree, gin, gout, geom, loc):
    """Realize-for-export switch + shade smooth (chimes_gn pattern)."""
    realize = safe_node(tree, "GeometryNodeRealizeInstances", loc)
    link_sockets(tree, geom, realize.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1]))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    rs = gin.outputs.get("Realize for export")
    if rs is not None:
        link_sockets(tree, rs, sw.inputs.get("Switch") or sw.inputs[0])
    link_sockets(tree, geom, _false_socket(sw))
    link_sockets(tree, realize.outputs["Geometry"], _true_socket(sw))
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (loc[0] + 440, loc[1]))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, _out_socket(sw), shade.inputs["Geometry"])
    _replace_output(tree, gout, shade.outputs["Geometry"])
    return shade.outputs["Geometry"]


def _store_uv(tree, loc, geom, name, value_sock):
    """Store a FLOAT2 / CORNER attribute (UV layer contract)."""
    st = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    try:
        st.data_type = "FLOAT2"
        st.domain = "CORNER"
    except Exception:
        pass
    try:
        st.inputs["Name"].default_value = name
    except Exception:
        pass
    link_sockets(tree, geom, st.inputs["Geometry"])
    v = st.inputs.get("Value") or st.inputs.get("Value_001")
    if v is not None and value_sock is not None:
        link_sockets(tree, value_sock, v)
    color_node(st, "attribute")
    return st.outputs["Geometry"]


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def _refresh_group_refs(tree, group_name):
    changed = 0
    ng = bpy.data.node_groups.get(group_name)
    if ng is None:
        return 0
    for n in tree.nodes:
        if n.type == "GROUP" and getattr(n, "node_tree", None) is None:
            n.node_tree = ng
            changed += 1
    return changed


def _set_in(node, name, value):
    if node is None:
        return False
    s = node.inputs.get(name)
    if s is None:
        return False
    try:
        s.default_value = value
        return True
    except Exception:
        return False


def _set_iface(tree, name, value):
    for item in tree.interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and getattr(item, "name", "") == name:
            try:
                item.default_value = value
                return True
            except Exception:
                return False
    return False


# ---------------------------------------------------------------------------
# Materials (copy-on-first-use; body reads UVFlow for the flow bands)
# ---------------------------------------------------------------------------


def _fish_material(name, base_color, metallic=0.0, roughness=0.4, flow=False):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if flow:
        # integer-frequency band pattern in v; UVFlow scrolls it. Loop-safe.
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.location = (-600, 0)
        attr.attribute_name = "UVFlow"
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        sep.location = (-400, 0)
        nt.links.new(attr.outputs["Vector"], sep.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.location = (-200, 0)
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 6.0 * TAU  # 6 bands per UV unit (integer)
        nt.links.new(sep.outputs["Y"], mul.inputs[0])
        sine = nt.nodes.new("ShaderNodeMath")
        sine.location = (0, 0)
        sine.operation = "SINE"
        nt.links.new(mul.outputs[0], sine.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.location = (150, 0)
        mr.inputs["From Min"].default_value = -1.0
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = 0.35
        try:
            mr.clamp = True
        except Exception:
            pass
        nt.links.new(sine.outputs[0], mr.inputs["Value"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.location = (150, -200)
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = (*base_color, 1.0)
        mix.inputs["B"].default_value = (1.0, 0.97, 0.93, 1.0)  # pearl sheen
        nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    mat["mel_fish"] = "1"
    return mat


def _ensure_fish_materials():
    body = _fish_material("MEL_fish_body", (0.92, 0.80, 0.86), metallic=0.15,
                          roughness=0.32, flow=True)
    fin = _fish_material("MEL_fish_fin", (0.86, 0.78, 0.92), metallic=0.05,
                         roughness=0.45, flow=True)
    eye = _fish_material("MEL_fish_eye", (0.95, 0.78, 0.35), metallic=1.0,
                         roughness=0.22)
    mouth = _fish_material("MEL_fish_mouth", (0.30, 0.16, 0.24),
                           roughness=0.5)
    return body, fin, eye, mouth


def _setmat(tree, loc, geom, mat):
    sm = safe_node(tree, "GeometryNodeSetMaterial", loc)
    if sm is not None:
        try:
            sm.inputs["Material"].default_value = mat
        except Exception:
            pass
        link_sockets(tree, geom, sm.inputs["Geometry"])
    return sm.outputs["Geometry"] if sm else geom


def _sweep(tree, loc, start, start_h, end, end_h, radius, profile_res=6, flat=1.0):
    """Bezier segment swept with a small circle profile -> a rounded fin/tail.

    Profile MUST be a curve (CurvePrimitiveCircle). A MeshCircle linked into
    'Profile Curve' converts to a 1-point profile and silently produces
    1-vert-per-ring slivers (measured 2026-09-18). flat<1 squashes the profile
    into a ribbon (flag tail / fin).
    """
    bez = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", loc)
    if bez is None:
        return None
    bez.inputs["Start"].default_value = start
    bez.inputs["Start Handle"].default_value = start_h
    bez.inputs["End"].default_value = end
    bez.inputs["End Handle"].default_value = end_h
    res_in = bez.inputs.get("Resolution")
    if res_in is not None:
        try:
            res_in.default_value = 8
        except Exception:
            pass
    circ = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0], loc[1] - 220))
    if circ is not None:
        try:
            circ.mode = "RADIUS"
        except Exception:
            pass
        for nm, val in (("Radius", radius), ("Resolution", profile_res)):
            s = circ.inputs.get(nm)
            if s is not None:
                try:
                    s.default_value = val
                except Exception:
                    pass
    res = safe_node(tree, "GeometryNodeResampleCurve", (loc[0] + 100, loc[1]))
    curve_out = bez.outputs["Curve"]
    if res is not None:
        link_sockets(tree, curve_out, res.inputs["Curve"])
        try:
            res.inputs["Count"].default_value = 10
        except Exception:
            pass
        try:
            res.mode = "COUNT"
        except Exception:
            pass
        curve_out = res.outputs["Curve"]
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (loc[0] + 200, loc[1]))
    if sweep is None:
        return None
    link_sockets(tree, curve_out, sweep.inputs["Curve"])
    prof = sweep.inputs.get("Profile Curve") or sweep.inputs.get("Profile")
    if prof is not None and circ is not None:
        prof_sock = circ.outputs.get("Curve") or circ.outputs[0]
        if flat != 1.0:
            flat_xf = safe_node(tree, "GeometryNodeTransform", (loc[0] + 60, loc[1] - 220))
            link_sockets(tree, prof_sock, flat_xf.inputs["Geometry"])
            try:
                flat_xf.inputs["Scale"].default_value = (1.0, flat, 1.0)
            except Exception:
                pass
            prof_sock = flat_xf.outputs["Geometry"]
        link_sockets(tree, prof_sock, prof)
    return sweep.outputs.get("Mesh") or sweep.outputs[0]


def _sphere(tree, loc, radius, seg=14, rings=10):
    n = safe_node(tree, "GeometryNodeMeshUVSphere", loc)
    if n is None:
        return None
    try:
        n.inputs["Segments"].default_value = seg
        n.inputs["Rings"].default_value = rings
        n.inputs["Radius"].default_value = radius
    except Exception:
        pass
    return n.outputs.get("Mesh") or n.outputs[0]


def _taper_by_x(tree, loc, geom, x_start, x_end, s_end):
    """Scale each vertex's Y/Z cross-section by a factor mapped from X.

    Factor is 1.0 at x_start, s_end at x_end (clamped) - the cheap reliable GN
    taper: SetPosition override, no capture needed. Only valid for parts whose
    spine sits near z=0 (body ellipse, tail peduncle).
    """
    if geom is None:
        return None
    pos = safe_node(tree, "GeometryNodeInputPosition", loc)
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (loc[0] + 140, loc[1] - 60))
    mr = safe_node(tree, "ShaderNodeMapRange", (loc[0] + 280, loc[1] - 60))
    if pos is None or sep is None or mr is None:
        return geom
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    mr.inputs["From Min"].default_value = x_start
    mr.inputs["From Max"].default_value = x_end
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = s_end
    try:
        mr.clamp = True
    except Exception:
        pass
    link_sockets(tree, sep.outputs["X"], mr.inputs["Value"])
    fac = _combine(tree, (loc[0] + 420, loc[1] - 60), x=1.0,
                   y=mr.outputs["Result"], z=mr.outputs["Result"])
    scaled = safe_node(tree, "ShaderNodeVectorMath", (loc[0] + 560, loc[1]))
    if scaled is not None:
        try:
            scaled.operation = "MULTIPLY"
        except Exception:
            pass
        link_sockets(tree, pos.outputs["Position"], scaled.inputs[0])
        link_sockets(tree, fac.outputs["Vector"], scaled.inputs[1])
        sp = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 700, loc[1]))
        if sp is not None:
            link_sockets(tree, geom, sp.inputs["Geometry"])
            link_sockets(tree, scaled.outputs["Vector"], sp.inputs["Position"])
            return sp.outputs["Geometry"]
    return geom


# ---------------------------------------------------------------------------
# MEL_music_note_fish - one note fish
# ---------------------------------------------------------------------------


def build_music_note_fish(group_name="MEL_music_note_fish"):
    """Note fish: note-head body + flag tail + side fins + bead eyes.

    UVs: UVMap (analytic cylindrical wrap) and UVFlow (animated, seam-exact
    loop with integer Flow Cycles).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.2, 3.0)
    add_int_param(tree, "Flow Cycles", 2, 0, 8)
    add_int_param(tree, "Loop Frames", 96, 24, 480)
    add_float_param(tree, "Phase", 0.0, 0.0, 2.0)
    add_bool_param(tree, "Realize for export", False)
    _set_iface(tree, "Music Influence", 0.0)  # fish stays put; pulse is opt-in

    body_mat, fin_mat, eye_mat, mouth_mat = _ensure_fish_materials()

    parts = []

    # --- body: the canonical note head (nested; stem+flag off) ---
    head = _ensure_group_node(tree, "MEL_music_note_head", build_music_note_head,
                              (bx - 900, by + 200))
    _set_in(head, "Has Stem", False)
    _set_in(head, "Has Flag", False)
    _set_in(head, "Scale", 0.9)
    head_xf = safe_node(tree, "GeometryNodeTransform", (bx - 780, by + 200))
    link_sockets(tree, head.outputs["Geometry"], head_xf.inputs["Geometry"])
    try:
        head_xf.inputs["Scale"].default_value = (1.05, 1.15, 1.45)
    except Exception:
        pass
    body = _taper_by_x(tree, (bx - 620, by + 430), head_xf.outputs["Geometry"],
                       0.0, -1.05, 0.88)
    body = _setmat(tree, (bx - 700, by + 200), body, body_mat)
    parts.append(body)

    # --- tail: tapering peduncle forking into two rounded lobes ---
    ped = _sweep(tree, (bx - 500, by - 100),
                 start=(-0.95, 0.0, 0.06), start_h=(-1.12, 0.02, 0.10),
                 end=(-1.42, 0.0, 0.02), end_h=(-1.30, 0.0, 0.06),
                 radius=0.20, flat=0.45)
    ped = _taper_by_x(tree, (bx - 380, by - 100), ped, -0.95, -1.44, 0.55)
    if ped is not None:
        parts.append(_setmat(tree, (bx - 260, by - 100), ped, fin_mat))
    for i, (s, sh, e, eh) in enumerate((
            ((-1.40, 0.0, 0.02), (-1.58, 0.0, 0.22),
             (-1.88, 0.0, 0.38), (-1.74, 0.0, 0.30)),
            ((-1.40, 0.0, 0.02), (-1.56, 0.0, -0.16),
             (-1.82, 0.0, -0.42), (-1.68, 0.0, -0.36)))):
        lobe = _sweep(tree, (bx - 500, by - 940 - i * 260),
                      start=s, start_h=sh, end=e, end_h=eh,
                      radius=0.15, flat=0.40)
        if lobe is not None:
            parts.append(_setmat(tree, (bx - 260, by - 940 - i * 260),
                                 lobe, fin_mat))

    # --- mouth: small curl hugging the nose surface ---
    mouth = _sweep(tree, (bx - 500, by + 240),
                   start=(0.97, 0.0, 0.08), start_h=(1.02, 0.0, 0.02),
                   end=(0.95, 0.0, -0.14), end_h=(1.005, 0.0, -0.10),
                   radius=0.055)
    if mouth is not None:
        parts.append(_setmat(tree, (bx - 260, by + 240), mouth, mouth_mat))

    # --- side fins: two small swept ribbons, mid-body, angled back ---
    for i, sgn in enumerate((1.0, -1.0)):
        fin = _sweep(tree, (bx - 500, by - 420 - i * 260),
                     start=(0.05, sgn * 0.60, -0.05),
                     start_h=(0.15, sgn * 0.85, -0.10),
                     end=(-0.50, sgn * 1.20, -0.32),
                     end_h=(-0.75, sgn * 1.14, -0.26),
                     radius=0.14, flat=0.5)
        if fin is not None:
            parts.append(_setmat(tree, (bx - 260, by - 420 - i * 260), fin, fin_mat))

    # --- eyes: two beads near the nose (+X) ---
    for i, sgn in enumerate((1.0, -1.0)):
        eye = _sphere(tree, (bx - 500, by + 520 + i * 240), 0.145)
        if eye is None:
            continue
        xf = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 520 + i * 240))
        link_sockets(tree, eye, xf.inputs["Geometry"])
        xf.inputs["Translation"].default_value = (0.74, sgn * 0.60, 0.20)
        parts.append(_setmat(tree, (bx - 140, by + 520 + i * 240),
                             xf.outputs["Geometry"], eye_mat))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 60, by + 100))
    for p in parts:
        link_sockets(tree, p, join.inputs["Geometry"])
    geo = join.outputs["Geometry"]

    # --- UV chain: analytic cylindrical UVMap, then animated UVFlow ---
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx + 200, by + 500))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 340, by + 500))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    atan = _math(tree, "ARCTAN2", (bx + 480, by + 560), sep.outputs["Z"], sep.outputs["Y"])
    u_div = _math(tree, "DIVIDE", (bx + 620, by + 560), atan.outputs[0] if atan else 0.0,
                  TAU)
    u_add = _math(tree, "ADD", (bx + 760, by + 560), u_div.outputs[0] if u_div else 0.0,
                  0.5)

    v_map = safe_node(tree, "ShaderNodeMapRange", (bx + 480, by + 380))
    if v_map is not None:
        v_map.inputs["From Min"].default_value = -2.0
        v_map.inputs["From Max"].default_value = 1.10
        v_map.inputs["To Min"].default_value = 0.0
        v_map.inputs["To Max"].default_value = 1.0
        try:
            v_map.clamp = True
        except Exception:
            pass
        link_sockets(tree, sep.outputs["X"], v_map.inputs["Value"])

    uv = _combine(tree, (bx + 900, by + 460),
                  x=u_add.outputs[0] if u_add else 0.0,
                  y=v_map.outputs["Result"] if v_map else 0.0,
                  z=0.0)
    geo = _store_uv(tree, (bx + 1060, by + 460), geo, "UVMap", uv.outputs["Vector"])

    # flow = MODULO((Frame-1) * FlowCycles / LoopFrames + Phase, 1)
    st = safe_node(tree, "GeometryNodeInputSceneTime", (bx + 480, by + 100))
    f_sub = _math(tree, "SUBTRACT", (bx + 620, by + 100), st.outputs["Frame"], 1.0)
    f_mul = _math(tree, "MULTIPLY", (bx + 760, by + 100), f_sub.outputs[0],
                  gin.outputs["Flow Cycles"])
    f_div = _math(tree, "DIVIDE", (bx + 900, by + 100), f_mul.outputs[0],
                  gin.outputs["Loop Frames"])
    f_add = _math(tree, "ADD", (bx + 1040, by + 100), f_div.outputs[0],
                  gin.outputs["Phase"])
    f_mod = _math(tree, "MODULO", (bx + 1180, by + 100), f_add.outputs[0], 1.0)
    fvec = _combine(tree, (bx + 1320, by + 100), x=0.0,
                    y=f_mod.outputs[0] if f_mod else 0.0, z=0.0)
    uv2 = safe_node(tree, "ShaderNodeVectorMath", (bx + 1320, by + 300))
    if uv2 is not None:
        uv2.operation = "ADD"
        link_sockets(tree, uv.outputs["Vector"], uv2.inputs[0])
        link_sockets(tree, fvec.outputs["Vector"], uv2.inputs[1])
    geo = _store_uv(tree, (bx + 1480, by + 300), geo, "UVFlow",
                    uv2.outputs["Vector"] if uv2 else None)

    # --- overall scale (after UVs so the map stays unit-normalised) ---
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1640, by + 300))
    link_sockets(tree, geo, xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1480, by + 640), x=gin.outputs["Scale"],
                  y=gin.outputs["Scale"], z=gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    geo = xf.outputs["Geometry"]

    _export_tail(tree, gin, gout, geo, (bx + 1860, by + 300))
    _refresh_group_refs(tree, "MEL_music_note_head")

    color_node(join, "geometry")
    color_node(xf, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("note head",), "role": "geometry"},
        {"title": "Tail And Fins", "nodes": ("sweep", "fins", "mouth"), "role": "geometry"},
        {"title": "UV", "nodes": ("uvmap", "uvflow", "flow"), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


register_builder(
    "MEL_music_note_fish", build_music_note_fish, "Note Fish",
    "Note-creature: note-head body, flag tail, bead eyes; analytic UVMap + "
    "animated UVFlow (integer Flow Cycles = exact loop seam).",
    "music",
)


# ---------------------------------------------------------------------------
# MEL_music_note_school - the school, riding a GUIDE curve (study idiom)
# ---------------------------------------------------------------------------


def build_music_note_school(group_name="MEL_music_note_school"):
    """Note fish school riding a GUIDE curve - the study's accessory idiom.

    Guide (Object socket, RELATIVE transform space) -> fish ride the curve,
    tangent-aligned, spread by index. The swim offset is
    MODULO((Frame-1)*SwimCycles/LoopFrames + Phase + i/Count, 1), so with an
    integer Swim Cycles count the loop seam is EXACT. NOTE: on an OPEN guide an
    integer Swim Cycles makes each fish wrap end->start once per loop (fine for
    a closed path; for open paths keep Swim Cycles 0 and let UVFlow animate).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    guide = make_group_input(tree, "NodeSocketObject", "Guide", default=None)
    add_int_param(tree, "Fish Count", 6, 1, 40)
    add_float_param(tree, "Fish Scale", 0.26, 0.05, 3.0)
    add_int_param(tree, "Swim Cycles", 0, 0, 8)
    add_int_param(tree, "Loop Frames", 96, 24, 480)
    add_float_param(tree, "Phase", 0.0, 0.0, 2.0)
    add_int_param(tree, "Flow Cycles", 2, 0, 8)
    add_float_param(tree, "Rise", 0.15, -2.0, 2.0)
    add_bool_param(tree, "Realize for export", False)
    _set_iface(tree, "Music Influence", 0.0)

    # guide -> geometry in HOST space (RELATIVE is load-bearing; see nikki_decor.py)
    obj_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 1500, by + 320))
    if obj_info is not None:
        try:
            obj_info.transform_space = "RELATIVE"
        except Exception:
            pass
        link_sockets(tree, guide, obj_info.inputs["Object"])
        color_node(obj_info, "curve")

    # fish template (nested; flow settings shared from the school)
    fish_grp = _ensure_group_node(tree, "MEL_music_note_fish", build_music_note_fish,
                                  (bx - 1500, by - 520))
    _set_in(fish_grp, "Scale", 1.0)
    if fish_grp is not None:
        link_sockets(tree, gin.outputs["Flow Cycles"], fish_grp.inputs["Flow Cycles"])
        link_sockets(tree, gin.outputs["Loop Frames"], fish_grp.inputs["Loop Frames"])

    # one point per fish
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1250, by + 60))
    if line is not None:
        link_sockets(tree, gin.outputs["Fish Count"], line.inputs["Count"])
        line.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
        line.inputs["Offset"].default_value = (0.0, 0.0, 0.0)

    # shared swim offset
    st = safe_node(tree, "GeometryNodeInputSceneTime", (bx - 1250, by - 760))
    f_sub = _math(tree, "SUBTRACT", (bx - 1100, by - 760), st.outputs["Frame"], 1.0)
    f_mul = _math(tree, "MULTIPLY", (bx - 950, by - 760), f_sub.outputs[0],
                  gin.outputs["Swim Cycles"])
    f_div = _math(tree, "DIVIDE", (bx - 800, by - 760), f_mul.outputs[0],
                  gin.outputs["Loop Frames"])
    f_add = _math(tree, "ADD", (bx - 650, by - 760), f_div.outputs[0],
                  gin.outputs["Phase"])
    f_mod = _math(tree, "MODULO", (bx - 500, by - 760), f_add.outputs[0], 1.0)

    # per-fish factor = MODULO(swim + index/Count, 1)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 1250, by - 560))
    i_div = _math(tree, "DIVIDE", (bx - 1100, by - 560), idx.outputs["Index"],
                  gin.outputs["Fish Count"])
    i_add = _math(tree, "ADD", (bx - 950, by - 560), i_div.outputs[0],
                  f_mod.outputs[0] if f_mod else 0.0)
    i_mod = _math(tree, "MODULO", (bx - 800, by - 560), i_add.outputs[0], 1.0)

    sample = safe_node(tree, "GeometryNodeSampleCurve", (bx - 620, by - 400))
    if sample is not None and obj_info is not None:
        link_sockets(tree, obj_info.outputs["Geometry"], sample.inputs["Curves"])
        link_sockets(tree, i_mod.outputs[0], sample.inputs["Factor"])

    on_curve = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by + 60))
    if on_curve is not None and line is not None:
        link_sockets(tree, line.outputs["Mesh"], on_curve.inputs["Geometry"])
        link_sockets(tree, sample.outputs["Position"], on_curve.inputs["Position"])

    risen = safe_node(tree, "GeometryNodeSetPosition", (bx - 220, by + 60))
    if risen is not None:
        link_sockets(tree, on_curve.outputs["Geometry"], risen.inputs["Geometry"])
        rz = _combine(tree, (bx - 400, by + 320), x=0.0, y=0.0,
                      z=gin.outputs["Rise"])
        link_sockets(tree, rz.outputs["Vector"], risen.inputs["Offset"])

    align = safe_node(tree, "FunctionNodeAlignEulerToVector", (bx - 400, by - 400))
    if align is not None and sample is not None:
        try:
            align.axis = "X"
        except Exception:
            pass
        link_sockets(tree, sample.outputs["Tangent"], align.inputs["Vector"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 20, by))
    if inst is not None and fish_grp is not None:
        link_sockets(tree, risen.outputs["Geometry"], inst.inputs["Points"])
        link_sockets(tree, fish_grp.outputs["Geometry"], inst.inputs["Instance"])
        link_sockets(tree, align.outputs["Rotation"], inst.inputs["Rotation"])
        sc = _combine(tree, (bx - 220, by + 320),
                      x=gin.outputs["Fish Scale"], y=gin.outputs["Fish Scale"],
                      z=gin.outputs["Fish Scale"])
        link_sockets(tree, sc.outputs["Vector"], inst.inputs["Scale"])

    geo = inst.outputs["Instances"] if inst else None

    # host-stack idiom: pass the host geometry through and ADD the school
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 80, by - 200))
    if join is not None:
        link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
        if geo is not None:
            link_sockets(tree, geo, join.inputs["Geometry"])
        geo = join.outputs["Geometry"]
        color_node(join, "geometry")

    # realize switch only - the fish template already shades itself smooth
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 260, by))
    if realize is not None and geo is not None:
        link_sockets(tree, geo, realize.inputs["Geometry"])
        sw = safe_node(tree, "GeometryNodeSwitch", (bx + 480, by))
        if sw is not None:
            try:
                sw.input_type = "GEOMETRY"
            except Exception:
                pass
            rs = gin.outputs.get("Realize for export")
            if rs is not None:
                link_sockets(tree, rs, sw.inputs.get("Switch") or sw.inputs[0])
            link_sockets(tree, geo, _false_socket(sw))
            link_sockets(tree, realize.outputs["Geometry"], _true_socket(sw))
            _replace_output(tree, gout, _out_socket(sw))
    elif geo is not None:
        _replace_output(tree, gout, geo)
    _refresh_group_refs(tree, "MEL_music_note_fish")
    if inst is not None:
        color_node(inst, "instance")

    return label_tree(tree, group_name, [
        {"title": "Guide", "nodes": ("object info",), "role": "curve"},
        {"title": "Swim", "nodes": ("time", "modulo", "sample"), "role": "attribute"},
        {"title": "Fish", "nodes": ("fish", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


register_builder(
    "MEL_music_note_school", build_music_note_school, "Note Fish School",
    "Guide-curve school: fish ride a Guide curve, tangent-aligned, index-spread; "
    "swim offset is loop-exact with integer Swim Cycles (0 = static spread).",
    "music",
)
