"""JRPG template ↔ Melodia rhythm bridge — pure Python mapping layer.

Maps TurnBasedJRPGTemplate enums/structs to gmm/game runtime types.
Used by battle_manager and UE scaffold verification.
"""
from __future__ import annotations

from gmm.game.battle_manager import (
    PHASE_AWAITING,
    PHASE_DEFEAT,
    PHASE_ENEMY,
    PHASE_FLED,
    PHASE_INTRO,
    PHASE_NONE,
    PHASE_RHYTHM,
    PHASE_VICTORY,
)

# Template E_ActionType → Melodia command
ACTION_TYPE_MAP = {
    "Attack": "basic_attack",
    "Skill": "skill",
    "Item": "item",
    "Flee": "flee",
    "None": "",
    "Interact": "interact",
}

# Template E_TurnType → battle phase hint
TURN_TYPE_MAP = {
    "Player": PHASE_AWAITING,
    "Enemy": PHASE_ENEMY,
}

# Template E_BattleResult / encounter result
BATTLE_RESULT_MAP = {
    "Victory": PHASE_VICTORY,
    "Defeat": PHASE_DEFEAT,
    "Fled": PHASE_FLED,
    "None": PHASE_NONE,
}

# E_EquipmentType → player_state slot keys
EQUIPMENT_TYPE_MAP = {
    "Weapon": "weapon",
    "Armor": "armor",
    "Shield": "shield",
    "Helm": "helm",
    "Boots": "boots",
}

# Melodia battle phase → template-friendly label for UI
PHASE_UI_LABEL = {
    PHASE_NONE: "Explore",
    PHASE_INTRO: "Battle Start",
    PHASE_AWAITING: "Command",
    PHASE_RHYTHM: "Rhythm",
    PHASE_ENEMY: "Enemy Turn",
    PHASE_VICTORY: "Victory",
    PHASE_DEFEAT: "Defeat",
    PHASE_FLED: "Escaped",
}


def template_action_to_melodia(action: str) -> str:
    return ACTION_TYPE_MAP.get(action, action.lower())


def melodia_phase_label(phase: str) -> str:
    return PHASE_UI_LABEL.get(phase, phase)


def unit_stats_to_melodia(unit: dict) -> dict:
    """Convert template S_UnitStats-shaped dict to Melodia EnemyStats fields."""
    return {
        "max_hp": unit.get("maxHP", unit.get("max_hp", 100)),
        "max_mp": unit.get("maxMP", unit.get("max_mp", 50)),
        "min_attack": unit.get("minAttack", unit.get("min_attack", 5)),
        "max_attack": unit.get("maxAttack", unit.get("max_attack", 15)),
        "defense": unit.get("defense", 5),
        "speed": unit.get("speed", 80),
        "hit": unit.get("hit", 0.9),
        "min_magical_attack": unit.get("minMagicalAttack", 0),
        "max_magical_attack": unit.get("maxMagicalAttack", 0),
        "magic_defense": unit.get("magicDefense", 5),
        "action_time": unit.get("actionTime", 1.0),
    }


def bridge_summary() -> dict:
    return {
        "action_types": len(ACTION_TYPE_MAP),
        "equipment_slots": len(EQUIPMENT_TYPE_MAP),
        "battle_phases": len(PHASE_UI_LABEL),
        "template_path": "/Game/_ThirdParty/TurnBasedJRPGTemplate",
        "melodia_bridge_path": "/Game/Melodia/Bridge/JRPG",
    }
