"""Generated-rule-backed songcraft skill effects.

These effects are intentionally small and declarative: the battle simulator
uses them to give individual songs tactical texture without hardcoding skill
IDs throughout combat flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from gmm.game.rules_generated import RULES


@dataclass(frozen=True)
class SongcraftSkillEffect:
    skill_id: str
    tags: tuple[str, ...] = ()
    toughness_scalar: float = 1.0
    bonus_damage_on_break: float = 0.0
    enemy_delay_on_break_av_fraction: float = 0.0
    enemy_delay_on_hit_av_fraction: float = 0.0
    heal_on_hit_scalar: float = 0.0
    ult_gain_bonus_on_perfect: float = 0.0
    sp_gain_on_perfect: int = 0
    modifiers_on_hit: tuple[str, ...] = field(default_factory=tuple)
    modifiers_on_perfect: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_rule(cls, rule: dict) -> "SongcraftSkillEffect":
        return cls(
            skill_id=str(rule["skill_id"]),
            tags=tuple(str(tag) for tag in rule.get("tags", ())),
            toughness_scalar=float(rule.get("toughness_scalar", 1.0)),
            bonus_damage_on_break=float(rule.get("bonus_damage_on_break", 0.0)),
            enemy_delay_on_break_av_fraction=float(rule.get("enemy_delay_on_break_av_fraction", 0.0)),
            enemy_delay_on_hit_av_fraction=float(rule.get("enemy_delay_on_hit_av_fraction", 0.0)),
            heal_on_hit_scalar=float(rule.get("heal_on_hit_scalar", 0.0)),
            ult_gain_bonus_on_perfect=float(rule.get("ult_gain_bonus_on_perfect", 0.0)),
            sp_gain_on_perfect=int(rule.get("sp_gain_on_perfect", 0)),
            modifiers_on_hit=tuple(str(mid) for mid in rule.get("modifiers_on_hit", ())),
            modifiers_on_perfect=tuple(str(mid) for mid in rule.get("modifiers_on_perfect", ())),
        )


_EFFECTS = {
    effect.skill_id: effect
    for effect in (
        SongcraftSkillEffect.from_rule(rule)
        for rule in RULES.get("songcraft", {}).get("skill_effects", ())
    )
}


def get_skill_effect(skill_id: str) -> SongcraftSkillEffect:
    return _EFFECTS.get(skill_id, SongcraftSkillEffect(skill_id=skill_id))


def songcraft_effect_summary() -> dict:
    return {
        "count": len(_EFFECTS),
        "skill_ids": list(_EFFECTS.keys()),
        "tags": sorted({tag for effect in _EFFECTS.values() for tag in effect.tags}),
    }
