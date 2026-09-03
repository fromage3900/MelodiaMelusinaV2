"""Battle Manager — full rhythm battle state machine.

Ties together:
    - MelodiaDataRegistry   (enemy + skill config)
    - MelodiaRhythmClock    (BPM beat clock + hit testing)
    - MelodiaPlayerState    (stats, inventory, XP/leveling)

Phase machine (matches C++ UMelodiaBattleSession):
    None -> Intro -> AwaitingPlayerCommand -> RhythmExecution ->
    EnemyTurn -> Victory | Defeat | Fled -> None

Elemental wheel (7 elements, cyclic multipliers):
    Forte > Stone > Umbral > Arcane > Radiant > Gale > Tide > Forte

Usage:
    mgr = MelodiaBattleManager()
    mgr.start_encounter("StoneGolem")
    mgr.player_command("skill", skill_id="TidalWave")
    grade, dmg = mgr.resolve_rhythm(128.0)  # input time in ms
    mgr.enemy_turn()
"""
from __future__ import annotations

import random
import time
from typing import Optional

from gmm.game.data_registry import MelodiaDataRegistry, EnemyStats, SkillData
from gmm.game.elements import ELEMENT_CYCLE, element_multiplier
from gmm.game.modifiers import ModifierStack
from gmm.game.rhythm_clock import MelodiaRhythmClock
from gmm.game.player_state import MelodiaPlayerState
from gmm.game.config import GAME_CFG
from gmm.game.songcraft_effects import get_skill_effect
from gmm.game.toughness import apply_toughness_damage, enemy_damage_multiplier
from gmm.game.afflictions import apply_affliction as apply_elemental_affliction, tick_afflictions, AFFLICTION_DEFS
from gmm.game.combo_rewards import check_combo_milestones
from gmm.game import battle_osc  # TD OSC bridge

# Lazy import to avoid circular dependency at module level
AudioEngine = None


# =============================================================================
# Affliction System — elemental status effects
# =============================================================================

AFFLICTION_ELEMENTS = ("Forte", "Stone", "Umbral", "Arcane", "Radiant", "Gale", "Tide")

AFFLICTION_DEFS: dict[str, dict] = {
    "Forte":    {"name": "Burn",       "tick_dmg": 0.08,  "duration": 3, "effect": "damage_over_time"},
    "Stone":    {"name": "Petrify",    "speed_down": 0.30, "duration": 2, "effect": "speed_reduction"},
    "Umbral":   {"name": "ShadowBind", "sp_lock": True,      "duration": 2, "effect": "sp_lock"},
    "Arcane":   {"name": "Silence",    "skill_lock": True,  "duration": 3, "effect": "skill_lock"},
    "Radiant":  {"name": "Blind",      "acc_down": 0.25,   "duration": 3, "effect": "accuracy_down"},
    "Gale":     {"name": "Gust",       "push_turn": True,   "duration": 1, "effect": "turn_manipulation"},
    "Tide":     {"name": "Drown",      "heal_block": True,  "duration": 3, "effect": "heal_block"},
}

def apply_affliction(target: dict, element: str, potency: float = 1.0) -> dict:
    """Apply an elemental affliction to a target. Returns the affliction dict."""
    if element not in AFFLICTION_DEFS:
        return {}
    base = AFFLICTION_DEFS[element].copy()
    base["element"] = element
    base["potency"] = potency
    base["remaining"] = base["duration"]
    base["source_element"] = element
    return base


# =============================================================================
# Combo Rewards — milestone bonuses
# =============================================================================

COMBO_MILESTONES = {
    5:  {"heal": 0.10, "sp_gain": 5,  "ult_gain": 5},
    10: {"heal": 0.20, "sp_gain": 10, "ult_gain": 15, "bonus_dmg": 0.5},
    15: {"heal": 0.30, "sp_gain": 15, "ult_gain": 25, "bonus_dmg": 1.0},
    20: {"heal": 0.50, "sp_gain": 25, "ult_gain": 40, "bonus_dmg": 2.0, "clean_afflictions": True},
}

