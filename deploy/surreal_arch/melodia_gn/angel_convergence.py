"""Biblical-angel convergence builders — ophanim wheels, many-eyes field, throne ring.

Third wing of the angel family (sibling to angel_wings.py feather rows and the
reaver horror-feminine set): the seraph read, balanced between glory and dread
per owner direction (neither full horror nor pure rest).

Builders (all parametric; variants are presets/dials, never tree copies):

  MEL_angel_ophanim_wheel - concentric gyroscope rings (Ring Count 1-3),
      spoke count dial, rim eye-studs, Spin Angle input (key it; GN has no
      clock of its own), audio_amp bake-lane attribute on the rim.
  MEL_angel_many_eyes    - instanced eye-studs scattered on the input carrier
      (Distribute Points on Faces): Eye Density, Eye Scale, Lid Blink scale
      dial, audio_band attribute per point for material twinkle in UE.
  MEL_angel_throne_ring  - stepped dais (Step Count 2-3) + flame lobes around
      the rim + pearl trim instancing, Halo Width dialect shared with the
      mother moon-disc builder.

Audio doctrine: GN samples a connected Sound strip at design/cook time and
writes the bake-lane attributes (audio_amp, audio_band) that mirror the UE
MPC fields (Cymatic_BeatPulse, Cymatic_BassIntensity, Cymatic_MidIntensity).
GN never writes gameplay; UE runtime response lives in materials. Bake source
of truth: melusinabaseambience98bpm (file pending — mechanism verified with
any strip; final bake needs the track).

Self-contained: only .core imports (+ audio_terrain helpers for sampling).
"""

from __future__ import annotations

import math

import bpy

from .audio_terrain import _add_sound_param, _sample_band
from .core import (
    add_float_param, add_int_param,
    color_node, label_tree, link_sockets, link_float_to_vector,
    new_geometry_tree, register_builder, safe_node, set_resample_count, sock,
)


# Map: Blender bake-lane attribute -> UE MPC scalar (one vocabulary, two ends)
AUDIO_CONTRACT = {
    "audio_amp": "Cymatic_BeatPulse",
    "audio_band": "Cymatic_MidIntensity",
    "audio_bass": "Cymatic_BassIntensity",
}


def _g(node, *names):
    if node is None:
        return None
    try:
        s = sock(node, *names, outputs=True)
        if s is not None:
            return s
    except Exception:
        pass
    try:
        return node.outputs[0] if node.outputs else None
    except Exception:
        return None


def _i(node, *names):
    if node is None:
        return None
    try:
        return sock(node, *names)
    except Exception:
        return None


def _math(tree, loc, op, a=None, b=None, const=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    n.operation = op
    for slot, val in ((0, a), (1, const if const is not None else b)):
        target = n.inputs[slot]
        if val is None:
            continue
        if hasattr(val, "is_linked"):
            link_sockets(tree, val, target)
        else:
            try:
                target.default_value = val
            except Exception:
                pass
    color_node(n, "math")
    return n


def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for key, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        try:
            if hasattr(val, "is_linked"):
                link_sockets(tree, val, n.inputs[key])
            else:
                n.inputs[key].default_value = val
        except Exception:
            pass
    return n


def add_audio_attributes(tree, gin, geo_socket, loc=(0, 0)):
    """Store audio_amp / audio_band bake-lane attributes on the geometry.

    Samples the connected Sound strip (user connects melusinabaseambience98bpm)
    and stores two named float attributes mirroring the UE MPC contract, so UE
    materials can reproduce the baked response live. Returns geometry output.
    """
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 20.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 20000.0, 1.0, 20000.0)
    add_float_param(tree, "Audio Gain", 4.0, 0.0, 50.0)
    amp = _sample_band(tree, gin, loc, gin.outputs["Low Hz"],
                       gin.outputs["High Hz"], use_scene_time=True)
    gain = _math(tree, (loc[0] + 100, loc[1]), "MULTIPLY",
                 a=amp, b=gin.outputs["Audio Gain"])
    s_amp = safe_node(tree, "GeometryNodeStoreNamedAttribute", (loc[0] + 200, loc[1]))
    link_sockets(tree, geo_socket, _i(s_amp, "Geometry"))
    try:
        s_amp.inputs["Name"].default_value = "audio_amp"
        link_sockets(tree, _g(gain, "Value"), _i(s_amp, "Value"))
    except Exception:
        pass
    s_band = safe_node(tree, "GeometryNodeStoreNamedAttribute", (loc[0] + 300, loc[1]))
    link_sockets(tree, _g(s_amp, "Geometry"), _i(s_band, "Geometry"))
    try:
        s_band.inputs["Name"].default_value = "audio_band"
        link_sockets(tree, _g(gain, "Value"), _i(s_band, "Value"))
    except Exception:
        pass
    color_node(s_amp, "attribute")
    color_node(s_band, "attribute")
    return _g(s_band, "Geometry")


