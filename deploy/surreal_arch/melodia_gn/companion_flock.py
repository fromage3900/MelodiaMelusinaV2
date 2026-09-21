"""Choral Sheep flock — audio-based GN variants (offline authoring/bake lane).

Blender 5.2 native-audio Geometry Node builders for Mr Sheep's flock.
Unreal remains the runtime rhythm authority; these trees are for flock
staging, lookdev, and bake-time preview. Never a second audio writer.

Trees
  MEL_sheep_choral_flock
      Ring-stages N sheep from one body object (Subject socket). Cymatic
      wool bloom on the body: analytic Chladni psi from UVs (same contract
      as MEL_garm_chladni_layer), antinode-weighted, audio band swells it.
      Each instance breathes on a golden-angle-staggered phase and faces
      inward. Stores chladni_psi + audio_amplitude (POINT) for handoff.
  MEL_sheep_wool_bloom
      Fleece-sprig distributor: Poisson points weighted by |psi| over the
      body, instancing micro-tuft spheres; Bloom Density 0 = exact
      passthrough (neutrality gate).

UV contract: 5.2 removed the GN UV input node; psi reads UVs through
GeometryNodeInputNamedAttribute (FLOAT2, name from "UV Attrib" dial,
default "uv" = active render UV). Missing UV => psi=0 => neutral, never NaN.

Per-instance eigen (m,n): instances SHARE the body's psi (a single mesh
cannot carry 12 different nodal fields without realize-per-instance). The
flock's mode variety comes from phase-staggered breathing + per-sheep
modifier dials in staging (set Eigen M/N per object). Baked eigenmode maps
from chladni_eigen.py remain the ship authority.

5.2 traps honored: silent-zero audio fallback; no scalar into Set Position
Offset (VectorMath SCALE only); ShaderNodeClamp output is 'Result' (unused
here by design); MODULO/FLOOR instead of arrays; Realize tail behind a bool;
dials wired multiply so 0 = neutral; NODES modifier type at the call site.
"""
from __future__ import annotations

import bpy  # noqa: F401  (builders run inside Blender)

