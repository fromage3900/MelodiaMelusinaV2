# Resonance Loom tests - pure-core coverage, no bpy required.
# Run from repo root:
#   python -m unittest discover -s Tools/BlenderAddons/melodia_resonance_loom/tests -v
#
# test_midi_grid is validated against the REAL project beatgrid
# (Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.mid) when the
# file is present, plus a deterministic synthetic fixture that always runs.

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADDON_ROOT = HERE.parent
BLENDER_ADDONS = ADDON_ROOT.parent
if str(BLENDER_ADDONS) not in sys.path:
    sys.path.insert(0, str(BLENDER_ADDONS))

from melodia_resonance_loom.loom_core import lanes  # noqa: E402
from melodia_resonance_loom.loom_core import naming  # noqa: E402
from melodia_resonance_loom.loom_core.midi_grid import (  # noqa: E402
    MidiParseError,
    accent_notes,
    load_beatgrid,
    parse_midi,
)
from melodia_resonance_loom.loom_core.sidecar import (  # noqa: E402
    build_sidecar,
    pattern_density,
    read_sidecar,
    validate_sidecar,
    write_sidecar,
)

REPO = BLENDER_ADDONS.parent.parent  # Tools/BlenderAddons -> Tools -> repo root
REAL_BEATGRID = REPO / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody_beatgrid.mid"


def _varlen(value: int) -> bytes:
    out = bytearray()
    out.append(value & 0x7F)
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def _synthetic_midi() -> bytes:
    """Format-0 SMF, 120 bpm, 4/4: 8 quarter notes, bar starts accented."""
    out = bytearray(b"MThd" + (6).to_bytes(4, "big")
                    + (0).to_bytes(2, "big") + (1).to_bytes(2, "big")
                    + (480).to_bytes(2, "big"))
    track = bytearray()
    track += b"\x00\xFF\x51\x03" + (500_000).to_bytes(3, "big")   # 120 bpm
    track += b"\x00\xFF\x58\x04" + bytes([4, 2, 24, 8])           # 4/4
    pitches = [60, 64, 67, 72, 60, 64, 67, 72]
    tick = 0
    for i, pitch in enumerate(pitches):
        vel = 100 if i % 4 == 0 else 64
        track.extend(_varlen(tick) + bytes([0x90, pitch, vel]))
        track.extend(_varlen(240) + bytes([0x80, pitch, 0]))
        tick = 240  # first event at tick 0, then quarter-note spacing
    track.extend(_varlen(240) + b"\xFF\x2F\x00")
    out += b"MTrk" + len(track).to_bytes(4, "big") + track
    return bytes(out)


class TestLanes(unittest.TestCase):
    def test_lane_vocabulary_matches_battle_ui(self) -> None:
        self.assertEqual(lanes.LANES, ("Q", "W", "O", "P"))

    def test_all_eight_authored_skill_ids_present(self) -> None:
        self.assertIn("cadence_strike", lanes.SKILL_IDS)
        self.assertIn("harmony_shield", lanes.SKILL_IDS)
        self.assertEqual(len(lanes.SKILL_IDS), 8)

    def test_expressive_guard_accepts_flourish_language(self) -> None:
        lanes.assert_expressive("flourish on accent beats")  # must not raise

    def test_expressive_guard_rejects_penalty_language(self) -> None:
        with self.assertRaises(ValueError):
            lanes.assert_expressive("no miss penalty")
        # 'dismiss' contains 'miss' but is NOT a whole-word use: allowed.
        lanes.assert_expressive("graceful dismissal")


