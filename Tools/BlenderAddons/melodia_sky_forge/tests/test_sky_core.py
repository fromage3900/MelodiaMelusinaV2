"""Offline tests for Melodia Sky Forge. No bpy, no Blender, no Unreal.

Guards the pure-Python contract:
  - the shipped theme library validates against the v1 rules;
  - every theme's musical identity uses the world_recipe vocabulary;
  - flatten_for_td() emits the stable sidecar keys TouchDesigner reads;
  - sun_direction() is a unit vector with sane elevation behaviour.

Run:
  python -B -m unittest discover -s Tools/BlenderAddons/melodia_sky_forge/tests -v
"""

import json
import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ADDON = os.path.normpath(os.path.join(_HERE, ".."))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

import sky_core  # noqa: E402


class TestLibrary(unittest.TestCase):
    def test_shipped_library_loads_and_validates(self):
        lib = sky_core.load_library()
        self.assertEqual(lib["schema"], sky_core.LIBRARY_SCHEMA_ID)
        self.assertGreaterEqual(len(lib["themes"]), 5)

    def test_one_theme_per_mode(self):
        lib = sky_core.load_library()
        modes = {t["musical"]["mode_id"] for t in lib["themes"]}
        self.assertEqual(modes, set(sky_core.MODE_IDS))

    def test_all_theme_ids_snake_case(self):
        lib = sky_core.load_library()
        for t in lib["themes"]:
            tid = t["theme_id"]
            self.assertTrue(tid[:1].islower(), tid)
            self.assertTrue(tid.replace("_", "a").isalnum(), tid)

    def test_get_theme_roundtrip(self):
        lib = sky_core.load_library()
        first = lib["themes"][0]
        self.assertIs(sky_core.get_theme(lib, first["theme_id"]), first)
        with self.assertRaises(KeyError):
            sky_core.get_theme(lib, "does_not_exist")


class TestValidateTheme(unittest.TestCase):
    def _valid(self):
        return {
            "schema": sky_core.SCHEMA_ID,
            "theme_id": "unit_test_sky",
            "musical": {"mode_id": "ionian", "root_pitch_class": 0, "bpm": 100},
            "sky": {
                "gradient": {"zenith": [0, 0, 1], "horizon": [1, 1, 1], "nadir": [0, 0, 0], "banding_steps": 6},
                "sun": {"azimuth_deg": 90, "elevation_deg": 30, "color": [1, 1, 1]},
                "clouds": {"coverage": 0.3},
            },
        }

    def test_valid_theme_passes(self):
        self.assertEqual(sky_core.validate_theme(self._valid()), [])

    def test_bad_mode_rejected(self):
        t = self._valid()
        t["musical"]["mode_id"] = "mixolydian"
        self.assertTrue(sky_core.validate_theme(t))

    def test_bad_pitch_class_rejected(self):
        t = self._valid()
        t["musical"]["root_pitch_class"] = 12
        self.assertTrue(sky_core.validate_theme(t))

    def test_out_of_range_color_rejected(self):
        t = self._valid()
        t["sky"]["gradient"]["zenith"] = [0, 0, 1.5]
        self.assertTrue(sky_core.validate_theme(t))

    def test_band_steps_range(self):
        t = self._valid()
        t["sky"]["gradient"]["banding_steps"] = 99
        self.assertTrue(sky_core.validate_theme(t))

    def test_band_profile_enum(self):
        t = self._valid()
        t["sky"]["gradient"]["banding_profile"] = "halo"
        self.assertEqual(sky_core.validate_theme(t), [])
        t["sky"]["gradient"]["banding_profile"] = "wiggly"
        self.assertTrue(sky_core.validate_theme(t))

    def test_sun_keying_enum_and_range(self):
        t = self._valid()
        t["sky"]["sun"]["keying"] = {"mode": "root_pitch_class", "semitone_degrees": 30}
        self.assertEqual(sky_core.validate_theme(t), [])
        t["sky"]["sun"]["keying"]["mode"] = "quartal"
        self.assertTrue(sky_core.validate_theme(t))
        t["sky"]["sun"]["keying"] = {"mode": "explicit", "semitone_degrees": 99}
        self.assertTrue(sky_core.validate_theme(t))

    def test_motion_range(self):
        t = self._valid()
        t["sky"]["motion"] = {"cloud_drift_per_beat": 0.5, "aurora_pulse_per_beat": 0.2}
        self.assertEqual(sky_core.validate_theme(t), [])
        t["sky"]["motion"]["aurora_pulse_per_beat"] = 2.0
        self.assertTrue(sky_core.validate_theme(t))
        t["sky"]["motion"]["cloud_drift_per_beat"] = -1
        self.assertTrue(sky_core.validate_theme(t))


