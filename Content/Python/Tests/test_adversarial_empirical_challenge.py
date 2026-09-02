import json
import math
import sys
import unittest
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TEST_DIR = Path(__file__).resolve().parent
PYTHON_DIR = TEST_DIR.parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import test_fabric_instances as mod_fabric
import test_audio_harmony as mod_audio
import test_real_world_workloads as mod_workloads
import wire_audio_water_modulation as water_mod
import wire_audio_material_pulsation as mat_pulse
import wire_water_bioluminescence_harmony as bio_harm

@unittest.skipUnless(HAS_DEPS, "numpy and/or PIL not available in this Python environment")
class TestEmpiricalViewAnglesAndToonShadow(unittest.TestCase):
    def test_extreme_fresnel_sheen_curve(self):
        presets = mod_fabric.CORE_FABRIC_PRESETS
        nv_values = [-1.0, -0.5, -0.01, -1e-6, 0.0, 1e-6, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.9999, 1.0, 1.05, 1.5]
        for name, preset in presets.items():
            sheen_tint = (1.0, 0.9, 0.95)
            sheen_curve = []
            for nv in nv_values:
                sr, sg, sb = mod_fabric.evaluate_grazing_sheen(
                    ndotv=nv, sheen_intensity=preset.fabric_sheen,
                    sheen_power=preset.sheen_power, sheen_tint=sheen_tint
                )
                self.assertFalse(math.isnan(sr) or math.isnan(sg) or math.isnan(sb))
                self.assertFalse(math.isinf(sr) or math.isinf(sg) or math.isinf(sb))
                self.assertGreaterEqual(sr, 0.0)
                self.assertGreaterEqual(sg, 0.0)
                self.assertGreaterEqual(sb, 0.0)
                sheen_curve.append((nv, sr, sg, sb))
            sr_1, sg_1, sb_1 = mod_fabric.evaluate_grazing_sheen(
                ndotv=1.0, sheen_intensity=preset.fabric_sheen,
                sheen_power=preset.sheen_power, sheen_tint=sheen_tint
            )
            self.assertAlmostEqual(sr_1, 0.0, places=5)
            sr_0, sg_0, sb_0 = mod_fabric.evaluate_grazing_sheen(
                ndotv=0.0, sheen_intensity=preset.fabric_sheen,
                sheen_power=preset.sheen_power, sheen_tint=sheen_tint
            )
            exp_max_r = preset.fabric_sheen * sheen_tint[0]
            self.assertAlmostEqual(sr_0, exp_max_r, places=5)
            pos_curve = [(nv, sr) for (nv, sr, sg, sb) in sheen_curve if 0.0 <= nv <= 1.0]
            for i in range(len(pos_curve) - 1):
                self.assertGreaterEqual(pos_curve[i][1], pos_curve[i + 1][1] - 1e-7)

    def test_toon_shadow_floor_preservation_under_extreme_backlighting(self):
        sim = mod_workloads.ShadingSimulator()
        toon_profiles = ['TP_Hero', 'TP_Gold', 'TP_Character']
        
        # Test colors: physical fabrics, dark cloth, and pure white
        physical_test_colors = [
            ('DarkSkirtBlack', np.array([0.066, 0.066, 0.066])),
            ('DeepCrimson', np.array([0.15, 0.02, 0.03])),
            ('RedVelvet', np.array([0.75, 0.08, 0.15])),
            ('PureWhite', np.array([1.0, 1.0, 1.0])),
        ]
        
        nl_sweep = np.linspace(-1.0, 1.0, 100)
        for tp in toon_profiles:
            # 1. Test pitch-black edge case: shadow floor must strictly prevent pitch-black crushing (lum >= 0.035)
            black_shadow = sim.evaluate_toon_diffuse_ramp(-1.0, np.array([0.0, 0.0, 0.0]), toon_profile=tp)
            black_lum = float(np.mean(black_shadow))
            self.assertGreaterEqual(black_lum, 0.035, f'{tp} black shadow floor must be >= 0.035')

            # 2. Test physical fabrics for monotonicity and non-crushing
            for c_name, base_col in physical_test_colors:
                diffuse_curve = []
                for nl in nl_sweep:
                    diffuse = sim.evaluate_toon_diffuse_ramp(nl, base_col, toon_profile=tp)
                    self.assertFalse(np.any(np.isnan(diffuse)), f'{tp} {c_name} NaN at N.L={nl}')
                    self.assertFalse(np.any(np.isinf(diffuse)), f'{tp} {c_name} Inf at N.L={nl}')
                    self.assertTrue(np.all(diffuse >= 0.0))
                    diffuse_curve.append((nl, diffuse))
                
                deep_shadow = diffuse_curve[0][1]
                lum = float(np.mean(deep_shadow))
                self.assertGreaterEqual(lum, 0.035)
                
                lit_diffuse = diffuse_curve[-1][1]
                self.assertGreaterEqual(np.mean(lit_diffuse), np.mean(base_col) * 0.99)
                
                lum_series = [float(np.mean(d)) for (nl, d) in diffuse_curve]
                for i in range(len(lum_series) - 1):
                    self.assertGreaterEqual(
                        lum_series[i + 1], lum_series[i] - 1e-6,
                        f'{tp} {c_name} diffuse ramp must be monotonically non-decreasing'
                    )

    def test_on_disk_authored_textures_toon_monotonicity(self):
        """Verify that 100% of authored fabric and character BaseColor textures produce strictly monotonic ramps."""
        sim = mod_workloads.ShadingSimulator()
        fabrics_dir = Path('BS_GodFile/Content/Textures/Fabrics')
        melusina_dir = Path('BS_GodFile/Content/Melodia/Characters/Melusina/Textures')
        
        all_bc_files = list(fabrics_dir.glob('T_Fabric_*_BC.png')) + list(melusina_dir.glob('T_Melusina_*_BC.png'))
        self.assertGreaterEqual(len(all_bc_files), 15)
        
        for bc_file in all_bc_files:
            with Image.open(bc_file) as img:
                arr = np.array(img).astype(np.float32) / 255.0
                avg_color = arr.mean(axis=(0,1))
                d_shadow = sim.evaluate_toon_diffuse_ramp(-1.0, avg_color, 'TP_Hero')
                d_term = sim.evaluate_toon_diffuse_ramp(0.35, avg_color, 'TP_Hero')
                d_lit = sim.evaluate_toon_diffuse_ramp(1.0, avg_color, 'TP_Hero')
                s_lum = np.mean(d_shadow)
                t_lum = np.mean(d_term)
                l_lum = np.mean(d_lit)
                self.assertLessEqual(s_lum, t_lum + 1e-5, f'{bc_file.name} shadow ({s_lum}) > terminator ({t_lum})')
                self.assertLessEqual(t_lum, l_lum + 1e-5, f'{bc_file.name} terminator ({t_lum}) > lit ({l_lum})')