class TestMidiGrid(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = parse_midi(_synthetic_midi())

    def test_synthetic_tempo_and_beats(self) -> None:
        self.assertAlmostEqual(self.grid.bpm, 120.0, places=2)
        self.assertEqual(self.grid.beats_per_bar, 4)
        self.assertAlmostEqual(self.grid.seconds_per_beat, 0.5, places=6)

    def test_notes_converted_to_seconds(self) -> None:
        self.assertTrue(self.grid.notes)
        self.assertAlmostEqual(self.grid.notes[0].start_sec, 0.0, places=6)

    def test_downbeats_every_four(self) -> None:
        idx = self.grid.downbeat_indices()
        self.assertEqual(idx[0], 0)
        self.assertIn(4, idx)

    def test_lane_of_pitch_is_deterministic_and_bounded(self) -> None:
        for pitch in range(0, 128):
            self.assertTrue(0 <= self.grid.lane_of_pitch(pitch) <= 3)

    def test_rejects_garbage(self) -> None:
        with self.assertRaises(MidiParseError):
            parse_midi(b"not a midi file at all")

    def test_real_project_beatgrid_parses(self) -> None:
        if not REAL_BEATGRID.exists():
            self.skipTest(f"{REAL_BEATGRID.name} not on this checkout")
        grid = load_beatgrid(REAL_BEATGRID)
        self.assertAlmostEqual(grid.bpm, 128.0, places=1)
        self.assertGreater(len(grid.notes), 0)
        self.assertGreater(grid.duration_sec, 0.0)

    def test_real_beatgrid_produces_accents(self) -> None:
        if not REAL_BEATGRID.exists():
            self.skipTest(f"{REAL_BEATGRID.name} not on this checkout")
        accents = accent_notes(load_beatgrid(REAL_BEATGRID))
        self.assertGreater(len(accents), 0)


class TestNaming(unittest.TestCase):
    def test_valid_cosmetic_ids(self) -> None:
        self.assertTrue(naming.is_valid_cosmetic_id("Cos_Dress_MelusinaElegance"))
        self.assertFalse(naming.is_valid_cosmetic_id("dress_melusina"))
        self.assertFalse(naming.is_valid_cosmetic_id(""))

    def test_short_name_collision_detection(self) -> None:
        collisions = naming.short_name_collisions(
            ["SK_Melusina_Dress", "sk_melusina_dress", "SK_LOOM_Accent"]
        )
        self.assertEqual(collisions, ["sk_melusina_dress"])

    def test_no_false_positive_on_unique_names(self) -> None:
        self.assertEqual(
            naming.short_name_collisions(["SK_LOOM_Accent", "SK_LOOM_Hit"]), []
        )

    def test_garment_names_require_valid_id(self) -> None:
        with self.assertRaises(ValueError):
            naming.garment_asset_names("not_cos")


class TestSidecar(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = parse_midi(_synthetic_midi())
        self.sidecar = build_sidecar(
            self.grid, "Cos_Dress_Test", "cadence_strike",
            midi_file="Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.mid",
        )

    def test_sidecar_fields_populated(self) -> None:
        self.assertEqual(self.sidecar.cosmetic_id, "Cos_Dress_Test")
        self.assertEqual(self.sidecar.skill_id, "cadence_strike")
        self.assertAlmostEqual(self.sidecar.bpm, 120.0, places=2)
        self.assertEqual(self.sidecar.tempo_band, "mid")

    def test_lane_hits_cover_all_four_lanes(self) -> None:
        self.assertEqual(set(self.sidecar.lane_hits), {"Q", "W", "O", "P"})
        self.assertEqual(sum(self.sidecar.lane_hits.values()), len(self.grid.notes))

    def test_unknown_skill_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_sidecar(self.grid, "Cos_Dress_Test", "not_a_skill_id")

    def test_pattern_density_bounded(self) -> None:
        d = pattern_density(self.grid)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_roundtrip_through_disk(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Cos_Dress_Test.melodia_rhythm.json"
            write_sidecar(self.sidecar, path)
            loaded = read_sidecar(path)
            self.assertEqual(loaded.cosmetic_id, "Cos_Dress_Test")
            self.assertEqual(loaded.lane_hits, self.sidecar.lane_hits)

    def test_validate_clean_sidecar_passes(self) -> None:
        from dataclasses import asdict
        self.assertEqual(validate_sidecar(asdict(self.sidecar)), [])

    def test_validate_rejects_unknown_skill(self) -> None:
        from dataclasses import asdict
        bad = asdict(self.sidecar)
        bad["skill_id"] = "nonsense"
        self.assertTrue(validate_sidecar(bad))

    def test_validate_rejects_wrong_lane_keys(self) -> None:
        from dataclasses import asdict
        bad = asdict(self.sidecar)
        bad["lane_hits"] = {"A": 1, "B": 2}
        self.assertTrue(validate_sidecar(bad))


class TestLaneStrategies(unittest.TestCase):
    """Phase 2: deterministic lane arrangement strategies (presentation only)."""

    def setUp(self) -> None:
        self.grid = parse_midi(_synthetic_midi())

    def test_unknown_strategy_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lanes.assign_lanes(self.grid, "vibes")

    def test_pitch_quartile_matches_lane_of_pitch(self) -> None:
        out = lanes.assign_lanes(self.grid, "pitch_quartile")
        expected = [self.grid.lane_of_pitch(n.pitch) for n in self.grid.notes]
        self.assertEqual(out, expected)

    def test_velocity_bands_follow_energy(self) -> None:
        out = lanes.assign_lanes(self.grid, "velocity_bands")
        for note, lane in zip(self.grid.notes, out):
            expected = 3 if note.velocity >= 112 else 2 if note.velocity >= 96 else 1 if note.velocity >= 80 else 0
            self.assertEqual(lane, expected)
        self.assertIn(2, out)  # bar-start notes are velocity 100 -> lane 2

    def test_bar_position_bounded(self) -> None:
        out = lanes.assign_lanes(self.grid, "bar_position")
        self.assertEqual(len(out), len(self.grid.notes))
        for lane in out:
            self.assertTrue(0 <= lane <= 3)

    def test_all_strategies_cover_every_note(self) -> None:
        for strategy in lanes.LANE_STRATEGIES:
            out = lanes.assign_lanes(self.grid, strategy)
            self.assertEqual(len(out), len(self.grid.notes), strategy)


class TestSidecarLaneStrategy(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = parse_midi(_synthetic_midi())
        self.sidecar = build_sidecar(
            self.grid, "Cos_Dress_Test", "cadence_strike",
            lane_strategy="velocity_bands",
        )

    def test_strategy_recorded_in_sidecar(self) -> None:
        self.assertEqual(self.sidecar.lane_strategy, "velocity_bands")

    def test_lane_hits_match_strategy(self) -> None:
        manual = lanes.assign_lanes(self.grid, "velocity_bands")
        counts: dict[str, int] = {"Q": 0, "W": 0, "O": 0, "P": 0}
        for lane in manual:
            counts[lanes.LANES[lane]] += 1
        self.assertEqual(self.sidecar.lane_hits, counts)

    def test_invalid_strategy_rejected_by_validator(self) -> None:
        from dataclasses import asdict
        bad = asdict(self.sidecar)
        bad["lane_strategy"] = "vibes"
        self.assertTrue(validate_sidecar(bad))

    def test_clean_strategy_passes_validator(self) -> None:
        from dataclasses import asdict
        self.assertEqual(validate_sidecar(asdict(self.sidecar)), [])


if __name__ == "__main__":
    unittest.main()


