"""Deterministic no-editor gameplay smoke checks for the Melodia slice.

This is intentionally small: it answers whether the current GMM simulator still
matches the vertical-slice feel targets before opening Unreal.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

from gmm.game.battle_manager import MelodiaBattleManager


@dataclass
class SmokeResult:
    label: str
    command: str
    grade: str
    damage: float
    enemy_hp: float
    enemy_toughness: float
    player_sp: float
    player_ult: float
    phase: str


def _run_single_command(
    *,
    label: str,
    command: str,
    input_ms: float,
    skill_id: str = "",
    enemy_id: str = "CrystalShard",
    seed: int = 1337,
) -> SmokeResult:
    random.seed(seed)
    mgr = MelodiaBattleManager()
    start = mgr.start_encounter(enemy_id)
    if not start.get("ok"):
        raise RuntimeError(start.get("error", "Failed to start encounter"))

    command_result = mgr.player_command(command, skill_id=skill_id)
    if not command_result.get("ok"):
        raise RuntimeError(command_result.get("error", "Failed to submit command"))

    result = mgr.resolve_rhythm(input_ms)
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Failed to resolve rhythm"))

    state = mgr.get_state()
    return SmokeResult(
        label=label,
        command=command if not skill_id else f"{command}:{skill_id}",
        grade=result["grade"],
        damage=float(result["damage"]),
        enemy_hp=float(result["enemy_hp"]),
        enemy_toughness=float(result["enemy_toughness"]),
        player_sp=float(state["player"]["sp"]),
        player_ult=float(state["player"]["ult"]),
        phase=result["phase"],
    )


def run_smoke(seed: int = 1337) -> dict:
    results = [
        _run_single_command(label="basic_miss", command="basic_attack", input_ms=300.0, seed=seed),
        _run_single_command(label="basic_good", command="basic_attack", input_ms=140.0, seed=seed),
        _run_single_command(label="basic_perfect", command="basic_attack", input_ms=20.0, seed=seed),
        _run_single_command(label="skill_perfect", command="skill", skill_id="TidalWave", input_ms=20.0, seed=seed),
    ]

    by_label = {result.label: result for result in results}
    checks = {
        "basic_damage_ordering": (
            by_label["basic_miss"].damage
            < by_label["basic_good"].damage
            < by_label["basic_perfect"].damage
        ),
        "skill_beats_basic_perfect": by_label["skill_perfect"].damage > by_label["basic_perfect"].damage,
        "skill_sp_spent": by_label["skill_perfect"].player_sp < by_label["basic_perfect"].player_sp,
        "miss_still_deals_damage": by_label["basic_miss"].damage > 0.0,
        "perfect_builds_ultimate": by_label["basic_perfect"].player_ult > by_label["basic_miss"].player_ult,
    }

    return {
        "ok": all(checks.values()),
        "seed": seed,
        "checks": checks,
        "results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Melodia gameplay smoke checks.")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--json-out", default="", help="Optional JSON report path.")
    args = parser.parse_args()

    report = run_smoke(seed=args.seed)
    text = json.dumps(report, indent=2)
    print(text)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
