"""Room Modifiers Extension — generated MelodySlime room modifiers.

This module provides the generated room modifiers (blessing/curse pairs) that extend
the roguelike system. These are loaded from DT_MelodySlime_RoomMods.json at runtime.

Each modifier is a blessing that references existing effect types in the roguelike system.
"""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# Generated room modifiers - blessing/curse pairs
ROOM_MODIFIERS: dict[str, dict] = {}  # Populated from data table


def load_room_modifiers() -> dict[str, dict]:
    """Load room modifiers from the generated data table."""
    global ROOM_MODIFIERS
    path = Path("Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        ROOM_MODIFIERS = data.get("Rows", {})
    return ROOM_MODIFIERS


def get_room_modifier(mod_id: str) -> Optional[dict]:
    """Get a room modifier by ID."""
    if not ROOM_MODIFIERS:
        load_room_modifiers()
    return ROOM_MODIFIERS.get(mod_id)


def apply_room_modifier_to_room(room_template: dict, mod_id: str) -> dict:
    """Apply a room modifier to a room template.
    
    Returns updated room template with modifier effects.
    """
    mod = get_room_modifier(mod_id)
    if not mod:
        return room_template
    
    # The blessing applies to the player entering the room
    # The curse is a potential negative effect
    return {
        **room_template,
        "room_modifier_id": mod_id,
        "blessing": mod.get("display_name", ""),
        "curse": mod.get("curse", ""),
    }


def summarize_modifiers() -> dict:
    """Get summary of available room modifiers."""
    if not ROOM_MODIFIERS:
        load_room_modifiers()
    
    return {
        "count": len(ROOM_MODIFIERS),
        "modifier_ids": list(ROOM_MODIFIERS.keys()),
    }


# Auto-load on import
load_room_modifiers()