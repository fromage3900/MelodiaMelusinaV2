"""Chladni garment layer — eigenmode-driven cymatic fabric displacement.

Phase 2 of the Universal Wardrobe Studio AAA pipeline.
Plan: .hermes/plans/2026-09-06_003500-universal-wardrobe-studio-aaa-pipeline.md

Pattern authority: Tools/Houdini/copernicus/chladni_eigen.py (exact plate physics,
simply-supported rectangular plate). That solver bakes Height maps for eigenmodes
(m, n) at resonant frequencies; the live-stage contract is freq -> (m, n) selection.

In-GN contract (offline authoring / bake preview only — UE owns runtime rhythm):
  - `Eigen U` / `Eigen V` float dials drive the analytic mode shape
        psi = sin(m*pi*u) * sin(n*pi*v)
    computed per-vertex from UVs (authoring approximation of the baked maps; baked
    eigenmode maps remain the ship authority per melodia-cymatic-eigenmode).
  - `Audio Band Select` picks a frequency; the in-GN Sample Sound Frequencies node
    provides amplitude in that band; cymatic amplitude rides the musical chain.
  - Stores `chladni_psi` and `audio_amplitude` (POINT domain) for Substance/UE handoff.

5.2 traps honored: no POWER on negatives (sines are bounded, but UV * pi scaled args
are still kept non-negative by construction), MAXIMUM-guard any radical, clamp output
is `Result`, audio via _add_sound_param with silent-zero fallback, Realize tail.
"""
from __future__ import annotations

