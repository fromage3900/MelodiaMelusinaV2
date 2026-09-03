"""Offline tests for terrain dressing, magic planning, and walkable mapping.

No bpy. Guards the defects found on 2026-08-24:
  - v3 mapping produced a 5.8:1 ribbon (unwalkable)
  - surface_height_at used round() instead of floor(), so points at *.5
    resolved to a neighbouring column
  - dressing jitter could push props over empty cells, floating them
  - chime_pillar placed zero props because no cell was ever tagged "ridge"

Run:
  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v
"""

import os
import sys
import math
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ADDON = os.path.normpath(os.path.join(_HERE, ".."))
if _ADDON not in sys.path:
    sys.path.insert(0, _ADDON)

import walkable_world as ww      # noqa: E402
import terrain_dressing as td    # noqa: E402


def _field(preset_id="walkable_highlands"):
    midi = os.path.join(ww._repo_root(), "Content", "MelodiaIntegration",
                        "MIDI", "128BPMarpeggiomelody.mid")
    mv = ww.load_voxel_module()
    tracks, tpb = mv.parse_midi(midi)
    p = ww.WALKABLE_PRESETS[preset_id]
    notes = list(tracks[0])
    bg = midi.replace(".mid", "_beatgrid.mid")
    if os.path.exists(bg):
        b, btpb = mv.parse_midi(bg)
        if b and btpb:
            s = float(tpb) / float(btpb)
            notes.extend((int(n[0] * s), n[1] + 36, n[2]) for n in b[0])
            notes.sort()
    f, _ = ww.build_heightfield(notes, p["cells_per_beat"], p["height_scale"],
                               p["plateau_radius"], tpb)
    return ww.limit_slope(ww.fill_gaps(f), p["max_slope"], p["smooth_passes"])


