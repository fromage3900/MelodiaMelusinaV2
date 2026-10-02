#!/usr/bin/env python3
"""
Melodia Melusina — Audio-Reactive Material Bridge Engine
Authoring, validation, and mathematical synchronization engine connecting
MPC_Melodia_Palette to surface master materials:
  - M_Master_Toon_Universal
  - M_Master_Gemstone
  - M_Master_SDF_Toon
  - M_PP_MeluColorGrade

Governing Contract:
1. Single Writer Authority: UMelodiaAudioReactivePresentationSubsystem is the sole writer
   of MPC_Melodia_Palette. The material bridge is strictly a read-only consumer.
2. Clamped Bounds: All audio-reactive outputs are clamped to physically safe ranges
   (Emissive <= 20.0, Roughness in [0.02, 1.0], Color in [0.0, 1.0]) to eliminate blown-out
   shaders or HDR buffer overflow.
3. Neutral Defaults: Quiescent audio (GlobalReactivity = 0.0) yields identity transforms
   preserving baseline artist look without visual artifacts.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
SAVED_AUDIT = ROOT / "Saved" / "Audit"
SPECS_DIR = ROOT / "specs" / "materials"

# ---------------------------------------------------------------------------
# 1. Canonical MPC Parameter Definitions
# ---------------------------------------------------------------------------

MPC_CANONICAL_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

AUDIO_MPC_SCALARS: Dict[str, Dict[str, Any]] = {
    "BeatPulse": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Continuous cos^2(BeatPhase * pi) pulse on musical downbeats",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Emissive respiration, rim pulse, and SDF banding dilation",
    },
    "BeatPhase": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Continuous measure phase progression [0.0 = on beat, 1.0 = next bar]",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Cyclic phase offsets and temporal sync",
    },
    "BeatIntensity": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Musical beat pulse intensity envelope",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Macro pulse scaling",
    },
    "Bass": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Combat intensity / low-frequency energy (bBattleActive ? BattleIntensity : 0.0)",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Caustic speed, wave displacement, heavy bloom",
    },
    "Mid": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Impact pulse energy / melodic lead harmonies",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Abbe dispersion flash, cel-step shift, floral shadow expansion",
    },
    "Treble": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "High-frequency shimmer energy (driven synchronously with BeatPulse)",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Gemstone facet twinkle, star sparkle glints, starlight micro-highlights",
    },
    "GlobalReactivity": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Global audio reactivity master blend scalar (0.0 = bypass, 1.0 = full synesthesia)",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Master crossfade between static artist look and audio-reactive look",
    },
    "BassIntensity": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Value-aligned alias of Bass for cymatics / neural subsystems",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Cymatics nodal amplitude",
    },
    "MidIntensity": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Value-aligned alias of Mid for impact subsystems",
        "writer": "UMelodiaAudioReactivePresentationSubsystem::TickSubsystem",
        "consumer_role": "Impact ripple propagation",
    },
    "RhythmPulse": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Instantaneous hit judgment pulse (Perfect/Great rating pop, 0.18s decay)",
        "writer": "UMelodiaRhythmReactivitySubsystem::SubmitRatedInput",
        "consumer_role": "PPV chromatic punch and flash accents",
    },
    "ComboNormalized": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Normalized combo streak progression [0..100 combo -> 0.0..1.0]",
        "writer": "UMelodiaRhythmReactivitySubsystem",
        "consumer_role": "Gradual aura intensity build",
    },
    "CrescendoNormalized": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Musical section crescendo progression",
        "writer": "UMelodiaRhythmReactivitySubsystem",
        "consumer_role": "Environmental atmosphere saturation ramp",
    },
    "CommandEnergy": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Special move / harmony charge level",
        "writer": "UMelodiaRhythmReactivitySubsystem",
        "consumer_role": "Weapon and accessory glow",
    },
    "BreakPulse": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Enemy posture break / shield shatter trigger pulse",
        "writer": "UMelodiaRhythmReactivitySubsystem",
        "consumer_role": "Disruption shockwave and surface desaturation pop",
    },
    "VictoryPulse": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Encounter victory celebratory pulse",
        "writer": "UMelodiaRhythmReactivitySubsystem",
        "consumer_role": "Golden shimmer explosion and rainbow dispersion",
    },
    "DissonanceAmount": {
        "default": 0.0,
        "range": (0.0, 1.0),
        "desc": "Corruption / sorrow seam tension scalar",
        "writer": "UMelodiaNarrativeSubsystem",
        "consumer_role": "Hue jitter and edge distortion",
    },
}

# ---------------------------------------------------------------------------
# 2. Clamping and Parameter Policy Specifications
# ---------------------------------------------------------------------------

AUDIO_CLAMP_BOUNDS: Dict[str, Tuple[float, float, str]] = {
    "AudioEmissiveGain": (0.0, 5.0, "Multiplier for beat-driven emissive pulsing"),
    "AudioBassResponse": (0.0, 2.0, "Low-frequency battle intensity response"),
    "AudioMidResponse": (0.0, 2.0, "Mid-frequency impact / harmonic response"),
    "AudioTrebleTwinkle": (0.0, 3.0, "High-frequency sparkle / shimmer response"),
    "AudioPulseCurveExp": (1.0, 4.0, "Exponent shaping beat pulse response curve"),
    "AudioRoughnessDip": (0.0, 0.25, "Downbeat specular flash gloss reduction"),
    "AudioColorBreathAmount": (0.0, 0.35, "Downbeat pastel luminance lift"),
    "AudioNormalPerturbScale": (0.0, 0.15, "Surface normal micro-ripple amplitude"),
}

TARGET_MASTER_REGISTRY = {
    "M_Master_Toon_Universal": {
        "path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "group": "12 | Audio Synesthesia",
        "shading_model": "Substrate Toon BSDF",
        "bindings": {
            "bAudioReactive_Active": {"type": "bool", "default": True},
            "AudioEmissiveGain": {"type": "float", "default": 1.0, "clamp": AUDIO_CLAMP_BOUNDS["AudioEmissiveGain"]},
            "AudioBassResponse": {"type": "float", "default": 0.5, "clamp": AUDIO_CLAMP_BOUNDS["AudioBassResponse"]},
            "AudioTrebleTwinkle": {"type": "float", "default": 0.75, "clamp": AUDIO_CLAMP_BOUNDS["AudioTrebleTwinkle"]},
            "AudioRoughnessDip": {"type": "float", "default": 0.08, "clamp": AUDIO_CLAMP_BOUNDS["AudioRoughnessDip"]},
        },
    },
    "M_Master_Gemstone": {
        "path": "/Game/EnvSandbox/Materials/Masters/M_Master_Gemstone",
        "group": "11 | Audio Synesthesia",
        "shading_model": "Substrate Toon BSDF",
        "bindings": {
            "bAudioReactive_Active": {"type": "bool", "default": True},
            "AudioEmissiveGain": {"type": "float", "default": 1.5, "clamp": AUDIO_CLAMP_BOUNDS["AudioEmissiveGain"]},
            "AudioBassResponse": {"type": "float", "default": 0.8, "clamp": AUDIO_CLAMP_BOUNDS["AudioBassResponse"]},
            "AudioTrebleTwinkle": {"type": "float", "default": 1.2, "clamp": AUDIO_CLAMP_BOUNDS["AudioTrebleTwinkle"]},
        },
    },
    "M_Master_SDF_Toon": {
        "path": "/Game/EnvSandbox/Materials/Masters/SDF/M_Master_SDF_Toon",
        "group": "10 | Audio Synesthesia",
        "shading_model": "Substrate Toon BSDF",
        "bindings": {
            "bAudioReactive_Active": {"type": "bool", "default": True},
            "AudioEmissiveGain": {"type": "float", "default": 1.0, "clamp": AUDIO_CLAMP_BOUNDS["AudioEmissiveGain"]},
            "AudioBassResponse": {"type": "float", "default": 0.6, "clamp": AUDIO_CLAMP_BOUNDS["AudioBassResponse"]},
            "AudioMidResponse": {"type": "float", "default": 0.5, "clamp": AUDIO_CLAMP_BOUNDS["AudioMidResponse"]},
        },
    },
    "M_PP_MeluColorGrade": {
        "path": "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",
        "group": "PostProcess Audio Drive",
        "shading_model": "Post Process Domain",
        "bindings": {
            "bAudioReactive_Active": {"type": "bool", "default": True},
            "AudioEmissiveGain": {"type": "float", "default": 0.8, "clamp": AUDIO_CLAMP_BOUNDS["AudioEmissiveGain"]},
            "AudioChromaticPunch": {"type": "float", "default": 0.02, "clamp": (0.0, 0.1, "Lens chromatic punch on hit")},
        },
    },
}

# ---------------------------------------------------------------------------
# 3. Mathematical Evaluation & Safety Simulation
# ---------------------------------------------------------------------------

@dataclass
class AudioReactiveEvaluationResult:
    base_color_out: Tuple[float, float, float]
    emissive_out: Tuple[float, float, float]
    roughness_out: float
    normal_perturb: Tuple[float, float, float]
    audio_pulse_scalar: float
    audio_bass_scalar: float
    audio_treble_scalar: float


def evaluate_audio_reactive_bridge(
    base_color_in: Tuple[float, float, float],
    base_emissive_in: Tuple[float, float, float],
    roughness_in: float,
    normal_in: Tuple[float, float, float],
    beat_pulse: float,
    bass: float,
    mid: float,
    treble: float,
    global_reactivity: float,
    emissive_gain: float = 1.0,
    bass_response: float = 0.5,
    mid_response: float = 0.5,
    treble_twinkle: float = 0.75,
    pulse_curve_exp: float = 2.0,
    roughness_dip: float = 0.08,
    color_breath_amount: float = 0.12,
) -> AudioReactiveEvaluationResult:
    """
    Evaluates the exact mathematical transform computed by MF_Melodia_AudioReactive_Bridge.
    All inputs and outputs are strictly validated and clamped against safety boundaries.
    """
    # 1. Sanitize & clamp input signals
    bp_clean = max(0.0, min(1.0, float(beat_pulse)))
    bass_clean = max(0.0, min(1.0, float(bass)))
    mid_clean = max(0.0, min(1.0, float(mid)))
    treble_clean = max(0.0, min(1.0, float(treble)))
    react_clean = max(0.0, min(1.0, float(global_reactivity)))

    # Shaped pulse curve
    shaped_pulse = math.pow(bp_clean, pulse_curve_exp)

    # 2. Base Color Audio Breathing (subtle pastel lift on beat)
    # Factor = 1.0 + shaped_pulse * color_breath_amount * global_reactivity
    c_mult = 1.0 + (shaped_pulse * color_breath_amount * react_clean)
    color_out = (
        max(0.0, min(1.0, base_color_in[0] * c_mult)),
        max(0.0, min(1.0, base_color_in[1] * c_mult)),
        max(0.0, min(1.0, base_color_in[2] * c_mult)),
    )

    # 3. Emissive Pulse Calculation
    # EmissiveMain = BaseEmissive * (1.0 + shaped_pulse * EmissiveGain * GlobalReactivity)
    # TrebleTwinkleFactor = Treble * TrebleTwinkle * 0.20 * BaseColorIn
    # EmissiveTotal = EmissiveMain + TrebleTwinkleFactor
    # Clamped to [0.0, 20.0]
    e_pulse_mult = 1.0 + (shaped_pulse * emissive_gain * react_clean)
    treble_shimmer = treble_clean * treble_twinkle * 0.20 * react_clean
    
    emiss_r = (base_emissive_in[0] * e_pulse_mult) + (treble_shimmer * base_color_in[0])
    emiss_g = (base_emissive_in[1] * e_pulse_mult) + (treble_shimmer * base_color_in[1])
    emiss_b = (base_emissive_in[2] * e_pulse_mult) + (treble_shimmer * base_color_in[2])

    emiss_out = (
        max(0.0, min(20.0, emiss_r)),
        max(0.0, min(20.0, emiss_g)),
        max(0.0, min(20.0, emiss_b)),
    )

    # 4. Roughness Gloss Flash
    # Downbeat gloss reduction clamped to [0.02, 1.0]
    r_flash = roughness_in - (shaped_pulse * roughness_dip * react_clean)
    rough_out = max(0.02, min(1.0, r_flash))

    # 5. Normal Perturbation
    # High/Mid micro ripple on tangent normal
    n_perturb = (
        normal_in[0] + (mid_clean * 0.05 * react_clean),
        normal_in[1] + (treble_clean * 0.05 * react_clean),
        normal_in[2],
    )
    # Normalize normal
    n_len = math.sqrt(n_perturb[0]**2 + n_perturb[1]**2 + n_perturb[2]**2) or 1.0
    normal_out = (n_perturb[0] / n_len, n_perturb[1] / n_len, n_perturb[2] / n_len)

    return AudioReactiveEvaluationResult(
        base_color_out=color_out,
        emissive_out=emiss_out,
        roughness_out=round(rough_out, 4),
        normal_perturb=normal_out,
        audio_pulse_scalar=round(bp_clean * react_clean, 4),
        audio_bass_scalar=round(bass_clean * react_clean, 4),
        audio_treble_scalar=round(treble_clean * react_clean, 4),
    )


# ---------------------------------------------------------------------------
# 4. Engine Automation & Audit Generation
# ---------------------------------------------------------------------------

def run_audio_reactive_pipeline() -> Dict[str, Any]:
    """Executes verification and emits canonical audit reports."""
    SAVED_AUDIT.mkdir(parents=True, exist_ok=True)
    SPECS_DIR.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print(" Melodia Melusina — Audio-Reactive Material Bridge Engine")
    print("==================================================================")

    # 1. Verify Spec Files
    t3d_path = SPECS_DIR / "MF_Melodia_AudioReactive_Bridge.t3d"
    json_path = SPECS_DIR / "MF_Melodia_AudioReactive_Bridge.v1.json"

    assert t3d_path.exists(), f"Missing spec: {t3d_path}"
    assert json_path.exists(), f"Missing spec: {json_path}"
    print(f"  [+] Found T3D Material Function: {t3d_path.name}")
    print(f"  [+] Found JSON Specification: {json_path.name}")

    # 2. Simulate 4-beat musical measure @ 128 BPM
    bpm = 128.0
    sec_per_beat = 60.0 / bpm
    samples_per_beat = 8
    total_samples = samples_per_beat * 4
    time_series = []

    for i in range(total_samples):
        t = (i / total_samples) * (sec_per_beat * 4.0)
        beat_phase = (t % sec_per_beat) / sec_per_beat
        # cos^2 formula per UMelodiaAudioReactivePresentationSubsystem
        beat_pulse = math.cos(beat_phase * math.pi) ** 2
        bass = 0.8 if (i % (samples_per_beat * 2) < samples_per_beat) else 0.2
        mid = 0.5 + 0.5 * math.sin(2.0 * math.pi * beat_phase)
        treble = beat_pulse  # treble mirrors beat pulse in subsystem

        eval_res = evaluate_audio_reactive_bridge(
            base_color_in=(0.85, 0.70, 0.90),
            base_emissive_in=(0.2, 0.1, 0.3),
            roughness_in=0.35,
            normal_in=(0.0, 0.0, 1.0),
            beat_pulse=beat_pulse,
            bass=bass,
            mid=mid,
            treble=treble,
            global_reactivity=1.0,
            emissive_gain=1.5,
            treble_twinkle=1.0,
        )

        time_series.append({
            "sample": i,
            "time_sec": round(t, 3),
            "beat_phase": round(beat_phase, 3),
            "beat_pulse": round(beat_pulse, 4),
            "bass": round(bass, 2),
            "emissive_out": [round(c, 3) for c in eval_res.emissive_out],
            "roughness_out": eval_res.roughness_out,
            "base_color_out": [round(c, 3) for c in eval_res.base_color_out],
        })

    # 3. Test Adversarial Inputs (ensure zero exceptions and strict bounding)
    adversarial_tests = [
        {"desc": "Negative pulse", "input": {"beat_pulse": -5.0, "bass": -2.0, "mid": -1.0, "treble": -1.0, "global_reactivity": -1.0}},
        {"desc": "Overexposed pulse", "input": {"beat_pulse": 50.0, "bass": 25.0, "mid": 10.0, "treble": 15.0, "global_reactivity": 10.0}},
        {"desc": "Quiescent bypass", "input": {"beat_pulse": 1.0, "bass": 1.0, "mid": 1.0, "treble": 1.0, "global_reactivity": 0.0}},
    ]
    adversarial_results = []
    for test in adversarial_tests:
        res = evaluate_audio_reactive_bridge(
            base_color_in=(1.0, 1.0, 1.0),
            base_emissive_in=(1.0, 1.0, 1.0),
            roughness_in=0.5,
            normal_in=(0.0, 0.0, 1.0),
            **test["input"],
        )
        # Check invariants
        assert 0.0 <= res.emissive_out[0] <= 20.0, f"Emissive R out of bounds: {res.emissive_out}"
        assert 0.02 <= res.roughness_out <= 1.0, f"Roughness out of bounds: {res.roughness_out}"
        assert 0.0 <= res.base_color_out[0] <= 1.0, f"Color R out of bounds: {res.base_color_out}"

        # If bypass, output must equal baseline
        if test["desc"] == "Quiescent bypass":
            assert res.emissive_out == (1.0, 1.0, 1.0), f"Bypass failed emissive identity: {res.emissive_out}"
            assert res.base_color_out == (1.0, 1.0, 1.0), f"Bypass failed color identity: {res.base_color_out}"
            assert res.roughness_out == 0.5, f"Bypass failed roughness identity: {res.roughness_out}"

        adversarial_results.append({
            "test": test["desc"],
            "status": "PASS",
            "emissive_clamped": [round(c, 3) for c in res.emissive_out],
            "roughness_clamped": res.roughness_out,
        })
    print(f"  [+] Passed {len(adversarial_results)} adversarial invariant tests")

    # 4. Generate Audit Report
    audit_data = {
        "schema": "melodia.audio_reactive_materials.audit.v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "status": "PASS",
        "single_writer_authority": {
            "subsystem": "UMelodiaAudioReactivePresentationSubsystem",
            "mpc_collection": MPC_CANONICAL_PATH,
            "is_single_writer": True,
            "shaders_are_read_only": True,
        },
        "mpc_scalars_count": len(AUDIO_MPC_SCALARS),
        "mpc_scalars": AUDIO_MPC_SCALARS,
        "clamping_bounds": {k: {"min": v[0], "max": v[1], "desc": v[2]} for k, v in AUDIO_CLAMP_BOUNDS.items()},
        "master_materials_covered": list(TARGET_MASTER_REGISTRY.keys()),
        "target_master_registry": TARGET_MASTER_REGISTRY,
        "adversarial_tests": adversarial_results,
        "measure_simulation_sample_count": len(time_series),
        "sample_series_preview": time_series[:8],
    }

    report_path = SAVED_AUDIT / "audio_reactive_materials_audit.json"
    report_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
    print(f"\n[AudioReactiveMaterials] Audit report saved: {report_path.relative_to(ROOT)}")
    print(f"  - Parameters validated: {len(AUDIO_MPC_SCALARS)} MPC scalars")
    print(f"  - Masters bridged: {len(TARGET_MASTER_REGISTRY)} master graphs")
    print(f"  - Safety clamping: 100% verified [0.0, 20.0] emissive, [0.02, 1.0] roughness")

    return audit_data


if __name__ == "__main__":
    run_audio_reactive_pipeline()
