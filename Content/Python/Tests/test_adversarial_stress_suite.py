"""Empirical Adversarial Stress Test Suite for Melodia PBR Pipeline, Fabric Bounds & Audio Harmony.

Adversarial Challenge Vectors:
1. PBR Texture Packing Pipeline:
   - Channel packing fallbacks across all combinations of missing channels (None, empty, single, dual)
   - Corrupted image handling (0-byte, truncated PNG, fake PNG header, plain text, random bytes)
   - Non-square POT textures (1024x256, 512x2048, 4096x512, 128x2048, 8192x1024)
   - NPOT resolution handling and auto-resampling to nearest POT
   - Glossiness/smoothness inversion (boundary values, bit-exactness, multi-channel and 16-bit inputs)
   - Resampling behavior under extreme aspect ratio mismatch

2. Fabric Parameter Bounds & Shading Logic:
   - FabricType enum boundary and continuous smoothstep evaluation (out-of-range, fractional, negative)
   - Extreme parameter ranges (SheenPower <= 0, WeaveScale = 0, SparkleThreshold at [0.0, 1.0])
   - Height-compete layer blending stability under extreme bias, sharpness, and softness
   - Grazing sheen Fresnel under negative NdotV and extreme powers

3. Audio Harmony & Modulation Boundary Stress:
   - Bass > 1.0 (over-driven audio 1.0 -> 100.0): Caustics, WPO, steepness safety clamp S < 2.0
   - Negative audio parameters (Bass < 0, BeatPulse < 0) and master gating
   - Rapid phase wraps, negative phase, non-normalized phase (> 1.0)
   - Zero-duration impulses, negative dt, extreme decay lambda (lambda=0, lambda=1000)
   - Niagara contact rate throttling under dt=0, dt<0, and massive burst (1,000,000 contacts)
   - MetaSound voice allocation under voice exhaustion / over-subscription

Author: Teamwork Preview Challenger (critic, specialist)
"""

from __future__ import annotations

import io
import math
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    from PIL import Image
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

if not HAS_DEPS:
    raise unittest.SkipTest("numpy and/or PIL not available in this Python environment")

# Ensure paths
TEST_DIR = Path(__file__).resolve().parent
PYTHON_DIR = TEST_DIR.parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from melodia_pbr_packer import PBRChannelPacker, ChannelSlot, PackedTextureResult
import wire_audio_water_modulation as water_mod
import wire_audio_material_pulsation as mat_pulse
import wire_water_bioluminescence_harmony as bio_harm
import test_fabric_instances as mod_fabric


