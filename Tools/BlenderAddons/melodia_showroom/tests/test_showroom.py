# Offline tests for Melodia Showroom.
# Verifies preset mapping and pipeline wiring without Blender.

import importlib.util
import os
import sys
import unittest


def _load(name, relpath):
    path = os.path.join(os.path.dirname(__file__), relpath)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


showroom_ops = _load("melodia_showroom.operators",
                     os.path.join("..", "operators.py"))
showroom_props = _load("melodia_showroom.properties",
                       os.path.join("..", "properties.py"))


class TestPresetMapping(unittest.TestCase):
    def test_all_showroom_presets_resolve(self):
        expected = {
            "verdant_default": ("resonant_default", "verdant"),
            "cathedral_wide_crystalline": ("cathedral_wide", "crystalline"),
            "toccata_spires_toccata": ("toccata_spires", "toccata_surface"),
            "waltz_garden_waltz": ("waltz_corridors", "waltz_garden"),
            "ballad_plaza_ballad": ("ballad_broadstage", "ballad_plaza"),
            "fugue_maze_fugue": ("fugue_labyrinth", "fugue_maze"),
            "nocturne_reflection_nocturne": ("nocturne_ribbon", "nocturne_reflection"),
            "lullaby_cave_lullaby": ("lullaby_undergrowth", "lullaby_cave"),
            "tarantella_bounce_saltarello": ("tarantella_bounce", "saltarello_ledges"),
            "canon_echo_pavane": ("canon_echo", "pavane_grotto"),
            "gavotte_hedges_aria": ("gavotte_hedges", "aria_mist"),
            "rhapsody_fold_chaconne": ("rhapsody_fold", "chaconne_weave"),
            "berceuse_overhang_madrigal": ("berceuse_overhang", "madrigal_canopy"),
            "ritornello_rings_madrigal": ("ritornello_rings", "madrigal_canopy"),
        }
        self.assertEqual(showroom_ops._preset_parts("verdant_default"), expected["verdant_default"])
        for pid, parts in expected.items():
            self.assertEqual(showroom_ops._preset_parts(pid), parts, pid)

    def test_unknown_preset_falls_back(self):
        self.assertEqual(showroom_ops._preset_parts("unknown"), ("resonant_default", "verdant"))

    def test_mapping_covers_operator_presets(self):
        enum_ids = [
            "verdant_default",
            "cathedral_wide_crystalline",
            "toccata_spires_toccata",
            "waltz_garden_waltz",
            "ballad_plaza_ballad",
            "fugue_maze_fugue",
            "nocturne_reflection_nocturne",
            "lullaby_cave_lullaby",
        ]
        for showroom_id in enum_ids:
            terrain_preset, dressing_style = showroom_ops._preset_parts(showroom_id)
            self.assertTrue(terrain_preset)
            self.assertTrue(dressing_style)


class TestPipelinePaths(unittest.TestCase):
    def test_studio_root_resolves(self):
        root = showroom_ops.mb.repo_root()
        self.assertTrue(os.path.isdir(root))
        self.assertTrue(os.path.isdir(os.path.join(root, "Content", "MelodiaIntegration", "MIDI")))

    def test_midi_bridge_loads(self):
        mb = showroom_ops.mb
        self.assertTrue(callable(getattr(mb, "generate_world", None)))
        self.assertTrue(callable(getattr(mb, "dress_terrain", None)))


if __name__ == "__main__":
    unittest.main()
