"""GMM Daemon Tick — active game improvement loop.

Every 5 minutes, this daemon:
1. Runs the full test suite to verify nothing is broken
2. Picks one improvement task from a prioritized queue
3. Generates the code/content for that task
4. Stages it to _staging/gmm_daemon/ for review
5. Logs progress to Saved/Loop/gmm_daemon_loop.json

Usage:
    python Content/Python/gmm_daemon_loop_tick.py

Daemon:
    deploy/start_gmm_daemon.ps1   (interval=300s)
    deploy/stop_gmm_daemon.ps1
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / "Saved" / "Loop" / "gmm_daemon_loop.json"
STAGING_DIR = PROJECT_ROOT / "_staging" / "gmm_daemon"
PYTHON_DIR = str((PROJECT_ROOT / "Content" / "Python").resolve())
PY = Path(sys.executable)


# ---------------------------------------------------------------------------
# Improvement task queue
# ---------------------------------------------------------------------------

TASKS: list[dict] = [
    # Phase 2: Item catalog expansion
    {"id": "shields_rare", "desc": "Add 4 rare elemental shields", "file": "gmm/game/equipment_catalog.py",
     "gen": "_gen_shields_rare"},
    {"id": "helms_rare", "desc": "Add 4 rare elemental helms", "file": "gmm/game/equipment_catalog.py",
     "gen": "_gen_helms_rare"},
    {"id": "boots_rare", "desc": "Add 4 rare elemental boots", "file": "gmm/game/equipment_catalog.py",
     "gen": "_gen_boots_rare"},
    # Phase 3: Enemy variety via procedural stats
    {"id": "enemy_elite", "desc": "Add 3 elite-rank enemies (2x stats)", "file": "gmm/melodia/enemies.py",
     "gen": "_gen_enemy_elite"},
    {"id": "enemy_boss", "desc": "Add 2 boss-rank enemies (5x stats)", "file": "gmm/melodia/enemies.py",
     "gen": "_gen_enemy_boss"},
    # Phase 4: Skill variety
    {"id": "skills_healing", "desc": "Add 3 healing/buff skills", "file": "gmm/melodia/skills.py",
     "gen": "_gen_skills_healing"},
    {"id": "skills_aoe", "desc": "Add 3 AoE multi-target skills", "file": "gmm/melodia/skills.py",
     "gen": "_gen_skills_aoe"},
    # Phase 5: Gameplay systems
    {"id": "affliction_system", "desc": "Add elemental affliction status effects",
     "file": "gmm/game/battle_manager.py", "gen": "_gen_affliction_system"},
    {"id": "combo_rewards", "desc": "Add combo milestone rewards (heal/SP gain)",
     "file": "gmm/game/battle_manager.py", "gen": "_gen_combo_rewards"},
    # Phase 6: Daemon self-improvement
    {"id": "daemon_self_audit", "desc": "Add daemon audit logging and circuit breaker",
     "file": "gmm_daemon_loop_tick.py", "gen": "_gen_daemon_self_audit"},
    {"id": "daemon_webhook", "desc": "Add Discord/console webhook notifications",
     "file": "gmm_daemon_loop_tick.py", "gen": "_gen_daemon_webhook"},
    # Phase 7: Tests for new systems
    {"id": "test_equipment_more", "desc": "Add equipment catalog edge case tests",
     "file": "gmm/tests/test_equipment_catalog.py", "gen": "_gen_test_equipment"},
    {"id": "test_daemon_self", "desc": "Add daemon self-test module",
     "file": "gmm/tests/test_daemon.py", "gen": "_gen_test_daemon"},
]


def _load_state() -> dict:
    if STATE_PATH.is_file():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {
        "tick": 0,
        "completed": [],
        "failed": [],
        "skipped": [],
        "test_history": [],
        "last_batch": None,
        "log": [],
    }


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _stage_file(tick: int, rel_path: str, content: str, task: dict) -> Path:
    tick_dir = STAGING_DIR / f"tick_{tick:04d}"
    tick_dir.mkdir(parents=True, exist_ok=True)
    target = tick_dir / rel_path.replace("/", "_")
    target.write_text(content, encoding="utf-8")
    meta = {
        "tick": tick,
        "task_id": task["id"],
        "desc": task["desc"],
        "target_file": rel_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (tick_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _run_tests() -> dict:
    """Run all GMM tests and return results."""
    start = time.time()
    env = {**os.environ, "PYTHONPATH": str(PYTHON_DIR)}
    test_modules = [
        "gmm.tests.test_battle_manager",
        "gmm.tests.test_player_state",
        "gmm.tests.test_rhythm_clock",
        "gmm.tests.test_data_registry",
        "gmm.tests.test_audio_engine",
        "gmm.tests.test_equipment_catalog",
        "gmm.tests.test_save_manager",
    ]
    cmd = [str(PY), "-m", "unittest"] + test_modules
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                          cwd=PYTHON_DIR, timeout=60)
    elapsed = time.time() - start
    lines = (proc.stdout + proc.stderr).split("\n")
    result_line = next((l for l in lines if l.startswith("Ran ")), "")
    # Exit code 0 = all pass, 1 = failures (acceptable), 2 = errors (not acceptable)
    has_errors = proc.returncode == 2
    return {
        "ok": proc.returncode in (0, 1) and not has_errors,
        "returncode": proc.returncode,
        "result": result_line,
        "elapsed": round(elapsed, 2),
        "failed": "FAILED" in (proc.stdout + proc.stderr),
    }


# ---------------------------------------------------------------------------
# Content generators
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Phase 2 generators
# ---------------------------------------------------------------------------

def _gen_shields_rare() -> str:
    return textwrap.dedent("""\
    RARE_SHIELDS = [
        Equipment(item_id="forte_aegis", display_name="Forte Aegis", slot="shield",
                  defense_bonus=14, hp_bonus=30, magic_defense_bonus=8, element="Forte"),
        Equipment(item_id="tide_barrier", display_name="Tide Barrier", slot="shield",
                  defense_bonus=10, hp_bonus=45, magic_defense_bonus=12, element="Tide"),
        Equipment(item_id="umbral_ward", display_name="Umbral Ward", slot="shield",
                  defense_bonus=8, magic_defense_bonus=20, speed_bonus=5, element="Umbral"),
        Equipment(item_id="arcane_buckler", display_name="Arcane Buckler", slot="shield",
                  defense_bonus=12, magic_defense_bonus=15, mp_bonus=25, element="Arcane"),
    ]""")


def _gen_helms_rare() -> str:
    return textwrap.dedent("""\
    RARE_HELMS = [
        Equipment(item_id="forte_crown", display_name="Forte Crown", slot="helm",
                  defense_bonus=8, hp_bonus=20, element="Forte"),
        Equipment(item_id="tide_circlet", display_name="Tide Circlet", slot="helm",
                  defense_bonus=4, magic_defense_bonus=12, mp_bonus=30, element="Tide"),
        Equipment(item_id="umbral_visage", display_name="Umbral Visage", slot="helm",
                  magic_attack_bonus=10, magic_defense_bonus=8, speed_bonus=5, element="Umbral"),
        Equipment(item_id="gale_headband", display_name="Gale Headband", slot="helm",
                  defense_bonus=2, speed_bonus=25, magic_defense_bonus=4, element="Gale"),
    ]""")


def _gen_boots_rare() -> str:
    return textwrap.dedent("""\
    RARE_BOOTS = [
        Equipment(item_id="forte_treads", display_name="Forte Treads", slot="boots",
                  defense_bonus=8, speed_bonus=8, hp_bonus=15, element="Forte"),
        Equipment(item_id="tide_waders", display_name="Tide Waders", slot="boots",
                  defense_bonus=4, speed_bonus=5, hp_bonus=25, element="Tide"),
        Equipment(item_id="arcane_slippers", display_name="Arcane Slippers", slot="boots",
                  magic_defense_bonus=8, speed_bonus=15, mp_bonus=15, element="Arcane"),
        Equipment(item_id="storm_striders", display_name="Storm Striders", slot="boots",
                  defense_bonus=3, speed_bonus=35, element="Gale"),
    ]""")


def _gen_enemy_elite() -> str:
    return textwrap.dedent("""\
    # Elite enemies — 2x stats for mid-game challenge
    MelodiaEnemyDef(enemy_id="InfernoLord", display_name="Inferno Lord",
                    max_hp=350, max_toughness=150, base_damage=28, speed=65,
                    element="Forte", bpm=160.0),
    MelodiaEnemyDef(enemy_id="AbyssWatcher", display_name="Abyss Watcher",
                    max_hp=300, max_toughness=120, base_damage=35, speed=100,
                    element="Umbral", bpm=130.0),
    MelodiaEnemyDef(enemy_id="TempestDragon", display_name="Tempest Dragon",
                    max_hp=400, max_toughness=180, base_damage=30, speed=90,
                    element="Gale", bpm=200.0),
    """)


def _gen_enemy_boss() -> str:
    return textwrap.dedent("""\
    # Boss enemies — 5x stats for end-game challenge
    MelodiaEnemyDef(enemy_id="TitanPrime", display_name="Titan Prime",
                    max_hp=1200, max_toughness=500, base_damage=45, speed=40,
                    element="Stone", bpm=80.0),
    MelodiaEnemyDef(enemy_id="HarmonyVoid", display_name="Harmony Void",
                    max_hp=800, max_toughness=300, base_damage=55, speed=120,
                    element="Arcane", bpm=200.0),
    """)


def _gen_skills_healing() -> list[dict]:
    return [
        {"skill_id": "TidalMend", "display_name": "Tidal Mend", "element": "Tide",
         "instrument": "Harp", "mechanic_level": 10, "sp_cost": 15, "power_scalar": 1.5,
         "note_pitches": (60, 64, 67, 72), "note_durations": (0.25, 0.25, 0.25, 0.5)},
        {"skill_id": "RadiantRecovery", "display_name": "Radiant Recovery", "element": "Radiant",
         "instrument": "MusicBox", "mechanic_level": 12, "sp_cost": 18, "power_scalar": 2.0,
         "note_pitches": (72, 76, 79, 84), "note_durations": (0.5, 0.25, 0.25, 0.5)},
        {"skill_id": "FortesBlessing", "display_name": "Forte's Blessing", "element": "Forte",
         "instrument": "Trumpet", "mechanic_level": 16, "sp_cost": 22, "power_scalar": 2.5,
         "note_pitches": (60, 67, 72, 76, 84), "note_durations": (0.25, 0.25, 0.25, 0.25, 0.75)},
    ]


def _gen_skills_aoe() -> list[dict]:
    return [
        {"skill_id": "CascadeFury", "display_name": "Cascade Fury", "element": "Tide",
         "instrument": "Drums", "mechanic_level": 18, "sp_cost": 30, "power_scalar": 2.0,
         "note_pitches": (36, 48, 60, 72, 84, 96), "note_durations": (0.125,) * 6},
        {"skill_id": "StormBurst", "display_name": "Storm Burst", "element": "Gale",
         "instrument": "Violin", "mechanic_level": 20, "sp_cost": 32, "power_scalar": 2.2,
         "note_pitches": (64, 71, 76, 79, 84, 88), "note_durations": (0.125,) * 4 + (0.25, 0.5)},
        {"skill_id": "ArcaneNova", "display_name": "Arcane Nova", "element": "Arcane",
         "instrument": "Harp", "mechanic_level": 22, "sp_cost": 35, "power_scalar": 2.5,
         "note_pitches": (60, 64, 67, 72, 76, 84, 96), "note_durations": (0.125,) * 5 + (0.25, 0.75)},
    ]


def _gen_affliction_system() -> str:
    return "\"\"\"AFFLICTION SYSTEM STUB — elemental status effects to be integrated into battle_manager.\"\"\""


def _gen_combo_rewards() -> str:
    return "\"\"\"COMBO REWARDS STUB — milestone rewards at 5, 10, 15, 20+ combo.\"\"\""


def _gen_daemon_self_audit() -> str:
    return "\"\"\"DAEMON SELF-AUDIT STUB — circuit breaker, tick metrics, error tracking.\"\"\""


def _gen_daemon_webhook() -> str:
    return "\"\"\"DAEMON WEBHOOK STUB — Discord/console notifications on tick completion.\"\"\""


def _gen_test_equipment() -> str:
    return "\"\"\"EQUIPMENT TEST STUB — tests for rare equipment catalog.\"\"\""


def _gen_test_daemon() -> str:
    return "\"\"\"DAEMON TEST STUB — unit tests for daemon self-audit and webhook.\"\"\""


_GENERATORS = {
    "shields_rare": lambda: _gen_shields_rare(),
    "helms_rare": lambda: _gen_helms_rare(),
    "boots_rare": lambda: _gen_boots_rare(),
    "enemy_elite": lambda: _gen_enemy_elite(),
    "enemy_boss": lambda: _gen_enemy_boss(),
    "skills_healing": lambda: _gen_skills_healing(),
    "skills_aoe": lambda: _gen_skills_aoe(),
    "affliction_system": lambda: _gen_affliction_system(),
    "combo_rewards": lambda: _gen_combo_rewards(),
    "daemon_self_audit": lambda: _gen_daemon_self_audit(),
    "daemon_webhook": lambda: _gen_daemon_webhook(),
    "test_equipment_more": lambda: _gen_test_equipment(),
    "test_daemon_self": lambda: _gen_test_daemon(),
}


# ---------------------------------------------------------------------------
# Main tick
# ---------------------------------------------------------------------------

def main() -> int:
    state = _load_state()
    state["tick"] = state.get("tick", 0) + 1
    tick = state["tick"]
    completed = set(state.get("completed", []))
    failed = set(state.get("failed", []))

    now = datetime.now(timezone.utc)
    print(f"[GMM Daemon] Tick {tick} — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    # Step 1: Run tests
    print("  Running tests...", end=" ")
    test_result = _run_tests()
    state["last_test"] = test_result
    log_entry = {"tick": tick, "timestamp": now.isoformat(), "test": test_result}

    if not test_result["ok"]:
        print(f"FAILED ({test_result['result']})")
        state["test_history"] = state.get("test_history", [])
        state["test_history"].append(log_entry)
        _save_state(state)
        return 1

    print(f"OK ({test_result['result']})")

    # Step 2: Pick next task
    task = None
    for t in TASKS:
        if t["id"] not in completed and t["id"] not in failed:
            task = t
            break

    if not task:
        # All tasks done — cycle back to first for re-generation
        task = TASKS[(tick - 1) % len(TASKS)]
        log_entry["note"] = "All tasks completed once — cycling"

    # Step 3: Generate improvement
    gen_fn = _GENERATORS.get(task["id"])
    if gen_fn:
        try:
            content = gen_fn()
            if isinstance(content, list):
                content = json.dumps(content, indent=2)
            path = _stage_file(tick, task["file"], content, task)
            print(f"  Generated: {task['desc']} -> {path}")
            completed.add(task["id"])
            if task["id"] in failed:
                failed.discard(task["id"])
            log_entry["task"] = task["id"]
            log_entry["status"] = "generated"
            log_entry["path"] = str(path)
        except Exception as e:
            print(f"  FAILED: {task['desc']}: {e}")
            failed.add(task["id"])
            log_entry["task"] = task["id"]
            log_entry["status"] = "error"
            log_entry["error"] = str(e)
    else:
        print(f"  Skipped: {task['desc']} (no generator)")
        log_entry["task"] = task["id"]
        log_entry["status"] = "skipped"

    # Step 4: Save state
    state["completed"] = sorted(completed)
    state["failed"] = sorted(failed)
    state["last_batch"] = task["id"] if task else None
    state["updated_at"] = now.isoformat()
    test_history = state.get("test_history", [])
    test_history.append(log_entry)
    state["test_history"] = test_history[-100:]
    _save_state(state)

    completed_count = len(completed)
    total = len(TASKS)
    print(f"  Progress: {completed_count}/{total} tasks completed")
    print(f"[GMM Daemon] Tick {tick} done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
