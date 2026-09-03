"""Deterministic no-editor songcraft smoke for the Melodia combat slice."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from gmm.game.battle_manager import (
    MelodiaBattleManager,
    PHASE_AWAITING,
    PHASE_ENEMY,
    PHASE_VICTORY,
    PHASE_NONE,
)


def _finish_enemy_if_needed(mgr: MelodiaBattleManager) -> None:
    if mgr.phase == PHASE_ENEMY:
        mgr.enemy_turn()


def _skill_step(mgr: MelodiaBattleManager, skill_id: str, input_ms: float) -> dict:
    if mgr.phase == PHASE_ENEMY:
        mgr.enemy_turn()
    if mgr.phase != PHASE_AWAITING:
        raise RuntimeError(f"Expected player command phase, got {mgr.phase}")

    submitted = mgr.player_command("skill", skill_id=skill_id)
    if not submitted.get("ok"):
        raise RuntimeError(submitted.get("error", f"Failed to submit {skill_id}"))
    resolved = mgr.resolve_rhythm(input_ms)
    if not resolved.get("ok"):
        raise RuntimeError(resolved.get("error", f"Failed to resolve {skill_id}"))
    return {
        "skill_id": skill_id,
        "grade": resolved["grade"],
        "phase": resolved["phase"],
        "damage": resolved["damage"],
        "enemy_hp": resolved["enemy_hp"],
        "enemy_toughness": resolved["enemy_toughness"],
        "enemy_broken": resolved["enemy_broken"],
        "songcraft": resolved.get("songcraft", {}),
        "player": mgr.get_state()["player"],
        "player_av": mgr.player_av,
        "enemy_av": mgr.enemy_av,
        "modifiers": mgr.modifiers.snapshot(),
    }


def _basic_step(mgr: MelodiaBattleManager, input_ms: float) -> dict:
    if mgr.phase == PHASE_ENEMY:
        mgr.enemy_turn()
    submitted = mgr.player_command("basic_attack")
    if not submitted.get("ok"):
        raise RuntimeError(submitted.get("error", "Failed to submit Basic"))
    resolved = mgr.resolve_rhythm(input_ms)
    if not resolved.get("ok"):
        raise RuntimeError(resolved.get("error", "Failed to resolve Basic"))
    return {
        "skill_id": "Basic",
        "grade": resolved["grade"],
        "phase": resolved["phase"],
        "damage": resolved["damage"],
        "enemy_hp": resolved["enemy_hp"],
        "enemy_toughness": resolved["enemy_toughness"],
        "player": mgr.get_state()["player"],
    }


def run_songcraft_smoke(seed: int = 20260710) -> dict:
    random.seed(seed)
    timeline: list[dict] = []

    opener = MelodiaBattleManager()
    opener.start_encounter("CrystalShard")
    timeline.append(_skill_step(opener, "StarlitPing", 20.0))

    breaker = MelodiaBattleManager()
    breaker.start_encounter("CrystalShard")
    breaker.battle_sp = 5.0
    before_enemy_av = breaker.enemy_av
    timeline.append(_skill_step(breaker, "TidalWave", 20.0))

    tempo = MelodiaBattleManager()
    tempo.start_encounter("CrystalShard")
    timeline.append(_skill_step(tempo, "GustStaccato", 20.0))
    speed_after_haste = tempo.modifiers.evaluate("speed", tempo.player.speed)

    guard = MelodiaBattleManager()
    guard.start_encounter("CrystalShard")
    timeline.append(_skill_step(guard, "StoneWall", 20.0))
    _finish_enemy_if_needed(guard)

    sustain = MelodiaBattleManager()
    sustain.start_encounter("StoneGolem")
    sustain.battle_hp = 50.0
    sustain.battle_sp = 20.0
    timeline.append(_skill_step(sustain, "TidalMend", 20.0))

    loop = MelodiaBattleManager()
    loop.start_encounter("CrystalShard")
    loop_timeline = [_basic_step(loop, 20.0)]
    while loop.phase not in (PHASE_VICTORY, PHASE_NONE) and len(loop_timeline) < 8:
        if loop.phase == PHASE_ENEMY:
            loop.enemy_turn()
        if loop.phase == PHASE_AWAITING:
            loop.battle_sp = max(loop.battle_sp, 4.0)
            loop_timeline.append(_skill_step(loop, "TidalWave", 20.0))
    finalized = False
    if loop.phase == PHASE_VICTORY:
        finalized = loop.end_encounter()["phase"] == PHASE_NONE

    by_skill = {entry["skill_id"]: entry for entry in timeline}
    checks = {
        "opener_rewards_perfect": (
            by_skill["StarlitPing"]["songcraft"]["sp_gain"] >= 1
            and by_skill["StarlitPing"]["songcraft"]["ult_bonus"] > 0
            and "Crescendo_Minor" in by_skill["StarlitPing"]["songcraft"]["modifiers"]
        ),
        "breaker_breaks_and_delays": (
            by_skill["TidalWave"]["enemy_broken"]
            and by_skill["TidalWave"]["songcraft"]["bonus_damage"] > 0
            and by_skill["TidalWave"]["enemy_av"] > before_enemy_av
        ),
        "tempo_hastes_player": speed_after_haste > tempo.player.speed,
        "guard_reduces_next_hit": guard.total_damage_taken < 3.0,
        "sustain_heals": by_skill["TidalMend"]["player"]["hp"] > 50.0,
        "loop_finalizes": finalized,
    }

    return {
        "ok": all(checks.values()),
        "seed": seed,
        "checks": checks,
        "timeline": timeline,
        "loop": loop_timeline,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Melodia songcraft smoke checks.")
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--json-out", default="", help="Optional JSON report path.")
    args = parser.parse_args()

    report = run_songcraft_smoke(seed=args.seed)
    text = json.dumps(report, indent=2)
    print(text)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
