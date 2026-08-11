"""Tests for generated-rule-backed elements, toughness, and modifiers."""
from __future__ import annotations

import random
import unittest
import json
from pathlib import Path

from gmm.game.battle_manager import MelodiaBattleManager, PHASE_ENEMY
from gmm.game.elements import ELEMENT_CYCLE, element_multiplier, element_summary
from gmm.game.modifiers import ModifierStack, modifier_registry_summary
from gmm.game.rules_generated import RULES
from gmm.game.toughness import apply_toughness_damage, enemy_damage_multiplier, toughness_damage


class TestGeneratedRuleParity(unittest.TestCase):
    def test_generated_python_matches_authoritative_json(self):
        root = Path(__file__).resolve().parents[4]
        source = json.loads((root / "Plugins/MelodiaCore/Rules/melodia_rules.json").read_text(encoding="utf-8"))
        expected = {key: value for key, value in source.items() if not key.startswith("_")}
        self.assertEqual(expected, RULES)


class TestGeneratedElementWheel(unittest.TestCase):
    def test_cycle_matches_generated_rules(self):
        self.assertEqual(ELEMENT_CYCLE, tuple(RULES["elements"]["cycle"]))

    def test_generated_strong_and_weak_multipliers(self):
        rules = RULES["elements"]
        for attack, defense in rules["weakness"].items():
            self.assertEqual(element_multiplier(attack, defense), rules["strong_multiplier"])
        for attack, defense in rules["resist"].items():
            self.assertEqual(element_multiplier(attack, defense), rules["weak_multiplier"])

    def test_summary_exposes_generated_shape(self):
        summary = element_summary()
        self.assertEqual(summary["cycle"], RULES["elements"]["cycle"])
        self.assertEqual(summary["weakness"], RULES["elements"]["weakness"])


class TestGeneratedToughness(unittest.TestCase):
    def test_toughness_damage_uses_generated_reduction(self):
        raw_damage = 50.0
        self.assertEqual(toughness_damage(raw_damage), raw_damage * RULES["toughness"]["reduction"])

    def test_apply_toughness_damage_reports_break_once(self):
        result = apply_toughness_damage(current=10.0, max_value=60.0, raw_damage=100.0)
        self.assertTrue(result.is_broken)
        self.assertTrue(result.broke_now)
        self.assertEqual(result.current, 0.0)

        already_broken = apply_toughness_damage(current=0.0, max_value=60.0, raw_damage=100.0)
        self.assertTrue(already_broken.is_broken)
        self.assertFalse(already_broken.broke_now)

    def test_broken_enemy_damage_multiplier_uses_generated_rule(self):
        self.assertEqual(enemy_damage_multiplier(True), RULES["toughness"]["broken_enemy_damage_mult"])
        self.assertEqual(enemy_damage_multiplier(False), 1.0)


class TestGeneratedModifierStack(unittest.TestCase):
    def test_registry_summary_matches_generated_rules(self):
        summary = modifier_registry_summary()
        self.assertEqual(summary["count"], len(RULES["modifiers"]["registry"]))
        self.assertEqual(summary["ids"], [entry["id"] for entry in RULES["modifiers"]["registry"]])

    def test_refresh_modifier_does_not_stack(self):
        stack = ModifierStack()
        self.assertTrue(stack.add("Crescendo_Minor"))
        self.assertTrue(stack.add("Crescendo_Minor"))
        snapshot = stack.snapshot()
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]["stacks"], 1)

    def test_stack_modifier_respects_max_stacks(self):
        stack = ModifierStack()
        rule = next(entry for entry in RULES["modifiers"]["registry"] if entry["id"] == "TempoBreak")
        for _ in range(rule["max_stacks"] + 2):
            stack.add("TempoBreak")
        snapshot = stack.snapshot()
        self.assertEqual(snapshot[0]["stacks"], rule["max_stacks"])
        expected = 100.0 * (rule["value"] ** rule["max_stacks"])
        self.assertAlmostEqual(stack.evaluate("speed", 100.0), expected)

    def test_duration_ticks_remove_expired_modifiers(self):
        stack = ModifierStack()
        rule = next(entry for entry in RULES["modifiers"]["registry"] if entry["id"] == "GuardHymn")
        stack.add("GuardHymn")
        self.assertEqual(len(stack.snapshot()), 1)
        for _ in range(rule["duration_turns"]):
            stack.tick_turn()
        self.assertEqual(stack.snapshot(), [])


class TestBattleSimulatorRuleIntegration(unittest.TestCase):
    def test_skill_uses_generated_element_multiplier(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("FireDrake")
        mgr.player_command("skill", skill_id="TidalWave")
        result = mgr.resolve_rhythm(20.0)
        self.assertEqual(result["phase"], PHASE_ENEMY)
        self.assertEqual(result["element_mult"], RULES["elements"]["strong_multiplier"])

    def test_toughness_break_reduces_enemy_turn_damage(self):
        random.seed(1337)
        normal = MelodiaBattleManager()
        normal.start_encounter("CrystalShard")
        normal.phase = PHASE_ENEMY
        normal_damage = normal.enemy_turn()["damage"]

        broken = MelodiaBattleManager()
        broken.start_encounter("CrystalShard")
        broken.enemy_toughness = 0.0
        broken.enemy_broken = True
        broken.phase = PHASE_ENEMY
        random.seed(1337)
        broken_damage = broken.enemy_turn()["damage"]

        self.assertLess(broken_damage, normal_damage)

    def test_attack_modifier_increases_player_damage(self):
        random.seed(1337)
        baseline = MelodiaBattleManager()
        baseline.start_encounter("CrystalShard")
        baseline.player_command("basic_attack")
        baseline_damage = baseline.resolve_rhythm(20.0)["damage"]

        random.seed(1337)
        modified = MelodiaBattleManager()
        modified.start_encounter("CrystalShard")
        self.assertTrue(modified.add_modifier("Crescendo_Minor"))
        modified.player_command("basic_attack")
        modified_damage = modified.resolve_rhythm(20.0)["damage"]

        self.assertGreater(modified_damage, baseline_damage)

    def test_guard_modifier_reduces_damage_taken_and_expires(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("CrystalShard")
        self.assertTrue(mgr.add_modifier("GuardHymn"))
        mgr.phase = PHASE_ENEMY
        guarded_damage = mgr.enemy_turn()["damage"]
        self.assertEqual(mgr.modifiers.snapshot(), [])

        random.seed(1337)
        baseline = MelodiaBattleManager()
        baseline.start_encounter("CrystalShard")
        baseline.phase = PHASE_ENEMY
        baseline_damage = baseline.enemy_turn()["damage"]

        self.assertLess(guarded_damage, baseline_damage)


if __name__ == "__main__":
    unittest.main()
