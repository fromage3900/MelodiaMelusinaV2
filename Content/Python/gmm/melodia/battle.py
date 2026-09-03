"""Battle session interaction via MCP and direct UE Python API.

Wraps the C++ battle lifecycle (AwaitingPlayerCommand -> RhythmExecution ->
EnemyTurn -> Victory/Defeat/Fled) via Monolith MCP or direct editor API.

Also provides a test harness for spawning and driving encounters
from Python without requiring MCP or a compiled MelodiaCore plugin.
"""
from __future__ import annotations

import time
from typing import Optional

from gmm.core import MonolithClient
from gmm.melodia.enemies import get_enemy, list_enemies, MelodiaEnemyDef
from gmm.melodia.skills import get_skill, list_skills


class MelodiaBattleSession:
    """Python-side wrapper for UMelodiaBattleSession C++ class."""

    BATTLE_NAMESPACE = "melodia"

    def __init__(self, mc: Optional[MonolithClient] = None):
        self.mc = mc or MonolithClient()

    def _call(self, action: str, params: dict | None = None) -> dict:
        try:
            return self.mc.call_action(self.BATTLE_NAMESPACE, action, params or {})
        except Exception:
            return {"ok": False, "error": "MCP unreachable — MelodiaCore may not be active"}

    def start_encounter(self, enemy_id: str = "CrystalShard") -> dict:
        return self._call("start_encounter", {"enemy_id": enemy_id})

    def player_command(self, command: str = "basic_attack", skill_id: str = "") -> dict:
        params: dict = {"command": command}
        if skill_id:
            params["skill_id"] = skill_id
        return self._call("player_command", params)

    def get_phase(self) -> dict:
        return self._call("get_phase")

    def abort(self) -> dict:
        return self._call("abort_encounter")

    def verify_plugin(self) -> dict:
        """Check if MelodiaCore plugin is available without MCP."""
        result = {"plugin_loaded": False, "methods": []}
        try:
            import MelodiaCore
            result["plugin_loaded"] = True
            result["methods"] = [m for m in dir(MelodiaCore) if not m.startswith("_")]
        except ImportError:
            result["error"] = "MelodiaCore not importable — plugin may not be compiled"
        except Exception as e:
            result["error"] = str(e)
        return result


# ---------------------------------------------------------------------------
# Test Harness — works without compiled plugin or MCP
# ---------------------------------------------------------------------------