from .core import (
    add_float_param,
    add_int_param,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .audio_terrain import _add_sound_param


def build_garm_chladni_layer(group_name="MEL_garm_chladni_layer"):
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_float_param(tree, "Eigen M", 2.0, 1.0, 12.0)      # eigenmode m
    add_float_param(tree, "Eigen N", 3.0, 1.0, 12.0)      # eigenmode n
    add_float_param(tree, "Cymatic Amplitude", 0.0, 0.0, 0.05)  # 0 = neutral
    add_float_param(tree, "Audio Gain", 1.0, 0.0, 10.0)
    add_float_param(tree, "Low Hz", 40.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 320.0, 1.0, 24000.0)
    add_int_param(tree, "Seed", 20260906, 0, 99999999)
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)

    # --- UV-based mode shape psi(u, v) = sin(m*pi*u) * sin(n*pi*v) ---
    uv = safe_node(tree, "GeometryNodeInputUV", (-820, 60))
    if uv is None:
        # fallback: derive u,v from position (authoring only)
        uv = safe_node(tree, "GeometryNodeInputPosition", (-820, 60))
    sep_uv = safe_node(tree, "ShaderNodeSeparateXYZ", (-640, 60))
    link_sockets(tree, uv.outputs[0], sep_uv.inputs["Vector"])

    pi_mul_u = safe_node(tree, "ShaderNodeMath", (-460, 160))
    pi_mul_u.operation = "MULTIPLY"
    link_sockets(tree, sep_uv.outputs["X"], pi_mul_u.inputs[0])
    pi_mul_u.inputs[1].default_value = 3.14159265

    pi_mul_v = safe_node(tree, "ShaderNodeMath", (-460, -40))
    pi_mul_v.operation = "MULTIPLY"
    link_sockets(tree, sep_uv.outputs["Y"], pi_mul_v.inputs[0])
    pi_mul_v.inputs[1].default_value = 3.14159265

    m_mul_u = safe_node(tree, "ShaderNodeMath", (-280, 160))
    m_mul_u.operation = "MULTIPLY"
    link_sockets(tree, pi_mul_u.outputs[0], m_mul_u.inputs[0])
    link_sockets(tree, gin.outputs["Eigen M"], m_mul_u.inputs[1])

    n_mul_v = safe_node(tree, "ShaderNodeMath", (-280, -40))
    n_mul_v.operation = "MULTIPLY"
    link_sockets(tree, pi_mul_v.outputs[0], n_mul_v.inputs[0])
    link_sockets(tree, gin.outputs["Eigen N"], n_mul_v.inputs[1])

    sin_u = safe_node(tree, "ShaderNodeMath", (-100, 160))
    sin_u.operation = "SINE"
    link_sockets(tree, m_mul_u.outputs[0], sin_u.inputs[0])

    sin_v = safe_node(tree, "ShaderNodeMath", (-100, -40))
    sin_v.operation = "SINE"
    link_sockets(tree, n_mul_v.outputs[0], sin_v.inputs[0])

    psi = safe_node(tree, "ShaderNodeMath", (80, 60))
    psi.operation = "MULTIPLY"
    link_sockets(tree, sin_u.outputs[0], psi.inputs[0])
    link_sockets(tree, sin_v.outputs[0], psi.inputs[1])

    # --- audio amplitude in selected band (proven pattern from starskiff_hull) ---
    span = safe_node(tree, "ShaderNodeMath", (-460, -260))
    span.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["High Hz"], span.inputs[0])
    link_sockets(tree, gin.outputs["Low Hz"], span.inputs[1])

    amp = None
    sample = safe_node(tree, "GeometryNodeSampleSoundFrequencies", (-100, -260))
    if sample is not None:
        link_sockets(tree, gin.outputs["Sound"], sample.inputs["Sound"])
        link_sockets(tree, gin.outputs["Time"], sample.inputs["Time"])
        link_sockets(tree, gin.outputs["Low Hz"], sample.inputs["Low"])
        link_sockets(tree, gin.outputs["High Hz"], sample.inputs["High"])
        try:
            sample.inputs["All Channels"].default_value = True
        except Exception:
            pass
        amp = sample.outputs["Amplitude"]
    if amp is None:
        zero = safe_node(tree, "ShaderNodeValue", (-100, -260))
        zero.inputs["Value"].default_value = 0.0
        amp = zero.outputs["Value"]

    gain = safe_node(tree, "ShaderNodeMath", (80, -260))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    # --- displacement: psi * (Cymatic Amplitude + audio * 0.01) along normal ---
    # zero-neutral: Cymatic Amplitude 0 AND audio gain only scales audio term; the
    # audio term is scaled by 0.01 so silent input at defaults = passthrough.
    audio_term = safe_node(tree, "ShaderNodeMath", (260, -200))
    audio_term.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], audio_term.inputs[0])
    audio_term.inputs[1].default_value = 0.01

    total_amp = safe_node(tree, "ShaderNodeMath", (440, -120))
    total_amp.operation = "ADD"
    link_sockets(tree, gin.outputs["Cymatic Amplitude"], total_amp.inputs[0])
    link_sockets(tree, audio_term.outputs[0], total_amp.inputs[1])

    disp = safe_node(tree, "ShaderNodeMath", (620, -40))
    disp.operation = "MULTIPLY"
    link_sockets(tree, psi.outputs[0], disp.inputs[0])
    link_sockets(tree, total_amp.outputs[0], disp.inputs[1])

    norm = safe_node(tree, "GeometryNodeInputNormal", (260, 240))
    off_vec = safe_node(tree, "ShaderNodeVectorMath", (800, 80))
    off_vec.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off_vec.inputs["Vector"])
    link_sockets(tree, disp.outputs[0], off_vec.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (980, 0))
    link_sockets(tree, geo, set_pos.inputs["Geometry"])
    link_sockets(tree, off_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # --- bake attributes (POINT domain): chladni_psi + audio_amplitude ---
    store_psi = safe_node(tree, "GeometryNodeStoreNamedAttribute", (1160, 120))
    store_psi.data_type = "FLOAT"
    store_psi.domain = "POINT"
    link_sockets(tree, set_pos.outputs["Geometry"], store_psi.inputs["Geometry"])
    store_psi.inputs["Name"].default_value = "chladni_psi"
    link_sockets(tree, psi.outputs[0], store_psi.inputs["Value"])

    store_amp = safe_node(tree, "GeometryNodeStoreNamedAttribute", (1160, -120))
    store_amp.data_type = "FLOAT"
    store_amp.domain = "POINT"
    link_sockets(tree, store_psi.outputs["Geometry"], store_amp.inputs["Geometry"])
    store_amp.inputs["Name"].default_value = "audio_amplitude"
    link_sockets(tree, gain.outputs[0], store_amp.inputs["Value"])

    link_sockets(tree, store_amp.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Eigenmode", "nodes": ("uv", "sin", "psi"), "role": "attribute"},
        {"title": "Audio Band", "nodes": ("sample",), "role": "attribute"},
        {"title": "Displacement", "nodes": ("disp", "off_vec", "set_position"), "role": "geometry"},
        {"title": "Bake Attrs", "nodes": ("store",), "role": "output"},
    ])


def register():
    register_builder(
        "MEL_garm_chladni_layer",
        build_garm_chladni_layer,
        "Wardrobe Chladni Layer",
        "Eigenmode cymatic fabric displacement; audio band selects drive, amplitude rides music (bake attrs: chladni_psi, audio_amplitude)",
        "Wardrobe",
    )
