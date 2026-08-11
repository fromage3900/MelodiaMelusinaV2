"""Deterministic combat pacing lab for Melodia.

This module is deliberately read-only with respect to game rules.  It drives the
existing GMM battle simulator and reports whether encounters produce a readable
arc: survive, break, spend SP, build crescendo, and finish before repetition.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from gmm.game.battle_manager import (
    MelodiaBattleManager,
    PHASE_AWAITING,
    PHASE_DEFEAT,
    PHASE_ENEMY,
    PHASE_VICTORY,
)
from gmm.game.config import GAME_CFG
from gmm.game.elements import element_multiplier
from gmm.game.player_state import MelodiaPlayerState


PROFILES = {
    "newcomer": (210.0, 145.0, 80.0, 190.0, 130.0),
    "learning": (145.0, 110.0, 75.0, 130.0, 95.0),
    "confident": (75.0, 45.0, 100.0, 60.0, 30.0),
}


@dataclass(frozen=True)
class FeelRun:
    enemy: str
    profile: str
    outcome: str
    turns: int
    player_hp_pct: float
    basic_count: int
    skill_count: int
    ultimate_count: int
    sp_spent: float
    ultimate_pct: float
    first_skill_turn: int | None
    first_ultimate_turn: int | None
    first_break_turn: int | None
    breaks: int
    grades: dict[str, int]
    damage_dealt: float
    damage_taken: float


def simulate(enemy_id: str, profile: str, *, seed: int = 1337, max_turns: int = 20,
             player: MelodiaPlayerState | None = None, persist: bool = False) -> FeelRun:
    """Run one reproducible player profile against one enemy."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")

    random.seed(seed)
    mgr = MelodiaBattleManager(player=player)
    start = mgr.start_encounter(enemy_id)
    if not start.get("ok"):
        raise ValueError(start.get("error", enemy_id))

    errors = PROFILES[profile]
    first_break_turn = None
    first_skill_turn = None
    first_ultimate_turn = None
    basic_count = 0
    skill_count = 0
    ultimate_count = 0
    sp_spent = 0.0

    # Keep onboarding simulations to readable early-game recipes. Choose the
    # strongest affordable option for the current enemy rather than hardcoding
    # a single element into every matchup.
    early_skills = [skill for skill in mgr.registry.skills.values() if skill.mechanic_level <= 6]

    def choose_skill():
        affordable = [skill for skill in early_skills if skill.sp_cost <= mgr.battle_sp]
        if not affordable:
            return None
        return max(
            affordable,
            key=lambda skill: (
                (skill.base_damage + mgr.player.min_magical_attack * 0.5)
                * element_multiplier(skill.element, mgr.enemy.element)
                / max(1, skill.sp_cost)
            ),
        )

    while mgr.phase not in (PHASE_VICTORY, PHASE_DEFEAT) and mgr.turn_count < max_turns:
        if mgr.phase == PHASE_AWAITING:
            if mgr.battle_ult >= GAME_CFG.ult_max:
                ultimate_count += 1
                if first_ultimate_turn is None:
                    first_ultimate_turn = mgr.turn_count + 1
                command = mgr.player_command("ultimate")
                if not command.get("ok"):
                    raise RuntimeError(command.get("error", "ultimate failed"))
                continue

            skill = None if mgr.turn_count == 0 else choose_skill()
            # Preserve a visible Basic -> Skill rhythm: never spend on two
            # consecutive player turns, even when SP is available.
            previous_was_skill = bool(len(mgr.history) >= 3
                                      and mgr.history[-1].get("event") == "enemy_attack"
                                      and mgr.history[-2].get("event") == "rhythm_resolve"
                                      and mgr.history[-3].get("event") == "player_command"
                                      and mgr.history[-3].get("command") == "skill")
            if skill is not None and not previous_was_skill:
                skill_count += 1
                sp_spent += float(skill.sp_cost)
                if first_skill_turn is None:
                    first_skill_turn = mgr.turn_count + 1
                command = mgr.player_command("skill", skill_id=skill.skill_id)
            else:
                basic_count += 1
                command = mgr.player_command("basic_attack")
            if not command.get("ok"):
                raise RuntimeError(command.get("error", "command failed"))
            result = mgr.resolve_rhythm(errors[(mgr.turn_count - 1) % len(errors)])
            if result.get("enemy_broke_now") and first_break_turn is None:
                first_break_turn = mgr.turn_count
        elif mgr.phase == PHASE_ENEMY:
            mgr.enemy_turn()
        else:
            raise RuntimeError(f"Unexpected phase: {mgr.phase}")

    state = mgr.get_state()
    max_hp = max(1.0, float(state["player"]["max_hp"]))
    run = FeelRun(
        enemy=enemy_id,
        profile=profile,
        outcome=mgr.phase,
        turns=mgr.turn_count,
        player_hp_pct=round(100.0 * mgr.battle_hp / max_hp, 1),
        basic_count=basic_count,
        skill_count=skill_count,
        ultimate_count=ultimate_count,
        sp_spent=round(sp_spent, 1),
        ultimate_pct=round(100.0 * mgr.battle_ult / 100.0, 1),
        first_skill_turn=first_skill_turn,
        first_ultimate_turn=first_ultimate_turn,
        first_break_turn=first_break_turn,
        breaks=mgr.enemy_break_count,
        grades=dict(mgr.grades),
        damage_dealt=round(mgr.total_damage_dealt, 1),
        damage_taken=round(mgr.total_damage_taken, 1),
    )
    if persist and mgr.phase in (PHASE_VICTORY, PHASE_DEFEAT):
        mgr.end_encounter()
    return run