class TestSunDirection(unittest.TestCase):
    def test_unit_length(self):
        for az in (0, 90, 180, 270, 359):
            for el in (-10, 0, 45, 90):
                x, y, z = sky_core.sun_direction(az, el)
                self.assertAlmostEqual(math.sqrt(x * x + y * y + z * z), 1.0, places=6)

    def test_zenith_is_up(self):
        _, _, z = sky_core.sun_direction(0, 90)
        self.assertAlmostEqual(z, 1.0, places=6)

    def test_horizon_north_is_negative_y(self):
        # Azimuth 0 = north; Blender world convention the builder assumes.
        x, y, z = sky_core.sun_direction(0, 0)
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, -1.0, places=6)
        self.assertAlmostEqual(z, 0.0, places=6)


class TestFlattenForTd(unittest.TestCase):
    REQUIRED_KEYS = (
        "schema", "theme_id", "mode_id", "root_pitch_class", "bpm",
        "band_profile",
        "grad_zenith", "grad_horizon", "grad_nadir", "grad_banding_steps",
        "sun_azimuth_deg", "sun_keyed_by", "sun_elevation_deg", "sun_dir", "sun_color",
        "sun_disc_radius_deg", "sun_glow_strength",
        "cloud_coverage", "cloud_scale", "cloud_softness", "cloud_seed",
        "cloud_lit", "cloud_shadow",
        "star_density", "star_color",
        "aurora_strength", "aurora_color_a", "aurora_color_b",
        "cloud_drift_per_beat", "aurora_pulse_per_beat",
    )

    def test_every_shipped_theme_flattens_with_all_keys(self):
        lib = sky_core.load_library()
        for theme in lib["themes"]:
            flat = sky_core.flatten_for_td(theme)
            for key in self.REQUIRED_KEYS:
                self.assertIn(key, flat, f"{theme['theme_id']} missing {key}")
            self.assertEqual(flat["schema"], "melodia.sky_theme_flat.v1")
            self.assertEqual(flat["mode_id"], theme["musical"]["mode_id"])
            sx, sy, sz = flat["sun_dir"]
            self.assertAlmostEqual(math.sqrt(sx * sx + sy * sy + sz * sz), 1.0, places=6)

    def test_flatten_rejects_invalid_theme(self):
        with self.assertRaises(ValueError):
            sky_core.flatten_for_td({"schema": "wrong", "theme_id": "x"})


class TestRootKeying(unittest.TestCase):
    def test_sakura_keyed_to_root(self):
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "sakura_dream_dorian")
        self.assertEqual(theme["sky"]["sun"]["keying"]["mode"], "root_pitch_class")
        flat = sky_core.flatten_for_td(theme)
        self.assertEqual(flat["sun_keyed_by"], "root_pitch_class")
        # root 9 * 30 deg = 270 (was 265 authored explicitly)
        self.assertAlmostEqual(flat["sun_azimuth_deg"], 270.0, places=6)
        sx, sy, sz = flat["sun_dir"]
        self.assertAlmostEqual(sx, math.sin(math.radians(270)) * math.cos(math.radians(12)), places=6)

    def test_explicit_theme_unkeyed(self):
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "morning_meadow_ionian")
        flat = sky_core.flatten_for_td(theme)
        self.assertEqual(flat["sun_keyed_by"], "explicit")
        self.assertAlmostEqual(flat["sun_azimuth_deg"], 95.0, places=6)

    def test_keyed_azimuth_mod_360(self):
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "sakura_dream_dorian")
        theme["musical"]["root_pitch_class"] = 11
        az, keyed_by = sky_core.resolved_sun_azimuth(theme)
        self.assertAlmostEqual(az, 11 * 30 % 360, places=6)
        self.assertEqual(keyed_by, "root_pitch_class")


