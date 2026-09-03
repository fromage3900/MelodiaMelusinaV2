"""Combo Milestone Rewards — bonuses at 5, 10, 15, 20+ combo.

Rewards scale with combo depth and provide:
  - HP healing (percentage of max HP)
  - SP gain (shared pool)
  - Ultimate gauge gain
  - Damage bonus for next hit
  - Affliction cleansing (at 20+)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gmm.game.config import GAME_CFG


@dataclass
class ComboReward:
    combo: int
    heal_pct: float = 0.0
    sp_gain: int = 0
    ult_gain: int = 0
    bonus_dmg: float = 0.0
    clean_afflictions: bool = False
    description: str = ""


COMBO_MILESTONES = {
    5:  ComboReward(5,  heal_pct=0.10, sp_gain=5,  ult_gain=5,  description="Spark of Rhythm"),
    10: ComboReward(10, heal_pct=0.20, sp_gain=10, ult_gain=15, bonus_dmg=0.5, description="Crescendo Surge"),
    15: ComboReward(15, heal_pct=0.30, sp_gain=15, ult_gain=25, bonus_dmg=1.0, description="Harmony Flow"),
    20: ComboReward(20, heal_pct=0.50, sp_gain=25, ult_gain=40, bonus_dmg=2.0, clean_afflictions=True, description="Grandmaster Finale"),
}


def check_combo_milestones(combo: int, prev_combo: int) -> list[ComboReward]:
    """Check if combo reached a new milestone. Returns list of rewards triggered."""
    rewards = []
    for milestone in sorted(COMBO_MILESTONES.keys()):
        if prev_combo < milestone <= combo:
            rewards.append(COMBO_MILESTONES[milestone])
    return rewards


def apply_combo_rewards(rewards: list[ComboReward], battle_mgr) -> list[dict]:
    """Apply combo rewards to battle manager. Returns list of events."""
    events = []
    for reward in rewards:
        events.append({
            "type": "combo_milestone",
            "combo": reward.combo,
            "description": reward.description,
            "reward": {
                "heal_pct": reward.heal_pct,
                "sp_gain": reward.sp_gain,
                "ult_gain": reward.ult_gain,
                "bonus_dmg": reward.bonus_dmg,
                "clean_afflictions": reward.clean_afflictions,
            }
        })

        # Apply heal
        if reward.heal_pct > 0:
            heal_amt = battle_mgr.player.max_hp * reward.heal_pct
            battle_mgr.battle_hp = min(battle_mgr.player.max_hp, battle_mgr.battle_hp + heal_amt)
            events.append({"type": "heal", "amount": round(heal_amt, 1)})

        # Apply SP gain
        if reward.sp_gain > 0:
            battle_mgr.battle_sp = min(GAME_CFG.shared_sp_max, battle_mgr.battle_sp + reward.sp_gain)
            events.append({"type": "sp_gain", "amount": reward.sp_gain})

        # Apply ult gain
        if reward.ult_gain > 0:
            battle_mgr.battle_ult = min(GAME_CFG.ult_max, battle_mgr.battle_ult + reward.ult_gain)
            events.append({"type": "ult_gain", "amount": reward.ult_gain})

        # Clean afflictions (enemy)
        if reward.clean_afflictions and hasattr(battle_mgr, 'enemy_afflictions'):
            battle_mgr.enemy_afflictions = []
            events.append({"type": "afflictions_cleared"})

    return events


def get_combo_damage_bonus(combo: int) -> float:
    """Get the damage bonus from combo milestones."""
    bonus = 0.0
    for milestone in sorted(COMBO_MILESTONES.keys()):
        if combo >= milestone:
            bonus += COMBO_MILESTONES[milestone].bonus_dmg
    return bonus