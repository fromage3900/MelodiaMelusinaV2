"""Songcraft combat expansion tests."""
from __future__ import annotations

import random
import unittest

from gmm.game.battle_manager import MelodiaBattleManager, PHASE_ENEMY
from gmm.game.rules_generated import RULES
from gmm.game.songcraft_effects import get_skill_effect, songcraft_effect_summary
from gmm.songcraft_smoke import run_songcraft_smoke


class TestSongcraftRules(unittest.TestCase):
    def test_effect_summary_matches_generated_rules(self):
        effects = RULES["songcraft"]["skill_effects"]
        summary = songcraft_effect_summary()
        self.assertEqual(summary["count"], len(effects))
        self.assertEqual(summary["skill_ids"], [entry["skill_id"] for entry in effects])

    def test_default_effect_is_neutral(self):
        effect = get_skill_effect("UnlistedSkill")
        self.assertEqual(effect.skill_id, "UnlistedSkill")
        self.assertEqual(effect.toughness_scalar, 1.0)
        self.assertEqual(effect.tags, ())


class TestSongcraftBattleEffects(unittest.TestCase):
    def test_starlit_ping_rewards_perfect_opener(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("CrystalShard")
        mgr.player_command("skill", skill_id="StarlitPing")
        result = mgr.resolve_rhythm(20.0)
        songcraft = result["songcraft"]

        self.assertIn("opener", songcraft["tags"])
        self.assertEqual(songcraft["sp_gain"], 1)
        self.assertGreater(songcraft["ult_bonus"], 0.0)
        self.assertIn("Crescendo_Minor", songcraft["modifiers"])

    def test_tidal_wave_is_breaker_with_bonus_and_delay(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("CrystalShard")
        before_enemy_av = mgr.enemy_av
        mgr.battle_sp = 5.0
        mgr.player_command("skill", skill_id="TidalWave")
        result = mgr.resolve_rhythm(20.0)
        songcraft = result["songcraft"]

        self.assertTrue(result["enemy_broke_now"])
        self.assertGreater(songcraft["bonus_damage"], 0.0)
        self.assertGreater(songcraft["enemy_delay_av"], 0.0)
        self.assertGreater(mgr.enemy_av, before_enemy_av)

    def test_gust_staccato_hastes_next_player_action(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("CrystalShard")
        base_speed = mgr.player.speed
        mgr.player_command("skill", skill_id="GustStaccato")
        result = mgr.resolve_rhythm(20.0)

        self.assertIn("HasteDance", result["songcraft"]["modifiers"])
        self.assertGreater(mgr.modifiers.evaluate("speed", base_speed), base_speed)

    def test_stone_wall_guard_reduces_next_enemy_hit(self):
        random.seed(1337)
        guarded = MelodiaBattleManager()
        guarded.start_encounter("StoneGolem")
        guarded.battle_sp = 5.0
        guarded.player_command("skill", skill_id="StoneWall")
        guarded.resolve_rhythm(20.0)
        guarded.phase = PHASE_ENEMY
        guarded_damage = guarded.enemy_turn()["damage"]

        random.seed(1337)
        baseline = MelodiaBattleManager()
        baseline.start_encounter("StoneGolem")
        baseline.phase = PHASE_ENEMY
        baseline_damage = baseline.enemy_turn()["damage"]

        self.assertLess(guarded_damage, baseline_damage)

    def test_tidal_mend_heals_on_hit(self):
        random.seed(1337)
        mgr = MelodiaBattleManager()
        mgr.start_encounter("StoneGolem")
        mgr.battle_hp = 50.0
        mgr.battle_sp = 20.0
        mgr.player_command("skill", skill_id="TidalMend")
        result = mgr.resolve_rhythm(20.0)

        self.assertGreater(result["songcraft"]["heal"], 0.0)
        self.assertGreater(mgr.battle_hp, 50.0)


class TestSongcraftSmoke(unittest.TestCase):
    def test_songcraft_smoke_is_green(self):
        report = run_songcraft_smoke()
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["checks"]["loop_finalizes"])


if __name__ == "__main__":
    unittest.main()
