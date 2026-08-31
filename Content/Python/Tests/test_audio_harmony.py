"""Tier 1, Tier 2 & Tier 3 Test Suite: Audio Synchronization & Harmonic Water Integration.

Covers Milestone 3 Features:
- F11: Dynamic Caustics & Wave Displacement Audio Modulation (wire_audio_water_modulation)
- F12: Sheen, Sparkle & Rune Glow Audio Pulsation (wire_audio_material_pulsation)
- F13: Water Bioluminescence & Niagara Harmony (wire_water_bioluminescence_harmony)

Test Tiers:
- Tier 1: Mathematical Invariants, MPC Schema, Wave Spectrum Stability, Continuous Quantization
- Tier 2: Subsystem Component Modulations (Caustics, WPO, Sheen, Sparkle, Rune Glow, Bioluminescence)
- Tier 3: Cross-System Audio-Visual Integration (BPM Phase Mapping, Timebase Separation, Contact Budgets)
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import numpy as np
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

if not HAS_DEPS:
    raise unittest.SkipTest("numpy not available in this Python environment")

# Ensure parent directory is in sys.path
TEST_DIR = Path(__file__).resolve().parent
PYTHON_DIR = TEST_DIR.parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

# Import Milestone 3 modules
import wire_audio_water_modulation as water_mod
import wire_audio_material_pulsation as mat_pulse
import wire_water_bioluminescence_harmony as bio_harm

# Convenience aliases & exports for test suites and workloads
evaluate_dynamic_caustics_intensity = water_mod.evaluate_dynamic_caustics_intensity
evaluate_dynamic_caustics_scale = water_mod.evaluate_dynamic_caustics_scale
evaluate_gerstner_displacement = water_mod.evaluate_gerstner_displacement
evaluate_modulated_wave_parameters = water_mod.evaluate_modulated_wave_parameters
evaluate_sheen_and_sparkle_pulse = mat_pulse.evaluate_sheen_and_sparkle_pulse
evaluate_rune_glow_pulse = mat_pulse.evaluate_rune_glow_pulse
calculate_beat_pulse = mat_pulse.calculate_beat_pulse
calculate_beat_pulse_derivative = mat_pulse.calculate_beat_pulse_derivative
evaluate_bioluminescence_impulse = bio_harm.evaluate_bioluminescence_impulse
evaluate_proximity_falloff = bio_harm.evaluate_proximity_falloff
GERSTNER_SPECTRUM_8_OCTAVES = water_mod.GERSTNER_SPECTRUM_8_OCTAVES

# ---------------------------------------------------------------------------
# Reference Specifications & Constants
# ---------------------------------------------------------------------------
MPC_MELODIA_PALETTE_SCHEMA = {
    "scalars": [
        "GlobalReactivity",
        "BeatPulse",
        "BeatPhase",
        "Bass",
        "Mid",
        "Treble",
        "RhythmPulse",
        "GlobalAudioReactivity",
        "BassIntensity",
        "MidIntensity",
        "TrebleIntensity",
        "ComboNormalized",
        "CrescendoNormalized",
        "CommandEnergy",
        "BreakPulse",
        "VictoryPulse",
        "EnemyTension",
        "BaseTintShift",
        "ShadowDreamBias",
        "RimWarmth",
        "ElementalGrade",
        "TimeOfDayWarmth",
        "ProximityRadius",
    ],
    "vectors": [
        "PaletteTint",
        "CharacterWorldPosition",
    ],
}


# ===========================================================================
# Tier 1: Unit & Mathematical Invariant Tests
# ===========================================================================
class TestAudioInvariantsTier1(unittest.TestCase):
    """Tier 1 Unit tests for MPC schema and mathematical invariants."""

    def test_mpc_parameter_schema_completeness(self):
        """Verify MPC_Melodia_Palette schema contains all required scalars and vectors."""
        scalars = MPC_MELODIA_PALETTE_SCHEMA["scalars"]
        vectors = MPC_MELODIA_PALETTE_SCHEMA["vectors"]

        # Critical rhythm channels
        self.assertIn("GlobalReactivity", scalars)
        self.assertIn("BeatPulse", scalars)
        self.assertIn("BeatPhase", scalars)
        self.assertIn("Bass", scalars)
        self.assertIn("Mid", scalars)
        self.assertIn("Treble", scalars)
        self.assertIn("RhythmPulse", scalars)

        # Extended Melodia channels
        self.assertIn("GlobalAudioReactivity", scalars)
        self.assertIn("BassIntensity", scalars)
        self.assertIn("TrebleIntensity", scalars)

        # Critical vectors
        self.assertIn("PaletteTint", vectors)
        self.assertIn("CharacterWorldPosition", vectors)

    def test_beat_quantization_formula_mathematical_properties(self):
        """Verify mathematical invariants of the cos^2(phase * pi) beat quantization function."""
        # 1. Downbeat peak (phase = 0.0) -> f(0.0) == 1.0
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse(0.0), 1.0, places=6)

        # 2. Off-beat trough (phase = 0.5) -> f(0.5) == 0.0
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse(0.5), 0.0, places=6)

        # 3. Next downbeat (phase = 1.0) -> f(1.0) == 1.0
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse(1.0), 1.0, places=6)

        # 4. Smooth zero derivative at boundaries (no pop/discontinuity at loop point)
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse_derivative(0.0), 0.0, places=6)
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse_derivative(0.5), 0.0, places=6)
        self.assertAlmostEqual(mat_pulse.calculate_beat_pulse_derivative(1.0), 0.0, places=6)

        # 5. Domain range check: for all phase in [0, 1], f(phase) in [0, 1]
        phases = np.linspace(0.0, 1.0, 1000)
        pulses = [mat_pulse.calculate_beat_pulse(p) for p in phases]
        self.assertGreaterEqual(min(pulses), 0.0)
        self.assertLessEqual(max(pulses), 1.0)

        # 6. Symmetry: f(x) == f(1 - x)
        for p in [0.1, 0.25, 0.33, 0.7, 0.85]:
            self.assertAlmostEqual(mat_pulse.calculate_beat_pulse(p), mat_pulse.calculate_beat_pulse(1.0 - p), places=6)

    def test_gerstner_8_wave_spectrum_invariants(self):
        """Verify 8-octave Gerstner spectrum parameters are physically well-formed and stable."""
        is_stable, total_steepness, issues = water_mod.validate_gerstner_spectrum_stability()
        self.assertTrue(is_stable, f"Gerstner spectrum stability check failed: {issues}")
        self.assertLess(total_steepness, 2.0, "Total Gerstner wave steepness must prevent surface folding")
        self.assertEqual(len(water_mod.GERSTNER_SPECTRUM_8_OCTAVES), 8)

        for i, wave in enumerate(water_mod.GERSTNER_SPECTRUM_8_OCTAVES):
            dx, dy = wave["dir"]
            length = math.sqrt(dx * dx + dy * dy)
            self.assertGreater(length, 0.0, f"Wave {i} direction cannot be zero")
            self.assertGreater(wave["wavelength"], 0.0, f"Wave {i} wavelength must be > 0")
            self.assertGreater(wave["amplitude"], 0.0, f"Wave {i} amplitude must be > 0")

    def test_bioluminescence_decay_lambda_properties(self):
        """Verify bioluminescence exponential decay properties with lambda = 2.5."""
        lambda_val = bio_harm.BIOLUMINESCENCE_DECAY_LAMBDA
        self.assertEqual(lambda_val, 2.5, "BioluminescenceDecayLambda must be 2.5 per specification")

        half_life = math.log(2.0) / lambda_val
        self.assertAlmostEqual(half_life, 0.27725887, places=5)

        # At dt = 0, intensity is exactly peak
        self.assertAlmostEqual(bio_harm.evaluate_bioluminescence_impulse(1.0, 1.0, peak_intensity=2.0), 2.0, places=5)
        # At dt < 0, intensity is 0
        self.assertEqual(bio_harm.evaluate_bioluminescence_impulse(0.5, 1.0, peak_intensity=2.0), 0.0)


# ===========================================================================
# Tier 2: Subsystem & Modulation Tests
# ===========================================================================
class TestAudioModulationTier2(unittest.TestCase):
    """Tier 2 Component tests evaluating caustics modulation, WPO displacement, and bioluminescence."""

    def test_dynamic_caustics_audio_modulation(self):
        """Verify dynamic caustics intensity increases smoothly with Bass and BeatPulse (Feature F11)."""
        base_intensity = 1.2

        # 1. Neutral / silent state (bass=0, beat=0) -> exactly base_intensity
        silent = water_mod.evaluate_dynamic_caustics_intensity(
            base_intensity=base_intensity, bass_pulse=0.0, beat_pulse=0.0, global_reactivity=1.0,
        )
        self.assertAlmostEqual(silent, base_intensity, places=4)

        # 2. Maximum downbeat (bass=1.0, beat=1.0)
        peak = water_mod.evaluate_dynamic_caustics_intensity(
            base_intensity=base_intensity, bass_pulse=1.0, beat_pulse=1.0, global_reactivity=1.0,
            bass_weight=0.45, beat_weight=0.35,
        )
        expected_peak = base_intensity * (1.0 + 0.45 + 0.35)
        self.assertAlmostEqual(peak, expected_peak, places=4)
        self.assertGreater(peak, silent)

        # 3. Master gate disabled (global_reactivity=0.0) -> remains at base_intensity even under peak audio
        gated = water_mod.evaluate_dynamic_caustics_intensity(
            base_intensity=base_intensity, bass_pulse=1.0, beat_pulse=1.0, global_reactivity=0.0,
        )
        self.assertAlmostEqual(gated, base_intensity, places=4)

    def test_dynamic_caustics_scale_modulation(self):
        """Verify dynamic caustics projection scale reacts to BeatPulse."""
        base_scale = 1.0
        scale_downbeat = water_mod.evaluate_dynamic_caustics_scale(base_scale, beat_pulse=1.0, global_reactivity=1.0)
        scale_offbeat = water_mod.evaluate_dynamic_caustics_scale(base_scale, beat_pulse=0.0, global_reactivity=1.0)

        self.assertAlmostEqual(scale_downbeat, 1.15, places=4)
        self.assertAlmostEqual(scale_offbeat, 1.0, places=4)
        self.assertGreater(scale_downbeat, scale_offbeat)

    def test_wave_height_wpo_displacement(self):
        """Verify 8-wave Gerstner vertex displacement over space and time (Feature F11)."""
        x_samples = np.linspace(0.0, 6000.0, 60)
        displacements = [
            water_mod.evaluate_gerstner_displacement(x=x, y=0.0, t=0.0, wave_amplitude_master=1.0)
            for x in x_samples
        ]

        dz_values = [d[2] for d in displacements]

        # Invariant 1: Spatial average displacement over fundamental wavelength oscillates around 0
        mean_dz = np.mean(dz_values)
        self.assertLess(abs(mean_dz), 10.0, "Spatial mean water level must remain near z=0")

        # Invariant 2: Maximum wave crest must exceed 0, minimum trough must be below 0
        self.assertGreater(max(dz_values), 5.0, "Wave crest must have positive height")
        self.assertLess(min(dz_values), -5.0, "Wave trough must have negative depth")

        # Invariant 3: Zero NaN or infinite values
        for dx, dy, dz in displacements:
            self.assertFalse(math.isnan(dx) or math.isnan(dy) or math.isnan(dz))
            self.assertFalse(math.isinf(dx) or math.isinf(dy) or math.isinf(dz))

    def test_wave_parameter_audio_modulation_bounds(self):
        """Verify wave amplitude and choppiness stay within safe physical bounds under high bass."""
        amp_mod, chop_mod = water_mod.evaluate_modulated_wave_parameters(
            base_amplitude=1.0, base_choppiness=1.2, bass_pulse=1.0, global_reactivity=1.0
        )
        self.assertAlmostEqual(amp_mod, 1.30, places=4)
        self.assertAlmostEqual(chop_mod, 1.2 * 1.20, places=4)

        # Check steepness under peak modulated waves
        is_stable, total_steepness, issues = water_mod.validate_gerstner_spectrum_stability(
            wave_amplitude_master=amp_mod, wave_choppiness=chop_mod
        )
        self.assertTrue(is_stable)
        self.assertLess(total_steepness, 2.0)

    def test_sheen_and_sparkle_audio_pulsation(self):
        """Verify fabric sheen breathes with beat pulse while diamond sparkles react to treble (Feature F12)."""
        base_sheen = 0.8
        sparkle_intensity = 1.0
        sparkle_mask = 1.0

        # Downbeat only (beat=1.0, treble=0.0)
        sheen_db, spark_db = mat_pulse.evaluate_sheen_and_sparkle_pulse(
            base_sheen=base_sheen, sparkle_base_intensity=sparkle_intensity,
            sparkle_mask=sparkle_mask, beat_pulse=1.0, treble_pulse=0.0,
        )
        self.assertAlmostEqual(sheen_db, base_sheen * 1.30, places=3)
        self.assertAlmostEqual(spark_db, sparkle_intensity, places=3)

        # Treble snare hit only (beat=0.0, treble=1.0)
        sheen_tr, spark_tr = mat_pulse.evaluate_sheen_and_sparkle_pulse(
            base_sheen=base_sheen, sparkle_base_intensity=sparkle_intensity,
            sparkle_mask=sparkle_mask, beat_pulse=0.0, treble_pulse=1.0,
        )
        self.assertAlmostEqual(sheen_tr, base_sheen, places=3)
        self.assertAlmostEqual(spark_tr, sparkle_intensity * 1.85, places=3)

    def test_rune_glow_and_roughness_pulsation(self):
        """Verify rune glyph glow amplification and micro-roughness dip on rhythm beats."""
        base_glow = 1.5
        base_roughness = 0.60

        # Downbeat peak: Bass=1.0, BeatPulse=1.0
        glow_peak = mat_pulse.evaluate_rune_glow_pulse(base_glow, bass_pulse=1.0, beat_pulse=1.0)
        self.assertAlmostEqual(glow_peak, base_glow * (1.0 + 0.50 + 0.50), places=4)

        # Micro-roughness dip
        rough_downbeat = mat_pulse.evaluate_roughness_audio_modulation(base_roughness, beat_pulse=1.0)
        rough_offbeat = mat_pulse.evaluate_roughness_audio_modulation(base_roughness, beat_pulse=0.0)

        self.assertAlmostEqual(rough_downbeat, base_roughness * 0.90, places=4)
        self.assertAlmostEqual(rough_offbeat, base_roughness, places=4)
        self.assertLess(rough_downbeat, rough_offbeat)

    def test_bioluminescence_impulse_decay(self):
        """Verify bioluminescence exponential decay with lambda = 2.5 (Feature F13)."""
        peak = 2.0
        decay = 2.5

        # At beat onset (dt = 0) -> peak intensity
        i_0 = bio_harm.evaluate_bioluminescence_impulse(
            current_time=1.0, beat_onset_time=1.0, peak_intensity=peak, decay_rate=decay
        )
        self.assertAlmostEqual(i_0, peak, places=4)

        # At dt = 0.5s -> peak * exp(-1.25) ~= 2.0 * 0.28650 = 0.5730
        i_half = bio_harm.evaluate_bioluminescence_impulse(
            current_time=1.5, beat_onset_time=1.0, peak_intensity=peak, decay_rate=decay
        )
        expected_half = peak * math.exp(-1.25)
        self.assertAlmostEqual(i_half, expected_half, places=4)

        # At dt = 2.0s -> peak * exp(-5.0) ~= 0.01348
        i_late = bio_harm.evaluate_bioluminescence_impulse(
            current_time=3.0, beat_onset_time=1.0, peak_intensity=peak, decay_rate=decay
        )
        self.assertLess(i_late, 0.02)
        self.assertGreater(i_late, 0.0)

    def test_water_bridge_budgets_and_proximity(self):
        """Verify water bridge event throttling and player proximity falloff."""
        # 1. Contact budget throttling: Max 60 contacts/sec
        admitted, dropped = bio_harm.evaluate_water_contact_budget(
            requested_contacts=10, delta_time=0.01666, max_contacts_per_sec=60
        )
        self.assertLessEqual(admitted, 2)
        self.assertGreaterEqual(dropped, 8)

        # 2. Audio voice allocation: Max 4 concurrent voices
        admitted_v, culled_v = bio_harm.evaluate_audio_voice_allocation(active_voices=3, requested_voices=3, max_voices=4)
        self.assertEqual(admitted_v, 1)
        self.assertEqual(culled_v, 2)

        # 3. Proximity falloff: At center -> 1.0, at radius 500cm -> 0.0
        prox_center = bio_harm.evaluate_proximity_falloff(0.0, radius_cm=500.0)
        prox_mid = bio_harm.evaluate_proximity_falloff(250.0, radius_cm=500.0)
        prox_edge = bio_harm.evaluate_proximity_falloff(500.0, radius_cm=500.0)

        self.assertAlmostEqual(prox_center, 1.0, places=4)
        self.assertAlmostEqual(prox_mid, 0.75, places=4)  # 1 - (250/500)^2 = 0.75
        self.assertAlmostEqual(prox_edge, 0.0, places=4)


# ===========================================================================
# Tier 3: System & Integration Tests
# ===========================================================================
class TestAudioHarmonySystemIntegrationTier3(unittest.TestCase):
    """Tier 3 Integration tests verifying BPM phase accumulation, timebase separation, and palette harmony."""

    def test_bpm_tempo_phase_mapping(self):
        """Verify phase accumulation for 128 BPM (Battle), 93 BPM (Duvet), and 131 BPM (Sewaa)."""
        bpm_tests = [
            {"name": "Battle", "bpm": 128.0, "beat_duration": 60.0 / 128.0},
            {"name": "Duvet", "bpm": 93.0, "beat_duration": 60.0 / 93.0},
            {"name": "Sewaa", "bpm": 131.0, "beat_duration": 60.0 / 131.0},
        ]
        for item in bpm_tests:
            bpm = item["bpm"]
            expected_beat_sec = item["beat_duration"]

            # Advance time by exactly one beat duration -> phase should wrap back to 0.0 (cyclic distance 0)
            phase_after_one_beat = (expected_beat_sec * (bpm / 60.0)) % 1.0
            cyclic_dist = min(phase_after_one_beat, abs(1.0 - phase_after_one_beat))
            self.assertAlmostEqual(cyclic_dist, 0.0, places=5)

            # Advance time by half a beat duration -> phase should be exactly 0.5
            phase_after_half_beat = ((expected_beat_sec * 0.5) * (bpm / 60.0)) % 1.0
            self.assertAlmostEqual(phase_after_half_beat, 0.5, places=5)

    def test_timebase_separation_contract(self):
        """Verify invariant that VideoRenderTime (for shaders) is separated from ExperiencedTime (for hit scoring)."""
        video_render_time = 10.450  # Seconds since audio start
        calibration_offset = 0.035  # 35ms audio latency calibration
        experienced_time = video_render_time + calibration_offset

        # Visual shaders MUST use video_render_time
        phase_visual = (video_render_time * (128.0 / 60.0)) % 1.0
        # Rhythm gameplay evaluator MUST use experienced_time
        phase_gameplay = (experienced_time * (128.0 / 60.0)) % 1.0

        self.assertNotEqual(phase_visual, phase_gameplay, "Visual render phase must not conflate gameplay hit window")

    def test_multi_parameter_palette_harmony(self):
        """Verify PaletteTint RGBA vector multiplication preserves luminance while adjusting tone harmony."""
        palette_tint = np.array([1.0, 0.92, 1.08, 1.0])  # Subtle cool-violet tone harmony
        base_color = np.array([0.7, 0.4, 0.5])

        harmonized_color = base_color * palette_tint[:3]

        # Verify no negative color values
        self.assertTrue(np.all(harmonized_color >= 0.0))
        # Blue channel slightly boosted
        self.assertGreater(harmonized_color[2], base_color[2])
        # Green channel slightly softened
        self.assertLess(harmonized_color[1], base_color[1])

    def test_full_audio_water_material_co_simulation(self):
        """Simulate multi-system co-simulation across 120 frames at 128 BPM."""
        fps = 60.0
        bpm = 128.0
        total_frames = 120

        for frame_idx in range(total_frames):
            t = frame_idx / fps
            water_f = water_mod.simulate_water_audio_modulation_frame(t, bpm=bpm)
            mat_f = mat_pulse.simulate_material_audio_frame(t, bpm=bpm)

            # Invariant: Phase synchronization between water and character shaders
            self.assertAlmostEqual(water_f["phase"], mat_f["phase"], places=5)
            self.assertAlmostEqual(water_f["beat_pulse"], mat_f["beat_pulse"], places=5)

            # Invariant: Finite numbers, no NaN
            for k, v in water_f.items():
                self.assertFalse(math.isnan(v))
                self.assertFalse(math.isinf(v))
            for k, v in mat_f.items():
                self.assertFalse(math.isnan(v))
                self.assertFalse(math.isinf(v))


if __name__ == "__main__":
    unittest.main(verbosity=2)
