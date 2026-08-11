"""Tests for MelodiaPlayerState — stats, XP/leveling, equipment, inventory, save/load."""
from __future__ import annotations

import os
import tempfile
import unittest

from gmm.game.player_state import MelodiaPlayerState, Equipment, InventoryItem, SaveSlot


class TestPlayerInitialState(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_default_level(self):
        self.assertEqual(self.ps.level, 1)

    def test_default_hp(self):
        self.assertEqual(self.ps.hp, 100.0)
        self.assertEqual(self.ps.max_hp, 100.0)

    def test_default_sp(self):
        self.assertEqual(self.ps.sp, 50.0)
        self.assertEqual(self.ps.max_sp, 100.0)

    def test_default_ult_gauge(self):
        self.assertEqual(self.ps.ult_gauge, 0.0)

    def test_default_gold(self):
        self.assertEqual(self.ps.gold, 0)

    def test_empty_inventory(self):
        self.assertEqual(len(self.ps.inventory), 0)

    def test_all_equipment_slots_none(self):
        for s in ("weapon", "armor", "shield", "helm", "boots"):
            self.assertIsNone(self.ps.equipment[s])

    def test_no_unlocked_skills(self):
        self.assertEqual(len(self.ps.unlocked_skills), 0)


class TestXPAndLeveling(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_xp_to_next_level_at_start(self):
        self.assertEqual(self.ps.xp_to_next_level(), 100)

    def test_add_xp_no_level_up(self):
        gained = self.ps.add_xp(50)
        self.assertEqual(gained, [])
        self.assertEqual(self.ps.xp, 50)
        self.assertEqual(self.ps.level, 1)

    def test_add_xp_exact_level_up(self):
        self.ps.add_xp(100)
        self.assertEqual(self.ps.level, 2)
        self.assertEqual(self.ps.xp, 0)

    def test_add_xp_excess_level_up(self):
        self.ps.add_xp(150)
        self.assertGreaterEqual(self.ps.level, 2)

    def test_add_xp_multiple_levels(self):
        gained = self.ps.add_xp(500)
        self.assertGreater(len(gained), 1)
        self.assertGreater(self.ps.level, 2)

    def test_level_up_increases_stats(self):
        old_max_hp = self.ps.max_hp
        self.ps.add_xp(100)
        self.assertGreater(self.ps.max_hp, old_max_hp)
        self.assertEqual(self.ps.hp, self.ps.max_hp)  # full heal on level up

    def test_xp_never_negative(self):
        gained = self.ps.add_xp(-50)
        self.assertEqual(self.ps.xp, 0)


class TestDamageAndHealing(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_take_damage_reduces_hp(self):
        actual = self.ps.take_damage(20)
        self.assertGreater(actual, 0)
        self.assertLess(self.ps.hp, 100.0)

    def test_take_damage_mitigated_by_defense(self):
        """Damage is reduced by defense * 0.5."""
        raw = 20
        expected = max(0, raw - self.ps.defense * 0.5)
        actual = self.ps.take_damage(raw)
        self.assertAlmostEqual(actual, expected)

    def test_damage_does_not_go_below_zero(self):
        self.ps.take_damage(9999)
        self.assertEqual(self.ps.hp, 0)

    def test_heal_restores_hp(self):
        self.ps.take_damage(30)
        self.ps.heal(20)
        self.assertAlmostEqual(self.ps.hp, 100 - (30 - self.ps.defense * 0.5) + 20)

    def test_heal_does_not_exceed_max(self):
        self.ps.heal(9999)
        self.assertEqual(self.ps.hp, self.ps.max_hp)

    def test_restore_mp(self):
        self.ps.mp = 50
        self.ps.restore_mp(30)
        self.assertAlmostEqual(self.ps.mp, 80)

    def test_full_restore(self):
        self.ps.take_damage(50)
        self.ps.full_restore()
        self.assertEqual(self.ps.hp, self.ps.max_hp)
        self.assertEqual(self.ps.mp, self.ps.max_mp)
        self.assertEqual(self.ps.sp, self.ps.max_sp)


class TestSPAndUlt(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_spend_sp_success(self):
        result = self.ps.spend_sp(20)
        self.assertTrue(result)
        self.assertAlmostEqual(self.ps.sp, 30.0)

    def test_spend_sp_insufficient(self):
        result = self.ps.spend_sp(999)
        self.assertFalse(result)
        self.assertAlmostEqual(self.ps.sp, 50.0)

    def test_add_ult(self):
        self.ps.add_ult(25)
        self.assertAlmostEqual(self.ps.ult_gauge, 25.0)

    def test_add_ult_caps_at_100(self):
        self.ps.add_ult(200)
        self.assertEqual(self.ps.ult_gauge, 100.0)

    def test_reset_ult(self):
        self.ps.add_ult(50)
        self.ps.reset_ult()
        self.assertEqual(self.ps.ult_gauge, 0.0)


class TestEquipment(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()
        self.sword = Equipment(
            item_id="iron_sword", display_name="Iron Sword", slot="weapon",
            min_attack_bonus=5, max_attack_bonus=8, speed_bonus=2,
        )
        self.shield = Equipment(
            item_id="iron_shield", display_name="Iron Shield", slot="shield",
            defense_bonus=10, hp_bonus=20,
        )

    def test_equip_item(self):
        self.ps.equip_item(self.sword)
        self.assertEqual(self.ps.equipment["weapon"].item_id, "iron_sword")

    def test_unequip_slot(self):
        self.ps.equip_item(self.sword)
        item = self.ps.unequip_slot("weapon")
        self.assertEqual(item.item_id, "iron_sword")
        self.assertIsNone(self.ps.equipment["weapon"])

    def test_unequip_empty_slot(self):
        item = self.ps.unequip_slot("boots")
        self.assertIsNone(item)

    def test_get_equipped_stats_base(self):
        stats = self.ps.get_equipped_stats()
        self.assertEqual(stats["min_attack"], self.ps.min_attack)
        self.assertEqual(stats["max_attack"], self.ps.max_attack)

    def test_get_equipped_stats_with_items(self):
        self.ps.equip_item(self.sword)
        self.ps.equip_item(self.shield)
        stats = self.ps.get_equipped_stats()
        self.assertAlmostEqual(stats["min_attack"], self.ps.min_attack + 5)
        self.assertAlmostEqual(stats["max_attack"], self.ps.max_attack + 8)
        self.assertAlmostEqual(stats["defense"], self.ps.defense + 10)
        self.assertEqual(stats["speed"], self.ps.speed + 2)
        self.assertAlmostEqual(stats["hp_bonus"], 20.0)


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()
        self.potion = InventoryItem(
            item_id="potion", display_name="Potion", item_type="usable",
            quantity=3, max_stack=99, heal_hp=30.0,
        )

    def test_add_item_new(self):
        self.ps.add_item(self.potion)
        self.assertIn("potion", self.ps.inventory)
        self.assertEqual(self.ps.inventory["potion"].quantity, 3)

    def test_add_item_stacks(self):
        self.ps.add_item(self.potion)
        self.ps.add_item(self.potion)
        self.assertEqual(self.ps.inventory["potion"].quantity, 6)

    def test_add_item_respects_max_stack(self):
        big = InventoryItem(item_id="potion", display_name="Potion", quantity=200, max_stack=99)
        self.ps.add_item(big)
        self.assertEqual(self.ps.inventory["potion"].quantity, 99)

    def test_remove_item_reduces(self):
        self.ps.add_item(self.potion)
        success = self.ps.remove_item("potion", 1)
        self.assertTrue(success)
        self.assertEqual(self.ps.inventory["potion"].quantity, 2)

    def test_remove_item_removes_if_zero(self):
        self.ps.add_item(self.potion)
        self.ps.remove_item("potion", 3)
        self.assertNotIn("potion", self.ps.inventory)

    def test_remove_item_insufficient(self):
        self.ps.add_item(self.potion)
        success = self.ps.remove_item("potion", 999)
        self.assertFalse(success)
        self.assertEqual(self.ps.inventory["potion"].quantity, 3)

    def test_has_item(self):
        self.ps.add_item(self.potion)
        self.assertTrue(self.ps.has_item("potion", 2))
        self.assertFalse(self.ps.has_item("potion", 999))

    def test_has_item_not_present(self):
        self.assertFalse(self.ps.has_item("nonexistent"))


class TestGold(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_add_gold(self):
        self.ps.add_gold(50)
        self.assertEqual(self.ps.gold, 50)

    def test_spend_gold_success(self):
        self.ps.add_gold(100)
        success = self.ps.spend_gold(30)
        self.assertTrue(success)
        self.assertEqual(self.ps.gold, 70)

    def test_spend_gold_insufficient(self):
        success = self.ps.spend_gold(999)
        self.assertFalse(success)
        self.assertEqual(self.ps.gold, 0)


class TestSkills(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_unlock_skill(self):
        self.ps.unlock_skill("TidalWave")
        self.assertIn("TidalWave", self.ps.unlocked_skills)

    def test_unlock_skill_idempotent(self):
        self.ps.unlock_skill("TidalWave")
        self.ps.unlock_skill("TidalWave")
        self.assertEqual(len(self.ps.unlocked_skills), 1)

    def test_has_skill(self):
        self.assertFalse(self.ps.has_skill("TidalWave"))
        self.ps.unlock_skill("TidalWave")
        self.assertTrue(self.ps.has_skill("TidalWave"))


class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()
        self.tmp = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_save_to_file_creates_file(self):
        path = self.ps.save_to_file(self.tmp)
        self.assertTrue(os.path.exists(path))

    def test_load_from_file_restores_state(self):
        self.ps.add_xp(100)
        self.ps.add_gold(50)
        self.ps.equip_item(Equipment(item_id="test_sword", display_name="TS", slot="weapon"))
        self.ps.add_item(InventoryItem(item_id="potion", display_name="Potion", quantity=3))
        self.ps.unlock_skill("TidalWave")
        self.ps.take_damage(20)
        path = self.ps.save_to_file(self.tmp)

        ps2 = MelodiaPlayerState()
        ps2.load_from_file(path)
        self.assertEqual(ps2.level, self.ps.level)
        self.assertEqual(ps2.gold, self.ps.gold)
        self.assertIn("TidalWave", ps2.unlocked_skills)
        self.assertEqual(ps2.hp, self.ps.hp)

    def test_load_from_nonexistent_file(self):
        result = self.ps.load_from_file("/nonexistent/path.json")
        self.assertFalse(result)

    def test_to_save_data_includes_play_time(self):
        save = self.ps.to_save_data()
        self.assertEqual(save.level, 1)
        self.assertGreater(save.play_time_seconds, 0)

    def test_round_trip_equipment_save_format(self):
        self.ps.equip_item(Equipment(item_id="sword", display_name="Sword", slot="weapon"))
        save = self.ps.to_save_data()
        self.assertEqual(save.equipment["weapon"], "sword")
        path = self.ps.save_to_file(self.tmp)
        ps2 = MelodiaPlayerState()
        ps2.load_from_file(path)
        self.assertEqual(ps2.xp, self.ps.xp)
        self.assertEqual(ps2.level, self.ps.level)


class TestDescribe(unittest.TestCase):
    def setUp(self):
        self.ps = MelodiaPlayerState()

    def test_describe_returns_dict(self):
        d = self.ps.describe()
        self.assertIn("level", d)
        self.assertIn("hp", d)
        self.assertIn("xp_to_next", d)
        self.assertEqual(d["level"], 1)


if __name__ == "__main__":
    unittest.main()