from .core import (
    add_bool_param,
    add_float_param,
    add_int_param,
    add_string_param,
    apply_universal_music_pass,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .audio_terrain import _add_sound_param

PI = 3.14159265
TAU = 6.2831853
GOLDEN = 2.3999632


def _psi_chain(tree, gin, uv_loc, m_sock, n_sock):
    """psi = sin(m*pi*u) * sin(n*pi*v) from the UV named attribute.

    m_sock/n_sock may be group sockets OR static float sockets from math nodes
    (they only need to be linkable float outputs — for constants we build
    ShaderNodeValue nodes upstream). Returns (psi_out, |psi|_out, uv_node).
    """
    x, y = uv_loc
    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (x - 260, y))
    # 5.2: NamedAttribute enum has no FLOAT2 — UV reads as FLOAT_VECTOR (z=0)
    attr.data_type = "FLOAT_VECTOR"
    if gin.outputs.get("UV Attrib") is not None:
        link_sockets(tree, gin.outputs["UV Attrib"], attr.inputs["Name"])
    else:
        attr.inputs["Name"].default_value = "uv"
    sepu = safe_node(tree, "ShaderNodeSeparateXYZ", (x - 80, y))
    link_sockets(tree, attr.outputs["Attribute"], sepu.inputs["Vector"])

    def mul(loc, a_sock, b_sock=None, b_const=None):
        n = safe_node(tree, "ShaderNodeMath", loc)
        n.operation = "MULTIPLY"
        link_sockets(tree, a_sock, n.inputs[0])
        if b_sock is not None:
            link_sockets(tree, b_sock, n.inputs[1])
        else:
            n.inputs[1].default_value = b_const
        return n.outputs[0]

    def sin(loc, a_sock):
        n = safe_node(tree, "ShaderNodeMath", loc)
        n.operation = "SINE"
        link_sockets(tree, a_sock, n.inputs[0])
        return n.outputs[0]

    arg_u = mul((x + 100, y + 90), sepu.outputs["X"], b_const=PI)
    arg_u = mul((x + 260, y + 90), arg_u, b_sock=m_sock)
    arg_v = mul((x + 100, y - 110), sepu.outputs["Y"], b_const=PI)
    arg_v = mul((x + 260, y - 110), arg_v, b_sock=n_sock)
    s_u = sin((x + 430, y + 90), arg_u)
    s_v = sin((x + 430, y - 110), arg_v)
    psi = safe_node(tree, "ShaderNodeMath", (x + 600, y - 10))
    psi.operation = "MULTIPLY"
    link_sockets(tree, s_u, psi.inputs[0])
    link_sockets(tree, s_v, psi.inputs[1])
    neg = safe_node(tree, "ShaderNodeMath", (x + 600, y - 190))
    neg.operation = "MULTIPLY"
    link_sockets(tree, psi.outputs[0], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    wabs = safe_node(tree, "ShaderNodeMath", (x + 770, y - 60))
    wabs.operation = "MAXIMUM"
    link_sockets(tree, psi.outputs[0], wabs.inputs[0])
    link_sockets(tree, neg.outputs[0], wabs.inputs[1])
    return psi.outputs[0], wabs.outputs[0], attr


def _const_node(tree, value, loc):
    n = safe_node(tree, "ShaderNodeValue", loc)
    n.inputs["Value"].default_value = value
    return n.outputs["Value"]


def _live_time(tree, gin, loc):
    """Seconds when Live Scene Time is on, else the Time dial (probe: 5.2 has
    GeometryNodeInputSceneTime -> Seconds/Frame). Switch FLOAT False/True names."""
    if gin.outputs.get("Live Scene Time") is None:
        return gin.outputs["Time"]
    st = safe_node(tree, "GeometryNodeInputSceneTime", loc)
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 180, loc[1]))
    sw.input_type = "FLOAT"
    link_sockets(tree, gin.outputs["Live Scene Time"], sw.inputs["Switch"])
    link_sockets(tree, gin.outputs["Time"], sock(sw, "False"))
    link_sockets(tree, st.outputs["Seconds"], sock(sw, "True"))
    return sw.outputs["Output"]


def _audio_amp(tree, gin, loc, time_sock=None):
    """Sample Sound Frequencies (Low Hz..High Hz) with silent-zero fallback."""
    if time_sock is None:
        time_sock = _live_time(tree, gin, (loc[0], loc[1] - 180))
    sample = safe_node(tree, "GeometryNodeSampleSoundFrequencies", loc)
    if sample is not None and gin.outputs.get("Sound") is not None:
        link_sockets(tree, gin.outputs["Sound"], sample.inputs["Sound"])
        link_sockets(tree, time_sock, sample.inputs["Time"])
        link_sockets(tree, gin.outputs["Low Hz"], sample.inputs["Low"])
        link_sockets(tree, gin.outputs["High Hz"], sample.inputs["High"])
        try:
            sample.inputs["All Channels"].default_value = True
        except Exception:
            pass
        return sample.outputs["Amplitude"]
    zero = safe_node(tree, "ShaderNodeValue", loc)
    zero.inputs["Value"].default_value = 0.0
    return zero.outputs["Value"]


def _store_float(tree, geometry, name, value_sock, loc):
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    store.data_type = "FLOAT"
    store.domain = "POINT"
    link_sockets(tree, geometry, store.inputs["Geometry"])
    store.inputs["Name"].default_value = name
    link_sockets(tree, value_sock, store.inputs["Value"])
    return store.outputs["Geometry"]