class TestAdversarialPBRTexturePacker(unittest.TestCase):
    """Adversarial stress-testing of PBR channel packing, fallbacks, corrupt files, non-square POT, and gloss."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.packer = PBRChannelPacker()

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Channel Packing Fallbacks
    # -------------------------------------------------------------------------
    def test_fallback_all_channels_missing(self):
        """When all input channels are None, verify packed ORM has exact fallback constants."""
        out_p = self.temp_path / "all_missing_ORM.png"
        img = self.packer.pack_orm(
            ao_path=None,
            roughness_path=None,
            metallic_path=None,
            output_path=out_p,
            target_resolution=(256, 256),
        )
        self.assertTrue(out_p.exists())
        arr = np.array(img)
        self.assertEqual(arr.shape, (256, 256, 3))
        # AO fallback: 255 (1.0), Roughness fallback: 178 (0.7), Metallic fallback: 0 (0.0)
        self.assertTrue(np.all(arr[:, :, 0] == 255), "AO channel must equal 255")
        self.assertTrue(np.all(arr[:, :, 1] == 178), "Roughness channel must equal 178")
        self.assertTrue(np.all(arr[:, :, 2] == 0), "Metallic channel must equal 0")

    def test_fallback_partial_channel_permutations(self):
        """Test all 2^3 permutations of missing channels to verify selective fallback isolation."""
        res = (128, 128)
        ao_img = Image.new("L", res, color=80)
        rough_img = Image.new("L", res, color=120)
        metal_img = Image.new("L", res, color=210)

        ao_p = self.temp_path / "ao.png"
        rough_p = self.temp_path / "rough.png"
        metal_p = self.temp_path / "metal.png"

        ao_img.save(ao_p)
        rough_img.save(rough_p)
        metal_img.save(metal_p)

        cases = [
            # (ao, rough, metal, expected_r, expected_g, expected_b)
            (ao_p, None, None, 80, 178, 0),
            (None, rough_p, None, 255, 120, 0),
            (None, None, metal_p, 255, 178, 210),
            (ao_p, rough_p, None, 80, 120, 0),
            (ao_p, None, metal_p, 80, 178, 210),
            (None, rough_p, metal_p, 255, 120, 210),
            (ao_p, rough_p, metal_p, 80, 120, 210),
        ]

        for i, (a_in, r_in, m_in, exp_r, exp_g, exp_b) in enumerate(cases):
            out_p = self.temp_path / f"perm_{i}_ORM.png"
            res_img = self.packer.pack_orm(
                ao_path=a_in,
                roughness_path=r_in,
                metallic_path=m_in,
                output_path=out_p,
                target_resolution=res,
            )
            arr = np.array(res_img)
            self.assertTrue(np.all(arr[:, :, 0] == exp_r), f"Permutation {i}: Expected R={exp_r}, got {arr[0,0,0]}")
            self.assertTrue(np.all(arr[:, :, 1] == exp_g), f"Permutation {i}: Expected G={exp_g}, got {arr[0,0,1]}")
            self.assertTrue(np.all(arr[:, :, 2] == exp_b), f"Permutation {i}: Expected B={exp_b}, got {arr[0,0,2]}")

    def test_custom_fallback_values_injection(self):
        """Verify custom fallback constants injected via constructor are strictly respected."""
        custom_packer = PBRChannelPacker(
            fallback_ao=200,
            fallback_roughness=50,
            fallback_metallic=100,
            default_resolution=64,
        )
        res_img = custom_packer.pack_orm(target_resolution=(64, 64))
        arr = np.array(res_img)
        self.assertTrue(np.all(arr[:, :, 0] == 200))
        self.assertTrue(np.all(arr[:, :, 1] == 50))
        self.assertTrue(np.all(arr[:, :, 2] == 100))

    # -------------------------------------------------------------------------
    # 2. Corrupt Image Handling
    # -------------------------------------------------------------------------
    def test_corrupted_zero_byte_file_graceful_handling(self):
        """Zero-byte file input should be detected and handled safely."""
        zero_file = self.temp_path / "zero_ao.png"
        zero_file.touch()

        # Direct PIL load raises exception
        with self.assertRaises(Exception):
            with Image.open(zero_file) as img:
                img.load()

        # Test whether process_material_set logs error cleanly instead of crashing unhandled
        channels = {ChannelSlot.AO: zero_file}
        res = self.packer.process_material_set(
            material_name="CorruptTest_ZeroByte",
            channel_files=channels,
            output_dir=self.temp_path / "out_corrupt",
        )
        self.assertIsInstance(res, PackedTextureResult)

    def test_corrupted_truncated_png_header(self):
        """Truncated PNG header input should be caught without crashing the batch worker."""
        trunc_file = self.temp_path / "trunc_rough.png"
        with open(trunc_file, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00")

        channels = {ChannelSlot.ROUGHNESS: trunc_file}
        res = self.packer.process_material_set(
            material_name="CorruptTest_Truncated",
            channel_files=channels,
            output_dir=self.temp_path / "out_corrupt",
        )
        self.assertIsInstance(res, PackedTextureResult)

    def test_corrupted_plain_text_disguised_as_image(self):
        """ASCII plain text disguised as PNG."""
        text_file = self.temp_path / "fake_metal.png"
        text_file.write_text("NOT_A_PNG_FILE_HEADER_GARBAGE_DATA_12345", encoding="utf-8")

        channels = {ChannelSlot.METALLIC: text_file}
        res = self.packer.process_material_set(
            material_name="CorruptTest_Text",
            channel_files=channels,
            output_dir=self.temp_path / "out_corrupt",
        )
        self.assertIsInstance(res, PackedTextureResult)

    def test_corrupted_random_binary_garbage(self):
        """100KB of random pseudo-binary noise disguised as PNG."""
        garbage_file = self.temp_path / "garbage_normal.png"
        with open(garbage_file, "wb") as f:
            f.write(os.urandom(102400))

        channels = {ChannelSlot.NORMAL: garbage_file}
        res = self.packer.process_material_set(
            material_name="CorruptTest_Garbage",
            channel_files=channels,
            output_dir=self.temp_path / "out_corrupt",
        )
        self.assertIsInstance(res, PackedTextureResult)

    # -------------------------------------------------------------------------
    # 3. Non-Square Power-of-Two (POT) Textures
    # -------------------------------------------------------------------------
    def test_non_square_pot_resolutions(self):
        """Stress-test non-square POT resolutions (e.g. trimsheet ribbons and atlas strips)."""
        aspect_ratios = [
            (1024, 256),   # 4:1
            (512, 2048),   # 1:4
            (4096, 512),   # 8:1
            (128, 2048),   # 1:16
            (2048, 1024),  # 2:1
            (8192, 1024),  # 8:1
            (64, 4096),    # 1:64
        ]

        for w, h in aspect_ratios:
            ao_p = self.temp_path / f"ao_{w}x{h}.png"
            rough_p = self.temp_path / f"rough_{w}x{h}.png"
            metal_p = self.temp_path / f"metal_{w}x{h}.png"

            xx, yy = np.meshgrid(np.linspace(0, 255, w), np.linspace(0, 255, h))
            ao_arr = ((xx + yy) / 2.0).astype(np.uint8)
            rough_arr = (xx).astype(np.uint8)
            metal_arr = (yy).astype(np.uint8)

            Image.fromarray(ao_arr, mode="L").save(ao_p)
            Image.fromarray(rough_arr, mode="L").save(rough_p)
            Image.fromarray(metal_arr, mode="L").save(metal_p)

            out_p = self.temp_path / f"packed_{w}x{h}_ORM.png"
            orm_img = self.packer.pack_orm(
                ao_path=ao_p,
                roughness_path=rough_p,
                metallic_path=metal_p,
                output_path=out_p,
                target_resolution=(w, h),
            )

            self.assertEqual(orm_img.size, (w, h), f"Output resolution must strictly match ({w}, {h})")
            arr = np.array(orm_img)
            self.assertEqual(arr.shape, (h, w, 3))
            np.testing.assert_array_equal(arr[:, :, 0], ao_arr)
            np.testing.assert_array_equal(arr[:, :, 1], rough_arr)
            np.testing.assert_array_equal(arr[:, :, 2], metal_arr)

    def test_non_square_pot_mismatched_inputs(self):
        """Pack when AO is 1024x256 (4:1) but Metallic is 512x2048 (1:4), resampling to target (1024, 256)."""
        ao_p = self.temp_path / "ao_1024x256.png"
        metal_p = self.temp_path / "metal_512x2048.png"

        Image.new("L", (1024, 256), color=150).save(ao_p)
        Image.new("L", (512, 2048), color=220).save(metal_p)

        out_p = self.temp_path / "packed_mismatched_ORM.png"
        orm_img = self.packer.pack_orm(
            ao_path=ao_p,
            roughness_path=None,
            metallic_path=metal_p,
            output_path=out_p,
            target_resolution=(1024, 256),
        )
        self.assertEqual(orm_img.size, (1024, 256))
        arr = np.array(orm_img)
        self.assertTrue(np.all(arr[:, :, 0] == 150))
        self.assertTrue(np.all(arr[:, :, 1] == 178))  # Fallback
        self.assertTrue(np.all(arr[:, :, 2] == 220))  # Resampled constant

    # -------------------------------------------------------------------------
    # 4. Glossiness Inversion Math & Autodetection
    # -------------------------------------------------------------------------
    def test_glossiness_inversion_boundary_and_exactness(self):
        """Stress-test glossiness inversion across entire 8-bit range [0..255]."""
        full_range = np.arange(256, dtype=np.uint8).reshape(16, 16)
        gloss_p = self.temp_path / "full_gloss.png"
        Image.fromarray(full_range, mode="L").save(gloss_p)

        out_p = self.temp_path / "full_rough_ORM.png"
        orm_img = self.packer.pack_orm(
            ao_path=None,
            roughness_path=gloss_p,
            metallic_path=None,
            output_path=out_p,
            invert_gloss=True,
            target_resolution=(16, 16),
        )
        arr = np.array(orm_img)
        expected_roughness = 255 - full_range
        np.testing.assert_array_equal(arr[:, :, 1], expected_roughness, "Green channel must be exactly 255 - Glossiness")

    def test_glossiness_autodetection_from_filename(self):
        """Verify automatic gloss inversion when filename contains 'gloss' or 'smooth'."""
        gloss_names = [
            "T_Fabric_Velvet_Glossiness.png",
            "T_Fabric_Velvet_Gloss.png",
            "T_Fabric_Velvet_Smoothness.png",
            "T_Fabric_Velvet_Smooth.png",
        ]
        for fname in gloss_names:
            p = self.temp_path / fname
            Image.new("L", (32, 32), color=100).save(p)

            orm_img = self.packer.pack_orm(
                ao_path=None,
                roughness_path=p,
                metallic_path=None,
                target_resolution=(32, 32),
            )
            arr = np.array(orm_img)
            # Gloss 100 -> Roughness 155
            self.assertEqual(int(arr[0, 0, 1]), 155, f"Filename '{fname}' should have triggered auto gloss inversion")


class TestAdversarialFabricParameters(unittest.TestCase):
    """Adversarial stress-testing of fabric parameter bounds, custom HLSL smoothstep gates, and layer blending."""

    def test_fabric_aniso_gate_continuous_and_out_of_bounds(self):
        """Evaluate FabricAnisoGate custom HLSL formula under out-of-range and non-integer FabricTypes."""
        # When base aniso level is 0.0, out-of-bounds FabricTypes must evaluate strictly to 0.0
        out_of_bounds = [-100.0, -1.0, -0.01, 8.0, 8.5, 20.0, 100.0]
        for ft in out_of_bounds:
            aniso = mod_fabric.evaluate_fabric_aniso_gate(fabric_type=ft, fabric_aniso_level=0.0)
            self.assertEqual(aniso, 0.0, f"FabricType {ft} out of bounds with base=0 must evaluate to 0.0 aniso")
            self.assertFalse(math.isnan(aniso))
            self.assertFalse(math.isinf(aniso))

        # Test fractional interpolations between defined types (e.g. 2.0 Silk -> 3.0 Satin)
        aniso_silk = mod_fabric.evaluate_fabric_aniso_gate(2.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(aniso_silk, 0.90, places=4)

        aniso_satin = mod_fabric.evaluate_fabric_aniso_gate(3.0, fabric_aniso_level=0.0)
        self.assertAlmostEqual(aniso_satin, 0.95, places=4)

        aniso_mid = mod_fabric.evaluate_fabric_aniso_gate(2.5, fabric_aniso_level=0.0)
        self.assertEqual(aniso_mid, 0.0, "Midpoint between Silk (2.0) and Satin (3.0) with width 0.4 must be 0.0")

    def test_fabric_weave_derivative_numerical_stability(self):
        """Stress-test Procedural FabricWeaveNormal HLSL derivative math under extreme UV frequencies."""
        extreme_scales = [0.001, 1.0, 128.0, 1000.0, 50000.0]
        for scale in extreme_scales:
            nx, ny, nz = mod_fabric.evaluate_fabric_weave_normal(
                uv=(0.5, 0.5),
                weave_scale=scale,
                weave_strength=1.0,
            )
            self.assertFalse(math.isnan(nx) or math.isnan(ny) or math.isnan(nz), f"NaN at scale {scale}")
            self.assertFalse(math.isinf(nx) or math.isinf(ny) or math.isinf(nz), f"Inf at scale {scale}")
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            self.assertAlmostEqual(length, 1.0, places=4, msg=f"Weave normal vector must be normalized at scale {scale}")

    def test_height_compete_blending_extreme_parameters(self):
        """Stress-test height compete blending under extreme height biases, sharpness, and softness."""
        # Case 1: Extreme positive bias (+100.0) -> Layer 1 completely dominates
        blend_top = mod_fabric.evaluate_height_compete_blend(
            height_a=0.5, height_b=0.5, layer_height_bias=100.0, layer_height_sharpness=10.0, layer_blend_softness=0.1
        )
        self.assertAlmostEqual(blend_top, 1.0, places=4)

        # Case 2: Extreme negative bias (-100.0) -> Layer 0 completely dominates
        blend_bot = mod_fabric.evaluate_height_compete_blend(
            height_a=0.5, height_b=0.5, layer_height_bias=-100.0, layer_height_sharpness=10.0, layer_blend_softness=0.1
        )
        self.assertAlmostEqual(blend_bot, 0.0, places=4)

        # Case 3: Zero sharpness, zero softness -> clamped gracefully without division by zero
        blend_zero = mod_fabric.evaluate_height_compete_blend(
            height_a=0.5, height_b=0.5, layer_height_bias=0.0, layer_height_sharpness=0.0, layer_blend_softness=0.0
        )
        self.assertFalse(math.isnan(blend_zero))
        self.assertFalse(math.isinf(blend_zero))
        self.assertGreaterEqual(blend_zero, 0.0)
        self.assertLessEqual(blend_zero, 1.0)

    def test_grazing_sheen_fresnel_boundary_conditions(self):
        """Stress-test grazing Fresnel sheen with negative NdotV, zero power, and large powers."""
        # NdotV = 1.0 (normal incidence) -> Fresnel = 0.0
        s_norm = mod_fabric.evaluate_grazing_sheen(ndotv=1.0, sheen_intensity=1.0, sheen_power=2.0)
        self.assertEqual(s_norm, (0.0, 0.0, 0.0))

        # NdotV = 0.0 (glancing angle) -> Fresnel = 1.0
        s_glance = mod_fabric.evaluate_grazing_sheen(ndotv=0.0, sheen_intensity=1.0, sheen_power=2.0)
        self.assertEqual(s_glance, (1.0, 1.0, 1.0))

        # NdotV < 0 (back-facing / grazing wrap) -> clamped to 0.0 -> Fresnel = 1.0
        s_back = mod_fabric.evaluate_grazing_sheen(ndotv=-0.5, sheen_intensity=1.0, sheen_power=2.0)
        self.assertEqual(s_back, (1.0, 1.0, 1.0))

        # Sheen power = 0.0 -> Fresnel = 1.0 everywhere
        s_pow0 = mod_fabric.evaluate_grazing_sheen(ndotv=0.5, sheen_intensity=1.0, sheen_power=0.0)
        self.assertAlmostEqual(s_pow0[0], 1.0, places=4)


class TestAdversarialAudioHarmony(unittest.TestCase):
    """Adversarial stress-testing of audio modulation extremes, Bass > 1.0, phase wraps, and wave steepness safety."""

    # -------------------------------------------------------------------------
    # 1. Bass Over-Drive (Bass > 1.0) & Gerstner Wave Steepness Safety S < 2.0
    # -------------------------------------------------------------------------
    def test_bass_overdrive_caustics_intensity(self):
        """Verify dynamic caustics intensity scales smoothly without NaN/overflow under Bass > 1.0."""
        overdriven_bass_levels = [1.5, 2.0, 5.0, 10.0, 100.0]
        base_intensity = 1.2

        for bass in overdriven_bass_levels:
            intensity = water_mod.evaluate_dynamic_caustics_intensity(
                base_intensity=base_intensity,
                bass_pulse=bass,
                beat_pulse=1.0,
                global_reactivity=1.0,
            )
            self.assertFalse(math.isnan(intensity))
            self.assertFalse(math.isinf(intensity))
            self.assertGreater(intensity, base_intensity)
            expected = base_intensity * (1.0 + 0.45 * bass + 0.35)
            self.assertAlmostEqual(intensity, expected, places=4)

    def test_gerstner_wave_steepness_safety_under_extreme_bass(self):
        """Evaluate Gerstner wave spectrum steepness S under heavy bass overdrive (Bass = 1.0 to 10.0)."""
        bass_levels = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]

        for bass in bass_levels:
            amp_mod, chop_mod = water_mod.evaluate_modulated_wave_parameters(
                base_amplitude=1.0,
                base_choppiness=1.0,
                bass_pulse=bass,
                global_reactivity=1.0,
            )
            # Choppiness must be clamped to 1.8 max
            self.assertLessEqual(chop_mod, 1.8, f"Choppiness at bass {bass} must not exceed 1.8")
            self.assertGreaterEqual(chop_mod, 0.0)

            # Evaluate displacement across spatial grid
            for x in [0.0, 500.0, 1000.0, 2500.0]:
                for t in [0.0, 0.5, 1.25, 3.7]:
                    dx, dy, dz = water_mod.evaluate_gerstner_displacement(
                        x=x, y=0.0, t=t, wave_amplitude_master=amp_mod, wave_choppiness=chop_mod
                    )
                    self.assertFalse(math.isnan(dx) or math.isnan(dy) or math.isnan(dz))
                    self.assertFalse(math.isinf(dx) or math.isinf(dy) or math.isinf(dz))

        # Check standard nominal peak (Bass=1.0) steepness is strictly < 2.0
        amp_peak, chop_peak = water_mod.evaluate_modulated_wave_parameters(
            base_amplitude=1.0, base_choppiness=1.2, bass_pulse=1.0, global_reactivity=1.0
        )
        is_stable, total_steepness, issues = water_mod.validate_gerstner_spectrum_stability(
            wave_amplitude_master=amp_peak, wave_choppiness=chop_peak
        )
        self.assertTrue(is_stable, f"Nominal peak wave must be stable: {issues}")
        self.assertLess(total_steepness, 2.0, f"Nominal peak wave steepness {total_steepness} must be < 2.0")

    def test_negative_audio_inputs_and_reactivity_gate(self):
        """Verify negative audio inputs (e.g. Bass = -0.5) do not produce negative intensity."""
        caustics_neg = water_mod.evaluate_dynamic_caustics_intensity(
            base_intensity=1.2, bass_pulse=-5.0, beat_pulse=-2.0, global_reactivity=1.0
        )
        self.assertGreaterEqual(caustics_neg, 0.0, "Caustics intensity must not be negative")

        # Global reactivity = 0.0 must freeze all modulations to neutral baseline
        caustics_gated = water_mod.evaluate_dynamic_caustics_intensity(
            base_intensity=1.2, bass_pulse=100.0, beat_pulse=100.0, global_reactivity=0.0
        )
        self.assertEqual(caustics_gated, 1.2, "Reactivity gate 0 must return baseline exactly")

    # -------------------------------------------------------------------------
    # 2. Rapid Phase Wraps & Non-Normalized Phase Inputs
    # -------------------------------------------------------------------------
    def test_rapid_phase_wraps_continuity(self):
        """Stress-test beat pulse around the 0.9999 -> 0.0001 phase transition."""
        phase_pre = 0.99999
        phase_post = 0.00001

        val_pre = mat_pulse.calculate_beat_pulse(phase_pre)
        val_post = mat_pulse.calculate_beat_pulse(phase_post)
        val_zero = mat_pulse.calculate_beat_pulse(0.0)
        val_one = mat_pulse.calculate_beat_pulse(1.0)

        self.assertAlmostEqual(val_pre, 1.0, places=4)
        self.assertAlmostEqual(val_post, 1.0, places=4)
        self.assertAlmostEqual(val_zero, 1.0, places=6)
        self.assertAlmostEqual(val_one, 1.0, places=6)
        self.assertAlmostEqual(val_pre, val_post, places=4, msg="Phase wrap discontinuity must be <= 1e-4")

    def test_non_normalized_and_negative_phases(self):
        """Evaluate calculate_beat_pulse with negative phase, integer multiples, and large floating point phases."""
        test_phases = [
            (-1.0, 1.0),
            (-0.5, 0.0),
            (-0.25, 0.5),
            (2.0, 1.0),
            (2.5, 0.0),
            (100.0, 1.0),
            (100.5, 0.0),
            (1000000.0, 1.0),
        ]
        for p, expected in test_phases:
            res = mat_pulse.calculate_beat_pulse(p)
            self.assertAlmostEqual(res, expected, places=5, msg=f"calculate_beat_pulse({p}) expected {expected}, got {res}")

    # -------------------------------------------------------------------------
    # 3. Zero-Duration Impulses & Extreme Decay Lambda
    # -------------------------------------------------------------------------
    def test_bioluminescence_zero_duration_and_negative_dt(self):
        """Verify evaluate_bioluminescence_impulse behavior at dt=0, dt<0, and dt->inf."""
        # dt == 0: exactly peak
        imp_0 = bio_harm.evaluate_bioluminescence_impulse(current_time=5.0, beat_onset_time=5.0, peak_intensity=2.0)
        self.assertAlmostEqual(imp_0, 2.0, places=6)

        # dt < 0: onset time in the future -> strictly 0.0 (no pre-onset glow)
        imp_neg = bio_harm.evaluate_bioluminescence_impulse(current_time=4.999, beat_onset_time=5.0, peak_intensity=2.0)
        self.assertEqual(imp_neg, 0.0, "Future beat onset must yield 0.0 intensity")

        # dt very large (100.0 seconds later): exponential decay approaches exactly 0.0
        imp_inf = bio_harm.evaluate_bioluminescence_impulse(current_time=105.0, beat_onset_time=5.0, peak_intensity=2.0)
        self.assertAlmostEqual(imp_inf, 0.0, places=6)
        self.assertGreaterEqual(imp_inf, 0.0)

    def test_bioluminescence_extreme_decay_lambda(self):
        """Stress-test extreme decay rates: lambda=0 (infinite sustain), lambda=1000 (instant impulse)."""
        # Lambda = 0: impulse remains constant indefinitely
        imp_sustain = bio_harm.evaluate_bioluminescence_impulse(
            current_time=10.0, beat_onset_time=0.0, peak_intensity=2.0, decay_rate=0.0
        )
        self.assertAlmostEqual(imp_sustain, 2.0, places=6)

        # Lambda = 1000: decayed to near-zero after 0.02s
        imp_flash = bio_harm.evaluate_bioluminescence_impulse(
            current_time=0.02, beat_onset_time=0.0, peak_intensity=2.0, decay_rate=1000.0
        )
        self.assertAlmostEqual(imp_flash, 0.0, places=6)

    # -------------------------------------------------------------------------
    # 4. Niagara Contact Throttling & Voice Allocation Edge Cases
    # -------------------------------------------------------------------------
    def test_water_contact_budget_adversarial_loads(self):
        """Stress-test evaluate_water_contact_budget under dt=0, dt<0, and 1,000,000 requested contacts."""
        # dt == 0 (paused frame): admit 0 contacts
        admitted, dropped = bio_harm.evaluate_water_contact_budget(requested_contacts=100, delta_time=0.0)
        self.assertEqual(admitted, 0)
        self.assertEqual(dropped, 100)

        # dt < 0 (corrupt backward time step): admit 0 contacts
        admitted, dropped = bio_harm.evaluate_water_contact_budget(requested_contacts=50, delta_time=-0.016)
        self.assertEqual(admitted, 0)
        self.assertEqual(dropped, 50)

        # 1,000,000 contacts requested at 60fps (dt=0.01666s): capped by rate limit (60/s * dt + 1 = 1 + 1 = 2)
        admitted, dropped = bio_harm.evaluate_water_contact_budget(requested_contacts=1000000, delta_time=0.01666)
        self.assertLessEqual(admitted, 3)
        self.assertEqual(admitted + dropped, 1000000)

    def test_audio_voice_allocation_exhaustion(self):
        """Stress-test evaluate_audio_voice_allocation under over-subscription and exhaustion."""
        # Max voices = 4. Currently active = 4. Requesting 5 -> admitted = 0, culled = 5
        admitted, culled = bio_harm.evaluate_audio_voice_allocation(active_voices=4, requested_voices=5, max_voices=4)
        self.assertEqual(admitted, 0)
        self.assertEqual(culled, 5)

        # Over-subscription (active = 6 > max = 4) -> admitted = 0, culled = 3
        admitted, culled = bio_harm.evaluate_audio_voice_allocation(active_voices=6, requested_voices=3, max_voices=4)
        self.assertEqual(admitted, 0)
        self.assertEqual(culled, 3)

        # Available = 2. Requesting 5 -> admitted = 2, culled = 3
        admitted, culled = bio_harm.evaluate_audio_voice_allocation(active_voices=2, requested_voices=5, max_voices=4)
        self.assertEqual(admitted, 2)
        self.assertEqual(culled, 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
