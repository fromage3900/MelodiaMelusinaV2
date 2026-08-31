"""Offline tests for the Melodia Studio MIDI bridge.

No bpy, no Blender, no Unreal. Guards the defects found on 2026-08-24:
  - STUDIO_ROOT resolved to Tools/Tools/MelodiaProceduralStudio
  - midi_voxel_v3 was imported without its directory on sys.path
  - preset height divisors were silently ignored by generate()

Run:
  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v
"""

import os
import sys
import json
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ADDON = os.path.normpath(os.path.join(_HERE, ".."))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

import midi_bridge  # noqa: E402


class TestPaths(unittest.TestCase):
    def test_repo_root_is_bs_godfile(self):
        self.assertEqual(os.path.basename(midi_bridge.repo_root()),
                         "BS_GodFile")

    def test_studio_root_not_doubled(self):
        """Regression: was Tools/Tools/MelodiaProceduralStudio."""
        root = midi_bridge.studio_root().replace("\\", "/")
        self.assertNotIn("Tools/Tools", root)
        self.assertTrue(root.endswith("Tools/MelodiaProceduralStudio"))

    def test_studio_root_exists(self):
        self.assertTrue(os.path.isdir(midi_bridge.studio_root()))

    def test_voxel_tool_dir_exists(self):
        self.assertTrue(os.path.isdir(midi_bridge.voxel_tool_dir()))

    def test_midi_content_dir_exists(self):
        self.assertTrue(os.path.isdir(midi_bridge.midi_content_dir()))


class TestVoxelImport(unittest.TestCase):
    def test_module_imports(self):
        """Regression: bare `from midi_voxel_v3 import ...` always failed."""
        mv = midi_bridge.load_voxel_module()
        for fn in ("parse_midi", "generate", "export_obj"):
            self.assertTrue(callable(getattr(mv, fn, None)), fn)

    def test_block_tables_present(self):
        mv = midi_bridge.load_voxel_module()
        self.assertIn(mv.BLOCK_STONE, mv.BLOCK_COLORS)
        self.assertIn(mv.BLOCK_GOLD, mv.BLOCK_NAMES)

    def test_vel2block_thresholds(self):
        mv = midi_bridge.load_voxel_module()
        self.assertEqual(mv.vel2block(10), mv.BLOCK_STONE)
        self.assertEqual(mv.vel2block(50), mv.BLOCK_WOOD)
        self.assertEqual(mv.vel2block(70), mv.BLOCK_CRYSTAL)
        self.assertEqual(mv.vel2block(120), mv.BLOCK_GOLD)


class TestPresets(unittest.TestCase):
    def test_defaults_have_required_keys(self):
        required = {"label", "chunk_beats", "use_beatgrid"}
        for name, preset in midi_bridge.DEFAULT_PRESETS.items():
            self.assertTrue(required.issubset(preset.keys()),
                            "%s missing %s" % (name, required - set(preset)))
        self.assertGreaterEqual(len(midi_bridge.DEFAULT_PRESETS), 8)

    def test_preset_items_shape(self):
        for item in midi_bridge.preset_items():
            self.assertEqual(len(item), 3)

    def test_write_and_reload_roundtrip(self):
        path = midi_bridge.write_presets()
        self.addCleanup(lambda: None)
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], "melodia.midi_presets.v1")
        self.assertIn("resonant_default", data["presets"])

    def test_dress_terrain_returns_status_string(self):
        if not os.path.exists(os.path.join(midi_bridge.midi_content_dir(), "128BPMarpeggiomelody.mid")):
            self.skipTest("missing project MIDI")
        status = midi_bridge.dress_terrain(None, "", style_id="verdant")
        self.assertIsInstance(status, str)
        self.assertIn("verdant", status.lower())


class TestDiscovery(unittest.TestCase):
    def test_finds_project_midi(self):
        found = midi_bridge.discover_midi()
        names = {os.path.basename(p) for p in found}
        self.assertIn("128BPMarpeggiomelody.mid", names)

    def test_beatgrid_pairing(self):
        melody = os.path.join(midi_bridge.midi_content_dir(),
                              "128BPMarpeggiomelody.mid")
        bg = midi_bridge.beatgrid_for(melody)
        self.assertIsNotNone(bg)
        self.assertTrue(bg.endswith("_beatgrid.mid"))

    def test_no_duplicates(self):
        found = midi_bridge.discover_midi()
        keys = [os.path.normcase(p) for p in found]
        self.assertEqual(len(keys), len(set(keys)))


class TestGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.midi = os.path.join(midi_bridge.midi_content_dir(),
                                "128BPMarpeggiomelody.mid")
        cls.tmp = tempfile.mkdtemp(prefix="melodia_test_")

    def _gen(self, preset_id):
        out = os.path.join(self.tmp, preset_id + ".obj")
        return midi_bridge.generate_world(self.midi, preset_id=preset_id,
                                          out_obj=out)

    def test_default_matches_known_baseline(self):
        """Locks the proven 192-note -> 346-voxel result."""
        r = self._gen("resonant_default")
        self.assertTrue(r["ok"])
        self.assertEqual(r["melody_notes"], 192)
        self.assertEqual(r["voxels"], 346)
        self.assertEqual(r["verts"], 2768)
        self.assertEqual(r["faces"], 1540)
        self.assertTrue(r["used_beatgrid"])

    def test_obj_file_written_with_colors(self):
        r = self._gen("resonant_default")
        self.assertTrue(os.path.exists(r["obj"]))
        with open(r["obj"]) as f:
            body = f.read()
        vline = next(l for l in body.splitlines() if l.startswith("v "))
        # v x y z r g b  -> 7 tokens; colour is what drives AuraColor
        self.assertEqual(len(vline.split()), 7)

    def test_surface_only_drops_cave_layer(self):
        r = self._gen("surface_only")
        self.assertFalse(r["used_beatgrid"])
        self.assertNotIn("void", r["blocks"])

    def test_chunk_beats_changes_topology(self):
        wide = self._gen("cathedral_wide")
        dense = self._gen("dense_spire")
        self.assertNotEqual(wide["voxels"], dense["voxels"])

    def test_all_presets_generate(self):
        for pid in midi_bridge.load_presets():
            r = self._gen(pid)
            self.assertTrue(r["ok"], pid)
            self.assertGreater(r["verts"], 0, pid)

    def test_height_divisors_are_honoured(self):
        """D7 FIX VERIFIED (2026-08-28): divisors are now threaded into
        generate_world via surface_div/cave_div kwargs.
        """
        default = self._gen("resonant_default")
        abyss = self._gen("abyss_caves")
        self.assertNotEqual(default["voxels"], abyss["voxels"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
