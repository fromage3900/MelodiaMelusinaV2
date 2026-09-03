"""Tests for MelodiaDataRegistry — enemy stats, skill data, player unit stats."""
from __future__ import annotations

import unittest

from gmm.game.data_registry import (
    MelodiaDataRegistry,
    EnemyStats,
    SkillData,
    PlayerUnitStats,
)


class TestEnemyStats(unittest.TestCase):
    def test_create_enemy(self):
        e = EnemyStats(
            enemy_id="TestGolem",
            display_name="Test Golem",
            element="Stone",
            bpm=100,
            max_hp=200,
            toughness=50,
            min_attack=12,
            max_attack=18,
            defense=10,
            speed=40,
            xp_reward=80,
            gold_reward=40,
        )
        self.assertEqual(e.enemy_id, "TestGolem")
        self.assertEqual(e.max_hp, 200)

    def test_enemy_to_dict(self):
        e = EnemyStats(enemy_id="T", display_name="Test", element="Neutral", bpm=120,
                       max_hp=100, toughness=20, min_attack=5, max_attack=10,
                       defense=5, speed=50, xp_reward=30, gold_reward=15)
        d = e.to_dict()
        self.assertEqual(d["enemy_id"], "T")
        self.assertEqual(d["max_hp"], 100)
        self.assertEqual(d["xp_reward"], 30)


class TestSkillData(unittest.TestCase):
    def test_create_skill(self):
        s = SkillData(
            skill_id="FireBlast",
            display_name="Fire Blast",
            element="Forte",
            instrument="keyboard",
            base_damage=45,
            sp_cost=15,
            mechanic_level=5,
        )
        self.assertEqual(s.skill_id, "FireBlast")
        self.assertEqual(s.base_damage, 45)

    def test_skill_to_dict(self):
        s = SkillData(skill_id="FB", display_name="Fire Blast", element="Forte",
                      instrument="keyboard", base_damage=45, sp_cost=15,
                      mechanic_level=5)
        d = s.to_dict()
        self.assertEqual(d["skill_id"], "FB")
        self.assertEqual(d["base_damage"], 45)


class TestPlayerUnitStats(unittest.TestCase):
    def test_create_player_stats(self):
        ps = PlayerUnitStats(
            unit_id="Melodia",
            display_name="Melodia",
            max_hp=150,
            max_mp=120,
            min_attack=10,
            max_attack=15,
            defense=10,
            speed=90,
        )
        self.assertEqual(ps.unit_id, "Melodia")
        self.assertEqual(ps.max_hp, 150)


class TestDataRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = MelodiaDataRegistry()

    def test_registry_has_demo_enemies(self):
        enemies = self.reg.list_enemies()
        self.assertGreater(len(enemies), 0)

    def test_get_enemy_by_id(self):
        e = self.reg.get_enemy("CrystalShard")
        self.assertIsNotNone(e)
        self.assertEqual(e.display_name, "Crystal Shard")

    def test_get_unknown_enemy(self):
        e = self.reg.get_enemy("Nonexistent")
        self.assertIsNone(e)

    def test_get_skill_by_id(self):
        s = self.reg.get_skill("TidalWave")
        self.assertIsNotNone(s)

    def test_get_unknown_skill(self):
        s = self.reg.get_skill("Nonexistent")
        self.assertIsNone(s)

    def test_list_enemies_returns_dicts(self):
        enemies = self.reg.list_enemies()
        self.assertIn("enemy_id", enemies[0])
        self.assertIn("display_name", enemies[0])

    def test_list_skills(self):
        skills = self.reg.list_skills()
        self.assertGreater(len(skills), 0)

    def test_get_player_unit(self):
        pu = self.reg.get_player_unit("melodist")
        self.assertIsNotNone(pu)
        self.assertEqual(pu.display_name, "Melodist")

    def test_get_player_unit_unknown(self):
        pu = self.reg.get_player_unit("nonexistent")
        self.assertIsNone(pu)

    def test_summary(self):
        s = self.reg.summary()
        self.assertGreater(s["enemy_count"], 0)
        self.assertGreater(s["skill_count"], 0)
        self.assertIn("enemies", s)

    def test_export_json(self):
        text = self.reg.export_json()
        self.assertIn("CrystalShard", text)
        self.assertIn("enemies", text)
        self.assertIn("skills", text)


if __name__ == "__main__":
    unittest.main()
