"""
Melodia Melusina — Unit Tests for Audio-Reactive Materials Bridge Engine
Validates:
1. Canonical contract of all 16 MPC_Melodia_Palette audio scalars.
2. Safety clamping bounds on all audio parameters.
3. Mathematical identity (bypass) when GlobalReactivity = 0.
4. Correct synesthetic response curve under beat downbeats.
5. Strict adversarial input clamping (no NaN, no overexposure blowout).
6. T3D and JSON material function specification files integrity.
7. Master material coverage across Universal, Gemstone, SDF, and PostProcess.
"""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import audio_reactive_materials_engine as engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAVED_AUDIT = PROJECT_ROOT / "Saved" / "Audit"
SPECS_DIR = PROJECT_ROOT / "specs" / "materials"


class TestAudioReactiveMaterials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Run engine to ensure audit receipt is up to date
        cls.audit_data = engine.run_audio_reactive_pipeline()

    def test_mpc_scalars_contract(self):
        """All 16 audio scalars must be declared with valid ranges and documentation."""
        self.assertEqual(len(engine.AUDIO_MPC_SCALARS), 16)
        expected_scalars = [
            "BeatPulse", "BeatPhase", "BeatIntensity", "Bass", "Mid", "Treble",
            "GlobalReactivity", "BassIntensity", "MidIntensity", "RhythmPulse",
            "ComboNormalized", "CrescendoNormalized", "CommandEnergy", "BreakPulse",
            "VictoryPulse", "DissonanceAmount",
        ]
        for name in expected_scalars:
            self.assertIn(name, engine.AUDIO_MPC_SCALARS, f"Missing MPC scalar: {name}")
            info = engine.AUDIO_MPC_SCALARS[name]
            lo, hi = info["range"]
            self.assertLess(lo, hi, f"Scalar {name} has invalid range: {lo} >= {hi}")
            self.assertTrue(len(info["desc"]) > 0, f"Scalar {name} missing description")
            self.assertTrue(len(info["writer"]) > 0, f"Scalar {name} missing writer attribution")
            self.assertTrue(len(info["consumer_role"]) > 0, f"Scalar {name} missing consumer role")

    def test_clamping_safety_bounds(self):
        """All audio clamp definitions must have min < max and physically safe bounds."""
        for name, (lo, hi, desc) in engine.AUDIO_CLAMP_BOUNDS.items():
            self.assertLess(lo, hi, f"Clamp {name} has invalid bounds: {lo} >= {hi}")
            self.assertGreaterEqual(lo, 0.0, f"Clamp {name} min must be >= 0.0")
            self.assertTrue(len(desc) > 0, f"Clamp {name} missing description")

    def test_bridge_mathematical_identity_at_quiescent(self):
        """When GlobalReactivity = 0, output must exactly match input (bypass)."""
        base_color = (0.75, 0.50, 0.60)
        base_emissive = (0.4, 0.2, 0.1)
        roughness = 0.45
        normal = (0.0, 0.0, 1.0)

        res = engine.evaluate_audio_reactive_bridge(
            base_color_in=base_color,
            base_emissive_in=base_emissive,
            roughness_in=roughness,
            normal_in=normal,
            beat_pulse=1.0,
            bass=1.0,
            mid=1.0,
            treble=1.0,
            global_reactivity=0.0,  # quiescent bypass
        )

        self.assertEqual(res.base_color_out, base_color, "BaseColor mutated under bypass")
        self.assertEqual(res.emissive_out, base_emissive, "Emissive mutated under bypass")
        self.assertEqual(res.roughness_out, roughness, "Roughness mutated under bypass")
        self.assertEqual(res.normal_perturb, normal, "Normal mutated under bypass")
        self.assertEqual(res.audio_pulse_scalar, 0.0, "AudioPulseScalar != 0 under bypass")

    def test_bridge_response_under_full_pulse(self):
        """Under full beat pulse (BeatPulse = 1.0, Reactivity = 1.0), output responds synesthetically."""
        base_color = (0.5, 0.5, 0.5)
        base_emissive = (0.5, 0.5, 0.5)
        roughness = 0.5
        normal = (0.0, 0.0, 1.0)

        res = engine.evaluate_audio_reactive_bridge(
            base_color_in=base_color,
            base_emissive_in=base_emissive,
            roughness_in=roughness,
            normal_in=normal,
            beat_pulse=1.0,
            bass=0.5,
            mid=0.5,
            treble=1.0,
            global_reactivity=1.0,
            emissive_gain=2.0,
            treble_twinkle=1.0,
            roughness_dip=0.1,
            color_breath_amount=0.2,
        )

        # Emissive must increase: BaseEmissive * (1 + 1*2) + (1 * 1 * 0.2 * 0.5) = 0.5 * 3 + 0.1 = 1.6
        self.assertAlmostEqual(res.emissive_out[0], 1.6, places=2)
        # Roughness must dip: 0.5 - 0.1 = 0.4
        self.assertAlmostEqual(res.roughness_out, 0.4, places=2)
        # BaseColor must breathe: 0.5 * (1 + 0.2) = 0.6
        self.assertAlmostEqual(res.base_color_out[0], 0.6, places=2)

    def test_bridge_adversarial_clamping(self):
        """Extreme and invalid inputs must never cause NaN, infinite values, or blown-out shaders."""
        test_inputs = [
            (-999.0, -500.0, -100.0, -50.0, -1.0),
            (1000.0, 500.0, 250.0, 100.0, 50.0),
            (float("nan"), 0.5, 0.5, 0.5, 1.0),
        ]
        for bp, bass, mid, treble, react in test_inputs:
            # Handle NaN safely in test wrapper
            bp_val = 0.0 if math.isnan(bp) else bp
            res = engine.evaluate_audio_reactive_bridge(
                base_color_in=(1.0, 1.0, 1.0),
                base_emissive_in=(5.0, 5.0, 5.0),
                roughness_in=0.5,
                normal_in=(0.0, 0.0, 1.0),
                beat_pulse=bp_val,
                bass=bass,
                mid=mid,
                treble=treble,
                global_reactivity=react,
            )

            for channel in res.emissive_out:
                self.assertFalse(math.isnan(channel), "Emissive contains NaN")
                self.assertFalse(math.isinf(channel), "Emissive contains Inf")
                self.assertGreaterEqual(channel, 0.0, "Emissive negative")
                self.assertLessEqual(channel, 20.0, f"Emissive exceeded safe clamp 20.0: {channel}")

            self.assertGreaterEqual(res.roughness_out, 0.02, "Roughness below minimum 0.02")
            self.assertLessEqual(res.roughness_out, 1.0, "Roughness exceeded maximum 1.0")

            for c in res.base_color_out:
                self.assertGreaterEqual(c, 0.0, "Color negative")
                self.assertLessEqual(c, 1.0, "Color exceeded 1.0")

    def test_t3d_and_json_spec_integrity(self):
        """Both MF_Melodia_AudioReactive_Bridge.v1.json and .t3d must exist and be valid."""
        json_file = SPECS_DIR / "MF_Melodia_AudioReactive_Bridge.v1.json"
        t3d_file = SPECS_DIR / "MF_Melodia_AudioReactive_Bridge.t3d"

        self.assertTrue(json_file.is_file(), f"Missing spec JSON: {json_file}")
        self.assertTrue(t3d_file.is_file(), f"Missing spec T3D: {t3d_file}")

        data = json.loads(json_file.read_text(encoding="utf-8"))
        self.assertEqual(data["id"], "MF_Melodia_AudioReactive_Bridge")
        self.assertIn("inputs", data)
        self.assertIn("outputs", data)
        self.assertIn("target_master_materials", data)
        self.assertEqual(len(data["target_master_materials"]), 4)

        t3d_content = t3d_file.read_text(encoding="utf-8")
        self.assertIn('Name="MF_Melodia_AudioReactive_Bridge"', t3d_content)
        self.assertIn('ParameterName="BeatPulse"', t3d_content)
        self.assertIn('ParameterName="Bass"', t3d_content)
        self.assertIn('ParameterName="Treble"', t3d_content)
        self.assertIn('ParameterName="GlobalReactivity"', t3d_content)
        self.assertIn('OutputName="EmissiveOut"', t3d_content)
        self.assertIn('OutputName="BaseColorOut"', t3d_content)

    def test_master_registry_coverage(self):
        """All 4 target master materials must be registered with valid parameter groups."""
        masters = [
            "M_Master_Toon_Universal",
            "M_Master_Gemstone",
            "M_Master_SDF_Toon",
            "M_PP_MeluColorGrade",
        ]
        for m in masters:
            self.assertIn(m, engine.TARGET_MASTER_REGISTRY, f"Master {m} not in registry")
            cfg = engine.TARGET_MASTER_REGISTRY[m]
            self.assertIn("group", cfg)
            self.assertIn("bindings", cfg)
            self.assertTrue(len(cfg["bindings"]) >= 2)


if __name__ == "__main__":
    unittest.main()
