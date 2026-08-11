"""Tests for EquipmentCatalog — equipment definitions, lookup, starter kit."""
from __future__ import annotations

import unittest

from gmm.game.equipment_catalog import (
    get_equipment,
    list_equipment,
    list_by_slot,
    starter_kit,
    catalog_summary,
    ALL_EQUIPMENT,
)


class TestEquipmentCatalog(unittest.TestCase):
    def test_catalog_has_items(self):
        self.assertGreater(len(ALL_EQUIPMENT), 0)

    def test_catalog_has_all_slots(self):
        slots = set(e.slot for e in ALL_EQUIPMENT)
        for expected in ("weapon", "armor", "shield", "helm", "boots"):
            self.assertIn(expected, slots)

    def test_get_equipment_by_id(self):
        item = get_equipment("iron_sword")
        self.assertIsNotNone(item)
        self.assertEqual(item.slot, "weapon")
        self.assertGreater(item.min_attack_bonus, 0)

    def test_get_equipment_unknown(self):
        item = get_equipment("nonexistent")
        self.assertIsNone(item)

    def test_list_equipment_all(self):
        items = list_equipment()
        self.assertEqual(len(items), len(ALL_EQUIPMENT))

    def test_list_equipment_by_slot(self):
        weapons = list_equipment("weapon")
        for w in weapons:
            self.assertEqual(w["slot"], "weapon")

    def test_list_by_slot_returns_dict(self):
        by_slot = list_by_slot()
        self.assertIn("weapon", by_slot)
        self.assertIn("armor", by_slot)

    def test_starter_kit_length(self):
        kit = starter_kit()
        self.assertEqual(len(kit), 5)

    def test_starter_kit_has_all_slots(self):
        kit = starter_kit()
        slots = [e.slot for e in kit if e]
        self.assertIn("weapon", slots)
        self.assertIn("armor", slots)
        self.assertIn("shield", slots)
        self.assertIn("helm", slots)
        self.assertIn("boots", slots)

    def test_catalog_summary(self):
        s = catalog_summary()
        self.assertEqual(s["total"], len(ALL_EQUIPMENT))
        self.assertIn("weapon", s["by_slot"])
        self.assertIn("items", s)

    def test_weapon_stats(self):
        sword = get_equipment("iron_sword")
        self.assertGreater(sword.min_attack_bonus, 0)
        self.assertGreater(sword.max_attack_bonus, sword.min_attack_bonus)

    def test_elemental_equipment(self):
        for item in ALL_EQUIPMENT:
            if item.element:
                self.assertIn(item.slot, ("weapon", "armor", "shield", "helm", "boots"))


if __name__ == "__main__":
    unittest.main()
