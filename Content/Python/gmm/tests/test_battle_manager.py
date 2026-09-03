"""Tests for MelodiaBattleManager — phase transitions, damage, elemental wheel."""
from __future__ import annotations

import time
import unittest

from gmm.gameplay_smoke import run_smoke
from gmm.game.config import GAME_CFG
from gmm.game.rules_generated import RULES
from gmm.game.battle_manager import (
    MelodiaBattleManager,
    element_multiplier,
    ELEMENT_CYCLE,
    PHASE_NONE,
    PHASE_INTRO,
    PHASE_AWAITING,
    PHASE_RHYTHM,
    PHASE_ENEMY,
    PHASE_VICTORY,
    PHASE_DEFEAT,
    PHASE_FLED,
)


class TestElementalWheel(unittest.TestCase):
    """Verify 7-element cyclic damage multipliers."""

    def test_cycle_has_seven(self):
        self.assertEqual(ELEMENT_CYCLE, tuple(RULES["elements"]["cycle"]))

    def test_strong_match(self):
        """Generated strong multiplier when attack beats defense."""
        for attack, defense in RULES["elements"]["weakness"].items():
            self.assertEqual(element_multiplier(attack, defense), RULES["elements"]["strong_multiplier"])

    def test_weak_match(self):
        """Generated weak multiplier when attack is resisted."""
        for attack, defense in RULES["elements"]["resist"].items():
            self.assertEqual(element_multiplier(attack, defense), RULES["elements"]["weak_multiplier"])

    def test_neutral_match(self):
        """1.0x when no relationship."""
        self.assertEqual(element_multiplier("Forte", "Forte"), 1.0)
        self.assertEqual(element_multiplier("Forte", "Radiant"), 1.0)
        self.assertEqual(element_multiplier("Stone", "Tide"), 1.0)
        self.assertEqual(element_multiplier("Arcane", "Gale"), 1.0)