class TestBandProfile(unittest.TestCase):
    def test_mode_flavors(self):
        lib = sky_core.load_library()
        expected = {
            "morning_meadow_ionian": "wide",
            "sakura_dream_dorian": "gradual",
            "harmonic_glass_lydian": "halo",
            "fallen_moon_aeolian": "narrow",
            "petal_cantata_phrygian": "cracked",
        }
        for theme in lib["themes"]:
            flat = sky_core.flatten_for_td(theme)
            self.assertEqual(flat["band_profile"], expected[theme["theme_id"]])

    def test_explicit_override_beats_mode(self):
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "morning_meadow_ionian")
        theme["sky"]["gradient"]["banding_profile"] = "narrow"
        self.assertEqual(sky_core.band_profile(theme), "narrow")

    def test_motion_defaults_zero_and_sakura_demo(self):
        lib = sky_core.load_library()
        meadow = sky_core.flatten_for_td(sky_core.get_theme(lib, "morning_meadow_ionian"))
        self.assertEqual(meadow["cloud_drift_per_beat"], 0.0)
        self.assertEqual(meadow["aurora_pulse_per_beat"], 0.0)
        sakura = sky_core.flatten_for_td(sky_core.get_theme(lib, "sakura_dream_dorian"))
        self.assertAlmostEqual(sakura["cloud_drift_per_beat"], 0.08, places=6)
        self.assertEqual(sakura["aurora_pulse_per_beat"], 0.0)


class TestBeatOffsets(unittest.TestCase):
    def test_frame0_is_static_sky(self):
        beats = sky_core.beat_offsets(8, bpm=88, drift_per_beat=0.08, aurora_pulse=0.1)
        self.assertEqual(len(beats), 8)
        b0 = beats[0]
        self.assertEqual(b0["frame"], 0)
        self.assertAlmostEqual(b0["phase"], 0.0, places=6)
        self.assertAlmostEqual(b0["cloud_w_offset"], 0.0, places=6)
        self.assertAlmostEqual(b0["aurora_pulse_multiplier"], 1.0, places=6)

    def test_phases_and_bar_seconds(self):
        beats = sky_core.beat_offsets(8, bpm=88, drift_per_beat=0.08, aurora_pulse=0.1)
        for i, b in enumerate(beats):
            self.assertAlmostEqual(b["phase"], i / 8, places=6)
            self.assertAlmostEqual(b["cloud_w_offset"], (i / 8) * 0.08 * 4, places=6)
        spb = 60.0 / 88
        self.assertAlmostEqual(beats[-1]["seconds_in_bar"], (7 / 8) * spb * 4, places=6)
        self.assertAlmostEqual(beats[0]["seconds_in_bar"], 0.0, places=6)

    def test_aurora_pulses_by_beat(self):
        beats = sky_core.beat_offsets(8, bpm=120, aurora_pulse=0.2)
        mid = beats[2]  # phase 0.25 -> sin(pi/2)=1
        self.assertAlmostEqual(mid["aurora_pulse_multiplier"], 1.2, places=6)
        back = beats[6]  # phase 0.75 -> sin(3pi/2) = -1
        self.assertAlmostEqual(back["aurora_pulse_multiplier"], 0.8, places=6)

    def test_single_frame_is_static(self):
        beats = sky_core.beat_offsets(1, bpm=88, drift_per_beat=0.5, aurora_pulse=0.5)
        self.assertEqual(len(beats), 1)
        self.assertAlmostEqual(beats[0]["cloud_w_offset"], 0.0, places=6)
        self.assertAlmostEqual(beats[0]["aurora_pulse_multiplier"], 1.0, places=6)


try:
    import jsonschema
except ImportError:  # optional offline dependency
    jsonschema = None


@unittest.skipIf(jsonschema is None, "jsonschema not installed")
class TestJsonSchemaContract(unittest.TestCase):
    def _schema(self):
        root = sky_core.repo_root()
        path = root / "specs" / "schemas" / "melodia_sky_theme.v1.schema.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_library_validates_against_schema(self):
        schema = self._schema()
        validator = jsonschema.Draft202012Validator(schema)
        lib = sky_core.load_library()
        for theme in lib["themes"]:
            validator.validate(theme)

    def test_new_v11_fields_validate(self):
        schema = self._schema()
        validator = jsonschema.Draft202012Validator(schema)
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "sakura_dream_dorian")
        self.assertIn("keying", theme["sky"]["sun"])
        self.assertIn("motion", theme["sky"])
        validator.validate(theme)  # keyed + motion theme passes

    def test_unknown_band_profile_rejected_by_schema(self):
        schema = self._schema()
        validator = jsonschema.Draft202012Validator(schema)
        lib = sky_core.load_library()
        theme = sky_core.get_theme(lib, "morning_meadow_ionian")
        theme["sky"]["gradient"]["banding_profile"] = "wiggly"
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(theme)


if __name__ == "__main__":
    unittest.main()
