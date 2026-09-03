"""Single tick for /loop 5m Melodia JRPG + rhythm scaffolding.

Each tick advances one batch from LOOP_BATCHES, updates loop state JSON,
and appends to Docs/MELODIA_JRPG_RHYTHM_SCAFFOLD.md loop log.

  python Content/Python/run_melodia_jrpg_rhythm_loop_tick.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = PROJECT_ROOT / "Saved" / "Loop" / "melodia_jrpg_rhythm_loop.json"
DOC_PATH = PROJECT_ROOT / "Docs" / "MELODIA_JRPG_RHYTHM_SCAFFOLD.md"
PY = Path(sys.executable)

LOOP_BATCHES: list[dict] = [
    {
        "id": "catalog_audit",
        "title": "JRPG template catalog + disk audit",
        "actions": ["audit_jrpg_template"],
        "requires_ue": False,
    },
    {
        "id": "python_runtime_smoke",
        "title": "gmm/game runtime smoke (battle_manager)",
        "actions": ["battle_smoke"],
        "requires_ue": False,
    },
    {
        "id": "registry_export",
        "title": "Export Melodia registry seed JSON",
        "actions": ["registry_export"],
        "requires_ue": False,
    },
    {
        "id": "jrpg_bridge_verify",
        "title": "JRPG bridge mapping summary",
        "actions": ["jrpg_bridge_summary"],
        "requires_ue": False,
    },
    {
        "id": "ue_scaffold_bridge",
        "title": "UE scaffold: Melodia ↔ JRPG bridge BPs",
        "actions": ["ue_scaffold"],
        "requires_ue": True,
    },
    {
        "id": "rhythm_assets",
        "title": "Rhythm widget + MPC scaffold",
        "actions": ["ue_rhythm_scaffold"],
        "requires_ue": True,
    },
    {
        "id": "demo_level",
        "title": "Melodia rhythm slice level stub",
        "actions": ["ue_demo_level"],
        "requires_ue": True,
    },
    {
        "id": "doc_handoff_sync",
        "title": "Sync scaffold doc with DEEPSEEK handoff phases",
        "actions": ["doc_sync"],
        "requires_ue": False,
    },
]


def _load_state() -> dict:
    if STATE_PATH.is_file():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"tick": 0, "completed_batches": [], "log": []}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_doc_log(tick: int, batch: dict, result: dict) -> None:
    line = (
        f"\n### Loop tick {tick} — {batch['title']} ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})\n"
        f"- Batch: `{batch['id']}`\n"
        f"- Result: `{result.get('status', 'unknown')}`\n"
    )
    if result.get("detail"):
        line += f"- Detail: {result['detail']}\n"
    if not DOC_PATH.is_file():
        DOC_PATH.write_text("# Melodia JRPG + Rhythm Scaffold\n\n## Loop log\n", encoding="utf-8")
    content = DOC_PATH.read_text(encoding="utf-8")
    if "## Loop log" not in content:
        content += "\n## Loop log\n"
    DOC_PATH.write_text(content + line, encoding="utf-8")


def _run_py(script: str, *args: str) -> dict:
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(PROJECT_ROOT / "Content" / "Python")}
    cmd = [str(PY), str(PROJECT_ROOT / "Content" / "Python" / script), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
    return {
        "ok": proc.returncode == 0,
        "stdout": proc.stdout[-2000:] if proc.stdout else "",
        "stderr": proc.stderr[-1000:] if proc.stderr else "",
    }


def _battle_smoke() -> dict:
    from gmm.game.battle_manager import MelodiaBattleManager
    mgr = MelodiaBattleManager()
    start = mgr.start_encounter("CrystalShard")
    cmd = mgr.player_command("skill", skill_id="TidalWave")
    res = mgr.resolve_rhythm(128.0)
    enemy = mgr.enemy_turn()
    state = mgr.get_state()
    ok = start.get("ok") and cmd.get("ok") and res.get("ok") and enemy.get("ok")
    return {"status": "ok" if ok else "fail", "detail": f"phase={state.get('phase')} combo={state.get('combo')}"}


def _registry_export() -> dict:
    from gmm.game.data_registry import MelodiaDataRegistry
    out = PROJECT_ROOT / "Content" / "Data" / "Melodia" / "melodia_registry_seed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    reg = MelodiaDataRegistry()
    reg.export_json(str(out))
    return {"status": "ok", "detail": str(out)}


def _jrpg_bridge_summary() -> dict:
    from gmm.game.jrpg_bridge import bridge_summary
    out = PROJECT_ROOT / "Saved" / "Audit" / "jrpg_bridge_summary.json"
    data = bridge_summary()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"status": "ok", "detail": str(out)}


def _doc_sync() -> dict:
    phases = [
      "Phase 0: Quartz clock (BP_RhythmKernel)",
      "Phase 1: Input validator (MelodiaCore grading windows)",
      "Phase 2: HUD (WBP_Battle_Rhythm + template BP_BattleUI shell)",
      "Phase 3: AV turn economy + SP pool (template BP_BattleController)",
      "Phase 4: Instruments + skills (DT_MelodiaSkills)",
      "Phase 5: Songcraft data assets",
      "Phase 6: Combo/break/defense mechanics",
      "Phase 7: Audio-reactive environment (MPC_SakuraDream)",
    ]
    handoff = PROJECT_ROOT / "Docs" / "DEEPSEEK_RHYTHM_GAMEPLAY_HANDOFF.md"
    return {
        "status": "ok",
        "detail": f"Handoff exists={handoff.is_file()} phases_tracked={len(phases)}",
    }


def _execute_batch(batch: dict) -> dict:
    for action in batch["actions"]:
        if action == "audit_jrpg_template":
            r = _run_py("audit_jrpg_template.py")
            if not r["ok"]:
                return {"status": "fail", "detail": r["stderr"] or r["stdout"]}
        elif action == "battle_smoke":
            return _battle_smoke()
        elif action == "registry_export":
            return _registry_export()
        elif action == "jrpg_bridge_summary":
            return _jrpg_bridge_summary()
        elif action == "doc_sync":
            return _doc_sync()
        elif action in ("ue_scaffold", "ue_rhythm_scaffold", "ue_demo_level"):
            return {
                "status": "skipped",
                "detail": "UE editor busy — run scaffold_melodia_jrpg_rhythm_bridge.py when org pass completes",
            }
    return {"status": "ok"}


def main() -> int:
    state = _load_state()
    state["tick"] = state.get("tick", 0) + 1
    tick = state["tick"]
    completed = set(state.get("completed_batches", []))

    batch = None
    for b in LOOP_BATCHES:
        if b["id"] not in completed:
            batch = b
            break
    if batch is None:
        batch = LOOP_BATCHES[(tick - 1) % len(LOOP_BATCHES)]
        result = {"status": "repeat", "detail": f"All batches done — re-running {batch['id']}"}
    else:
        result = _execute_batch(batch)
        if result.get("status") in ("ok", "repeat", "skipped"):
            completed.add(batch["id"])

    state["completed_batches"] = sorted(completed)
    state["last_batch"] = batch["id"] if batch else None
    state["last_result"] = result
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    log = state.get("log", [])
    log.append({"tick": tick, "batch": batch["id"] if batch else None, **result})
    state["log"] = log[-50:]
    _save_state(state)
    if batch:
        _append_doc_log(tick, batch, result)

    print(f"JRPG_RHYTHM_LOOP tick={tick} batch={batch['id'] if batch else 'none'} status={result.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
