"""Tests for SaveManager — save/load persistence layer."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from gmm.game.save_manager import SaveManager
from gmm.game.player_state import MelodiaPlayerState, SaveSlot


class TestSaveManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sm = SaveManager(save_dir=self.tmp)
        self.player = MelodiaPlayerState()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_creates_file(self):
        path = self.sm.save(self.player)
        self.assertTrue(os.path.exists(path))

    def test_save_returns_path(self):
        path = self.sm.save(self.player)
        self.assertTrue(path.endswith(".json"))
        self.assertIn(self.tmp, path)

    def test_load_returns_true_on_existing_save(self):
        self.sm.save(self.player)
        p2 = MelodiaPlayerState()
        result = self.sm.load(p2)
        self.assertTrue(result)

    def test_load_returns_false_on_no_save(self):
        p2 = MelodiaPlayerState()
        result = self.sm.load(p2)
        self.assertFalse(result)

    def test_load_restores_level(self):
        self.player.add_xp(999999)
        self.sm.save(self.player)
        p2 = MelodiaPlayerState()
        self.sm.load(p2)
        self.assertGreaterEqual(p2.level, 1)

    def test_load_restores_gold(self):
        self.player.gold = 999
        self.sm.save(self.player)
        p2 = MelodiaPlayerState()
        self.sm.load(p2)
        self.assertEqual(p2.gold, 999)

    def test_load_restores_hp(self):
        self.player.take_damage(30)
        self.sm.save(self.player)
        p2 = MelodiaPlayerState()
        self.sm.load(p2)
        expected = self.player.hp
        self.assertEqual(p2.hp, expected)

    def test_latest_save_path_after_save(self):
        self.assertIsNone(self.sm.latest_save_path())
        self.sm.save(self.player)
        self.assertIsNotNone(self.sm.latest_save_path())

    def test_list_slots_empty(self):
        self.assertEqual(self.sm.list_slots(), [])

    def test_list_slots_after_save(self):
        self.sm.save(self.player)
        slots = self.sm.list_slots()
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["slot"], self.sm.slot_name)

    def test_list_slots_multiple(self):
        self.sm.save(self.player, slot="slot_a.json")
        self.sm.save(self.player, slot="slot_b.json")
        slots = self.sm.list_slots()
        self.assertEqual(len(slots), 2)

    def test_list_slots_ignores_non_json(self):
        with open(os.path.join(self.tmp, "notes.txt"), "w") as f:
            f.write("hello")
        self.sm.save(self.player)
        self.assertEqual(len(self.sm.list_slots()), 1)

    def test_delete_slot(self):
        path = self.sm.save(self.player)
        self.assertTrue(os.path.exists(path))
        result = self.sm.delete_slot(self.sm.slot_name)
        self.assertTrue(result)
        self.assertFalse(os.path.exists(path))

    def test_delete_nonexistent_slot(self):
        result = self.sm.delete_slot("nonexistent.json")
        self.assertFalse(result)

    def test_describe_after_save(self):
        self.sm.save(self.player)
        desc = self.sm.describe()
        self.assertEqual(desc["save_dir"], self.tmp)
        self.assertTrue(desc["exists"])
        self.assertEqual(desc["slots"], 1)

    def test_save_custom_slot_name(self):
        path = self.sm.save(self.player, slot="my_save.json")
        self.assertTrue(path.endswith("my_save.json"))
        p2 = MelodiaPlayerState()
        self.sm.load(p2)
        self.assertFalse(self.sm.load(p2, slot="wrong.json"))

    def test_roundtrip_preserves_inventory(self):
        self.player.gold = 777
        self.player.add_xp(5000)
        self.sm.save(self.player)
        p2 = MelodiaPlayerState()
        self.sm.load(p2)
        self.assertEqual(p2.gold, 777)

    def test_corrupt_file_handling(self):
        with open(os.path.join(self.tmp, self.sm.slot_name), "w") as f:
            f.write("not json")
        p2 = MelodiaPlayerState()
        result = self.sm.load(p2)
        self.assertFalse(result)

    def test_list_slots_marks_corrupt(self):
        with open(os.path.join(self.tmp, "corrupt.json"), "w") as f:
            f.write("{bad")
        slots = self.sm.list_slots()
        self.assertEqual(len(slots), 1)
        self.assertIn("error", slots[0])
        self.assertEqual(slots[0]["error"], "corrupt")

    def test_save_creates_dir_if_missing(self):
        new_dir = os.path.join(self.tmp, "nested", "saves")
        sm = SaveManager(save_dir=new_dir)
        path = sm.save(self.player)
        self.assertTrue(os.path.exists(path))

    def test_multiple_saves_independent(self):
        sm1 = SaveManager(save_dir=self.tmp)
        p1 = MelodiaPlayerState()
        p1.gold = 100
        sm1.save(p1, slot="p1.json")
        sm2 = SaveManager(save_dir=self.tmp)
        p2 = MelodiaPlayerState()
        sm2.load(p2, slot="p1.json")
        self.assertEqual(p2.gold, 100)

    def test_save_contains_metadata(self):
        path = self.sm.save(self.player)
        with open(path) as f:
            data = json.load(f)
        self.assertIn("save_date", data)
        self.assertIn("play_time_seconds", data)
        self.assertIn("level", data)

    def test_save_slot_inherits_fields(self):
        slot = SaveSlot(level=42, player_hp=200.0, xp=50000,
                        gold=999, completed_encounters=[], inventory=[],
                        equipment={}, unlocked_skills=[])
        self.assertEqual(slot.level, 42)
        self.assertEqual(slot.gold, 999)
        self.assertEqual(slot.player_hp, 200.0)
