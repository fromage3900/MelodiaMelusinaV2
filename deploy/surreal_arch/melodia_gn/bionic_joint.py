"""MEL_bionic_joint — marionette doll-joint builder family.

Direction (owner, 2026-09-23): joint-adjacent doll, think marionette.
NOT cyborg limbs: visible ball/hinge joints with seam rings, optional cuff
rings at clothing boundaries, and a string eyelet for the puppet read.

Vocabulary per joint type (presets, never tree copies):
  shoulder/hip  - ball joint, 2 seam rings
  elbow/knee    - hinge joint (squashed ball between 2 rings)
  wrist/ankle   - ball + cuff ring at the clothing line (absorbs the
                  hand-made DollBall_* + CuffRing_* staged 2026-09-22/23)
  neck/waist    - ball joint, 3 seam rings, eyelet

Audio: audio_amp bake-lane attribute on the full geometry (emissive seam
option rides the existing UE MPC contract, same as angel family).

Gate note: Delete Geometry deletes where Selection is TRUE, so every
optional part is gated with an inverted (1 - keep) mask.
"""
from __future__ import annotations

import bpy

from .angel_convergence import _g, _i, _math, add_audio_attributes
from .core import (
    add_bool_param, add_float_param, add_int_param,
    add_mesh_torus_linked, label_tree, link_sockets, new_geometry_tree,
    register_builder, safe_node,
)


BIONIC_PRESETS = {
    "MARIONETTE_BALANCED": {
        "label": "Marionette Balanced",
        "params": {
            "MEL_bionic_joint": {
                "Ball Radius": 0.025, "Seam Rings": 2, "Seam Width": 0.25,
                "Hinge": 0.0, "Cup Depth": 0.35, "Eyelet": 1.0,
                "Cuff": 0.0, "Cuff Radius": 0.07, "Cuff Height": 0.01,
            },
        },
    },
    "KNEE_HINGE": {
        "label": "Knee Hinge",
        "params": {
            "MEL_bionic_joint": {
                "Ball Radius": 0.032, "Seam Rings": 2, "Seam Width": 0.3,
                "Hinge": 1.0, "Cup Depth": 0.4, "Eyelet": 0.0,
                "Cuff": 0.0, "Cuff Radius": 0.07, "Cuff Height": 0.01,
            },
        },
    },
    "WRIST_BALL": {
        "label": "Wrist Ball",
        "params": {
            "MEL_bionic_joint": {
                "Ball Radius": 0.022, "Seam Rings": 1, "Seam Width": 0.3,
                "Hinge": 0.0, "Cup Depth": 0.25, "Eyelet": 0.0,
                "Cuff": 0.0, "Cuff Radius": 0.06, "Cuff Height": 0.008,
            },
        },
    },
    "ANKLE_CUFFED": {
        "label": "Ankle Cuffed",
        "params": {
            "MEL_bionic_joint": {
                "Ball Radius": 0.025, "Seam Rings": 1, "Seam Width": 0.3,
                "Hinge": 0.0, "Cup Depth": 0.0, "Eyelet": 0.0,
                "Cuff": 1.0, "Cuff Radius": 0.078, "Cuff Height": 0.008,
            },
        },
    },
    "NECK_EYELET": {
        "label": "Neck Eyelet",
        "params": {
            "MEL_bionic_joint": {
                "Ball Radius": 0.028, "Seam Rings": 3, "Seam Width": 0.2,
                "Hinge": 0.0, "Cup Depth": 0.3, "Eyelet": 1.0,
                "Cuff": 0.0, "Cuff Radius": 0.06, "Cuff Height": 0.01,
            },
        },
    },
}


def _not(tree, loc, keep_sock):
    """1 - keep, as a float mask for Delete Geometry selection."""
    one = safe_node(tree, "ShaderNodeValue", (loc[0] - 150, loc[1]))
    one.outputs[0].default_value = 1.0
    inv = _math(tree, loc, "SUBTRACT", a=_g(one, "Value"), b=keep_sock)
    return _g(inv, "Value")


