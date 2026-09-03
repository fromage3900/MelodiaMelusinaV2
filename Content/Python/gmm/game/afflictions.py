"""Elemental Affliction System — status effects applied on successful skill hits.

Each element has a unique affliction that ticks over time:
  Forte  -> Burn       (DoT, reduces toughness)
  Stone  -> Petrify    (speed reduction, AV delay)
  Umbral -> Shadow     (SP drain, accuracy debuff)
  Arcane -> Arcane     (damage amp taken, ult drain)
  Radiant-> Purify     (heals enemy, clears debuffs)
  Gale   -> Gust       (AV delay, evasion up)
  Tide   -> Soak       (toughness weakness, SP gain for player)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

AFFLICTION_DEFS: dict[str, dict] = {
    "Burn": {
        "element": "Forte",
        "name": "Burn",
        "description": "Deals fire DoT each turn, reduces toughness",
        "max_stacks": 5,
        "tick_interval": 1,  # every turn
        "on_apply": lambda self, target: None,
        "on_tick": lambda self, target: self._tick_burn(target),
        "on_expire": lambda self, target: None,
    },
    "Petrify": {
        "element": "Stone",
        "name": "Petrify",
        "description": "Slows speed, delays action value",
        "max_stacks": 3,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_petrify(target),
        "on_tick": lambda self, target: self._tick_petrify(target),
        "on_expire": lambda self, target: self._expire_petrify(target),
    },
    "Shadow": {
        "element": "Umbral",
        "name": "Shadow",
        "description": "Drains SP, reduces accuracy",
        "max_stacks": 4,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_shadow(target),
        "on_tick": lambda self, target: self._tick_shadow(target),
        "on_expire": lambda self, target: self._expire_shadow(target),
    },
    "Arcane": {
        "element": "Arcane",
        "name": "Arcane",
        "description": "Increases damage taken, drains ult gauge",
        "max_stacks": 3,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_arcane(target),
        "on_tick": lambda self, target: self._tick_arcane(target),
        "on_expire": lambda self, target: self._expire_arcane(target),
    },
    "Purify": {
        "element": "Radiant",
        "name": "Purify",
        "description": "Heals enemy, clears negative effects",
        "max_stacks": 2,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_purify(target),
        "on_tick": lambda self, target: self._tick_purify(target),
        "on_expire": lambda self, target: None,
    },
    "Gust": {
        "element": "Gale",
        "name": "Gust",
        "description": "Delays action value, grants evasion",
        "max_stacks": 3,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_gust(target),
        "on_tick": lambda self, target: self._tick_gust(target),
        "on_expire": lambda self, target: self._expire_gust(target),
    },
    "Soak": {
        "element": "Tide",
        "name": "Soak",
        "description": "Reduces toughness, grants player SP",
        "max_stacks": 4,
        "tick_interval": 1,
        "on_apply": lambda self, target: self._apply_soak(target),
        "on_tick": lambda self, target: self._tick_soak(target),
        "on_expire": lambda self, target: self._expire_soak(target),
    },
}

ELEMENT_TO_AFFLICTION = {
    "Forte": "Burn",
    "Stone": "Petrify",
    "Umbral": "Shadow",
    "Arcane": "Arcane",
    "Radiant": "Purify",
    "Gale": "Gust",
    "Tide": "Soak",
}


@dataclass
class AfflictionInstance:
    name: str
    element: str
    stacks: int = 1
    turns_remaining: int = 3
    max_stacks: int = 5
    source_element: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "element": self.element,
            "stacks": self.stacks,
            "turns_remaining": self.turns_remaining,
            "max_stacks": self.max_stacks,
            "source_element": self.source_element,
        }


def apply_affliction(current_afflictions: list[dict], element: str, max_stacks: Optional[int] = None) -> Optional[dict]:
    """Apply or refresh an affliction from an element. Returns the new affliction dict if applied."""
    aff_name = ELEMENT_TO_AFFLICTION.get(element)
    if not aff_name:
        return None

    defn = AFFLICTION_DEFS.get(aff_name)
    if not defn:
        return None

    max_stk = max_stacks or defn.get("max_stacks", 5)

    # Check if already exists
    for aff in current_afflictions:
        if aff["name"] == aff_name:
            if aff["stacks"] < max_stk:
                aff["stacks"] += 1
                aff["turns_remaining"] = max(aff["turns_remaining"], 3)
            else:
                aff["turns_remaining"] = max(aff["turns_remaining"], 3)
            return aff

    # New affliction
    new_aff = {
        "name": aff_name,
        "element": element,
        "stacks": 1,
        "turns_remaining": 3,
        "max_stacks": max_stk,
        "source_element": element,
    }
    current_afflictions.append(new_aff)
    return new_aff


def tick_afflictions(afflictions: list[dict], battle_mgr=None) -> list[str]:
    """Tick all afflictions, return list of events."""
    events = []
    if not afflictions:
        return events

    to_remove = []
    for i, aff in enumerate(afflictions):
        aff["turns_remaining"] -= 1

        # On_tick effect
        defn = AFFLICTION_DEFS.get(aff["name"])
        if defn and "on_tick" in defn:
            # The tick effect would be handled by battle manager
            pass

        if aff["turns_remaining"] <= 0:
            to_remove.append(i)

    # Remove expired
    for i in reversed(to_remove):
        expired = afflictions.pop(i)
        defn = AFFLICTION_DEFS.get(expired["name"])
        if defn and "on_expire" in defn:
            pass  # Handled by battle manager

    return events


def get_affliction_def(name: str) -> dict:
    return AFFLICTION_DEFS.get(name, {})


def clear_afflictions(afflictions: list[dict]) -> None:
    afflictions.clear()