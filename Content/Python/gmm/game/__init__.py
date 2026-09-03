"""Melodia Game Runtime — data registry, rhythm clock, player state, battle manager.

Provides pure-Python game runtime components that mirror the planned C++
kernel, enabling playable gameplay without compiling MelodiaCore.

Components:
    data_registry      — UDataTable generator for config-driven enemies, skills, stats
    rhythm_clock       — BPM beat clock with timing windows and note resolution
    player_state       — Stats, XP/leveling, inventory, equipment, save/load
    battle_manager     — Full rhythm battle state machine tying all systems together
    config             — Extracted tunable constants (GAME_CFG)
    save_manager       — Save/load directory management with auto-save
    audio_engine       — winsound-based beep feedback for rhythm
    equipment_catalog  — 24 starter equipment pieces across 5 slots
"""
from __future__ import annotations

from gmm.game.data_registry import MelodiaDataRegistry
from gmm.game.rhythm_clock import MelodiaRhythmClock
from gmm.game.player_state import MelodiaPlayerState
from gmm.game.battle_manager import MelodiaBattleManager
from gmm.game.elements import ELEMENT_CYCLE, element_multiplier, element_summary
from gmm.game.toughness import apply_toughness_damage, enemy_damage_multiplier, toughness_damage
from gmm.game.modifiers import ModifierStack, modifier_registry_summary
from gmm.game.songcraft_effects import get_skill_effect, songcraft_effect_summary
from gmm.game.config import GameConfig, GAME_CFG
from gmm.game.save_manager import SaveManager
from gmm.game.audio_engine import AudioEngine
from gmm.game.equipment_catalog import get_equipment, list_equipment, starter_kit, catalog_summary
from gmm.game.jrpg_bridge import bridge_summary, melodia_phase_label, template_action_to_melodia

# Re-export the pure-Python battle harness for UI testing
from gmm.melodia.battle import BattleTestHarness