def simulate_campaign(profile: str, *, seed: int = 1337) -> dict:
    """Run the onboarding sequence with persistent HP/SP/Crescendo state."""
    player = MelodiaPlayerState()
    order = ("CrystalShard", "SakuraPhantom", "StoneGolem")
    runs = []
    for index, enemy in enumerate(order):
        run = simulate(enemy, profile, seed=seed + index, player=player, persist=True)
        runs.append(run)
        if run.outcome != PHASE_VICTORY:
            break
    return {
        "profile": profile,
        "completed": len(runs) == len(order) and all(run.outcome == PHASE_VICTORY for run in runs),
        "ultimate_used": any(run.ultimate_count > 0 for run in runs),
        "ultimate_encounter": next((run.enemy for run in runs if run.ultimate_count > 0), None),
        "final_crescendo": round(player.ult_gauge, 1),
        "runs": [asdict(run) for run in runs],
    }


def run_lab(*, seed: int = 1337) -> dict:
    enemies = ("CrystalShard", "StoneGolem", "SakuraPhantom")
    runs = [simulate(enemy, profile, seed=seed) for enemy in enemies for profile in PROFILES]
    campaigns = [simulate_campaign(profile, seed=seed) for profile in PROFILES]
    turn_bands = {
        "CrystalShard": (3, 5),
        "SakuraPhantom": (5, 8),
        "StoneGolem": (5, 10),
    }
    findings = []
    for run in runs:
        if run.outcome != PHASE_VICTORY:
            findings.append(f"{run.enemy}/{run.profile}: no victory within the run")
        low, high = turn_bands[run.enemy]
        if not low <= run.turns <= high:
            findings.append(f"{run.enemy}/{run.profile}: {run.turns} turns outside {low}-{high}")
        if run.first_break_turn is None:
            findings.append(f"{run.enemy}/{run.profile}: toughness never creates a payoff")
        if run.skill_count <= 0 or run.basic_count <= 0:
            findings.append(f"{run.enemy}/{run.profile}: skill resource never enters the loop")
    for campaign in campaigns:
        if not campaign["completed"]:
            findings.append(f"campaign/{campaign['profile']}: onboarding sequence not completed")
        if not campaign["ultimate_used"] and campaign["final_crescendo"] < 80.0:
            findings.append(f"campaign/{campaign['profile']}: no Crescendo payoff or ready state")

    return {
        "seed": seed,
        "profiles": {name: list(errors) for name, errors in PROFILES.items()},
        "runs": [asdict(run) for run in runs],
        "campaigns": campaigns,
        "turn_bands": {enemy: list(band) for enemy, band in turn_bands.items()},
        "ok": not findings,
        "findings": findings,
        "note": "Thresholds are design alarms, not pass/fail tests.",
    }


def run_seed_matrix(*, start_seed: int = 100, seed_count: int = 50) -> dict:
    """Prove the target bands are stable across deterministic RNG variance."""
    reports = [run_lab(seed=seed) for seed in range(start_seed, start_seed + seed_count)]
    failures = [
        {"seed": report["seed"], "findings": report["findings"]}
        for report in reports if not report["ok"]
    ]
    return {
        "ok": not failures,
        "start_seed": start_seed,
        "seed_count": seed_count,
        "passing": seed_count - len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure deterministic Melodia combat feel.")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--seed-count", type=int, default=1,
                        help="Run a robustness matrix beginning at --seed.")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()
    report = (run_seed_matrix(start_seed=args.seed, seed_count=args.seed_count)
              if args.seed_count > 1 else run_lab(seed=args.seed))
    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
