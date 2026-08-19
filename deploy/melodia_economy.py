"""
Melodia Global Economy — P0 gameplay economy for rhythm-combat skills.

4 global float resources: healing, mana, utility, grief (all 0.0–100.0)
Grief modifier: higher grief => more mana gain, less healing gain per rhythm hit.
All functions follow an immutable pattern: return (new_economy, result_dict).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class MelodiaGlobalEconomy:
    healing: float = 0.0
    mana: float = 0.0
    utility: float = 0.0
    grief: float = 0.0


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def _clamp_economy(eco: MelodiaGlobalEconomy) -> MelodiaGlobalEconomy:
    return replace(
        eco,
        healing=_clamp(eco.healing),
        mana=_clamp(eco.mana),
        utility=_clamp(eco.utility),
        grief=_clamp(eco.grief),
    )


def on_rhythm_hit(economy: MelodiaGlobalEconomy, accuracy: float) -> tuple[MelodiaGlobalEconomy, dict[str, Any]]:
    """Apply a rhythm hit with accuracy 0.0–1.0, modified by current grief level.

    Grief boosts mana gain but softly penalizes healing gain.
    Grief dissipates slightly on each successful hit.
    """
    acc = max(0.0, min(1.0, accuracy))
    mana_gain = acc * (1 + economy.grief / 100)
    healing_gain = acc * (1 - economy.grief / 200)
    utility_gain = acc * 0.3
    grief_delta = -0.5 * acc

    new_eco = _clamp_economy(replace(
        economy,
        mana=economy.mana + mana_gain,
        healing=economy.healing + healing_gain,
        utility=economy.utility + utility_gain,
        grief=economy.grief + grief_delta,
    ))

    result: dict[str, Any] = {
        "event": "rhythm_hit",
        "accuracy": acc,
        "mana_gain": round(mana_gain, 4),
        "healing_gain": round(healing_gain, 4),
        "utility_gain": round(utility_gain, 4),
        "grief_delta": round(grief_delta, 4),
        "new_state": _economy_dict(new_eco),
    }
    return new_eco, result


def cast_healing_song(economy: MelodiaGlobalEconomy, tier: int = 1) -> tuple[MelodiaGlobalEconomy, dict[str, Any]]:
    """Consume healing (10*tier), grant 5 mana bonus."""
    cost = 10.0 * tier
    mana_bonus = 5.0
    if economy.healing < cost:
        return economy, {
            "skill": "healing_song",
            "tier": tier,
            "success": False,
            "reason": "insufficient healing",
            "required": cost,
            "available": economy.healing,
            "mana_gain": 0.0,
            "new_state": _economy_dict(economy),
        }

    new_eco = _clamp_economy(replace(
        economy,
        healing=economy.healing - cost,
        mana=economy.mana + mana_bonus,
    ))

    result: dict[str, Any] = {
        "skill": "healing_song",
        "tier": tier,
        "success": True,
        "healing_consumed": cost,
        "mana_gain": mana_bonus,
        "heal_applied": cost,
        "new_state": _economy_dict(new_eco),
    }
    return new_eco, result


def cast_mana_song(economy: MelodiaGlobalEconomy, tier: int = 1) -> tuple[MelodiaGlobalEconomy, dict[str, Any]]:
    """Consume mana (10*tier), reduce grief by 10*tier."""
    cost = 10.0 * tier
    grief_reduction = 10.0 * tier
    if economy.mana < cost:
        return economy, {
            "skill": "mana_song",
            "tier": tier,
            "success": False,
            "reason": "insufficient mana",
            "required": cost,
            "available": economy.mana,
            "grief_reduction": 0.0,
            "new_state": _economy_dict(economy),
        }

    new_eco = _clamp_economy(replace(
        economy,
        mana=economy.mana - cost,
        grief=economy.grief - grief_reduction,
    ))

    result: dict[str, Any] = {
        "skill": "mana_song",
        "tier": tier,
        "success": True,
        "mana_consumed": cost,
        "grief_reduction": grief_reduction,
        "new_state": _economy_dict(new_eco),
    }
    return new_eco, result


def cast_utility_debuff(economy: MelodiaGlobalEconomy, tier: int = 1) -> tuple[MelodiaGlobalEconomy, dict[str, Any]]:
    """Consume utility (8*tier), apply mana_drain debuff (enemy loses 15*tier mana)."""
    cost = 8.0 * tier
    enemy_mana_drain = 15.0 * tier
    if economy.utility < cost:
        return economy, {
            "skill": "utility_debuff",
            "tier": tier,
            "success": False,
            "reason": "insufficient utility",
            "required": cost,
            "available": economy.utility,
        }

    new_eco = _clamp_economy(replace(
        economy,
        utility=economy.utility - cost,
    ))

    result: dict[str, Any] = {
        "skill": "utility_debuff",
        "tier": tier,
        "success": True,
        "utility_consumed": cost,
        "debuff": "mana_drain",
        "enemy_mana_drained": enemy_mana_drain,
        "new_state": _economy_dict(new_eco),
    }
    return new_eco, result


def activate_grief_hook(economy: MelodiaGlobalEconomy, dungeon_id: str) -> tuple[MelodiaGlobalEconomy, dict[str, Any]]:
    """Set grief to 30 on dungeon entry — the grief hook activation."""
    new_eco = _clamp_economy(replace(economy, grief=30.0))
    result: dict[str, Any] = {
        "event": "grief_hook_activated",
        "dungeon_id": dungeon_id,
        "grief_set_to": 30.0,
        "new_state": _economy_dict(new_eco),
    }
    return new_eco, result


_cast_history: set[str] = set()


def record_cast(skill_id: str) -> None:
    _cast_history.add(skill_id)


def get_cast_history() -> set[str]:
    return set(_cast_history)


def reset_cast_history() -> None:
    _cast_history.clear()


def _economy_dict(eco: MelodiaGlobalEconomy) -> dict[str, float]:
    return {
        "healing": round(eco.healing, 4),
        "mana": round(eco.mana, 4),
        "utility": round(eco.utility, 4),
        "grief": round(eco.grief, 4),
    }