class BattleTestHarness:
    """Simulates battle state for testing UI, commands, and flow.

    Tracks a local state machine that mirrors the C++ battle phases
    so menu commands and UI can be tested without a running game.

    Phase transitions:
        None -> AwaitingPlayerCommand -> RhythmExecution -> EnemyTurn
        -> Victory | Defeat | Fled -> None
    """

    PHASES = ("None", "AwaitingPlayerCommand", "RhythmExecution",
              "EnemyTurn", "Victory", "Defeat", "Fled")

    def __init__(self):
        self.phase: str = "None"
        self.enemy: Optional[MelodiaEnemyDef] = None
        self.player_hp: float = 100.0
        self.player_sp: float = 50.0
        self.player_ult: float = 0.0
        self.enemy_hp: float = 0.0
        self.enemy_toughness: float = 0.0
        self.combo: int = 0
        self.grades: dict[str, int] = {"perfect": 0, "great": 0, "good": 0, "miss": 0}
        self.current_command: str = ""
        self.turn_count: int = 0
        self.history: list[dict] = []

    def spawn_encounter(self, enemy_id: str = "CrystalShard") -> dict:
        """Spawn a test encounter with the given enemy definition."""
        enemy = get_enemy(enemy_id)
        if not enemy:
            known = list(list_enemies())
            return {
                "ok": False,
                "error": f"Unknown enemy '{enemy_id}'. Known: {[e['enemy_id'] for e in known]}",
            }

        self.enemy = enemy
        self.enemy_hp = enemy.max_hp
        self.enemy_toughness = enemy.max_toughness
        self.phase = "AwaitingPlayerCommand"
        self.player_hp = 100.0
        self.player_sp = 50.0
        self.player_ult = 0.0
        self.combo = 0
        self.grades = {"perfect": 0, "great": 0, "good": 0, "miss": 0}
        self.current_command = ""
        self.turn_count = 0
        self.history = []

        entry = {
            "event": "encounter_start",
            "enemy_id": enemy_id,
            "enemy_name": enemy.display_name,
            "enemy_hp": self.enemy_hp,
            "enemy_toughness": self.enemy_toughness,
            "bpm": enemy.bpm,
            "element": enemy.element,
        }
        self.history.append(entry)

        return {
            "ok": True,
            "phase": self.phase,
            "enemy": enemy.to_dict(),
            "player": self._player_state(),
        }

    def issue_command(self, command: str = "basic_attack", skill_id: str = "") -> dict:
        """Issue a player command to the test harness.

        Commands: basic_attack, skill, ultimate, defend, flee.
        """
        if self.phase != "AwaitingPlayerCommand":
            return {"ok": False, "error": f"Cannot issue command in phase '{self.phase}'"}

        valid_commands = ("basic_attack", "skill", "ultimate", "defend", "flee")
        if command not in valid_commands:
            return {
                "ok": False,
                "error": f"Unknown command '{command}'. Valid: {valid_commands}",
            }

        if command == "skill" and not skill_id:
            return {"ok": False, "error": "skill_id required for 'skill' command"}

        if command == "skill":
            skill = get_skill(skill_id)
            if not skill:
                return {"ok": False, "error": f"Unknown skill '{skill_id}'"}

        self.current_command = command
        self.turn_count += 1

        entry = {
            "event": "player_command",
            "command": command,
            "skill_id": skill_id,
            "turn": self.turn_count,
        }
        self.history.append(entry)

        self.phase = "RhythmExecution"
        return {"ok": True, "phase": self.phase, "command": command, "turn": self.turn_count}

    def resolve_rhythm(self, grade: str = "perfect") -> dict:
        """Simulate rhythm resolution with a given grade.

        Grades: perfect (0.0-0.09s), great (0.09-0.12s), good (0.12-0.16s), miss.
        """
        if self.phase != "RhythmExecution":
            return {"ok": False, "error": f"Cannot resolve rhythm in phase '{self.phase}'"}

        if grade not in self.grades:
            return {"ok": False, "error": f"Invalid grade '{grade}'. Valid: {list(self.grades.keys())}"}

        self.grades[grade] += 1

        if grade == "miss":
            self.combo = 0
        else:
            self.combo += 1

        damage = 0.0
        if self.current_command == "basic_attack":
            damage = 12.0
        elif self.current_command == "skill":
            damage = 25.0
        elif self.current_command == "ultimate":
            damage = 50.0

        if grade == "perfect":
            damage *= 1.5
        elif grade == "great":
            damage *= 1.2
        elif grade == "good":
            damage *= 0.8
        elif grade == "miss":
            damage = 0.0

        toughness_dmg = damage * 0.5
        self.enemy_hp = max(0, self.enemy_hp - damage)
        self.enemy_toughness = max(0, self.enemy_toughness - toughness_dmg)
        self.player_ult = min(100, self.player_ult + 5.0)

        entry = {
            "event": "rhythm_resolve",
            "grade": grade,
            "combo": self.combo,
            "damage": damage,
            "enemy_hp_remaining": self.enemy_hp,
        }
        self.history.append(entry)

        self.current_command = ""

        if self.enemy_hp <= 0:
            self.phase = "Victory"
            self.history.append({"event": "victory", "grades": dict(self.grades)})
        else:
            self.phase = "EnemyTurn"

        return {
            "ok": True,
            "phase": self.phase,
            "grade": grade,
            "combo": self.combo,
            "damage": damage,
            "enemy_hp": self.enemy_hp,
            "enemy_toughness": self.enemy_toughness,
        }

    def enemy_attack(self) -> dict:
        """Simulate enemy turn damage."""
        if self.phase != "EnemyTurn":
            return {"ok": False, "error": f"Cannot process enemy turn in phase '{self.phase}'"}

        if not self.enemy:
            return {"ok": False, "error": "No enemy in encounter"}

        incoming = self.enemy.base_damage
        self.player_hp = max(0, self.player_hp - incoming)

        entry = {
            "event": "enemy_attack",
            "damage": incoming,
            "player_hp_remaining": self.player_hp,
        }
        self.history.append(entry)

        if self.player_hp <= 0:
            self.phase = "Defeat"
            self.history.append({"event": "defeat"})
        else:
            self.phase = "AwaitingPlayerCommand"

        return {
            "ok": True,
            "phase": self.phase,
            "damage": incoming,
            "player_hp": self.player_hp,
        }

    def poll_state(self) -> dict:
        """Return the current battle state snapshot."""
        return {
            "ok": True,
            "phase": self.phase,
            "player": self._player_state(),
            "enemy": self._enemy_state(),
            "combo": self.combo,
            "grades": dict(self.grades),
            "turn": self.turn_count,
            "command": self.current_command,
            "history_count": len(self.history),
        }

    def flee(self) -> dict:
        """Flee from the encounter."""
        if self.phase not in ("AwaitingPlayerCommand", "EnemyTurn"):
            return {"ok": False, "error": f"Cannot flee in phase '{self.phase}'"}
        self.phase = "Fled"
        self.history.append({"event": "fled"})
        return {"ok": True, "phase": self.phase}

    def end_encounter(self) -> dict:
        """Reset the test harness."""
        entry = {"event": "end_encounter", "final_grades": dict(self.grades),
                 "turns": self.turn_count}
        self.history.append(entry)
        self.phase = "None"
        self.enemy = None
        return {"ok": True, "phase": self.phase, "summary": entry}

    def _player_state(self) -> dict:
        return {
            "hp": self.player_hp,
            "max_hp": 100.0,
            "sp": self.player_sp,
            "max_sp": 100.0,
            "ult": self.player_ult,
            "max_ult": 100.0,
        }

    def _enemy_state(self) -> dict:
        if not self.enemy:
            return {}
        return {
            "id": self.enemy.enemy_id,
            "name": self.enemy.display_name,
            "hp": self.enemy_hp,
            "max_hp": self.enemy.max_hp,
            "toughness": self.enemy_toughness,
            "max_toughness": self.enemy.max_toughness,
            "element": self.enemy.element,
            "bpm": self.enemy.bpm,
        }
