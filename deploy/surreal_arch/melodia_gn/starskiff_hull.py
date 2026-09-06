
"""
Starskiff hull GN builder — parametric hull form + audio-reactive surface.

Offline authoring/bake lane only: Unreal remains the runtime rhythm authority.
Audio reactivity here is for shape authoring and bake-time preview; it never
becomes a second audio writer in the engine.

Builds on the existing intake-mesh + loom + audio-drape patterns already proven
in this addon (garment_loom.py, garment_audio_drape.py, audio_terrain.py).
One hull base, many forms, music-reactive surface — then livery dresses on top.

Blender 5.2 native-audio node used:
  GeometryNodeSampleSoundFrequencies — Sound / Time / Low / High / All Channels
  -> Amplitude. Same node the audio_terrain builders use; no invented nodes.
"""

from __future__ import annotations

from .core import (
    add_float_param,
    add_int_param,
    add_music_influence_params,
    apply_universal_music_pass,
    color_node,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .audio_terrain import _add_sound_param


# --------------------------------------------------------------------------- #
# hull form variation — seed-driven shape of the intake hull shell
# --------------------------------------------------------------------------- #
def build_starskiff_hull_form(group_name="MEL_starskiff_hull_form"):
    """Seed-driven hull form variation over an intake hull shell.

    Intake mesh = Hull_Shell (or any hull-shaped shell with a clean UV).
    Output keeps UV, keeps WeightedNormal+Bevel modifiers non-destructive.
    Form knobs: Symmetry, Beam, Length, Rocker, Tumble, Taper — the classic
    small-boat hull shaping dials, so variants read as intentional designs,
    not random noise.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    seed = add_int_param(tree, "Seed", 20260903, 0, 99999999)
    sym = add_float_param(tree, "Symmetry", 1.0, 0.0, 2.0)
    beam = add_float_param(tree, "Beam", 1.0, 0.5, 2.0)
    length = add_float_param(tree, "Length", 1.0, 0.5, 2.0)
    rocker = add_float_param(tree, "Rocker", 0.0, -1.0, 1.0)
    tumble = add_float_param(tree, "Tumble", 0.0, -1.0, 1.0)
    taper = add_float_param(tree, "Taper", 1.0, 0.0, 2.0)

    # Position + local frame (5.2: InputPosition auto-consumes context geometry,
    # no Geometry input socket — don't try to feed it)
    pos = safe_node(tree, "GeometryNodeInputPosition", (-360, 80))
    norm = safe_node(tree, "GeometryNodeInputNormal", (-360, -120))

    # Hull-local Y up, X along length, Z across beam — use world Y as up proxy
    # (intake is authored upright). Separate for local frame math.
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-540, -120))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Seeded noise for stochastic hull variation (same W-sock quirk as loom)
    noise = safe_node(tree, "ShaderNodeTexNoise", (-540, -260))
    try:
        noise.inputs["Scale"].default_value = 3.0
        noise.inputs["Detail"].default_value = 4.0
        w = sock(noise, "W")
        if w is not None:
            w.default_value = float(seed.default_value % 1000) * 0.001
    except Exception:
        pass
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])

    nz = sock(noise, "Fac") or noise.outputs[0]

    # --- form math (blend-space hull shaping) ---
    # Beam: scale across Z by beam (wider/narrower hull)
    beam_z = safe_node(tree, "ShaderNodeMath", (-720, -260))
    beam_z.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Z"], beam_z.inputs[0])
    link_sockets(tree, gin.outputs["Beam"], beam_z.inputs[1])

    # Length: scale along X by length
    len_x = safe_node(tree, "ShaderNodeMath", (-720, -360))
    len_x.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], len_x.inputs[0])
    link_sockets(tree, gin.outputs["Length"], len_x.inputs[1])

    # Rocker: parabolic up/down along length (bow/stern lift)
    rocker_x = safe_node(tree, "ShaderNodeMath", (-720, -440))
    rocker_x.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], rocker_x.inputs[0])
    rocker_sq = safe_node(tree, "ShaderNodeMath", (-540, -440))
    rocker_sq.operation = "MULTIPLY"
    link_sockets(tree, rocker_x.outputs[0], rocker_sq.inputs[0])
    link_sockets(tree, rocker_x.outputs[0], rocker_sq.inputs[1])
    rocker_off = safe_node(tree, "ShaderNodeMath", (-360, -440))
    rocker_off.operation = "MULTIPLY"
    link_sockets(tree, rocker_sq.outputs[0], rocker_off.inputs[0])
    link_sockets(tree, gin.outputs["Rocker"], rocker_off.inputs[1])

    # Tumble: pitch the whole hull (angle about Z)
    tumble_z = safe_node(tree, "ShaderNodeMath", (-720, -520))
    tumble_z.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], tumble_z.inputs[0])
    link_sockets(tree, gin.outputs["Tumble"], tumble_z.inputs[1])

    # Taper: scale toward bow (X positive) — narrower at bow
    taper_x = safe_node(tree, "ShaderNodeMath", (-720, -600))
    taper_x.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], taper_x.inputs[0])
    taper_w = safe_node(tree, "ShaderNodeMath", (-540, -600))
    taper_w.operation = "MULTIPLY"
    link_sockets(tree, taper_x.outputs[0], taper_w.inputs[0])
    link_sockets(tree, gin.outputs["Taper"], taper_w.inputs[1])

    # Composite offset = beam_z (z) + rocker (z) + tumble (y) + taper (x)
    off_z = safe_node(tree, "ShaderNodeMath", (-360, -520))
    off_z.operation = "ADD"
    link_sockets(tree, beam_z.outputs[0], off_z.inputs[0])
    link_sockets(tree, rocker_off.outputs[0], off_z.inputs[1])

    off_y = safe_node(tree, "ShaderNodeMath", (-360, -600))
    off_y.operation = "ADD"
    link_sockets(tree, tumble_z.outputs[0], off_y.inputs[0])
    # add a little stochastic bump from noise to keep form alive
    nz_scale = safe_node(tree, "ShaderNodeMath", (-180, -600))
    nz_scale.operation = "MULTIPLY"
    link_sockets(tree, nz, nz_scale.inputs[0])
    nz_scale.inputs[1].default_value = 0.15
    link_sockets(tree, nz_scale.outputs[0], off_y.inputs[1])

    off_x = safe_node(tree, "ShaderNodeMath", (-360, -680))
    off_x.operation = "ADD"
    link_sockets(tree, len_x.outputs[0], off_x.inputs[0])
    link_sockets(tree, taper_w.outputs[0], off_x.inputs[1])

    # Symmetry: mirror weight — blend between the form and its mirrored twin
    # (keeps hull readable as one boat, not broken in half)
    sep_z = safe_node(tree, "ShaderNodeSeparateXYZ", (-540, -100))
    link_sockets(tree, pos.outputs["Position"], sep_z.inputs["Vector"])
    sign = safe_node(tree, "ShaderNodeMath", (-360, -100))
    sign.operation = "MULTIPLY"
    link_sockets(tree, sep_z.outputs["Z"], sign.inputs[0])
    sign.inputs[1].default_value = -1.0
    sym_w = safe_node(tree, "ShaderNodeMath", (-180, -100))
    sym_w.operation = "MULTIPLY"
    link_sockets(tree, sign.outputs[0], sym_w.inputs[0])
    link_sockets(tree, gin.outputs["Symmetry"], sym_w.inputs[1])
    clamp_sym = safe_node(tree, "ShaderNodeClamp", (0, -100))
    clamp_sym.inputs["Min"].default_value = 0.0
    clamp_sym.inputs["Max"].default_value = 1.0
    link_sockets(tree, sym_w.outputs[0], clamp_sym.inputs["Value"])

    off_vec = safe_node(tree, "ShaderNodeCombineXYZ", (120, -360))
    link_sockets(tree, off_x.outputs[0], off_vec.inputs["X"])
    link_sockets(tree, off_y.outputs[0], off_vec.inputs["Y"])
    link_sockets(tree, off_z.outputs[0], off_vec.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (360, -160))
    link_sockets(tree, geo, set_pos.inputs["Geometry"])
    link_sockets(tree, norm.outputs["Normal"], set_pos.inputs["Offset"])
    # offset path: scale Normal (vector) by the scalar total displacement
    off_scale = safe_node(tree, "ShaderNodeVectorMath", (360, -80))
    off_scale.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off_scale.inputs["Vector"])
    link_sockets(tree, off_vec.outputs["Vector"], off_scale.inputs["Scale"])
    link_sockets(tree, off_scale.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(
        tree,
        group_name,
        [
            {"title": "Intake", "nodes": ("position", "normal",), "role": "input"},
            {"title": "Form Seed", "nodes": ("noise",), "role": "attribute"},
            {"title": "Hull Dials", "nodes": ("beam", "length", "rocker", "tumble", "taper", "symmetry"), "role": "attribute"},
            {"title": "Form Math", "nodes": ("beam_z", "len_x", "rocker_sq", "rocker_off", "tumble_z", "taper_w", "off_x", "off_y", "off_z"), "role": "geometry"},
            {"title": "Displace", "nodes": ("off_vec", "off_scale", "set_position"), "role": "output"},
        ],
    )


# --------------------------------------------------------------------------- #
# hull audio surface — audio-reactive micro-displacement on the hull skin
# --------------------------------------------------------------------------- #
def build_starskiff_hull_audio(group_name="MEL_starskiff_hull_audio"):
    """Audio-reactive micro-surface on top of the hull form.

    Uses GeometryNodeSampleSoundFrequencies directly (same node + same band
    pattern as garment_audio_drape / audio_terrain). Gain-scaled micro
    displacement along hull normal — cloth/hull skin tension feel, not a
    second audio writer. Stores audio_amplitude attribute for Substance bake.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    # Sound interface — exactly the same as audio_drape / audio_terrain:
    # _add_sound_param creates the Group Input output socket; link through gin.outputs["Sound"]
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 40.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 320.0, 1.0, 24000.0)
    add_float_param(tree, "Band Width", 0.06, 0.001, 1.0)
    add_float_param(tree, "Audio Gain", 1.2, 0.0, 100.0)
    add_float_param(tree, "Micro Displacement", 0.004, 0.0, 0.2)
    add_int_param(tree, "Seed", 20260903, 0, 99999999)

    add_music_influence_params(tree)

    # Band math — identical pattern to garment_audio_drape
    span = safe_node(tree, "ShaderNodeMath", (-640, -220))
    span.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["High Hz"], span.inputs[0])
    link_sockets(tree, gin.outputs["Low Hz"], span.inputs[1])
    scaled_span = safe_node(tree, "ShaderNodeMath", (-450, -220))
    scaled_span.operation = "MULTIPLY"
    link_sockets(tree, span.outputs[0], scaled_span.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], scaled_span.inputs[1])
    band_high = safe_node(tree, "ShaderNodeMath", (-260, -180))
    band_high.operation = "ADD"
    link_sockets(tree, gin.outputs["Low Hz"], band_high.inputs[0])
    link_sockets(tree, scaled_span.outputs[0], band_high.inputs[1])

    amp = None
    sample = safe_node(tree, "GeometryNodeSampleSoundFrequencies", (-60, -140))
    if sample is not None:
        link_sockets(tree, gin.outputs["Sound"], sample.inputs["Sound"])
        link_sockets(tree, gin.outputs["Time"], sample.inputs["Time"])
        link_sockets(tree, gin.outputs["Low Hz"], sample.inputs["Low"])
        link_sockets(tree, band_high.outputs[0], sample.inputs["High"])
        sample.inputs["All Channels"].default_value = True
        amp = sample.outputs["Amplitude"]

    if amp is None:
        # fallback: no audio node in this build — silent zero (offline-authoring safe)
        zero = safe_node(tree, "ShaderNodeValue", (-60, -140))
        zero.inputs["Value"].default_value = 0.0
        amp = zero.outputs["Value"]

    gain = safe_node(tree, "ShaderNodeMath", (130, -140))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    # Seeded micro-pattern on the hull surface (same W-sock quirk)
    # 5.2: InputPosition / InputNormal auto-consume context geometry — no link needed
    pos = safe_node(tree, "GeometryNodeInputPosition", (-360, 80))
    noise = safe_node(tree, "ShaderNodeTexNoise", (-360, -260))
    try:
        noise.inputs["Scale"].default_value = 8.0
        noise.inputs["Detail"].default_value = 3.0
        w = sock(noise, "W")
        if w is not None:
            w.default_value = float(gin.outputs["Seed"].default_value % 100) * 0.01
    except Exception:
        pass
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    nz = sock(noise, "Fac") or noise.outputs[0]

    # micro displacement = audio * (0.5 + noise) * micro_displacement
    nz_half = safe_node(tree, "ShaderNodeMath", (-180, -260))
    nz_half.operation = "MULTIPLY"
    link_sockets(tree, nz, nz_half.inputs[0])
    nz_half.inputs[1].default_value = 0.5
    micro = safe_node(tree, "ShaderNodeMath", (60, -260))
    micro.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], micro.inputs[0])
    link_sockets(tree, nz_half.outputs[0], micro.inputs[1])
    micro_final = safe_node(tree, "ShaderNodeMath", (240, -260))
    micro_final.operation = "MULTIPLY"
    link_sockets(tree, micro.outputs[0], micro_final.inputs[0])
    link_sockets(tree, gin.outputs["Micro Displacement"], micro_final.inputs[1])

    norm = safe_node(tree, "GeometryNodeInputNormal", (-360, -360))
    off_vec = safe_node(tree, "ShaderNodeVectorMath", (360, -360))
    off_vec.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off_vec.inputs["Vector"])
    link_sockets(tree, micro_final.outputs[0], off_vec.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (540, -160))
    link_sockets(tree, geo, set_pos.inputs["Geometry"])
    link_sockets(tree, off_vec.outputs["Vector"], set_pos.inputs["Offset"])
    geom_out = set_pos.outputs["Geometry"]

    # store audio_amplitude for bake / Substance handoff (same as audio_terrain)
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (540, -360))
    store.data_type = "FLOAT"
    store.domain = "POINT"
    link_sockets(tree, geom_out, store.inputs["Geometry"])
    store.inputs["Name"].default_value = "audio_amplitude"
    link_sockets(tree, gain.outputs[0], store.inputs["Value"])

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(
        tree,
        group_name,
        [
            {"title": "Audio Band", "nodes": ("sample_sound",), "role": "attribute"},
            {"title": "Micro Pattern", "nodes": ("position", "noise",), "role": "attribute"},
            {"title": "Displacement", "nodes": ("gain", "nz_half", "micro", "micro_final", "off_vec", "set_position"), "role": "geometry"},
            {"title": "Bake Attr", "nodes": ("store_audio"), "role": "output"},
        ],
    )


# --------------------------------------------------------------------------- #
# register
# --------------------------------------------------------------------------- #
def register():
    register_builder(
        "MEL_starskiff_hull_form",
        build_starskiff_hull_form,
        "Starskiff Hull Form",
        "Parametric hull shape variation over an intake hull shell (beam / length / rocker / tumble / taper / symmetry)",
        "Starskiff",
    )
    register_builder(
        "MEL_starskiff_hull_audio",
        build_starskiff_hull_audio,
        "Starskiff Hull Audio Surface",
        "Audio-reactive micro-displacement on the hull skin (offline bake-lane; Unreal owns runtime rhythm)",
        "Starskiff",
    )
