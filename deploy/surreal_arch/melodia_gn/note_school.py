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

Design units: metres. Nose = +X, tail = -X. Body-to-lobe-tip ~3.25 u.
Palette (house canon): pearl-pink body with pearl-white belly (BellyMix
attribute), lavender dorsal crest, pale fins, gold bead eyes, plum mouth.
"""

from __future__ import annotations

import json
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


def _fish_material(name, base_color, metallic=0.0, roughness=0.4, flow=False,
                   belly=None, belly_attr="BellyMix"):
    # Rebuild-in-place semantics: if authored values changed since last time,
    # rebuild the node tree (stale .blend materials must not survive a rebuild).
    # ID-props allow only flat float/int/bool arrays -> flat signature.
    sig = [round(c, 4) for c in base_color]
    sig += [round(metallic, 4), round(roughness, 4), bool(flow)]
    if belly is not None:
        sig += [round(c, 4) for c in belly] + [1.0]
    else:
        sig += [-1.0, -1.0, -1.0, 0.0]
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat["_melodia_sig"] = ""
    if mat.get("_melodia_sig", "") == json.dumps(sig) and \
            mat.get("_melodia_battr", "") == belly_attr:
        return mat
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
    color_out = bsdf.inputs["Base Color"]
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
        mr.inputs["To Max"].default_value = 0.22
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
        color_out = mix.outputs["Result"]
    if belly is not None:
        # point-domain mask stored by the builder (1.0 = underside)
        battr = nt.nodes.new("ShaderNodeAttribute")
        battr.location = (-600, -300)
        battr.attribute_name = belly_attr
        bmr = nt.nodes.new("ShaderNodeMapRange")
        bmr.location = (-300, -300)
        bmr.inputs["To Min"].default_value = 0.0
        bmr.inputs["To Max"].default_value = 1.0
        try:
            bmr.clamp = True
        except Exception:
            pass
        nt.links.new(battr.outputs["Fac"], bmr.inputs["Value"])
        bmix = nt.nodes.new("ShaderNodeMix")
        bmix.location = (0, -260)
        bmix.data_type = "RGBA"
        bmix.inputs["A"].default_value = (*base_color, 1.0)
        bmix.inputs["B"].default_value = (*belly, 1.0)
        # A = pre-belly color: whatever color_out currently drives (flow result
        # when flow=True, otherwise the A default = base color)
        if color_out.is_output:
            nt.links.new(color_out, bmix.inputs["A"])
        nt.links.new(bmr.outputs["Result"], bmix.inputs["Factor"])
        color_out = bmix.outputs["Result"]
    _bc = bsdf.inputs["Base Color"]
    # RNA wrappers are fresh objects per access -> never compare node identity.
    # The real invariant: color_out must be an OUTPUT socket to drive Base Color.
    if color_out.is_output:
        nt.links.new(color_out, _bc)
    mat["_melodia_sig"] = json.dumps(sig)
    mat["mel_fish"] = "1"
    return mat


# ---------------------------------------------------------------------------
# Element gem taxonomy (P2 variety - canon: brooch gem map, no inventing)
# ---------------------------------------------------------------------------

_ELEMENTS = (
    # name, gem, accent (dorsal crest + fins), body wash
    ("tide", "Aquamarine", (0.30, 0.78, 0.74), (0.80, 0.90, 0.88)),
    ("radiant", "Opal", (0.72, 0.90, 0.82), (0.93, 0.90, 0.94)),
    ("forte", "Ruby", (0.86, 0.26, 0.34), (0.92, 0.78, 0.80)),
    ("arcane", "Amethyst", (0.60, 0.44, 0.86), (0.87, 0.80, 0.92)),
    ("umbral", "Onyx", (0.20, 0.20, 0.26), (0.58, 0.58, 0.66)),
    ("stone", "Jade", (0.36, 0.70, 0.52), (0.78, 0.88, 0.80)),
    ("gale", "Citrine", (0.90, 0.76, 0.30), (0.93, 0.90, 0.78)),
)


def _ensure_fish_materials(element=None):
    """Element colorways: None = canon pearl-pink; else the gem taxonomy.

    Variant materials get a ``_tide``-style suffix so all eight sets coexist.
    The pearl-white belly and gold bead eyes stay canon for every element
    (one feeling: a hatched note, still wet); the element reads in the body
    wash + dorsal/fin accents.
    """
    if element is None:
        body_c = (0.87, 0.66, 0.76)
        fin_c = (0.86, 0.78, 0.92)
        dor_c = (0.58, 0.53, 0.86)
        suffix = ""
    else:
        gem = {e[0]: e for e in _ELEMENTS}.get(element)
        if gem is None:
            raise ValueError("unknown element: %s" % element)
        acc = gem[2]
        # body = pearl-pink pulled halfway to the gem hue: unmistakable at
        # school scale, still pastel enough for the one-feeling rule
        PEARL = (0.87, 0.66, 0.76)
        body_c = tuple(0.5 * a + 0.5 * p for a, p in zip(acc, PEARL))
        fin_c = tuple(0.45 + 0.55 * c for c in acc)
        dor_c = tuple(0.82 * c for c in acc)
        suffix = "_" + element
    body = _fish_material("MEL_fish_body" + suffix, body_c, metallic=0.15,
                          roughness=0.32, flow=True,
                          belly=(0.98, 0.96, 0.94))
    fin = _fish_material("MEL_fish_fin" + suffix, fin_c, metallic=0.05,
                         roughness=0.45, flow=True)
    dorsal = _fish_material("MEL_fish_dorsal" + suffix, dor_c, metallic=0.08,
                            roughness=0.38, flow=True)
    eye = _fish_material("MEL_fish_eye" + suffix, (0.95, 0.78, 0.35),
                         metallic=1.0, roughness=0.22)
    mouth = _fish_material("MEL_fish_mouth" + suffix, (0.30, 0.16, 0.24),
                           roughness=0.5)
    return body, fin, dorsal, eye, mouth


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


def build_music_note_fish(group_name="MEL_music_note_fish", element=None):
    """Note fish: note-head body + flag tail + side fins + bead eyes.

    UVs: UVMap (analytic cylindrical wrap) and UVFlow (animated, seam-exact
    loop with integer Flow Cycles). element=None builds the canon pearl-pink
    fish under ``MEL_music_note_fish``; an element name builds
    ``MEL_music_note_fish_<element>`` with that element's gem colorway.
    """
    if element is not None:
        group_name = "MEL_music_note_fish_" + element
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.2, 3.0)
    add_int_param(tree, "Flow Cycles", 2, 0, 8)
    add_int_param(tree, "Loop Frames", 96, 24, 480)
    add_float_param(tree, "Phase", 0.0, 0.0, 2.0)
    add_bool_param(tree, "Realize for export", False)
    _set_iface(tree, "Music Influence", 0.0)  # fish stays put; pulse is opt-in

    body_mat, fin_mat, dorsal_mat, eye_mat, mouth_mat = _ensure_fish_materials(element)

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
        head_xf.inputs["Scale"].default_value = (1.05, 0.92, 1.45)
    except Exception:
        pass
    body = _taper_by_x(tree, (bx - 620, by + 430), head_xf.outputs["Geometry"],
                       0.0, -1.05, 0.88)
    # belly/back two-tone mask (1.0 = underside; body material mixes pearl-white)
    bpos = safe_node(tree, "GeometryNodeInputPosition", (bx - 620, by + 660))
    bsep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 500, by + 660))
    bmr = safe_node(tree, "ShaderNodeMapRange", (bx - 380, by + 660))
    bstore = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 240, by + 660))
    if bpos is not None and bsep is not None and bmr is not None \
            and bstore is not None and body is not None:
        link_sockets(tree, bpos.outputs["Position"], bsep.inputs["Vector"])
        bmr.inputs["From Min"].default_value = -0.45
        bmr.inputs["From Max"].default_value = 0.10
        bmr.inputs["To Min"].default_value = 1.0
        bmr.inputs["To Max"].default_value = 0.0
        try:
            bmr.clamp = True
        except Exception:
            pass
        link_sockets(tree, bsep.outputs["Z"], bmr.inputs["Value"])
        try:
            bstore.data_type = "FLOAT"
            bstore.domain = "POINT"
            bstore.inputs["Name"].default_value = "BellyMix"
        except Exception:
            pass
        link_sockets(tree, body, bstore.inputs["Geometry"])
        link_sockets(tree, bmr.outputs["Result"],
                     bstore.inputs.get("Value") or bstore.inputs.get("Value_001"))
        body = bstore.outputs["Geometry"]
        color_node(bstore, "attribute")
    body = _setmat(tree, (bx - 700, by + 200), body, body_mat)
    parts.append(body)

    # --- tail: tapering peduncle forking into two rounded lobes ---
    ped = _sweep(tree, (bx - 500, by - 100),
                 start=(-0.95, 0.0, 0.06), start_h=(-1.12, 0.02, 0.10),
                 end=(-1.48, 0.0, 0.02), end_h=(-1.30, 0.0, 0.06),
                 radius=0.20, flat=0.45)
    ped = _taper_by_x(tree, (bx - 380, by - 100), ped, -0.95, -1.50, 0.55)
    if ped is not None:
        parts.append(_setmat(tree, (bx - 260, by - 100), ped, fin_mat))
    for i, (s, sh, e, eh) in enumerate((
            ((-1.40, 0.0, 0.02), (-1.62, 0.0, 0.26),
             (-2.05, 0.0, 0.52), (-1.86, 0.0, 0.42)),
            ((-1.40, 0.0, 0.02), (-1.60, 0.0, -0.18),
             (-1.98, 0.0, -0.56), (-1.78, 0.0, -0.44)))):
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
                     start=(0.05, sgn * 0.48, -0.05),
                     start_h=(0.15, sgn * 0.68, -0.10),
                     end=(-0.62, sgn * 1.52, -0.40),
                     end_h=(-0.92, sgn * 1.44, -0.30),
                     radius=0.16, flat=0.5)
        if fin is not None:
            parts.append(_setmat(tree, (bx - 260, by - 420 - i * 260), fin, fin_mat))

    # --- dorsal: lavender crest riding the top ridge (palette accent) ---
    dor = _sweep(tree, (bx - 500, by + 900),
                 start=(0.28, 0.0, 0.66), start_h=(0.36, 0.0, 0.76),
                 end=(-0.28, 0.0, 0.80), end_h=(-0.46, 0.0, 0.74),
                 radius=0.12, flat=0.45)
    if dor is not None:
        parts.append(_setmat(tree, (bx - 260, by + 900), dor, dorsal_mat))

    # --- eyes: two beads near the nose (+X) ---
    for i, sgn in enumerate((1.0, -1.0)):
        eye = _sphere(tree, (bx - 500, by + 520 + i * 240), 0.185)
        if eye is None:
            continue
        xf = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 520 + i * 240))
        link_sockets(tree, eye, xf.inputs["Geometry"])
        xf.inputs["Translation"].default_value = (0.74, sgn * 0.48, 0.22)
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
        v_map.inputs["From Min"].default_value = -2.25
        v_map.inputs["From Max"].default_value = 1.15
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
    "Note-creature: note-head body (pearl-white belly via BellyMix), flag tail, "
    "lavender dorsal, bead eyes; analytic UVMap + animated UVFlow (integer "
    "Flow Cycles = exact loop seam).",
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
    Bob: sin(2*pi*MODULO((Frame-1)*BobCycles/LoopFrames + Phase + i/Count, 1))
    * Bob Height - integer Bob Cycles keep the seam exact on open guides.
    Per-fish scale variance (0.86-1.12 of Fish Scale) breaks the uniform row.
    Element palette (P2): each fish picks one of the seven element fish trees
    (brooch gem taxonomy) via Pick Instance + Index %% 7 - shared animation,
    per-element colorways.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    guide = make_group_input(tree, "NodeSocketObject", "Guide", default=None)
    add_int_param(tree, "Fish Count", 7, 1, 40)
    add_float_param(tree, "Fish Scale", 0.26, 0.05, 3.0)
    add_int_param(tree, "Swim Cycles", 0, 0, 8)
    add_int_param(tree, "Bob Cycles", 2, 0, 8)
    add_float_param(tree, "Bob Height", 0.045, 0.0, 0.5)
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

    # element variant strip (P2): one pre-instanced fish per Melodia element
    # (brooch gem taxonomy). The main chain below picks among them with
    # Pick Instance + Index % 7, so bob/swim/scale stay shared and seam-exact
    # while the school shows all seven colorways. Fish Count n shows the
    # first n mod 7 elements (n = 7 -> one of each; 14 -> two of each).
    variants = []
    for ei, (ename, gem_name, _acc, _wash) in enumerate(_ELEMENTS):
        vgrp = _ensure_group_node(
            tree, "MEL_music_note_fish_" + ename,
            (lambda en: (lambda gname: build_music_note_fish(gname, element=en)))(ename),
            (bx - 1500, by - 520 - ei * 300))
        _set_in(vgrp, "Scale", 1.0)
        if vgrp is not None:
            link_sockets(tree, gin.outputs["Flow Cycles"], vgrp.inputs["Flow Cycles"])
            link_sockets(tree, gin.outputs["Loop Frames"], vgrp.inputs["Loop Frames"])
        vline = safe_node(tree, "GeometryNodeMeshLine", (bx - 1250, by - 520 - ei * 300))
        if vline is not None:
            vline.inputs["Count"].default_value = 1
            vline.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
            vline.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
            try:
                vline.name = "variant line " + ename
            except Exception:
                pass
        vinst = safe_node(tree, "GeometryNodeInstanceOnPoints",
                          (bx - 1080, by - 520 - ei * 300))
        if vinst is not None and vline is not None and vgrp is not None:
            link_sockets(tree, vline.outputs["Mesh"], vinst.inputs["Points"])
            link_sockets(tree, vgrp.outputs["Geometry"], vinst.inputs["Instance"])
            try:
                vinst.name = "variant " + ename + " (" + gem_name + ")"
            except Exception:
                pass
            color_node(vinst, "instance")
            variants.append(vinst.outputs["Instances"])

    vjoin = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 900, by - 260))
    if vjoin is not None:
        for v in variants:
            link_sockets(tree, v, vjoin.inputs["Geometry"])
        color_node(vjoin, "geometry")

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

    # seam-safe bob: sin(2*pi*MODULO((Frame-1)*BobCycles/LoopFrames
    #                 + Phase + i/Count, 1)) * Bob Height
    b_mul = _math(tree, "MULTIPLY", (bx - 1100, by - 1020), f_sub.outputs[0],
                  gin.outputs["Bob Cycles"])
    b_div = _math(tree, "DIVIDE", (bx - 950, by - 1020), b_mul.outputs[0],
                  gin.outputs["Loop Frames"])
    b_add = _math(tree, "ADD", (bx - 800, by - 1020), b_div.outputs[0],
                  gin.outputs["Phase"])
    b_add2 = _math(tree, "ADD", (bx - 650, by - 1020), b_add.outputs[0],
                   i_div.outputs[0])
    b_mod = _math(tree, "MODULO", (bx - 500, by - 1020), b_add2.outputs[0], 1.0)
    b_tau = _math(tree, "MULTIPLY", (bx - 350, by - 1020), b_mod.outputs[0], TAU)
    b_sin = _math(tree, "SINE", (bx - 200, by - 1020), b_tau.outputs[0])
    b_h = _math(tree, "MULTIPLY", (bx - 50, by - 1020), b_sin.outputs[0],
                gin.outputs["Bob Height"])

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
        b_sum = _math(tree, "ADD", (bx - 400, by + 500),
                      gin.outputs["Rise"], b_h.outputs[0])
        rz = _combine(tree, (bx - 400, by + 320), x=0.0, y=0.0,
                      z=b_sum.outputs[0] if b_sum else gin.outputs["Rise"])
        link_sockets(tree, rz.outputs["Vector"], risen.inputs["Offset"])

    align = safe_node(tree, "FunctionNodeAlignEulerToVector", (bx - 400, by - 400))
    if align is not None and sample is not None:
        try:
            align.axis = "X"
        except Exception:
            pass
        link_sockets(tree, sample.outputs["Tangent"], align.inputs["Vector"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 20, by))
    if inst is not None and vjoin is not None:
        link_sockets(tree, risen.outputs["Geometry"], inst.inputs["Points"])
        link_sockets(tree, vjoin.outputs["Geometry"], inst.inputs["Instance"])
        # element palette: deterministic i % 7 variant pick per fish
        # (5.2: Pick Instance is an input socket, not a node property)
        _set_in(inst, "Pick Instance", True)
        imod = _math(tree, "MODULO", (bx - 400, by + 180),
                     idx.outputs["Index"], float(len(_ELEMENTS)))
        if imod is not None and inst.inputs.get("Instance Index") is not None:
            link_sockets(tree, imod.outputs[0], inst.inputs["Instance Index"])
        link_sockets(tree, align.outputs["Rotation"], inst.inputs["Rotation"])
        # per-fish scale variance (deterministic per index; no seam impact)
        wn = safe_node(tree, "ShaderNodeTexWhiteNoise", (bx - 400, by + 660))
        if wn is not None:
            try:
                wn.noise_dimensions = "1D"
            except Exception:
                pass
            link_sockets(tree, idx.outputs["Index"], wn.inputs["W"])
        var = safe_node(tree, "ShaderNodeMapRange", (bx - 260, by + 660))
        if var is not None:
            var.inputs["To Min"].default_value = 0.86
            var.inputs["To Max"].default_value = 1.12
            try:
                var.clamp = True
            except Exception:
                pass
            if wn is not None:
                link_sockets(tree, wn.outputs["Value"], var.inputs["Value"])
            svar = _math(tree, "MULTIPLY", (bx - 120, by + 660),
                         var.outputs["Result"], gin.outputs["Fish Scale"])
            sv = svar.outputs[0] if svar else gin.outputs["Fish Scale"]
        else:
            sv = gin.outputs["Fish Scale"]
        sc = _combine(tree, (bx - 220, by + 320), x=sv, y=sv, z=sv)
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
    _refresh_element_refs = ("MEL_music_note_fish",) + tuple(
        "MEL_music_note_fish_" + e[0] for e in _ELEMENTS)
    for _gn in _refresh_element_refs:
        _refresh_group_refs(tree, _gn)
    if inst is not None:
        color_node(inst, "instance")

    return label_tree(tree, group_name, [
        {"title": "Guide", "nodes": ("object info",), "role": "curve"},
        {"title": "Swim", "nodes": ("time", "modulo", "sample"), "role": "attribute"},
        {"title": "Fish", "nodes": ("variant", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


register_builder(
    "MEL_music_note_school", build_music_note_school, "Note Fish School",
    "Guide-curve school: fish ride a Guide curve, tangent-aligned, index-spread; "
    "swim offset is loop-exact with integer Swim Cycles (0 = static spread); "
    "seam-safe bob (integer Bob Cycles) + per-fish scale variance. Element "
    "palette: seven gem-taxonomy fish (Pick Instance i%7) share the animation.",
    "music",
)