class TestEmpiricalAudioChannelSeparation(unittest.TestCase):
    def test_audio_frequency_crosstalk_isolation_matrix(self):
        base_intensity = 1.2
        base_scale = 1.0
        base_amp = 1.0
        base_chop = 1.0
        base_sheen = 0.85
        sparkle_intensity = 1.0
        sparkle_mask = 1.0
        rune_glow = 1.5
        base_roughness = 0.60
        caustic_base = water_mod.evaluate_dynamic_caustics_intensity(base_intensity, 0, 0)
        caustic_mid = water_mod.evaluate_dynamic_caustics_intensity(base_intensity, bass_pulse=0.0, beat_pulse=0.0)
        caustic_treble = water_mod.evaluate_dynamic_caustics_intensity(base_intensity, bass_pulse=0.0, beat_pulse=0.0)
        caustic_bass = water_mod.evaluate_dynamic_caustics_intensity(base_intensity, bass_pulse=1.0, beat_pulse=0.0)
        caustic_beat = water_mod.evaluate_dynamic_caustics_intensity(base_intensity, bass_pulse=0.0, beat_pulse=1.0)
        self.assertAlmostEqual(caustic_mid, caustic_base, places=6)
        self.assertAlmostEqual(caustic_treble, caustic_base, places=6)
        self.assertAlmostEqual(caustic_bass, caustic_base * 1.45, places=6)
        self.assertAlmostEqual(caustic_beat, caustic_base * 1.35, places=6)
        scale_base = water_mod.evaluate_dynamic_caustics_scale(base_scale, beat_pulse=0.0)
        scale_beat = water_mod.evaluate_dynamic_caustics_scale(base_scale, beat_pulse=1.0)
        self.assertAlmostEqual(scale_base, 1.0, places=6)
        self.assertAlmostEqual(scale_beat, 1.15, places=6)
        amp_base, chop_base = water_mod.evaluate_modulated_wave_parameters(base_amp, base_chop, bass_pulse=0.0)
        amp_bass, chop_bass = water_mod.evaluate_modulated_wave_parameters(base_amp, base_chop, bass_pulse=1.0)
        self.assertAlmostEqual(amp_base, 1.0, places=6)
        self.assertAlmostEqual(chop_base, 1.0, places=6)
        self.assertAlmostEqual(amp_bass, 1.30, places=6)
        self.assertAlmostEqual(chop_bass, 1.20, places=6)
        sheen_base, _ = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=0.0, treble_pulse=0.0)
        sheen_beat, _ = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=1.0, treble_pulse=0.0)
        sheen_treble, _ = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=0.0, treble_pulse=1.0)
        self.assertAlmostEqual(sheen_base, base_sheen, places=6)
        self.assertAlmostEqual(sheen_beat, base_sheen * 1.30, places=6)
        self.assertAlmostEqual(sheen_treble, base_sheen, places=6)
        _, spark_base = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=0.0, treble_pulse=0.0)
        _, spark_treble = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=0.0, treble_pulse=1.0)
        _, spark_beat = mat_pulse.evaluate_sheen_and_sparkle_pulse(base_sheen, sparkle_intensity, sparkle_mask, beat_pulse=1.0, treble_pulse=0.0)
        self.assertAlmostEqual(spark_base, sparkle_intensity, places=6)
        self.assertAlmostEqual(spark_treble, sparkle_intensity * 1.85, places=6)
        self.assertAlmostEqual(spark_beat, sparkle_intensity, places=6)
        rune_base = mat_pulse.evaluate_rune_glow_pulse(rune_glow, bass_pulse=0.0, beat_pulse=0.0)
        rune_bass = mat_pulse.evaluate_rune_glow_pulse(rune_glow, bass_pulse=1.0, beat_pulse=0.0)
        rune_beat = mat_pulse.evaluate_rune_glow_pulse(rune_glow, bass_pulse=0.0, beat_pulse=1.0)
        self.assertAlmostEqual(rune_base, rune_glow, places=6)
        self.assertAlmostEqual(rune_bass, rune_glow * 1.50, places=6)
        self.assertAlmostEqual(rune_beat, rune_glow * 1.50, places=6)
        rough_base = mat_pulse.evaluate_roughness_audio_modulation(base_roughness, beat_pulse=0.0)
        rough_beat = mat_pulse.evaluate_roughness_audio_modulation(base_roughness, beat_pulse=1.0)
        self.assertAlmostEqual(rough_base, base_roughness, places=6)
        self.assertAlmostEqual(rough_beat, base_roughness * 0.90, places=6)

    def test_phase_wrap_continuity_and_no_visual_popping(self):
        eps = 1e-7
        p_left = 1.0 - eps
        p_right = eps
        val_left = mat_pulse.calculate_beat_pulse(p_left)
        val_right = mat_pulse.calculate_beat_pulse(p_right)
        val_zero = mat_pulse.calculate_beat_pulse(0.0)
        val_one = mat_pulse.calculate_beat_pulse(1.0)
        self.assertAlmostEqual(val_left, 1.0, places=6)
        self.assertAlmostEqual(val_right, 1.0, places=6)
        self.assertAlmostEqual(val_zero, 1.0, places=6)
        self.assertAlmostEqual(val_one, 1.0, places=6)
        self.assertAlmostEqual(abs(val_left - val_right), 0.0, places=6)
        d0 = mat_pulse.calculate_beat_pulse_derivative(0.0)
        d05 = mat_pulse.calculate_beat_pulse_derivative(0.5)
        d1 = mat_pulse.calculate_beat_pulse_derivative(1.0)
        self.assertAlmostEqual(d0, 0.0, places=6)
        self.assertAlmostEqual(d05, 0.0, places=6)
        self.assertAlmostEqual(d1, 0.0, places=6)
        fps = 60.0
        bpm = 128.0
        dt = 1.0 / fps
        beat_duration = 60.0 / bpm
        d_phase = dt / beat_duration
        phases = np.arange(0.0, 1.0, d_phase)
        pulses = [mat_pulse.calculate_beat_pulse(p) for p in phases]
        for i in range(len(pulses) - 1):
            frame_delta = abs(pulses[i + 1] - pulses[i])
            self.assertLess(frame_delta, 0.12)