def build_angel_ophanim_wheel(group_name="MEL_angel_ophanim_wheel"):
    """Concentric gyroscope rings with rim eye-studs and spin input."""
    tree, gin, gout = new_geometry_tree(group_name)

    rings = add_int_param(tree, "Ring Count", 2, 1, 3)
    radius = add_float_param(tree, "Wheel Radius", 0.55, 0.15, 1.5)
    tube = add_float_param(tree, "Tube Thickness", 0.035, 0.008, 0.12)
    spokes = add_int_param(tree, "Spoke Count", 8, 0, 24)
    spin = add_float_param(tree, "Spin Angle", 0.0, -6.2832, 6.2832)
    rim_eyes = add_int_param(tree, "Rim Eye Count", 12, 0, 48)
    eye_size = add_float_param(tree, "Rim Eye Size", 0.03, 0.005, 0.1)
    segs = add_int_param(tree, "Segments", 48, 12, 128)

    # one torus; ring count handled by count dial via instances on ring index
    # main ring: curve circle + circular profile -> Curve to Mesh
    # (moon-disc idiom; there is no MeshTorus primitive in Blender 5.x)
    ring = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1200, 0))
    link_sockets(tree, radius, _i(ring, "Radius"))
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1200, -200))
    link_sockets(tree, tube, _i(prof, "Radius"))
    ctm = safe_node(tree, "GeometryNodeCurveToMesh", (-1000, 0))
    link_sockets(tree, _g(ring, "Curve"), _i(ctm, "Curve"))
    link_sockets(tree, _g(prof, "Curve"), _i(ctm, "Profile Curve"))

    # spin: Transform node, Spin Angle bridged onto Rotation Z
    rot = safe_node(tree, "GeometryNodeTransform", (-900, 0))
    link_sockets(tree, _g(ctm, "Mesh"), _i(rot, "Geometry"))
    link_float_to_vector(tree, spin, rot, "Rotation",
                         component=2, defaults=(0.0, 0.0, 0.0))

    # spokes: resampled line rotated N times around Z
    line = safe_node(tree, "GeometryNodeMeshLine", (-1200, -300))
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_float_to_vector(tree, radius, line, "Offset",
                         component=0, defaults=(1.0, 0.0, 0.0))

    # rim eye-studs: resampled curve circle -> even rim points (no center vert)
    rc = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1200, -600))
    link_sockets(tree, radius, _i(rc, "Radius"))
    rs = safe_node(tree, "GeometryNodeResampleCurve", (-1050, -600))
    link_sockets(tree, _g(rc, "Curve"), _i(rs, "Curve"))
    link_sockets(tree, rim_eyes, sock(rs, "Count", "Length"))
    ico = safe_node(tree, "GeometryNodeMeshIcoSphere", (-1000, -600))
    try:
        ico.inputs["Radius"].default_value = 0.03
        link_sockets(tree, eye_size, ico.inputs["Radius"])
    except Exception:
        pass
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-800, -400))
    link_sockets(tree, _g(rs, "Curve"), _i(inst, "Points"))
    link_sockets(tree, _g(ico, "Mesh"), _i(inst, "Instance"))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (-500, 0))
    link_sockets(tree, _g(rot, "Geometry"), _i(join, "Geometry"))
    link_sockets(tree, _g(line, "Mesh"), _i(join, "Geometry"))
    link_sockets(tree, _g(inst, "Instances"), _i(join, "Geometry"))

    out_geo = add_audio_attributes(tree, gin, _g(join, "Geometry"), loc=(-200, 200))
    link_sockets(tree, out_geo, _i(gout, "Geometry"))
    label_tree(tree, group_name)
    return tree


