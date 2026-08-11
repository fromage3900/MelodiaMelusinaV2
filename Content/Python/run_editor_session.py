"""Editor-only portfolio session — never spawns UnrealEditor-Cmd.

Use when headless UE hangs or file-locks the universal master. Close
M_Master_Toon_Universal in any open tab before running.

Output Log (editor open):
  py Content/Python/run_editor_session.py
  py Content/Python/run_editor_session.py --rebuild-master
  py Content/Python/run_editor_session.py --showcase

Steps (in order):
  1. Optional universal master rebuild (--rebuild-master, slow ~5–15 min)
  2. Material work plan (instances, sakura, MPC, trimsheet) — always skips rebuild
  3. UDS time-of-day audit (UseUDSTimeOfDay wiring check)
  4. Toon outline PP (rebuild graph)
  5. Storybook vines post-process (--rebuild graph)
  6. Niagara starter library
  7. Template + VFX showcase levels (--showcase)
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "editor_session.json"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _print_shell_help() -> None:
    script = (PROJECT_ROOT / "Content" / "Python" / "run_editor_session.py").as_posix()
    print("Editor-only session — Unreal Editor must be open.")
    print("This script does NOT launch UnrealEditor-Cmd (avoids hangs / file locks).")
    print()
    print("1. Open BS_GodFile in Unreal Editor")
    print("2. Close M_Master_Toon_Universal if it is open in a tab")
    print("3. Window -> Developer Tools -> Output Log, then run:")
    print(f'   py "{script}"')
    print(f'   py "{script}" --rebuild-master   # slow; only when master graph changed')
    print(f'   py "{script}" --showcase         # also builds L_Template + L_VFX_Showcase')


def _run_session() -> int:
    import unreal

    rebuild_master = "--rebuild-master" in sys.argv
    showcase = "--showcase" in sys.argv
    orchestrator = "--orchestrator" in sys.argv
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()

    unreal.log("=== EDITOR SESSION (no headless) ===")
    unreal.log(
        "[EditorSession] Close M_Master_Toon_Universal tab if open — avoids Error 32 on save."
    )

    steps: list[dict] = []
    ok = 0

    def step(label: str, fn, *, optional: bool = False) -> None:
        nonlocal ok
        unreal.log(f"[EditorSession] >>> {label}")
        entry = {"step": label, "ok": False, "error": None, "optional": optional}
        try:
            fn()
            entry["ok"] = True
            ok += 1
            unreal.log(f"[EditorSession] ok: {label}")
        except Exception as exc:
            entry["error"] = str(exc)
            if optional:
                unreal.log_warning(f"[EditorSession] skipped (optional) {label}: {exc}")
            else:
                unreal.log_error(f"[EditorSession] FAILED {label}: {exc}")
                unreal.log_error(traceback.format_exc())
        steps.append(entry)

    if rebuild_master:
        def do_master():
            sys.argv = ["setup_master_universal.py", "--force"]
            __import__("setup_master_universal").build()

        step("rebuild universal master (--force)", do_master)
    else:
        unreal.log("[EditorSession] skipping master rebuild (pass --rebuild-master to include)")

    step(
        "material work plan",
        lambda: __import__("run_material_work_plan")._run_in_ue(skip_rebuild=True),
    )

    step("UDS time-of-day audit", lambda: __import__("setup_time_of_day_mpc").main())

    step(
        "toon outline PP",
        lambda: __import__("setup_audio_outline").build_all(force=True),
    )

    step(
        "storybook vines PP",
        lambda: __import__("setup_storybook_outline").build_all(force=True),
        optional=True,
    )

    step(
        "niagara library",
        lambda: __import__("setup_niagara_library").build_all(showcase=showcase),
    )

    step(
        "sakura dream niagara",
        lambda: __import__("run_sakura_niagara_plan").run_plan(
            rebuild=False, skip_master=True, showcase=showcase
        ),
        optional=True,
    )

    step(
        "pcg portfolio audit",
        lambda: __import__("audit_pcg_portfolio")._audit_in_ue(),
        optional=True,
    )

    step(
        "universal pcg build",
        lambda: __import__("setup_pcg_universal").build_all(force=rebuild_master),
        optional=True,
    )

    step(
        "sakura pcg showcase wrapper",
        lambda: __import__("setup_pcg_sakura").build_all(rebuild=False, spawn=True),
        optional=True,
    )

    if showcase:
        step("template showcase level", lambda: __import__("setup_template_showcase").build_all())

    if orchestrator:
        step(
            "portfolio orchestrator tick",
            lambda: __import__("run_portfolio_orchestrator_loop_tick")._run_in_ue(),
            optional=True,
        )

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    elapsed = round(time.monotonic() - t0, 1)
    total = len(steps)
    required = [s for s in steps if not s.get("optional")]
    required_ok = sum(1 for s in required if s["ok"])
    report = {
        "timestamp": started,
        "elapsed_seconds": elapsed,
        "flags": {
            "rebuild_master": rebuild_master,
            "showcase": showcase,
            "orchestrator": orchestrator,
        },
        "steps_ok": ok,
        "steps_total": total,
        "required_ok": required_ok,
        "required_total": len(required),
        "steps": steps,
        "audit_files": [
            "Saved/Audit/universal_instances.json",
            "Saved/Audit/trimsheet_instances.json",
            "Saved/Audit/portfolio_mpc.json",
            "Saved/Audit/uds_time_of_day_sync.json",
            "Saved/Audit/storybook_outline_build.json",
            "Saved/Audit/niagara_library_build.json",
            "Saved/Audit/sakura_pcg_build.json",
            "Saved/Audit/pcg_portfolio_audit.json",
            "Saved/Audit/pcg_universal_build.json",
            "Saved/Audit/portfolio_orchestrator_loop.json",
        ],
    }
    if showcase:
        report["audit_files"].append("Saved/Audit/template_showcase.json")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    unreal.log(f"[EditorSession] report -> {REPORT_PATH}")
    unreal.log(f"=== EDITOR SESSION COMPLETE ({required_ok}/{len(required)} required, {ok}/{total} total, {elapsed}s) ===")
    return 0 if required_ok == len(required) else 1


def main() -> int:
    if _in_ue():
        return _run_session()
    _print_shell_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