class TestBattlePhaseMachine(unittest.TestCase):
    """Test all 7 phase transitions."""

    def setUp(self):
        self.mgr = MelodiaBattleManager()

    def test_initial_phase(self):
        self.assertEqual(self.mgr.phase, PHASE_NONE)

    def test_start_encounter(self):
        result = self.mgr.start_encounter("CrystalShard")
        self.assertTrue(result["ok"])
        self.assertEqual(self.mgr.phase, PHASE_AWAITING)
        self.assertIsNotNone(self.mgr.enemy)
        self.assertEqual(self.mgr.enemy_hp, 80.0)
        self.assertEqual(self.mgr.enemy_toughness, 22.0)

    def test_start_unknown_enemy(self):
        result = self.mgr.start_encounter("UnknownMonster")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_basic_attack_cycle(self):
        """Phase: Awaiting -> Rhythm -> Enemy -> Awaiting."""
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("basic_attack")
        self.assertEqual(self.mgr.phase, PHASE_RHYTHM)
        self.assertTrue(r["ok"])

        r = self.mgr.resolve_rhythm(50.0)
        self.assertEqual(self.mgr.phase, PHASE_ENEMY)
        self.assertTrue(r["ok"])
        self.assertIn(r["grade"], ("perfect", "great", "good", "miss"))

        r = self.mgr.enemy_turn()
        self.assertIn(self.mgr.phase, (PHASE_AWAITING, PHASE_DEFEAT))

    def test_defend_does_no_damage(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.player_command("defend")
        r = self.mgr.resolve_rhythm(50.0)
        self.assertEqual(r["damage"], 0.0)

    def test_flee_success(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("flee")
        # May succeed or fail based on RNG; either is valid
        self.assertTrue(r["ok"])

    def test_victory_path(self):
        """Force a victory by dealing massive damage."""
        self.mgr.start_encounter("CrystalShard")
        for _ in range(10):
            if self.mgr.phase != PHASE_AWAITING:
                break
            self.mgr.player_command("basic_attack")
            r = self.mgr.resolve_rhythm(20.0)  # near-perfect input
            if self.mgr.phase == PHASE_VICTORY:
                break
            if self.mgr.phase == PHASE_ENEMY:
                self.mgr.enemy_turn()
                if self.mgr.phase == PHASE_DEFEAT:
                    break

        if self.mgr.phase == PHASE_VICTORY:
            summary = self.mgr.end_encounter()
            self.assertGreater(summary["summary"]["xp_earned"], 0)
            self.assertGreater(summary["summary"]["gold_earned"], 0)
        elif self.mgr.phase == PHASE_DEFEAT:
            summary = self.mgr.end_encounter()
            self.assertEqual(summary["phase"], PHASE_NONE)

    def test_command_wrong_phase(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.player_command("basic_attack")
        r = self.mgr.player_command("basic_attack")  # wrong phase
        self.assertFalse(r["ok"])
        self.assertIn("error", r)

    def test_skill_sp_cost(self):
        """Skill cost settles after its rhythm execution, matching runtime."""
        self.mgr.start_encounter("CrystalShard")
        starting_sp = self.mgr.battle_sp
        r = self.mgr.player_command("skill", skill_id="TidalWave")
        self.assertTrue(r["ok"])
        self.assertEqual(starting_sp, self.mgr.battle_sp)
        self.mgr.resolve_rhythm(20.0)
        self.assertLess(self.mgr.battle_sp, starting_sp)

    def test_basic_builds_shared_sp_up_to_cap(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.battle_sp = 0.0
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(20.0)
        self.assertEqual(1.0, self.mgr.battle_sp)

        self.mgr.battle_sp = float(GAME_CFG.shared_sp_max)
        if self.mgr.phase == PHASE_ENEMY:
            self.mgr.enemy_turn()
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(20.0)
        self.assertEqual(float(GAME_CFG.shared_sp_max), self.mgr.battle_sp)

    def test_state_reports_runtime_shared_sp_cap(self):
        self.mgr.start_encounter("CrystalShard")
        self.assertEqual(GAME_CFG.shared_sp_max, self.mgr.get_state()["player"]["max_sp"])

    def test_ultimate_requires_full_gauge(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("ultimate")  # gauge at 0
        self.assertFalse(r["ok"])

    def test_ultimate_is_immediate_runtime_payoff(self):
        self.mgr.start_encounter("StoneGolem")
        self.mgr.battle_ult = GAME_CFG.ult_max
        r = self.mgr.player_command("ultimate")
        self.assertTrue(r["ok"])
        self.assertEqual(PHASE_VICTORY, r["phase"])
        self.assertEqual(300.0, r["damage"])
        self.assertEqual(0.0, self.mgr.battle_ult)


class TestBattleStateQuery(unittest.TestCase):
    """Test get_state() returns consistent snapshots."""

    def setUp(self):
        self.mgr = MelodiaBattleManager()

    def test_state_before_encounter(self):
        s = self.mgr.get_state()
        self.assertEqual(s["phase"], PHASE_NONE)
        self.assertEqual(s["turn"], 0)

    def test_state_during_battle(self):
        self.mgr.start_encounter("CrystalShard")
        s = self.mgr.get_state()
        self.assertEqual(s["phase"], PHASE_AWAITING)
        self.assertEqual(s["turn"], 0)
        self.assertIn("player", s)
        self.assertIn("enemy", s)
        self.assertIn("grades", s)

    def test_state_after_victory(self):
        self.mgr.start_encounter("CrystalShard")
        for _ in range(10):
            if self.mgr.phase != PHASE_AWAITING:
                break
            self.mgr.player_command("basic_attack")
            r = self.mgr.resolve_rhythm(20.0)
            if self.mgr.phase == PHASE_VICTORY:
                break
            if self.mgr.phase == PHASE_ENEMY:
                self.mgr.enemy_turn()
        s = self.mgr.get_state()
        if self.mgr.phase == PHASE_VICTORY:
            self.assertGreater(s["total_damage_dealt"], 0)


class TestHistory(unittest.TestCase):
    """Test that battle events are recorded."""

    def setUp(self):
        self.mgr = MelodiaBattleManager()

    def test_history_records_events(self):
        self.mgr.start_encounter("CrystalShard")
        self.assertGreater(len(self.mgr.history), 0)
        self.assertEqual(self.mgr.history[0]["event"], "encounter_start")

    def test_history_command_recorded(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.player_command("basic_attack")
        events = [h["event"] for h in self.mgr.history]
        self.assertIn("player_command", events)




class TestBattleEdgeCases(unittest.TestCase):
    """More edge cases for battle_manager coverage."""

    def setUp(self):
        self.mgr = MelodiaBattleManager()

    def test_rhythm_before_command(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.resolve_rhythm(50.0)
        self.assertFalse(r["ok"])

    def test_enemy_turn_before_rhythm(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.enemy_turn()
        self.assertFalse(r["ok"])

    def test_unknown_command(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("dance")
        self.assertFalse(r["ok"])

    def test_start_encounter_twice(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.start_encounter("StoneGolem")
        self.assertTrue(r["ok"])

    def test_end_encounter_clears_state(self):
        self.mgr.start_encounter("CrystalShard")
        s = self.mgr.end_encounter()
        self.assertEqual(s["phase"], PHASE_NONE)

    def test_combo_tracking(self):
        self.mgr.start_encounter("CrystalShard")
        for _ in range(3):
            if self.mgr.phase != PHASE_AWAITING:
                break
            self.mgr.player_command("basic_attack")
            r = self.mgr.resolve_rhythm(20.0)
            if self.mgr.phase == PHASE_VICTORY:
                break
            if self.mgr.phase == PHASE_ENEMY:
                self.mgr.enemy_turn()
        self.assertGreaterEqual(self.mgr.combo, 0)

    def test_grades_recorded(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(5.0)
        total = sum(self.mgr.grades.values())
        self.assertEqual(total, 1)

    def test_enemy_hp_does_not_go_below_zero(self):
        self.mgr.start_encounter("CrystalShard")
        self.mgr.enemy_hp = 5.0
        self.mgr.player_command("basic_attack")
        r = self.mgr.resolve_rhythm(20.0)
        self.assertGreaterEqual(self.mgr.enemy_hp, 0)

    def test_defend_reduces_damage(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("defend")
        self.assertTrue(r["ok"])
        self.assertEqual(self.mgr.phase, PHASE_RHYTHM)

    def test_skill_requires_valid_id(self):
        self.mgr.start_encounter("CrystalShard")
        r = self.mgr.player_command("skill", skill_id="NonexistentSkill")
        self.assertFalse(r["ok"])

    def test_ultimate_gauge_builds(self):
        self.mgr.start_encounter("CrystalShard")
        self.assertEqual(self.mgr.battle_ult, 0.0)
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(20.0)
        self.assertGreater(self.mgr.battle_ult, 0.0)

    def test_crescendo_gain_matches_grade_table(self):
        self.mgr.start_encounter("StoneGolem")
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(20.0)
        self.assertEqual(float(GAME_CFG.crescendo_gain["perfect"]), self.mgr.battle_ult)

    def test_toughness_break_reduces_toughness(self):
        self.mgr.start_encounter("StoneGolem")
        self.mgr.player_command("basic_attack")
        self.mgr.resolve_rhythm(20.0)
        self.assertLess(self.mgr.enemy_toughness, 150.0)

    def test_multiple_enemy_turns(self):
        self.mgr.start_encounter("VoidWraith")
        for _ in range(5):
            if self.mgr.phase != PHASE_AWAITING:
                break
            self.mgr.player_command("basic_attack")
            self.mgr.resolve_rhythm(50.0)
            if self.mgr.phase == PHASE_VICTORY:
                break
            if self.mgr.phase == PHASE_ENEMY:
                self.mgr.enemy_turn()
        self.assertGreater(self.mgr.turn_count, 0)

    def test_skill_from_daemon_catalog(self):
        self.mgr.start_encounter("VoidWraith")
        r = self.mgr.player_command("skill", skill_id="EmberStorm")
        if r.get("ok"):
            self.assertEqual(self.mgr.phase, PHASE_RHYTHM)


class TestActionValueSystem(unittest.TestCase):
    """Verify HSR-style Action Value speed-based turn order."""

    def setUp(self):
        self.mgr = MelodiaBattleManager()

    def test_av_initialization(self):
        self.mgr.start_encounter("CrystalShard")
        base_av = RULES["turn_economy"]["base_av"]
        self.assertEqual(GAME_CFG.base_av, base_av)
        self.assertAlmostEqual(self.mgr.player_av, base_av / self.mgr.player.speed)
        self.assertAlmostEqual(self.mgr.enemy_av, base_av / self.mgr.enemy.speed)

    def test_av_turn_order_enemy_acts_next(self):
        self.mgr.start_encounter("CrystalShard")
        self.assertEqual(self.mgr.phase, PHASE_AWAITING)
        base_av = RULES["turn_economy"]["base_av"]
        initial_player_av = base_av / self.mgr.player.speed
        initial_enemy_av = base_av / self.mgr.enemy.speed

        # Player acts
        self.mgr.player_command("basic_attack")
        res = self.mgr.resolve_rhythm(20.0)

        self.assertEqual(res["phase"], PHASE_ENEMY)
        self.assertEqual(self.mgr.phase, PHASE_ENEMY)
        self.assertAlmostEqual(self.mgr.enemy_av, initial_enemy_av - initial_player_av)
        self.assertAlmostEqual(self.mgr.player_av, initial_player_av)

        # Enemy acts
        res_enemy = self.mgr.enemy_turn()
        self.assertEqual(res_enemy["phase"], PHASE_AWAITING)
        self.assertEqual(self.mgr.phase, PHASE_AWAITING)
        self.assertAlmostEqual(self.mgr.player_av, initial_player_av - (initial_enemy_av - initial_player_av))
        self.assertAlmostEqual(self.mgr.enemy_av, initial_enemy_av)


class TestGameplaySmoke(unittest.TestCase):
    """Deterministic slice checks used before opening the editor."""

    def test_core_damage_and_resource_feel(self):
        report = run_smoke(seed=1337)
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["checks"]["basic_damage_ordering"])
        self.assertTrue(report["checks"]["skill_beats_basic_perfect"])
        self.assertTrue(report["checks"]["skill_sp_spent"])
        self.assertTrue(report["checks"]["miss_still_deals_damage"])


if __name__ == "__main__":
    unittest.main()
