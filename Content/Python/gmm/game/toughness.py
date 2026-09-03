"""Toughness and break helpers backed by generated Melodia rules."""
from __future__ import annotations

from dataclasses import dataclass

from gmm.game.rules_generated import RULES


_TOUGHNESS_RULES = RULES["toughness"]


@dataclass(frozen=True)
class ToughnessResult:
    current: float
    max_value: float
    damage: float
    was_broken: bool
    is_broken: bool
    broke_now: bool


def toughness_damage(raw_damage: float) -> float:
    return max(0.0, raw_damage) * float(_TOUGHNESS_RULES["reduction"])


def apply_toughness_damage(current: float, max_value: float, raw_damage: float) -> ToughnessResult:
    safe_max = max(1.0, max_value)
    previous = max(0.0, min(current, safe_max))
    was_broken = previous <= 0.0
    amount = toughness_damage(raw_damage)
    new_value = max(0.0, min(previous - amount, safe_max))
    is_broken = new_value <= 0.0
    return ToughnessResult(
        current=new_value,
        max_value=safe_max,
        damage=amount,
        was_broken=was_broken,
        is_broken=is_broken,
        broke_now=is_broken and not was_broken,
    )


def enemy_damage_multiplier(is_broken: bool) -> float:
    if is_broken:
        return float(_TOUGHNESS_RULES["broken_enemy_damage_mult"])
    return 1.0