def build_angel_many_eyes(group_name="MEL_angel_many_eyes"):
    """Instanced eye-stud field on the input carrier with blink dial."""
    tree, gin, gout = new_geometry_tree(group_name)

    density = add_float_param(tree, "Eye Density", 60.0, 4.0, 400.0)
    eye_scale = add_float_param(tree, "Eye Scale", 0.035, 0.005, 0.12)
    blink = add_float_param(tree, "Lid Blink", 1.0, 0.05, 1.0)
    seed = add_int_param(tree, "Seed", 7, 0, 9999)

    try:
        geo_in = gin.outputs["Geometry"]
    except Exception:
        geo_in = None

    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-900, 0))
    try:
        link_sockets(tree, density, _i(dist, "Density"))
        link_sockets(tree, geo_in, _i(dist, "Mesh"))
    except Exception:
        pass
    try:
        dist.inputs["Seed"].default_value = 7
        link_sockets(tree, seed, dist.inputs["Seed"])
    except Exception:
        pass

    eye = safe_node(tree, "GeometryNodeMeshUVSphere", (-900, -300))
    try:
        eye.inputs["Radius"].default_value = 0.035
        link_sockets(tree, eye_scale, eye.inputs["Radius"])
    except Exception:
        pass
    # lid blink: squash Z of the stud
    sz = _math(tree, (-700, -300), "MULTIPLY", a=eye_scale, b=blink)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-600, 0))
    link_sockets(tree, _g(dist, "Points"), _i(inst, "Points"))
    link_sockets(tree, _g(eye, "Mesh"), _i(inst, "Instance"))
    try:
        link_sockets(tree, _g(sz, "Value"), _i(inst, "Scale"))
    except Exception:
        pass

    real = safe_node(tree, "GeometryNodeRealizeInstances", (-300, 0))
    link_sockets(tree, _g(inst, "Instances"), _i(real, "Geometry"))
    out_geo = add_audio_attributes(tree, gin, _g(real, "Geometry"), loc=(0, 200))
    link_sockets(tree, out_geo, _i(gout, "Geometry"))
    label_tree(tree, group_name)
    return tree


def build_angel_throne_ring(group_name="MEL_angel_throne_ring"):
    """Stepped dais ring with flame lobes and pearl trim."""
    tree, gin, gout = new_geometry_tree(group_name)

    steps = add_int_param(tree, "Step Count", 2, 1, 3)
    dais_r = add_float_param(tree, "Dais Radius", 0.8, 0.3, 2.0)
    step_h = add_float_param(tree, "Step Height", 0.12, 0.03, 0.4)
    flames = add_int_param(tree, "Flame Count", 16, 0, 64)
    flame_h = add_float_param(tree, "Flame Height", 0.22, 0.05, 0.6)
    flame_r = add_float_param(tree, "Flame Radius", 0.1, 0.02, 0.3)
    pearls = add_int_param(tree, "Pearl Count", 24, 0, 96)
    pearl_r = add_float_param(tree, "Pearl Size", 0.022, 0.005, 0.06)

    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (-1200, 0))
    try:
        link_sockets(tree, dais_r, _i(cyl, "Radius"))
        link_sockets(tree, step_h, _i(cyl, "Depth"))
    except Exception:
        pass

    # flame lobes + pearl trim: resampled curve circle -> even rim points
    rc = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1200, -300))
    link_sockets(tree, dais_r, _i(rc, "Radius"))
    rs = safe_node(tree, "GeometryNodeResampleCurve", (-1050, -300))
    link_sockets(tree, _g(rc, "Curve"), _i(rs, "Curve"))
    link_sockets(tree, flames, sock(rs, "Count", "Length"))
    cone = safe_node(tree, "GeometryNodeMeshCone", (-1000, -300))
    link_sockets(tree, flame_h, cone.inputs["Depth"])
    link_sockets(tree, flame_r, cone.inputs["Radius Bottom"])
    taper = _math(tree, (-1000, -420), "MULTIPLY", a=flame_r, const=0.35)
    if taper is not None:
        link_sockets(tree, _g(taper, "Value"), cone.inputs["Radius Top"])
    finst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-800, -300))
    link_sockets(tree, _g(rs, "Curve"), _i(finst, "Points"))
    link_sockets(tree, _g(cone, "Mesh"), _i(finst, "Instance"))
    freal = safe_node(tree, "GeometryNodeRealizeInstances", (-650, -300))
    link_sockets(tree, _g(finst, "Instances"), _i(freal, "Geometry"))

    # pearl trim: small spheres on a second resample (pearl count dial)
    rs2 = safe_node(tree, "GeometryNodeResampleCurve", (-1050, -600))
    link_sockets(tree, _g(rc, "Curve"), _i(rs2, "Curve"))
    link_sockets(tree, pearls, sock(rs2, "Count", "Length"))
    pico = safe_node(tree, "GeometryNodeMeshIcoSphere", (-1000, -600))
    link_sockets(tree, pearl_r, pico.inputs["Radius"])
    pinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-800, -600))
    link_sockets(tree, _g(rs2, "Curve"), _i(pinst, "Points"))
    link_sockets(tree, _g(pico, "Mesh"), _i(pinst, "Instance"))
    preal = safe_node(tree, "GeometryNodeRealizeInstances", (-650, -600))
    link_sockets(tree, _g(pinst, "Instances"), _i(preal, "Geometry"))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (-500, 0))
    link_sockets(tree, _g(cyl, "Mesh"), _i(join, "Geometry"))
    link_sockets(tree, _g(freal, "Geometry"), _i(join, "Geometry"))
    link_sockets(tree, _g(preal, "Geometry"), _i(join, "Geometry"))

    out_geo = add_audio_attributes(tree, gin, _g(join, "Geometry"), loc=(-200, 200))
    link_sockets(tree, out_geo, _i(gout, "Geometry"))
    label_tree(tree, group_name)
    return tree