class TestWalkableMapping(unittest.TestCase):
    def test_footprint_is_not_a_ribbon(self):
        """v3 was 64x11 (aspect 5.8). v4 must be roughly square."""
        for pid in ww.WALKABLE_PRESETS:
            f = _field(pid)
            m = ww.walkability(f, ww.WALKABLE_PRESETS[pid]["max_slope"])
            self.assertLess(m["aspect_ratio"], 1.6,
                            "%s aspect %.2f" % (pid, m["aspect_ratio"]))

    def test_terrain_is_traversable(self):
        for pid in ww.WALKABLE_PRESETS:
            f = _field(pid)
            slope = ww.WALKABLE_PRESETS[pid]["max_slope"]
            m = ww.walkability(f, slope)
            self.assertGreaterEqual(m["walkable_fraction"], 0.85, pid)

    def test_single_connected_region(self):
        """Whole surface reachable on foot -- no isolated islands."""
        for pid in ww.WALKABLE_PRESETS:
            f = _field(pid)
            slope = ww.WALKABLE_PRESETS[pid]["max_slope"]
            biggest = ww.largest_connected_region(f, slope)
            self.assertEqual(biggest, len(f), pid)

    def test_has_real_elevation(self):
        """v3 gave 3 units of relief; v4 must do better."""
        f = _field("walkable_highlands")
        m = ww.walkability(f)
        self.assertGreaterEqual(m["height_span"], 5)

    def test_serpentine_keeps_time_adjacent(self):
        """Consecutive beats must be strict 4-neighbours across the fold.

        The original assertion allowed a Manhattan step of 2, which would have
        passed even for a broken fold that jumped diagonally. Measured worst
        step is 1 for every grid width, so assert exactly that.
        """
        for w in (2, 3, 4, 8, 15, 16):
            for i in range(w * 5 - 1):
                x0, y0 = ww.serpentine_xy(i, w)
                x1, y1 = ww.serpentine_xy(i + 1, w)
                step = abs(x0 - x1) + abs(y0 - y1)
                self.assertEqual(
                    step, 1,
                    "grid_w=%d index %d->%d jumped %d (%s -> %s)" % (
                        w, i, i + 1, step, (x0, y0), (x1, y1)))

    def test_serpentine_is_a_bijection(self):
        """Every index must map to a unique cell -- no two beats stacking."""
        for w in (3, 8, 15):
            seen = set()
            for i in range(w * 4):
                cell = ww.serpentine_xy(i, w)
                self.assertNotIn(cell, seen, "duplicate cell at index %d" % i)
                seen.add(cell)

    def test_serpentine_rows_alternate_direction(self):
        """Row 0 runs +x, row 1 runs -x. That reversal IS the fold."""
        w = 6
        row0 = [ww.serpentine_xy(i, w)[0] for i in range(w)]
        row1 = [ww.serpentine_xy(i + w, w)[0] for i in range(w)]
        self.assertEqual(row0, sorted(row0))
        self.assertEqual(row1, sorted(row1, reverse=True))

    def test_serpentine_stays_in_bounds(self):
        for w in (1, 2, 7, 16):
            for i in range(w * 6):
                x, y = ww.serpentine_xy(i, w)
                self.assertGreaterEqual(x, 0)
                self.assertLess(x, w)
                self.assertEqual(y, i // w)


class TestSpiralFold(unittest.TestCase):
    def test_spiral_is_strict_4_neighbour(self):
        for w in (3, 4, 8, 15):
            for i in range(w * w - 1):
                a = ww.spiral_xy(i, w)
                b = ww.spiral_xy(i + 1, w)
                step = abs(a[0] - b[0]) + abs(a[1] - b[1])
                self.assertEqual(step, 1,
                                 "w=%d %d->%d step %d" % (w, i, i + 1, step))

    def test_spiral_is_bijection(self):
        for w in (3, 4, 8, 15):
            cells = {ww.spiral_xy(i, w) for i in range(w * w)}
            self.assertEqual(len(cells), w * w)

    def test_spiral_starts_at_origin_and_ends_inward(self):
        w = 9
        self.assertEqual(ww.spiral_xy(0, w), (0, 0))
        last = ww.spiral_xy(w * w - 1, w)
        # Final cell must be interior, not on the rim.
        self.assertGreater(last[0], 0)
        self.assertLess(last[0], w - 1)
        self.assertGreater(last[1], 0)
        self.assertLess(last[1], w - 1)

    def test_spiral_stays_in_bounds(self):
        for w in (1, 2, 5, 16):
            for i in range(w * w):
                x, y = ww.spiral_xy(i, w)
                self.assertTrue(0 <= x < w and 0 <= y < w)

    def test_spiral_degenerate_width_safe(self):
        self.assertEqual(ww.spiral_xy(0, 0), (0, 0))
        self.assertEqual(ww.spiral_xy(5, 1), (0, 0))

    def test_fold_xy_dispatch(self):
        self.assertEqual(ww.fold_xy(5, 8, "serpentine"),
                         ww.serpentine_xy(5, 8))
        self.assertEqual(ww.fold_xy(5, 8, "spiral"), ww.spiral_xy(5, 8))
        # Unknown mode must fall back, not crash.
        self.assertEqual(ww.fold_xy(5, 8, "nonsense"),
                         ww.serpentine_xy(5, 8))

    def test_spiral_preset_produces_walkable_terrain(self):
        f = _field("walkable_spiral_arena")
        slope = ww.WALKABLE_PRESETS["walkable_spiral_arena"]["max_slope"]
        m = ww.walkability(f, slope)
        self.assertGreaterEqual(m["walkable_fraction"], 0.85)
        self.assertEqual(ww.largest_connected_region(f, slope), len(f))
        self.assertLess(m["aspect_ratio"], 1.6)


class TestSurfaceHeight(unittest.TestCase):
    def test_floor_not_round(self):
        """Regression: round() sent *.5 coords to the wrong column."""
        field = {(0, 0): (3, 90), (1, 0): (7, 90)}
        # 0.5 lies inside cell 0, so it must report 3 -- round() gave 7.
        self.assertEqual(td.surface_height_at(field, 0.5, 0.2), 3)
        self.assertEqual(td.surface_height_at(field, 1.5, 0.2), 7)

    def test_exact_cell_lookup(self):
        field = {(4, 6): (5, 80)}
        self.assertEqual(td.surface_height_at(field, 4, 6), 5)

    def test_offgrid_falls_back_to_nearest(self):
        field = {(0, 0): (9, 70)}
        self.assertEqual(td.surface_height_at(field, 40, 40), 9)

    def test_empty_field_safe(self):
        self.assertEqual(td.surface_height_at({}, 1, 1), 0)


class TestClassify(unittest.TestCase):
    def test_all_tags_present(self):
        """chime_pillar needs 'ridge'; it was previously never produced."""
        tags = td.classify_cells(_field())
        kinds = {v["tag"] for v in tags.values()}
        for expected in ("peak", "ridge", "valley", "path", "slope"):
            self.assertIn(expected, kinds)

    def test_every_cell_tagged(self):
        f = _field()
        self.assertEqual(len(td.classify_cells(f)), len(f))


class TestDressing(unittest.TestCase):
    def setUp(self):
        self.field = _field()

    def test_props_sit_on_ground(self):
        """Every prop's Z must equal the height of the column it stands on."""
        for style in td.DRESSING_STYLES:
            props, _ = td.plan_dressing(self.field, style)
            for spec in props:
                x, y, z = spec["location"]
                ground = td.surface_height_at(self.field, x, y)
                self.assertAlmostEqual(
                    z, ground, places=6,
                    msg="%s prop %s floating at %s over %s" % (
                        style, spec["kind"], z, ground))

    def test_props_land_on_real_cells(self):
        """Jitter must not push a prop over an empty cell."""
        props, _ = td.plan_dressing(self.field, "full_bloom")
        for spec in props:
            x, y, _z = spec["location"]
            key = (int(math.floor(x)), int(math.floor(y)))
            self.assertIn(key, self.field, spec["kind"])

    def test_all_kinds_place_at_least_one(self):
        props, stats = td.plan_dressing(self.field, "full_bloom")
        for kind in td.DRESSING_KINDS:
            self.assertGreater(stats["by_kind"].get(kind, 0), 0, kind)

    def test_bare_style_is_empty(self):
        props, stats = td.plan_dressing(self.field, "bare")
        self.assertEqual(props, [])
        self.assertEqual(stats["placed"], 0)

    def test_deterministic_for_seed(self):
        a, _ = td.plan_dressing(self.field, "full_bloom", seed=11)
        b, _ = td.plan_dressing(self.field, "full_bloom", seed=11)
        self.assertEqual([p["location"] for p in a],
                         [p["location"] for p in b])

    def test_budget_respected(self):
        props, _ = td.plan_dressing(self.field, "full_bloom", budget=12)
        self.assertLessEqual(len(props), 12)


class TestMagic(unittest.TestCase):
    def setUp(self):
        self.field = _field()

    def test_styles_declare_known_systems(self):
        for style, spec in td.DRESSING_STYLES.items():
            for sys_id in spec["magic"]:
                self.assertIn(sys_id, td.MAGIC_SYSTEMS, style)

    def test_plan_returns_all_requested(self):
        for style, spec in td.DRESSING_STYLES.items():
            magic, stats = td.plan_magic(self.field, style)
            self.assertEqual(stats["systems"], len(spec["magic"]), style)

    def test_water_level_inside_terrain_range(self):
        magic, _ = td.plan_magic(self.field, "cathedral")
        water = [m for m in magic if m["kind"] == "water"]
        self.assertTrue(water)
        heights = [v[0] for v in self.field.values()]
        self.assertGreaterEqual(water[0]["level"], min(heights))
        self.assertLessEqual(water[0]["level"], max(heights))

    def test_rings_sit_on_local_ground(self):
        magic, _ = td.plan_magic(self.field, "crystalline")
        rings = [m for m in magic if m["kind"] == "rings"]
        self.assertTrue(rings)
        cx, cy = rings[0]["centre"]
        self.assertEqual(rings[0]["base_height"],
                         td.surface_height_at(self.field, cx, cy))

    def test_empty_field_safe(self):
        magic, stats = td.plan_magic({}, "full_bloom")
        self.assertEqual(magic, [])
        self.assertEqual(stats["systems"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