def check_combo_milestones(combo: int, prev_combo: int, battle_mgr) -> list[dict]:
    """Check if combo reached a new milestone. Returns list of reward events."""
    events = []
    for milestone in sorted(COMBO_MILESTONES.keys()):
        if prev_combo < milestone <= combo:
            reward = COMBO_MILESTONES[milestone]
            events.append({"type": "combo_milestone", "combo": milestone, "reward": reward})
            # Apply rewards
            if "heal" in reward:
                heal_amt = battle_mgr.player.max_hp * reward["heal"]
                battle_mgr.battle_hp = min(battle_mgr.player.max_hp, battle_mgr.battle_hp + heal_amt)
                events.append({"type": "heal", "amount": heal_amt})
            if "sp_gain" in reward:
                battle_mgr.battle_sp = min(GAME_CFG.shared_sp_max, battle_mgr.battle_sp + reward["sp_gain"])
                events.append({"type": "sp_gain", "amount": reward["sp_gain"]})
            if "ult_gain" in reward:
                battle_mgr.battle_ult = min(GAME_CFG.ult_max, battle_mgr.battle_ult + reward["ult_gain"])
                events.append({"type": "ult_gain", "amount": reward["ult_gain"]})
            if "clean_afflictions" in reward and reward["clean_afflictions"]:
                if battle_mgr.enemy:
                    battle_mgr.enemy_afflictions = []
                events.append({"type": "afflictions_cleared"})
    return events


def _get_audio_engine():
    global AudioEngine
    if AudioEngine is None:
        from gmm.game.audio_engine import AudioEngine as _AE
        AudioEngine = _AE
    return AudioEngine


# ---------------------------------------------------------------------------
# Battle phase constants (matches C++ UMelodiaBattleSession)
# ---------------------------------------------------------------------------
PHASE_NONE = "None"
PHASE_INTRO = "Intro"
PHASE_AWAITING = "AwaitingPlayerCommand"
PHASE_RHYTHM = "RhythmExecution"
PHASE_ENEMY = "EnemyTurn"
PHASE_VICTORY = "Victory"
PHASE_DEFEAT = "Defeat"
PHASE_FLED = "Fled"