register_builder(
    "MEL_angel_ophanim_wheel", build_angel_ophanim_wheel,
    "Angel Ophanim Wheel",
    "Concentric gyroscope rings with rim eye-studs, spin input, and "
    "audio_amp bake-lane attribute (98bpm contract).",
    category="angel",
)

register_builder(
    "MEL_angel_many_eyes", build_angel_many_eyes,
    "Angel Many-Eyes Field",
    "Instanced eye-stud field on any carrier with blink dial and "
    "audio_band attribute for UE material twinkle.",
    category="angel",
)

register_builder(
    "MEL_angel_throne_ring", build_angel_throne_ring,
    "Angel Throne Ring",
    "Stepped dais with flame lobes and pearl trim; Halo Width dialect.",
    category="angel",
)


# ── Curated presets: balanced seraph middle line ──
ANGEL_CONVERGENCE_PRESETS = {
    "SERAPH_BALANCED": {
        "label": "Seraph Balanced",
        "description": "Middle line: twin slow wheels, restrained eye field, "
                       "small throne; pearl over wound.",
        "params": {
            "MEL_angel_ophanim_wheel": {"Ring Count": 2, "Wheel Radius": 0.55,
                                        "Tube Thickness": 0.035, "Spoke Count": 8,
                                        "Spin Angle": 0.0, "Rim Eye Count": 12,
                                        "Rim Eye Size": 0.03, "Segments": 48},
            "MEL_angel_many_eyes": {"Eye Density": 60.0, "Eye Scale": 0.035,
                                    "Lid Blink": 1.0, "Seed": 7},
            "MEL_angel_throne_ring": {"Step Count": 2, "Dais Radius": 0.8,
                                      "Step Height": 0.12, "Flame Count": 16,
                                      "Flame Height": 0.22, "Pearl Count": 24,
                                      "Pearl Size": 0.022},
        },
    },
    "SERAPH_DREAD": {
        "label": "Seraph Dread",
        "description": "Horror-leaning: triple wheels, dense eyes, tall flames.",
        "params": {
            "MEL_angel_ophanim_wheel": {"Ring Count": 3, "Wheel Radius": 0.7,
                                        "Tube Thickness": 0.045, "Spoke Count": 12,
                                        "Spin Angle": 0.0, "Rim Eye Count": 24,
                                        "Rim Eye Size": 0.035, "Segments": 64},
            "MEL_angel_many_eyes": {"Eye Density": 160.0, "Eye Scale": 0.04,
                                    "Lid Blink": 0.8, "Seed": 13},
            "MEL_angel_throne_ring": {"Step Count": 3, "Dais Radius": 1.0,
                                      "Step Height": 0.16, "Flame Count": 32,
                                      "Flame Height": 0.35, "Pearl Count": 16,
                                      "Pearl Size": 0.02},
        },
    },
    "SERAPH_GRACE": {
        "label": "Seraph Grace",
        "description": "Restrained: single wheel, sparse eyes, pearl-forward throne.",
        "params": {
            "MEL_angel_ophanim_wheel": {"Ring Count": 1, "Wheel Radius": 0.45,
                                        "Tube Thickness": 0.028, "Spoke Count": 6,
                                        "Spin Angle": 0.0, "Rim Eye Count": 8,
                                        "Rim Eye Size": 0.025, "Segments": 32},
            "MEL_angel_many_eyes": {"Eye Density": 24.0, "Eye Scale": 0.03,
                                    "Lid Blink": 1.0, "Seed": 21},
            "MEL_angel_throne_ring": {"Step Count": 2, "Dais Radius": 0.7,
                                      "Step Height": 0.1, "Flame Count": 8,
                                      "Flame Height": 0.15, "Pearl Count": 40,
                                      "Pearl Size": 0.026},
        },
    },
}