def build_mel_bionic_joint(group_name="MEL_bionic_joint"):
    """Marionette joint: ball/hinge + seam rings + cups + eyelet + cuff."""
    tree, gin, gout = new_geometry_tree(group_name)

    ball_r = add_float_param(tree, "Ball Radius", 0.025, 0.01, 0.06)
    rings = add_int_param(tree, "Seam Rings", 2, 0, 4)
    seam_w = add_float_param(tree, "Seam Width", 0.25, 0.1, 0.6)
    hinge = add_float_param(tree, "Hinge", 0.0, 0.0, 1.0)
    cup_d = add_float_param(tree, "Cup Depth", 0.35, 0.0, 1.0)
    eyelet = add_bool_param(tree, "Eyelet", True)
    cuff = add_bool_param(tree, "Cuff", False)
    cuff_r = add_float_param(tree, "Cuff Radius", 0.07, 0.03, 0.12)
    cuff_h = add_float_param(tree, "Cuff Height", 0.008, 0.004, 0.02)

    one = safe_node(tree, "ShaderNodeValue", (-1600, 300))
    one.outputs[0].default_value = 1.0
    one.label = "1.0"

    join = safe_node(tree, "GeometryNodeJoinGeometry", (-150, 0))

    # ---- ball: UV sphere (true extents in all axes; ico under-extends
    # x/y to 0.895r), z-squashed by Hinge -----------------------------
    ico = safe_node(tree, "GeometryNodeMeshUVSphere", (-1200, 400))
    ico.inputs["Segments"].default_value = 24
    ico.inputs["Rings"].default_value = 12
    link_sockets(tree, ball_r, ico.inputs["Radius"])
    zscale = _math(tree, (-1200, 250), "MULTIPLY", a=hinge, const=-0.45)
    zsum = _math(tree, (-1050, 250), "ADD", a=_g(one, "Value"), b=_g(zscale, "Value"))
    scale_xyz = safe_node(tree, "ShaderNodeCombineXYZ", (-900, 250))
    link_sockets(tree, _g(one, "Value"), scale_xyz.inputs["X"])
    link_sockets(tree, _g(one, "Value"), scale_xyz.inputs["Y"])
    link_sockets(tree, _g(zsum, "Value"), scale_xyz.inputs["Z"])
    xform_ball = safe_node(tree, "GeometryNodeTransform", (-700, 400))
    link_sockets(tree, _g(ico, "Mesh"), _i(xform_ball, "Geometry"))
    link_sockets(tree, _g(scale_xyz, "Vector"), _i(xform_ball, "Scale"))
    link_sockets(tree, _g(xform_ball, "Geometry"), _i(join, "Geometry"))

    # ---- seam rings (4 fixed slots, gated by Seam Rings count) -------------
    ring_slots = [(-0.72, 0), (-0.24, 1), (0.24, 2), (0.72, 3)]
    for i, (frac, idx) in enumerate(ring_slots):
        y = -200 - i * 200
        idx_val = safe_node(tree, "ShaderNodeValue", (-1500, y))
        idx_val.outputs[0].default_value = float(idx)
        idx_val.label = "ring idx %d" % idx
        keep = _math(tree, (-1350, y), "LESS_THAN",
                     a=_g(idx_val, "Value"), b=None)
        link_sockets(tree, rings, keep.inputs[1])
        del_sel = _not(tree, (-1200, y), _g(keep, "Value"))
        major = _math(tree, (-1350, y - 100), "MULTIPLY",
                      a=ball_r, const=(1.0 - frac * frac) ** 0.5)
        minor = _math(tree, (-1200, y - 100), "MULTIPLY",
                      a=ball_r, b=None)
        link_sockets(tree, seam_w, minor.inputs[1])
        minor2 = _math(tree, (-1050, y - 100), "MULTIPLY",
                       a=_g(minor, "Value"), const=0.12)
        tor = add_mesh_torus_linked(tree, (-900, y),
                                    _g(major, "Value"), _g(minor2, "Value"))
        zoff = _math(tree, (-900, y - 220), "MULTIPLY", a=ball_r, const=frac)
        zhs = _math(tree, (-750, y - 220), "MULTIPLY",
                    a=_g(zsum, "Value"), b=_g(zoff, "Value"))
        loc = safe_node(tree, "ShaderNodeCombineXYZ", (-600, y - 100))
        link_sockets(tree, _g(zhs, "Value"), loc.inputs["Z"])
        xf = safe_node(tree, "GeometryNodeTransform", (-450, y))
        link_sockets(tree, _g(tor, "Mesh"), _i(xf, "Geometry"))
        link_sockets(tree, _g(loc, "Vector"), _i(xf, "Translation"))
        deln = safe_node(tree, "GeometryNodeDeleteGeometry", (-300, y))
        link_sockets(tree, _g(xf, "Geometry"), _i(deln, "Geometry"))
        link_sockets(tree, del_sel, _i(deln, "Selection"))
        link_sockets(tree, _g(deln, "Geometry"), _i(join, "Geometry"))

    # ---- socket cups (two truncated cones along Z, gated by Cup Depth) -----
    cup_r = _math(tree, (-1500, 600), "MULTIPLY", a=ball_r, const=0.62)
    cup_z = _math(tree, (-1350, 720), "MULTIPLY", a=ball_r, b=_g(cup_d, "Value"))
    eps = safe_node(tree, "ShaderNodeValue", (-1500, 800))
    eps.outputs[0].default_value = 0.001
    eps.label = "eps"
    keepc = _math(tree, (-1350, 800), "LESS_THAN",
                  a=_g(eps, "Value"), b=_g(cup_d, "Value"))
    delc_sel = _not(tree, (-1200, 800), _g(keepc, "Value"))
    for sign, yoff in ((1.0, 0), (-1.0, 160)):
        y = 600 + yoff
        cone = safe_node(tree, "GeometryNodeMeshCone", (-1050, y))
        link_sockets(tree, _g(cup_r, "Value"), cone.inputs["Radius Bottom"])
        link_sockets(tree, _g(cup_r, "Value"), cone.inputs["Radius Top"])
        link_sockets(tree, _g(cup_z, "Value"), cone.inputs["Depth"])
        zmul = _math(tree, (-900, y + 120), "MULTIPLY",
                     a=_g(cup_z, "Value"), const=sign)
        locc = safe_node(tree, "ShaderNodeCombineXYZ", (-750, y + 40))
        link_sockets(tree, _g(zmul, "Value"), locc.inputs["Z"])
        xfc = safe_node(tree, "GeometryNodeTransform", (-600, y))
        link_sockets(tree, _g(cone, "Mesh"), _i(xfc, "Geometry"))
        link_sockets(tree, _g(locc, "Vector"), _i(xfc, "Translation"))
        delc = safe_node(tree, "GeometryNodeDeleteGeometry", (-450, y))
        link_sockets(tree, _g(xfc, "Geometry"), _i(delc, "Geometry"))
        link_sockets(tree, delc_sel, _i(delc, "Selection"))
        link_sockets(tree, _g(delc, "Geometry"), _i(join, "Geometry"))

    # ---- eyelet: small vertical loop above the ball ------------------------
    emaj = _math(tree, (-1500, 1000), "MULTIPLY", a=ball_r, const=0.35)
    emin = _math(tree, (-1500, 1100), "MULTIPLY", a=ball_r, const=0.1)
    etor = add_mesh_torus_linked(tree, (-1350, 1000),
                                 _g(emaj, "Value"), _g(emin, "Value"))
    ez = _math(tree, (-1200, 1100), "MULTIPLY", a=ball_r, const=1.35)
    eloc = safe_node(tree, "ShaderNodeCombineXYZ", (-1050, 1100))
    link_sockets(tree, _g(ez, "Value"), eloc.inputs["Z"])
    exf = safe_node(tree, "GeometryNodeTransform", (-900, 1000))
    link_sockets(tree, _g(etor, "Mesh"), _i(exf, "Geometry"))
    link_sockets(tree, _g(eloc, "Vector"), _i(exf, "Translation"))
    exf.inputs["Rotation"].default_value = (1.5707963, 0.0, 0.0)
    dele_sel = _not(tree, (-1200, 1000), eyelet)
    dele = safe_node(tree, "GeometryNodeDeleteGeometry", (-600, 1000))
    link_sockets(tree, _g(exf, "Geometry"), _i(dele, "Geometry"))
    link_sockets(tree, dele_sel, _i(dele, "Selection"))
    link_sockets(tree, _g(dele, "Geometry"), _i(join, "Geometry"))

    # ---- cuff: torus below the ball, gated by Cuff bool --------------------
    ctor = add_mesh_torus_linked(tree, (-1350, 1300),
                                 cuff_r, cuff_h)
    cz = _math(tree, (-1200, 1400), "MULTIPLY", a=ball_r, const=-1.6)
    cloc = safe_node(tree, "ShaderNodeCombineXYZ", (-1050, 1400))
    link_sockets(tree, _g(cz, "Value"), cloc.inputs["Z"])
    cxf = safe_node(tree, "GeometryNodeTransform", (-900, 1300))
    link_sockets(tree, _g(ctor, "Mesh"), _i(cxf, "Geometry"))
    link_sockets(tree, _g(cloc, "Vector"), _i(cxf, "Translation"))
    delc2_sel = _not(tree, (-1200, 1300), cuff)
    delc2 = safe_node(tree, "GeometryNodeDeleteGeometry", (-600, 1300))
    link_sockets(tree, _g(cxf, "Geometry"), _i(delc2, "Geometry"))
    link_sockets(tree, delc2_sel, _i(delc2, "Selection"))
    link_sockets(tree, _g(delc2, "Geometry"), _i(join, "Geometry"))

    # ---- audio bake-lane attribute ------------------------------------------
    out_geo = add_audio_attributes(tree, gin, _g(join, "Geometry"), loc=(100, 200))
    link_sockets(tree, out_geo, _i(gout, "Geometry"))
    label_tree(tree, group_name)
    return tree


register_builder(
    "MEL_bionic_joint",
    build_mel_bionic_joint,
    "Bionic Marionette Joint",
    "Marionette doll joint: ball/hinge + seam rings + socket cups + "
    "string eyelet + optional cuff ring. Presets absorb the staged "
    "DollBall/CuffRing set.",
    category="bionic",
)