class TestEmpiricalMelusinaWardrobeSlotBindings(unittest.TestCase):
    def test_wardrobe_disk_textures_and_slot_mappings(self):
        melusina_tex_dir = Path(r'C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Textures')
        self.assertTrue(melusina_tex_dir.exists())
        slot_requirements = {
            'FrontPanel': ['BC', 'ORM', 'N', 'H', 'Sheen'],
            'Shawl': ['BC', 'ORM', 'N', 'H'],
            'Skirt': ['BC', 'ORM', 'N', 'H'],
            'Sleeve': ['BC', 'ORM', 'N', 'H', 'Alpha'],
            'Shirt': ['BC', 'ORM', 'N', 'H'],
        }
        for slot, channels in slot_requirements.items():
            for ch in channels:
                fname = f'T_Melusina_{slot}_{ch}.png'
                fpath = melusina_tex_dir / fname
                self.assertTrue(fpath.exists(), f'Missing {fname}')
                with Image.open(fpath) as img:
                    w, h = img.size
                    self.assertTrue(w > 0 and (w & (w - 1)) == 0)
                    self.assertTrue(h > 0 and (h & (h - 1)) == 0)
                    if ch == 'ORM':
                        self.assertEqual(img.mode, 'RGB')
                        arr = np.array(img)
                        self.assertGreater(float(arr[:, :, 0].mean()), 80.0)
                        self.assertGreater(float(arr[:, :, 1].mean()), 10.0)
                    elif ch == 'N':
                        self.assertEqual(img.mode, 'RGB')
                        arr = np.array(img)
                        self.assertGreater(float(arr[:, :, 2].mean()), 110.0)

    def test_wardrobe_json_manifest_integrity(self):
        json_path = Path(r'C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_wardrobe_wiring.json')
        self.assertTrue(json_path.exists())
        data = json.loads(json_path.read_text(encoding='utf-8'))
        self.assertEqual(data.get('slots_wired'), 5)
        self.assertTrue(data.get('valid', False))
        self.assertEqual(len(data.get('errors', [])), 0)
        bindings = data.get('bindings', {})
        expected_slots = ['M_frontpanel_001', 'M_SHAWL_001', 'M_SKIRT_003', 'M_sleeve_003', 'M_shirt_001']
        for slot in expected_slots:
            self.assertIn(slot, bindings)
            b = bindings[slot]
            self.assertFalse(b['static_switches']['bUseSeparateRoughnessMap'])
            self.assertFalse(b['static_switches']['bUseSeparateMetallicMap'])
            self.assertTrue(b['static_switches']['bEnableFabricAnisoGate'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