def build_sheep_choral_flock(group_name="MEL_sheep_choral_flock"):
    """Ring of sheep, phase-staggered breathing, cymatic wool bloom on bodies."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # --- interface ---
    tree.interface.new_socket(name="Subject", in_out="INPUT",
                              socket_type="NodeSocketObject")
    add_int_param(tree, "Flock Size", 12, 1, 24)
    add_float_param(tree, "Ring Radius", 2.6, 0.5, 12.0)
    add_bool_param(tree, "Facing Inward", True)
    add_float_param(tree, "Eigen M", 3.0, 1.0, 12.0)
    add_float_param(tree, "Eigen N", 4.0, 1.0, 12.0)
    add_float_param(tree, "Cymatic Bloom", 0.0, 0.0, 0.25)     # 0 = neutral
    add_float_param(tree, "Audio Gain", 1.0, 0.0, 10.0)
    add_float_param(tree, "Low Hz", 60.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 900.0, 1.0, 24000.0)
    add_float_param(tree, "Breath Amount", 0.0, 0.0, 0.30)     # 0 = neutral
    add_float_param(tree, "Bob Strength", 0.0, 0.0, 0.40)      # audio-gated
    add_float_param(tree, "Breath Rate", 0.5, 0.01, 4.0)
    add_string_param(tree, "UV Attrib", "uv")
    add_bool_param(tree, "Realize Flock", False)
    add_bool_param(tree, "Live Scene Time", False)  # True = follow scene clock
    add_float_param(tree, "Phase Offset", 0.0, 0.0, 6.28319)  # per-copy stagger
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)

    # subject socket -> group input node output -> Object Info
    info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 800, by + 260))
    info.transform_space = "ORIGINAL"
    info.inputs["As Instance"].default_value = False  # body must be real geo for Set Position
    gi_node = next(n for n in tree.nodes if n.type == "GROUP_INPUT")
    link_sockets(tree, gi_node.outputs["Subject"], info.inputs["Object"])
    body = info.outputs["Geometry"]

    # --- cymatic psi on body ---
    psi, wabs, _attr = _psi_chain(tree, gin, (bx - 800, by - 220),
                                  gin.outputs["Eigen M"], gin.outputs["Eigen N"])
    # amplitude total = Cymatic Bloom + audio*gain*0.05 (0+0 = neutral)
    amp = _audio_amp(tree, gin, (bx - 800, by - 520))
    time_s = _live_time(tree, gin, (bx - 800, by - 660))
    ag = safe_node(tree, "ShaderNodeMath", (bx - 560, by - 520))
    ag.operation = "MULTIPLY"
    link_sockets(tree, amp, ag.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], ag.inputs[1])
    au5 = safe_node(tree, "ShaderNodeMath", (bx - 380, by - 520))
    au5.operation = "MULTIPLY"
    link_sockets(tree, ag.outputs[0], au5.inputs[0])
    au5.inputs[1].default_value = 0.05
    tot = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 400))
    tot.operation = "ADD"
    link_sockets(tree, gin.outputs["Cymatic Bloom"], tot.inputs[0])
    link_sockets(tree, au5.outputs[0], tot.inputs[1])
    # shape = psi * |psi| (rides antinodes) * total
    shape = safe_node(tree, "ShaderNodeMath", (bx, by - 160))
    shape.operation = "MULTIPLY"
    link_sockets(tree, psi, shape.inputs[0])
    link_sockets(tree, wabs, shape.inputs[1])
    disp = safe_node(tree, "ShaderNodeMath", (bx + 180, by - 160))
    disp.operation = "MULTIPLY"
    link_sockets(tree, shape.outputs[0], disp.inputs[0])
    link_sockets(tree, tot.outputs[0], disp.inputs[1])
    nrm = safe_node(tree, "GeometryNodeInputNormal", (bx, by + 40))
    off = safe_node(tree, "ShaderNodeVectorMath", (bx + 360, by - 20))
    off.operation = "SCALE"
    link_sockets(tree, nrm.outputs["Normal"], off.inputs["Vector"])
    link_sockets(tree, disp.outputs[0], off.inputs["Scale"])
    setp = safe_node(tree, "GeometryNodeSetPosition", (bx + 540, by + 160))
    link_sockets(tree, body, setp.inputs["Geometry"])
    link_sockets(tree, off.outputs["Vector"], setp.inputs["Offset"])
    geo = setp.outputs["Geometry"]

    # bake attributes for Substance/UE handoff
    geo = _store_float(tree, geo, "chladni_psi", psi, (bx + 720, by + 220))
    geo = _store_float(tree, geo, "audio_amplitude", ag.outputs[0], (bx + 900, by + 220))
    # universal musical waddle (Music Influence 0 = neutral)
    geo = apply_universal_music_pass(tree, gin, geo, loc=(bx + 1080, by + 220))

    # --- breathing phase per point: index*GOLDEN + Time*BreathRate*2pi ---
    circ = safe_node(tree, "GeometryNodeMeshCircle", (bx - 800, by - 760))
    # 5.2 MeshCircle exposes only Vertices+Radius (no Fill Type; see probe)
    link_sockets(tree, gin.outputs["Flock Size"], circ.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Ring Radius"], circ.inputs["Radius"])
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 620, by - 760))
    link_sockets(tree, circ.outputs["Mesh"], pts.inputs["Mesh"])
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 620, by - 940))
    gp = safe_node(tree, "ShaderNodeMath", (bx - 440, by - 940))
    gp.operation = "MULTIPLY"
    link_sockets(tree, idx.outputs[0], gp.inputs[0])
    gp.inputs[1].default_value = GOLDEN
    tr = safe_node(tree, "ShaderNodeMath", (bx - 440, by - 1100))
    tr.operation = "MULTIPLY"
    link_sockets(tree, time_s, tr.inputs[0])
    link_sockets(tree, gin.outputs["Breath Rate"], tr.inputs[1])
    tau = safe_node(tree, "ShaderNodeMath", (bx - 260, by - 1100))
    tau.operation = "MULTIPLY"
    link_sockets(tree, tr.outputs[0], tau.inputs[0])
    tau.inputs[1].default_value = TAU
    phase = safe_node(tree, "ShaderNodeMath", (bx - 80, by - 1000))
    phase.operation = "ADD"
    link_sockets(tree, gp.outputs[0], phase.inputs[0])
    link_sockets(tree, tau.outputs[0], phase.inputs[1])
    ph2 = safe_node(tree, "ShaderNodeMath", (bx + 10, by - 860))
    ph2.operation = "ADD"
    link_sockets(tree, phase.outputs[0], ph2.inputs[0])
    link_sockets(tree, gin.outputs["Phase Offset"], ph2.inputs[1])
    breathe = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 1000))
    breathe.operation = "SINE"
    link_sockets(tree, ph2.outputs[0], breathe.inputs[0])

    # scale = 1 + Breath Amount * breathe (0 = exact 1.0)
    bscale = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 1000))
    bscale.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Breath Amount"], bscale.inputs[0])
    link_sockets(tree, breathe.outputs[0], bscale.inputs[1])
    one_plus = safe_node(tree, "ShaderNodeMath", (bx + 460, by - 1000))
    one_plus.operation = "ADD"
    link_sockets(tree, bscale.outputs[0], one_plus.inputs[0])
    one_plus.inputs[1].default_value = 1.0
    comb_s = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 640, by - 1000))
    link_sockets(tree, one_plus.outputs[0], comb_s.inputs["X"])
    link_sockets(tree, one_plus.outputs[0], comb_s.inputs["Y"])
    link_sockets(tree, one_plus.outputs[0], comb_s.inputs["Z"])

    # --- instancing ---
    iop = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 1300, by))
    link_sockets(tree, pts.outputs["Points"], iop.inputs["Points"])
    link_sockets(tree, geo, iop.inputs["Instance"])
    link_sockets(tree, comb_s.outputs["Vector"], iop.inputs["Scale"])

    # bob Z = Bob Strength * breathe * audio amp (audio-gated; silent = flat)
    bob1 = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 760))
    bob1.operation = "MULTIPLY"
    link_sockets(tree, breathe.outputs[0], bob1.inputs[0])
    link_sockets(tree, amp, bob1.inputs[1])
    bob_z = safe_node(tree, "ShaderNodeMath", (bx + 460, by - 760))
    bob_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Bob Strength"], bob_z.inputs[0])
    link_sockets(tree, bob1.outputs[0], bob_z.inputs[1])
    bob_v = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 640, by - 760))
    link_sockets(tree, bob_z.outputs[0], bob_v.inputs["Z"])
    trn = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 1480, by - 140))
    link_sockets(tree, iop.outputs["Instances"], trn.inputs["Instances"])
    link_sockets(tree, bob_v.outputs["Vector"], trn.inputs["Translation"])
    trn.inputs["Local Space"].default_value = True

    # face inward: rotZ = atan2(y,x) + pi when Facing Inward
    pos_r = safe_node(tree, "GeometryNodeInputPosition", (bx - 620, by - 1260))
    sepp = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 440, by - 1260))
    link_sockets(tree, pos_r.outputs["Position"], sepp.inputs["Vector"])
    ang = safe_node(tree, "ShaderNodeMath", (bx - 260, by - 1260))
    ang.operation = "ARCTAN2"
    link_sockets(tree, sepp.outputs["Y"], ang.inputs[0])
    link_sockets(tree, sepp.outputs["X"], ang.inputs[1])
    flip = safe_node(tree, "ShaderNodeMath", (bx - 80, by - 1260))
    flip.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Facing Inward"], flip.inputs[0])
    flip.inputs[1].default_value = PI
    rot = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 1260))
    rot.operation = "ADD"
    link_sockets(tree, ang.outputs[0], rot.inputs[0])
    link_sockets(tree, flip.outputs[0], rot.inputs[1])
    comb_r = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 280, by - 1260))
    link_sockets(tree, rot.outputs[0], comb_r.inputs["Z"])
    rin = safe_node(tree, "GeometryNodeRotateInstances", (bx + 1660, by - 260))
    link_sockets(tree, trn.outputs["Instances"], rin.inputs["Instances"])
    link_sockets(tree, comb_r.outputs["Vector"], rin.inputs["Rotation"])

    # realize toggle (export/proof convenience)
    jn = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1840, by - 60))
    link_sockets(tree, rin.outputs["Instances"], jn.inputs["Geometry"])
    rlz = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 2020, by + 0))
    link_sockets(tree, jn.outputs["Geometry"], rlz.inputs["Geometry"])
    swp = safe_node(tree, "GeometryNodeSwitch", (bx + 2220, by + 60))
    swp.input_type = "GEOMETRY"
    # 5.2 GEOMETRY switch sockets are literally named False/True (probe truth)
    link_sockets(tree, gin.outputs["Realize Flock"], swp.inputs["Switch"])
    link_sockets(tree, jn.outputs["Geometry"], sock(swp, "False"))
    link_sockets(tree, rlz.outputs["Geometry"], sock(swp, "True"))
    link_sockets(tree, swp.outputs["Output"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Source Body", "nodes": ("object info",), "role": "input"},
        {"title": "Cymatic Bloom", "nodes": ("set position",), "role": "geometry"},
        {"title": "Breath Phase", "nodes": ("mesh circle",), "role": "geometry"},
        {"title": "Flock Ring", "nodes": ("instance on points",), "role": "geometry"},
        {"title": "Bake Attrs", "nodes": ("store named attribute",), "role": "output"},
    ])


def build_sheep_wool_bloom(group_name="MEL_sheep_wool_bloom"):
    """Fleece-sprig distributor; Bloom Density 0 => exact passthrough."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Bloom Density", 0.0, 0.0, 600.0)   # pts/m^2
    add_float_param(tree, "Tuft Size", 0.02, 0.001, 0.2)
    add_float_param(tree, "Audio Gain", 1.0, 0.0, 10.0)
    add_float_param(tree, "Low Hz", 60.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 900.0, 1.0, 24000.0)
    add_float_param(tree, "Eigen M", 3.0, 1.0, 12.0)
    add_float_param(tree, "Eigen N", 4.0, 1.0, 12.0)
    add_string_param(tree, "UV Attrib", "uv")
    add_int_param(tree, "Seed", 20260909, 0, 99999999)
    add_bool_param(tree, "Live Scene Time", False)
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)

    geo = gin.outputs["Geometry"]
    psi, wabs, _ = _psi_chain(tree, gin, (bx - 800, by), 
                              gin.outputs["Eigen M"], gin.outputs["Eigen N"])
    # mask = 0.5 + 0.5*|psi| in [0.5, 1] (density field never kills body UV islands)
    mhalf = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 140))
    mhalf.operation = "MULTIPLY"
    link_sockets(tree, wabs, mhalf.inputs[0])
    mhalf.inputs[1].default_value = 0.5
    mask = safe_node(tree, "ShaderNodeMath", (bx + 280, by - 140))
    mask.operation = "ADD"
    link_sockets(tree, mhalf.outputs[0], mask.inputs[0])
    mask.inputs[1].default_value = 0.5

    # strict neutrality: RANDOM Density = dial (0 => zero points => passthrough);
    # antinode mask rides Density Factor (multiplies dial, never negates it).
    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx + 560, by))
    # 5.2 TRAP (proven 2026-09-09): POISSON silently returns ZERO points when
    # Density Max is any linked FIELD. RANDOM honors fields on Density + Factor.
    dist.distribute_method = "RANDOM"
    link_sockets(tree, geo, dist.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Bloom Density"], sock(dist, "Density"))
    link_sockets(tree, mask.outputs[0], sock(dist, "Density Factor"))
    link_sockets(tree, gin.outputs["Seed"], sock(dist, "Seed"))

    spher = safe_node(tree, "GeometryNodeMeshUVSphere", (bx + 560, by - 260))
    spher.inputs["Segments"].default_value = 8
    spher.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Tuft Size"], spher.inputs["Radius"])

    # per-tuft scale ripple from audio (silent = 1.0): 1 + AudioGain*amp*0.3
    amp = _audio_amp(tree, gin, (bx - 800, by - 420),
                     _live_time(tree, gin, (bx - 1060, by - 480)))
    g = safe_node(tree, "ShaderNodeMath", (bx - 560, by - 420))
    g.operation = "MULTIPLY"
    link_sockets(tree, amp, g.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], g.inputs[1])
    k = safe_node(tree, "ShaderNodeMath", (bx - 380, by - 420))
    k.operation = "MULTIPLY"
    link_sockets(tree, g.outputs[0], k.inputs[0])
    k.inputs[1].default_value = 0.3
    sone = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 420))
    sone.operation = "ADD"
    link_sockets(tree, k.outputs[0], sone.inputs[0])
    sone.inputs[1].default_value = 1.0
    tc = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 20, by - 420))
    link_sockets(tree, sone.outputs[0], tc.inputs["X"])
    link_sockets(tree, sone.outputs[0], tc.inputs["Y"])
    link_sockets(tree, sone.outputs[0], tc.inputs["Z"])

    iop = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 860, by))
    link_sockets(tree, dist.outputs["Points"], iop.inputs["Points"])
    link_sockets(tree, spher.outputs["Mesh"], iop.inputs["Instance"])
    link_sockets(tree, tc.outputs["Vector"], iop.inputs["Scale"])

    jn = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1100, by + 60))
    link_sockets(tree, iop.outputs["Instances"], jn.inputs["Geometry"])
    link_sockets(tree, geo, jn.inputs["Geometry"])
    geo_out = _store_float(tree, jn.outputs["Geometry"], "chladni_psi", psi,
                           (bx + 1280, by + 60))
    link_sockets(tree, geo_out, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Cymatic Mask", "nodes": ("distribute points on faces",), "role": "geometry"},
        {"title": "Audio Ripple", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Tufts", "nodes": ("instance on points",), "role": "geometry"},
    ])


def register():
    register_builder(
        "MEL_sheep_choral_flock", build_sheep_choral_flock,
        "Choral Sheep Flock",
        "Ring of sheep with phase-staggered breathing + cymatic wool bloom (audio band swell; stores chladni_psi, audio_amplitude)",
        "companions",
    )
    register_builder(
        "MEL_sheep_wool_bloom", build_sheep_wool_bloom,
        "Sheep Wool Bloom",
        "Antinode-weighted fleece sprig distributor; Bloom Density 0 = passthrough",
        "companions",
    )


register()
