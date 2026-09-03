"""Game Configuration — extracted constants for the Melodia rhythm battle game.

Centralizes all tunable parameters so `battle_manager.py`, `rhythm_clock.py`,
and `player_state.py` read from one source rather than hardcoding values.

Usage:
    from gmm.game.config import GAME_CFG
    bpm = GAME_CFG.default_bpm
    window = GAME_CFG.timing_windows["perfect"]
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict


# Single source of truth: Plugins/MelodiaCore/Rules/melodia_rules.json,
# mirrored into rules_generated.py by Tools/generate_melodia_rules.py.
# Fallback literals below match rules v1 and exist only for import safety.
try:
    from gmm.game.rules_generated import RULES as _RULES
except Exception:  # pragma: no cover - generated file missing
    _RULES = {}

_R = _RULES.get("rhythm", {})
_W = _R.get("windows_ms", {})
_G = _R.get("grade_multipliers", {})
_T = _RULES.get("turn_economy", {})
_S = _RULES.get("songcraft", {})


@dataclass
class TimingWindows:
    perfect: float = _W.get("perfect", 90.0)   # ms
    great: float = _W.get("great", 120.0)      # ms
    good: float = _W.get("good", 160.0)        # ms


@dataclass
class GradeMultipliers:
    # NOTE: the old hand-typed values here had drifted from the C++ runtime
    # (great 1.2 vs 1.25, miss 0.0 vs 0.4) — exactly why the shared JSON exists.
    perfect: float = _G.get("perfect", 1.5)
    great: float = _G.get("great", 1.25)
    good: float = _G.get("good", 1.0)
    miss: float = _G.get("miss", 0.4)


@dataclass
class GameConfig:
    """All tunable game parameters in one place."""

    # Rhythm
    default_bpm: float = 120.0
    timing_windows: TimingWindows = field(default_factory=TimingWindows)
    grade_multipliers: GradeMultipliers = field(default_factory=GradeMultipliers)

    # Battle
    base_av: float = float(_T.get("base_av", 10000))
    shared_sp_start: int = _T.get("shared_sp_start", 3)
    shared_sp_max: int = _T.get("shared_sp_max", 5)
    basic_sp_gain: int = 1
    crescendo_gain: dict[str, float] = field(default_factory=lambda: dict(
        _S.get("crescendo_gain", {"perfect": 12, "great": 8, "good": 5, "miss": 0})
    ))
    toughness_reduction: float = 0.4        # fraction of damage applied to toughness
    toughness_damage_reduction: float = 0.5 # enemy damage mult when toughness broken
    defense_mitigation: float = 0.5         # defense * this = flat damage reduction
    flee_base_chance: float = 0.5
    flee_speed_factor: float = 0.005

    # Ultimate
    ult_gain_per_hit: float = 5.0
    ult_gain_perfect: float = 10.0
    ult_max: float = 100.0
    ultimate_damage_mult: float = 3.0

    # XP / Leveling
    base_xp_to_next: int = 100
    xp_mult: float = 1.5
    combo_xp_bonus: int = 5

    # HP/SP growth per level
    hp_gain_per_level: float = 8.0
    hp_gain_per_level_scale: float = 2.0
    mp_gain_per_level: float = 5.0
    mp_gain_per_level_scale: float = 1.0
    sp_gain_per_level: float = 5.0
    stat_gain_per_level: float = 1.0
    stat_gain_per_level_scale: float = 0.5

    # Defeat penalty
    defeat_hp_recovery: float = 0.5
    defeat_sp_recovery: float = 0.5

    # Save
    save_dir_name: str = "saves"
    save_slot_name: str = "melodia_save.json"
    auto_save_on_victory: bool = True
    auto_save_on_defeat: bool = False

    # Display
    show_bpm_on_start: bool = True
    show_grade_ascii: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timing_windows"] = asdict(self.timing_windows)
        d["grade_multipliers"] = asdict(self.grade_multipliers)
        return d

    def save_to_file(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    @classmethod
    def load_from_file(cls, path: str) -> "GameConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tw = TimingWindows(**data.pop("timing_windows", {}))
        gm = GradeMultipliers(**data.pop("grade_multipliers", {}))
        return cls(timing_windows=tw, grade_multipliers=gm, **data)


GAME_CFG = GameConfig()
