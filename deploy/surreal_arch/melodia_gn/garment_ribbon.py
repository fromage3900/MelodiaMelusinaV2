"""Garment ribbon kit - flowing ribbon bands hanging from a garment guide ring.

Sibling to skirt_decor.py in the Nikki decor language. Where the charm row
hangs a rigid ornament per station, this kit sweeps a flat ribbon BAND per
station: a mesh line dropped along -Z, bowed by a half-sine sag, waved by a
harmonic whose envelope opens toward the free tip, widened by an edge extrude.

The band is anchored at local z = 0 (the guide) and hangs downward, so
``Hang Length`` reads as ribbon drop below the guide, matching ``Hang`` on
the charm row. Per-station variation uses the deterministic bead-string
idiom (1 + Jitter * sin(Index * k)) - no seed param, stable under re-eval.

* guides are NodeSocketObject params with an in-graph curve fallback, never
  hard-coded Object Info pointers (family convention);
* ``Ribbon Count`` 0 is a hard passthrough of the host geometry (neutrality
  at interface defaults), via a geometry Switch on Count > 0;
* Realize Instances sits at the tail so evaluated meshes are visible to
  new_from_object (instances-domain eval truth).

Requires skirt_decor.py helpers (laptop-lane module): import resolves in the
live AppData install; repo deploys must converge skirt_decor alongside.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    add_bool_param, add_float_param, add_int_param,
    color_node, label_tree, link_sockets, link_float_to_vector,
    new_geometry_tree, register_builder, require_node, safe_node,
)
from .skirt_decor import (
    _combine, _feed, _frames, _gsock, _guide_geometry, _guide_params,
    _isock, _join, _material_param, _mk, _out, _resample, _set_material,
    _set_position, _shade, V,
)


def _build_ribbon_band(tree, loc, hang, sag, wave_count, wave_amp, width, segments):
    """The shared ribbon strip: anchor at origin, hangs down -Z.

    Returns the finished geometry socket (shaded, attributes stored).
    """
    bx, by = loc

    # mesh line: Segments steps, each (0,0,-Hang/(Segments-1)) -> per-step offset trap
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1400, by))
    line.mode = "OFFSET"
    link_sockets(tree, segments, _isock(line, "Count"))
    segs_m1 = _mk(tree, (bx - 1580, by - 160), "SUBTRACT", const=1, a=segments)
    seg_len = _out(tree, (bx - 1700, by - 160), "DIVIDE", a=hang, b=V(segs_m1))
    seg_dn = _out(tree, (bx - 1820, by - 160), "MULTIPLY", const=-1.0, a=seg_len)
    link_float_to_vector(tree, seg_dn, line, "Offset", component=2,
                         defaults=(0.0, 0.0, 1.0))

    # t = Index / (Segments - 1)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 1580, by - 380))
    color_node(idx, "attribute")
    t = _out(tree, (bx - 1440, by - 380), "DIVIDE", a=_gsock(idx, "Index"),
             b=V(segs_m1))

    # sag: half-sine bulge, zero at both ends -> x_sag = Sag * Hang * sin(pi * t)
    pi_t = _out(tree, (bx - 1300, by - 520), "MULTIPLY", const=math.pi, a=t)
    sag_x = _out(tree, (bx - 1140, by - 520), "MULTIPLY",
                 a=_out(tree, (bx - 1300, by - 640), "MULTIPLY", a=sag, b=hang),
                 b=_out(tree, (bx - 1140, by - 640), "SINE", a=pi_t))

    # wave: x_wave = WaveAmp * Hang * sin(WaveCount * 2pi * t) * t  (tip envelope)
    phase = _out(tree, (bx - 980, by - 520), "MULTIPLY",
                 a=_out(tree, (bx - 1140, by - 760), "MULTIPLY",
                        a=wave_count, b=math.tau),
                 b=t)
    wave_x = _out(tree, (bx - 820, by - 520), "MULTIPLY",
                  a=_out(tree, (bx - 980, by - 640), "SINE", a=phase),
                  b=_out(tree, (bx - 980, by - 760), "MULTIPLY", a=wave_amp, b=hang))
    wave_env = _out(tree, (bx - 660, by - 520), "MULTIPLY", a=wave_x, b=t)
    x_total = _out(tree, (bx - 500, by - 560), "ADD", a=sag_x, b=wave_env)

    # position = (x_total, 0, z) - keep the line's hanging z
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 1440, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 1280, by - 200))
    link_sockets(tree, _gsock(pos, "Position"), sep.inputs["Vector"])
    position = _combine(tree, (bx - 340, by - 460),
                        x=x_total, y=None, z=_gsock(sep, "Z"))
    set_pos = _set_position(tree, (bx - 160, by),
                            _gsock(line, "Mesh"), position=position)

    # width: edge extrude along local X (strip lies along Z)
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx + 40, by))
    extrude.mode = "EDGES"
    link_sockets(tree, set_pos, extrude.inputs["Mesh"])
    link_float_to_vector(tree, width, extrude, "Offset Scale", component=0,
                         defaults=(1.0, 0.0, 0.0))
    color_node(extrude, "geometry")

    shaded = _shade(tree, (bx + 220, by), _gsock(extrude, "Mesh"))

    # per-point attributes for shader shimmer + downstream lanes
    store_t = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_t.data_type = "FLOAT"
    store_t.domain = "POINT"
    link_sockets(tree, shaded, store_t.inputs["Geometry"])
    _isock(store_t, "Name").default_value = "ribbon_t"
    link_sockets(tree, t, _isock(store_t, "Value"))

    store_w = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 580, by))
    store_w.data_type = "FLOAT"
    store_w.domain = "POINT"
    link_sockets(tree, _gsock(store_t, "Geometry"), store_w.inputs["Geometry"])
    _isock(store_w, "Name").default_value = "ribbon_width"
    link_sockets(tree, width, _isock(store_w, "Value"))

    return _gsock(store_w, "Geometry")


def build_garm_ribbon_trail(group_name="MEL_garm_ribbon_trail"):
    """Flowing ribbon bands hanging from a guide ring - the garment ribbon run.

    Params:
        Ribbon Count: bands around the ring (0 = hard passthrough, neutral)
        Hang Length:  ribbon drop below the guide (m)
        Sag:          half-sine bow depth as a fraction of Hang (0 = straight)
        Wave Count:   harmonic waves along each band (float, art-directable)
        Wave Amp:     wave amplitude as a fraction of Hang
        Ribbon Width: band width (m)
        Jitter:       per-station scale variation (deterministic, seeded by Index)
        Spin Variety: per-station yaw scatter - which way each bow faces
        Segments:     band resolution along its length
    """
    tree, gin, gout = new_geometry_tree(group_name)

    guide, guide_curve, use_curve = _guide_params(tree)
    ring_from_host = add_bool_param(tree, "Ring From Host", True)
    ring_scale = add_float_param(tree, "Ring Scale", 1.0, 0.4, 1.6)
    anchor_band = add_float_param(tree, "Anchor Band", 0.12, 0.0, 1.0)
    count = add_int_param(tree, "Ribbon Count", 0, 0, 64)
    hang = add_float_param(tree, "Hang Length", 0.35, 0.0, 1.2)
    sag = add_float_param(tree, "Sag", 0.45, 0.0, 1.0)
    wave_count = add_float_param(tree, "Wave Count", 2.5, 0.0, 10.0)
    wave_amp = add_float_param(tree, "Wave Amp", 0.05, 0.0, 0.3)
    width = add_float_param(tree, "Ribbon Width", 0.035, 0.002, 0.15)
    jitter = add_float_param(tree, "Jitter", 0.25, 0.0, 1.0)
    spin = add_float_param(tree, "Spin Variety", 0.6, 0.0, 1.0)
    segments = add_int_param(tree, "Segments", 32, 8, 96)
    mat = _material_param(tree)

    guide_geom = _guide_geometry(tree, (-1600, 0), guide, guide_curve, use_curve)

    # host-derived hem ring (height-aware default): bbox Z at Anchor Band,
    # radius = half the max XY extent x Ring Scale
    bb = require_node(tree, "GeometryNodeBoundBox", (-1980, -180),
                      "GeometryNodeBoundingBox")
    color_node(bb, "attribute")
    link_sockets(tree, gin.outputs["Geometry"], bb.inputs["Geometry"])
    sep_min = safe_node(tree, "ShaderNodeSeparateXYZ", (-1820, -100))
    link_sockets(tree, _gsock(bb, "Min"), sep_min.inputs["Vector"])
    sep_max = safe_node(tree, "ShaderNodeSeparateXYZ", (-1820, -260))
    link_sockets(tree, _gsock(bb, "Max"), sep_max.inputs["Vector"])
    span_z = _out(tree, (-1660, -260), "SUBTRACT", a=_gsock(sep_max, "Z"),
                  b=_gsock(sep_min, "Z"))
    band_z = _out(tree, (-1500, -260), "ADD", a=_gsock(sep_min, "Z"),
                  b=_out(tree, (-1660, -360), "MULTIPLY", a=anchor_band, b=span_z))
    center_x = _out(tree, (-1660, -100), "MULTIPLY", const=0.5,
                    a=_out(tree, (-1820, -60), "ADD", a=_gsock(sep_min, "X"),
                           b=_gsock(sep_max, "X")))
    center_y = _out(tree, (-1660, -160), "MULTIPLY", const=0.5,
                    a=_out(tree, (-1820, -160), "ADD", a=_gsock(sep_min, "Y"),
                           b=_gsock(sep_max, "Y")))
    extent_x = _out(tree, (-1820, -420), "SUBTRACT", a=_gsock(sep_max, "X"),
                    b=_gsock(sep_min, "X"))
    extent_y = _out(tree, (-1820, -520), "SUBTRACT", a=_gsock(sep_max, "Y"),
                    b=_gsock(sep_min, "Y"))
    radius = _out(tree, (-1500, -460), "MULTIPLY",
                  a=_out(tree, (-1660, -470), "MULTIPLY", const=0.5,
                         a=_out(tree, (-1820, -620), "MAXIMUM", a=extent_x,
                                b=extent_y)),
                  b=ring_scale)
    circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1340, -180))
    color_node(circle, "curve")
    _feed_int(circle, "Resolution", 64)
    link_sockets(tree, radius, _isock(circle, "Radius"))
    ring = safe_node(tree, "GeometryNodeTransform", (-1180, -180))
    color_node(ring, "geometry")
    link_sockets(tree, _gsock(circle, "Curve"), ring.inputs["Geometry"])
    _feed(tree, _combine(tree, (-1340, -340), x=center_x, y=center_y, z=band_z),
          ring.inputs["Translation"])
    guide_final = _geometry_switch_sw(tree, (-1020, -180),
                                      ring_from_host,
                                      _gsock(ring, "Geometry"), guide_geom)
    stations = _resample(tree, (-1400, 120), guide_final, count)

    # per-station deterministic jitter: 1 + Jitter * sin(Index * 12.9898) [bead-string idiom]
    idx = safe_node(tree, "GeometryNodeInputIndex", (-1400, -420))
    color_node(idx, "attribute")
    jf = _out(tree, (-1000, -420), "ADD", 1.0,
              a=_mk(tree, (-1160, -420), "MULTIPLY",
                    a=_out(tree, (-1320, -420), "SINE",
                           a=_out(tree, (-1480, -420), "MULTIPLY",
                                  a=_gsock(idx, "Index"), b=12.9898)),
                    b=jitter))
    scale_v = _combine(tree, (-840, -300), x=jf, y=jf, z=jf)

    # per-station yaw scatter: SpinVariety * 2pi * sin(Index * 7.771)
    rot_z = _out(tree, (-1000, -560), "MULTIPLY",
                 a=_out(tree, (-1160, -560), "MULTIPLY", a=spin, b=math.tau),
                 b=_out(tree, (-1320, -560), "SINE",
                        a=_out(tree, (-1480, -560), "MULTIPLY",
                               a=_gsock(idx, "Index"), b=7.771)))
    rot_v = _combine(tree, (-840, -560), x=None, y=None, z=rot_z)

    band = _build_ribbon_band(tree, (200, 400), hang, sag, wave_count,
                              wave_amp, width, segments)

    charms = safe_node(tree, "GeometryNodeInstanceOnPoints", (-640, 120))
    color_node(charms, "instance")
    link_sockets(tree, stations, charms.inputs["Points"])
    link_sockets(tree, band, charms.inputs["Instance"])
    link_sockets(tree, scale_v, charms.inputs["Scale"])
    link_sockets(tree, rot_v, charms.inputs["Rotation"])

    realized = safe_node(tree, "GeometryNodeRealizeInstances", (-460, 120))
    color_node(realized, "geometry")
    link_sockets(tree, _gsock(charms, "Instances"), realized.inputs["Geometry"])

    orn = _set_material(tree, (-280, 120), _gsock(realized, "Geometry"),
                        material_sock=mat)
    merged = _join(tree, (-100, 120), [gin.outputs["Geometry"], orn])

    # Count > 0 gates the whole branch; 0 = hard host passthrough (neutrality)
    enabled = safe_node(tree, "FunctionNodeCompare", (-1560, 300))
    enabled.data_type = "INT"
    enabled.operation = "GREATER_THAN"
    link_sockets(tree, count, enabled.inputs[0])
    enabled.inputs[1].default_value = 0
    out = _geometry_switch_sw(tree, (-1600, -900), _gsock(enabled, "Result"),
                              merged, gin.outputs["Geometry"])
    link_sockets(tree, out, gout.inputs["Geometry"])

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Guide", "curve", guide_geom, stations),
        ("Band", "curve", band),
        ("Ribbon Row", "instance", charms, realized),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


def _feed_int(node, input_name, value):
    """Write an int default through sock()-resolved input (None-safe)."""
    if node is None:
        return
    s = _isock(node, input_name)
    if s is not None:
        try:
            s.default_value = value
        except Exception:
            pass


def _geometry_switch_sw(tree, loc, condition_sock, when_true, when_false):
    """Geometry Switch - local copy to keep skirt_decor import surface stable."""
    n = safe_node(tree, "GeometryNodeSwitch", loc)
    if n is None:
        return when_false
    try:
        n.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, condition_sock, n.inputs["Switch"])
    if when_true is not None:
        link_sockets(tree, when_true, n.inputs["True"])
    if when_false is not None:
        link_sockets(tree, when_false, n.inputs["False"])
    color_node(n, "geometry")
    return _gsock(n, "Output")


try:
    from .core import register_builder as _rb  # noqa: F401

    register_builder(
        "MEL_garm_ribbon_trail", build_garm_ribbon_trail,
        "Garment Ribbon Trail",
        "Flowing ribbon bands from a guide ring: catenary sag, tip-enveloped "
        "harmonic wave, deterministic jitter, yaw scatter; Count 0 = passthrough",
        category="decor",
    )
    print("[garment_ribbon] registered MEL_garm_ribbon_trail")
except ImportError:
    print("[garment_ribbon] standalone mode (no core registry)")


if __name__ == "__main__":
    build_garm_ribbon_trail()