class MelodiaBattleManager:
    """Full rhythm battle state machine.

    Each battle instance tracks its own:
    - Enemy stats (from data registry)
    - Player snapshot (HP, SP, ult gauge)
    - Rhythm clock (BPM from enemy)
    - Turn/phase state
    - Grade history
    """

    def __init__(self, registry: Optional[MelodiaDataRegistry] = None,
                 player: Optional[MelodiaPlayerState] = None,
                 audio: Optional[AudioEngine] = None):
        self.registry = registry or MelodiaDataRegistry()
        self.player = player or MelodiaPlayerState()
        self.clock = MelodiaRhythmClock(bpm=120)
        self.audio = audio
        self.modifiers = ModifierStack()

        self.phase: str = PHASE_NONE
        self.enemy: Optional[EnemyStats] = None
        self.enemy_hp: float = 0.0
        self.enemy_toughness: float = 0.0

        self.player_av: float = 0.0
        self.enemy_av: float = 0.0

        # Battle snapshot (copy of player state at encounter start)
        self.battle_hp: float = 0.0
        self.battle_sp: float = 0.0
        self.battle_ult: float = 0.0
        self.battle_mana: float = 0.0  # Mana for token-integrated skills

        self.turn_count: int = 0
        self.combo: int = 0
        self.max_combo: int = 0
        self.grades: dict[str, int] = {"perfect": 0, "great": 0, "good": 0, "miss": 0}
        self.total_damage_dealt: float = 0.0
        self.total_damage_taken: float = 0.0
        self.xp_earned: int = 0
        self.gold_earned: int = 0
        self._victory_rewards_granted: bool = False

        self.current_command: str = ""
        self.current_skill: Optional[SkillData] = None
        self.last_grade: str = ""
        self.last_error_ms: float = 0.0
        self.enemy_broken: bool = False
        self.enemy_break_count: int = 0

        # Affliction system
        self.enemy_afflictions: list[dict] = []
        self.player_afflictions: list[dict] = []

        self.history: list[dict] = []

    # -- Public API --

    def start_encounter(self, enemy_id: str = "CrystalShard") -> dict:
        """Begin a new encounter with the given enemy."""
        enemy = self.registry.get_enemy(enemy_id)
        if not enemy:
            return {"ok": False, "error": f"Unknown enemy '{enemy_id}'"}

        self.enemy = enemy
        self.enemy_hp = enemy.max_hp
        self.enemy_toughness = enemy.toughness
        self.enemy_broken = self.enemy_toughness <= 0
        self.enemy_break_count = 0
        self.phase = PHASE_INTRO

        # Snapshot current player state
        self.battle_hp = self.player.hp
        # Runtime uses a small shared command pool, not the player's larger
        # persistent RPG resource. Mirror MelodiaCore's SkillPointMax contract.
        self.battle_sp = min(
            self.player.sp,
            float(GAME_CFG.shared_sp_start),
            float(GAME_CFG.shared_sp_max),
        )
        self.battle_ult = self.player.ult_gauge

        self.turn_count = 0
        self.combo = 0
        self.max_combo = 0
        self.grades = {"perfect": 0, "great": 0, "good": 0, "miss": 0}
        self.total_damage_dealt = 0.0
        self.total_damage_taken = 0.0
        self.xp_earned = 0
        self.gold_earned = 0
        self._victory_rewards_granted = False
        self.current_command = ""
        self.current_skill = None
        self.modifiers.clear()
        self.enemy_afflictions = []
        self.player_afflictions = []
        self.history = []

        self.player_av = GAME_CFG.base_av / max(1.0, float(self.player.speed))
        self.enemy_av = GAME_CFG.base_av / max(1.0, float(enemy.speed))

        # Configure rhythm clock
        self.clock.set_bpm(enemy.bpm)
        self.clock.reset()
        if self.audio:
            self.audio.start_metronome(enemy.bpm)

        self.phase = PHASE_AWAITING

        entry = {
            "event": "encounter_start",
            "enemy_id": enemy.enemy_id,
            "enemy_name": enemy.display_name,
            "enemy_hp": self.enemy_hp,
            "enemy_toughness": self.enemy_toughness,
            "enemy_broken": self.enemy_broken,
            "bpm": enemy.bpm,
            "element": enemy.element,
            "player_hp": self.battle_hp,
            "player_sp": self.battle_sp,
        }
        self.history.append(entry)

        # OSC: notify TouchDesigner of encounter start
        battle_osc.on_encounter_start(enemy.enemy_id, enemy.bpm, enemy.element)
        battle_osc.on_phase_change(self.phase)

        return {"ok": True, "phase": self.phase, "enemy": enemy.to_dict(),
                "player": self._player_state()}

    def player_command(self, command: str = "basic_attack",
                       skill_id: str = "") -> dict:
        """Issue a player command.

        Commands: basic_attack, skill, ultimate, defend, flee
        """
        if self.phase != PHASE_AWAITING:
            return {"ok": False, "error": f"Cannot act in phase '{self.phase}'"}

        valid = ("basic_attack", "skill", "ultimate", "defend", "flee")
        if command not in valid:
            return {"ok": False, "error": f"Unknown command '{command}'"}

        if command == "flee":
            player_speed = self.modifiers.evaluate("speed", self.player.speed)
            flee_chance = (
                GAME_CFG.flee_base_chance
                + (player_speed - (self.enemy.speed if self.enemy else 80)) * GAME_CFG.flee_speed_factor
            )
            if random.random() < max(0.1, min(0.95, flee_chance)):
                self.phase = PHASE_FLED
                battle_osc.on_battle_end("fled")
                self.history.append({"event": "fled"})
                return {"ok": True, "phase": self.phase, "fled": True}
            self.phase = PHASE_ENEMY
            self.history.append({"event": "flee_failed"})
            return {"ok": True, "phase": self.phase, "fled": False,
                    "message": "Flee failed!"}

        if command == "skill":
            skill = self.registry.get_skill(skill_id)
            if not skill:
                return {"ok": False, "error": f"Unknown skill '{skill_id}'"}
            if self.battle_sp < skill.sp_cost:
                return {"ok": False, "error": f"Not enough SP ({skill.sp_cost} needed, {self.battle_sp:.0f} available)"}
            self.current_skill = skill
        else:
            self.current_skill = None

        if command == "ultimate":
            if self.battle_ult < GAME_CFG.ult_max:
                return {"ok": False, "error": f"Ult gauge not full ({self.battle_ult:.0f}/{GAME_CFG.ult_max:.0f})"}
            # MelodiaCore resolves Crescendo immediately rather than launching
            # another rhythm highway. It is the payoff for prior performance.
            ultimate_damage = 100.0 + self.battle_ult * 2.0
            self.battle_ult = 0.0
            self.turn_count += 1
            self.enemy_hp = max(0.0, self.enemy_hp - ultimate_damage)
            self.total_damage_dealt += ultimate_damage
            self.history.append({
                "event": "ultimate",
                "turn": self.turn_count,
                "damage": round(ultimate_damage, 1),
                "enemy_hp_remaining": round(self.enemy_hp, 1),
            })
            if self.enemy_hp <= 0:
                self.phase = PHASE_VICTORY
                self._on_victory()
                self.history.append({"event": "victory", "grades": dict(self.grades),
                                     "combo": self.combo, "turns": self.turn_count})
            else:
                self.phase = PHASE_ENEMY
            return {
                "ok": True,
                "phase": self.phase,
                "command": command,
                "turn": self.turn_count,
                "damage": round(ultimate_damage, 1),
                "enemy_hp": round(self.enemy_hp, 1),
            }

        self.current_command = command
        self.turn_count += 1
        self.phase = PHASE_RHYTHM
        self.clock.start()

        entry = {
            "event": "player_command",
            "command": command,
            "skill_id": skill_id,
            "turn": self.turn_count,
            "player_sp": self.battle_sp,
            "bpm": self.clock.bpm,
        }
        self.history.append(entry)

        return {"ok": True, "phase": self.phase, "command": command,
                "turn": self.turn_count, "bpm": self.clock.bpm}

    def resolve_rhythm(self, input_time_ms: Optional[float] = None) -> dict:
        """Resolve the rhythm input and apply damage/effects.

        Args:
            input_time_ms: Player input timestamp. If None, uses
                          time_since_command to simulate input.

        Returns:
            Dict with grade, damage, combo, new phase, etc.
        """
        if self.phase != PHASE_RHYTHM:
            return {"ok": False, "error": f"Not in rhythm phase (current: {self.phase})"}

        self.clock.stop()

        if input_time_ms is None:
            input_time_ms = self.clock.elapsed_ms

        # Hit test
        grade, error_ms = self.clock.hit_test(input_time_ms)
        self.last_grade = grade
        self.last_error_ms = error_ms
        self.grades[grade] += 1

        if grade == "miss":
            self.combo = 0
        else:
            self.combo += 1
            if self.combo > self.max_combo:
                self.max_combo = self.combo

        # Calculate damage
        base_damage = self._calculate_base_damage()
        mult = self.clock.grade_multiplier(grade)

        # Elemental modifier
        elem_mult = 1.0
        if self.enemy and self.current_skill:
            elem_mult = element_multiplier(self.current_skill.element, self.enemy.element)
        elif self.enemy and self.current_command == "basic_attack":
            # Player uses their highest element or neutral
            pass

        active_skill = self.current_skill
        skill_effect = get_skill_effect(active_skill.skill_id) if active_skill else None
        toughness_scalar = skill_effect.toughness_scalar if skill_effect else 1.0

        damage = base_damage * mult * elem_mult
        toughness_result = apply_toughness_damage(
            self.enemy_toughness,
            self.enemy.toughness if self.enemy else 1.0,
            damage * toughness_scalar,
        )
        toughness_dmg = toughness_result.damage

        # Apply
        if self.enemy:
            self.enemy_hp = max(0, self.enemy_hp - damage)
            self.enemy_toughness = toughness_result.current
            self.enemy_broken = toughness_result.is_broken
            if toughness_result.broke_now:
                self.enemy_break_count += 1
        self.total_damage_dealt += damage

        # Match MelodiaCore: command resources settle only after a valid rhythm
        # execution. Basics build one shared SP; skills spend their recipe cost.
        if self.current_command == "basic_attack":
            self.battle_sp = min(
                float(GAME_CFG.shared_sp_max),
                self.battle_sp + float(GAME_CFG.basic_sp_gain),
            )
        elif self.current_command == "skill" and self.current_skill:
            self.battle_sp = max(0.0, self.battle_sp - float(self.current_skill.sp_cost))

        # Audio feedback
        if self.audio:
            self.audio.play_grade(grade)
            if self.audio._running:
                self.audio.stop_metronome()

        ult_gain = float(GAME_CFG.crescendo_gain.get(grade, 0.0))
        ult_gain = self.modifiers.evaluate("ult_gain", ult_gain)
        self.battle_ult = min(GAME_CFG.ult_max, self.battle_ult + ult_gain)

        songcraft = self._apply_songcraft_effects(
            skill_effect=skill_effect,
            grade=grade,
            damage=damage,
            broke_now=toughness_result.broke_now,
        )

        # Apply elemental affliction on successful skill hits
        if self.current_command == "skill" and self.current_skill and self.enemy and grade != "miss":
            affliction = apply_affliction(self.enemy_afflictions, self.current_skill.element)
            if affliction:
                songcraft["affliction_applied"] = affliction["name"]

        # Check combo milestones
        prev_combo = self.combo - 1 if grade != "miss" else self.combo
        milestone_events = check_combo_milestones(self.combo, prev_combo, self)
        if milestone_events:
            songcraft["combo_milestones"] = milestone_events

        self.current_command = ""
        self.current_skill = None

        entry = {
            "event": "rhythm_resolve",
            "grade": grade,
            "error_ms": round(error_ms, 2),
            "combo": self.combo,
            "damage": round(damage, 1),
            "toughness_damage": round(toughness_dmg, 1),
            "enemy_broken": self.enemy_broken,
            "enemy_broke_now": toughness_result.broke_now,
            "element_mult": round(elem_mult, 2),
            "enemy_hp_remaining": round(self.enemy_hp, 1) if self.enemy else 0,
            "modifiers": self.modifiers.snapshot(),
            "songcraft": songcraft,
        }
        self.history.append(entry)

        # Player completed action. Advance time by player's current AV cost.
        elapsed = self.player_av
        self.enemy_av = max(0.0, self.enemy_av - elapsed)
        player_speed = self.modifiers.evaluate("speed", self.player.speed)
        self.player_av = GAME_CFG.base_av / max(1.0, player_speed)
        delay_fraction = float(songcraft.get("enemy_delay_av_fraction", 0.0))
        if delay_fraction > 0.0:
            delay_amount = GAME_CFG.base_av * delay_fraction
            self.enemy_av += delay_amount
            songcraft["enemy_delay_av"] = round(delay_amount, 2)

        # Check victory
        if self.enemy and self.enemy_hp <= 0:
            self.phase = PHASE_VICTORY
            if self.audio:
                self.audio.play_victory()
            self._on_victory()
            battle_osc.on_battle_end("victory")
            entry = {"event": "victory", "grades": dict(self.grades),
                     "combo": self.combo, "turns": self.turn_count}
            self.history.append(entry)
        else:
            self._determine_next_turn()

        # OSC: notify TouchDesigner of hit result
        battle_osc.on_hit_result(
            grade=grade, error_ms=round(error_ms, 2), combo=self.combo,
            damage_dealt=round(damage, 1),
            enemy_hp=round(self.enemy_hp, 1) if self.enemy else 0,
            enemy_broken=toughness_result.broke_now if toughness_result else False,
            ult_gauge=self.battle_ult,
        )

        return {
            "ok": True,
            "phase": self.phase,
            "grade": grade,
            "error_ms": round(error_ms, 2),
            "combo": self.combo,
            "damage": round(damage, 1),
            "element_mult": round(elem_mult, 2),
            "enemy_hp": round(self.enemy_hp, 1) if self.enemy else 0,
            "enemy_toughness": round(self.enemy_toughness, 1) if self.enemy else 0,
            "enemy_broken": self.enemy_broken,
            "enemy_broke_now": toughness_result.broke_now,
            "songcraft": songcraft,
        }

    def enemy_turn(self) -> dict:
        """Process the enemy attack phase."""
        if self.phase != PHASE_ENEMY:
            return {"ok": False, "error": f"Not in enemy phase (current: {self.phase})"}

        if not self.enemy:
            return {"ok": False, "error": "No enemy in encounter"}

        # Scale damage by enemy's min/max attack
        base_damage = random.uniform(self.enemy.min_attack, self.enemy.max_attack)

        # Element multiplier against player (neutral for now)
        elem_mult = 1.0

        # Toughness reduction: broken enemy deals less damage
        base_damage *= enemy_damage_multiplier(self.enemy_broken)

        damage = base_damage * elem_mult
        actual = self._take_damage(damage)
        self.total_damage_taken += actual

        entry = {
            "event": "enemy_attack",
            "base_damage": round(base_damage, 1),
            "element_mult": round(elem_mult, 2),
            "damage_dealt": round(actual, 1),
            "player_hp_remaining": round(self.battle_hp, 1),
        }
        self.history.append(entry)

        # Enemy completed action. Advance time by enemy's current AV cost.
        elapsed = self.enemy_av
        self.player_av = max(0.0, self.player_av - elapsed)
        enemy_speed = self.enemy.speed if self.enemy else 80.0
        self.enemy_av = GAME_CFG.base_av / max(1.0, enemy_speed)

        if self.battle_hp <= 0:
            self.phase = PHASE_DEFEAT
            battle_osc.on_battle_end("defeat")
            if self.audio:
                self.audio.play_defeat()
            self.history.append({"event": "defeat"})
        else:
            self._determine_next_turn()

        self.modifiers.tick_turn()

        # Tick afflictions
        if self.enemy_afflictions:
            aff_events = tick_afflictions(self.enemy_afflictions)
            if aff_events:
                self.history.extend([{"event": "affliction", **e} for e in aff_events])

        return {
            "ok": True,
            "phase": self.phase,
            "damage": round(actual, 1),
            "player_hp": round(self.battle_hp, 1),
            "enemy_broken": self.enemy_broken,
        }

    def _determine_next_turn(self):
        """Update phase based on remaining AVs."""
        if not self.enemy:
            self.phase = PHASE_AWAITING
            return

        if self.player_av <= self.enemy_av:
            self.phase = PHASE_AWAITING
        else:
            self.phase = PHASE_ENEMY

    def get_state(self) -> dict:
        """Return full current battle state snapshot."""
        return {
            "ok": True,
            "phase": self.phase,
            "turn": self.turn_count,
            "combo": self.combo,
            "max_combo": self.max_combo,
            "grades": dict(self.grades),
            "player": self._player_state(),
            "enemy": self._enemy_state(),
            "total_damage_dealt": round(self.total_damage_dealt, 1),
            "total_damage_taken": round(self.total_damage_taken, 1),
            "history_count": len(self.history),
            "last_grade": self.last_grade,
            "last_error_ms": round(self.last_error_ms, 2),
            "modifiers": self.modifiers.snapshot(),
            "player_av": round(self.player_av, 2),
            "enemy_av": round(self.enemy_av, 2),
        }

    def end_encounter(self) -> dict:
        """End the current encounter and sync changes to player state."""
        summary = {
            "event": "end_encounter",
            "phase": self.phase,
            "turns": self.turn_count,
            "grades": dict(self.grades),
            "max_combo": self.max_combo,
            "xp_earned": self.xp_earned,
            "gold_earned": self.gold_earned,
            "total_damage_dealt": round(self.total_damage_dealt, 1),
            "total_damage_taken": round(self.total_damage_taken, 1),
        }
        self.history.append(summary)

        # Write results back to player state if victory/fled
        if self.phase in (PHASE_VICTORY, PHASE_FLED):
            self.player.hp = self.battle_hp
            self.player.sp = self.battle_sp
            self.player.ult_gauge = self.battle_ult
            self.player.add_xp(self.xp_earned)
            self.player.add_gold(self.gold_earned)

            if self.phase == PHASE_VICTORY and self.enemy:
                if self.enemy.enemy_id not in self.player.completed_encounters:
                    self.player.completed_encounters.append(self.enemy.enemy_id)
        elif self.phase == PHASE_DEFEAT:
            self.player.hp = max(1, self.player.max_hp * GAME_CFG.defeat_hp_recovery)
            self.player.sp = self.player.max_sp * GAME_CFG.defeat_sp_recovery

        self.phase = PHASE_NONE
        self.enemy = None

        return {"ok": True, "phase": self.phase, "summary": summary}

    def add_modifier(self, modifier_id: str) -> bool:
        """Apply a generated-rule modifier to the active battle."""
        applied = self.modifiers.add(modifier_id)
        if applied:
            self.history.append({
                "event": "modifier_added",
                "modifier_id": modifier_id,
                "modifiers": self.modifiers.snapshot(),
            })
        return applied

    def _apply_songcraft_effects(self, *, skill_effect, grade: str, damage: float, broke_now: bool) -> dict:
        """Apply generated songcraft effects after one valid rhythm result."""
        if not skill_effect:
            return {}

        hit = grade != "miss"
        perfect = grade == "perfect"
        applied_modifiers: list[str] = []
        bonus_damage = 0.0
        heal = 0.0
        sp_gain = 0
        ult_bonus = 0.0
        delay_fraction = 0.0

        if hit:
            for modifier_id in skill_effect.modifiers_on_hit:
                if self.add_modifier(modifier_id):
                    applied_modifiers.append(modifier_id)
            if skill_effect.heal_on_hit_scalar > 0.0:
                heal = max(0.0, damage * skill_effect.heal_on_hit_scalar)
                self.battle_hp = min(self.player.max_hp, self.battle_hp + heal)
            delay_fraction += skill_effect.enemy_delay_on_hit_av_fraction

        if perfect:
            for modifier_id in skill_effect.modifiers_on_perfect:
                if self.add_modifier(modifier_id):
                    applied_modifiers.append(modifier_id)
            if skill_effect.sp_gain_on_perfect > 0:
                previous_sp = self.battle_sp
                self.battle_sp = min(
                    float(GAME_CFG.shared_sp_max),
                    self.battle_sp + float(skill_effect.sp_gain_on_perfect),
                )
                sp_gain = int(self.battle_sp - previous_sp)
            if skill_effect.ult_gain_bonus_on_perfect > 0.0:
                ult_bonus = skill_effect.ult_gain_bonus_on_perfect
                self.battle_ult = min(GAME_CFG.ult_max, self.battle_ult + ult_bonus)

        if broke_now:
            bonus_damage = max(0.0, skill_effect.bonus_damage_on_break)
            if bonus_damage > 0.0 and self.enemy:
                self.enemy_hp = max(0.0, self.enemy_hp - bonus_damage)
                self.total_damage_dealt += bonus_damage
            delay_fraction += skill_effect.enemy_delay_on_break_av_fraction

        report = {
            "skill_id": skill_effect.skill_id,
            "tags": list(skill_effect.tags),
            "toughness_scalar": skill_effect.toughness_scalar,
            "bonus_damage": round(bonus_damage, 1),
            "heal": round(heal, 1),
            "sp_gain": sp_gain,
            "ult_bonus": round(ult_bonus, 1),
            "enemy_delay_av_fraction": round(delay_fraction, 3),
            "modifiers": applied_modifiers,
        }
        self.history.append({"event": "songcraft_effect", **report})
        return report

    # -- Internal --

    def _calculate_base_damage(self) -> float:
        """Calculate base damage based on current command."""
        equipped = self.player.get_equipped_stats()

        if self.current_command == "basic_attack":
            base = random.uniform(equipped["min_attack"], equipped["max_attack"])
            return self.modifiers.evaluate("attack", base)

        if self.current_command == "skill" and self.current_skill:
            base = self.current_skill.base_damage + equipped["min_magical_attack"] * 0.5
            return self.modifiers.evaluate("attack", base)

        if self.current_command == "ultimate":
            base = random.uniform(equipped["min_attack"], equipped["max_attack"]) * GAME_CFG.ultimate_damage_mult
            return self.modifiers.evaluate("attack", base)

        if self.current_command == "defend":
            return 0.0

        return 10.0

    def _take_damage(self, raw_damage: float) -> float:
        """Apply damage to battle HP with defense mitigation."""
        equipped = self.player.get_equipped_stats()
        defense = equipped["defense"]
        modified_damage = self.modifiers.evaluate("damage_taken", raw_damage)
        effective = max(1.0, modified_damage - defense * GAME_CFG.defense_mitigation)
        self.battle_hp = max(0, self.battle_hp - effective)
        return effective

    def _on_victory(self):
        """Calculate rewards including tokens."""
        if not self.enemy or self._victory_rewards_granted:
            return
        self._victory_rewards_granted = True
        self.xp_earned = self.enemy.xp_reward
        self.gold_earned = self.enemy.gold_reward

        # Bonus XP from combo
        combo_bonus = int(self.max_combo * 5)
        self.xp_earned += combo_bonus
        
        # Grant tokens based on enemy element and performance
        self._grant_victory_tokens()

    def _grant_victory_tokens(self) -> dict:
        """Grant tokens to player on victory. Returns token changes dict."""
        from gmm.game.tokens import TOKEN_TYPES
        
        changes = {"shards": {}, "mana": 0, "golden": 0}
        
        if not self.enemy:
            return changes
        
        # Base token grant: 1-3 golden tokens
        golden_base = 1 + (self.max_combo // 10)
        changes["golden"] = golden_base
        self.player.token_wallet.add_golden(golden_base)
        
        # Mana regen based on grade performance
        mana_gain = 20.0 * (1 + self.grades.get("perfect", 0) * 0.2)
        changes["mana"] = mana_gain
        self.player.token_wallet.add_mana(mana_gain)
        
        # Elemental shard based on enemy element defeated
        enemy_element = self.enemy.element if self.enemy else ""
        shard_gain = 1 + (self.max_combo // 5)
        
        # Find matching token type
        for token_id, data in TOKEN_TYPES.items():
            if data.get("element") == enemy_element:
                new_count = self.player.token_wallet.add_shard(enemy_element, shard_gain)
                changes["shards"][enemy_element] = new_count
                break
        
        return changes

    def _player_state(self) -> dict:
        return {
            "hp": round(self.battle_hp, 1),
            "max_hp": self.player.max_hp,
            "sp": round(self.battle_sp, 1),
            "max_sp": GAME_CFG.shared_sp_max,
            "ult": round(self.battle_ult, 1),
            "max_ult": GAME_CFG.ult_max,
            "mana": round(self.player.token_wallet.mana_current, 1),
            "max_mana": self.player.token_wallet.mana_max,
            "shards": self.player.token_wallet.shards,
            "golden_tokens": self.player.token_wallet.golden_tokens,
        }

    def _enemy_state(self) -> dict:
        if not self.enemy:
            return {}
        return {
            "id": self.enemy.enemy_id,
            "name": self.enemy.display_name,
            "hp": round(self.enemy_hp, 1),
            "max_hp": self.enemy.max_hp,
            "toughness": round(self.enemy_toughness, 1),
            "max_toughness": self.enemy.toughness,
            "broken": self.enemy_broken,
            "break_count": self.enemy_break_count,
            "element": self.enemy.element,
            "bpm": self.enemy.bpm,
            "level": 1,
        }
