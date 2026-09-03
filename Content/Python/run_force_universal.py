"""Rebuild M_Master_Toon_Universal — forces --force so UE argv quirks cannot skip.

Run in UE Output Log (editor open, close master material tab first):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_force_universal.py"

Headless (editor closed):
  python Content/Python/run_force_universal.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "run_force_universal.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")


def _run_build() -> dict:
    import unreal

    sys.argv = ["setup_master_universal.py", "--force"]
    os.environ["BS_MASTER_FORCE"] = "1"
    print("UNIVERSAL_START force=1 — rebuild takes ~5–15 min, wait for UNIVERSAL_RESULT")
    unreal.log("=== RUN_FORCE_UNIVERSAL: rebuilding M_Master_Toon_Universal ===")
    import importlib
    import setup_master_universal

    setup_master_universal = importlib.reload(setup_master_universal)
    path = setup_master_universal.build()
    audit_path = PROJECT_ROOT / "Saved" / "Audit" / "universal_build_last.json"
    wires = None
    if audit_path.is_file():
        wires = json.loads(audit_path.read_text(encoding="utf-8"))
    return {"ok": True, "path": str(path), "wires": wires}


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    report: dict = {"started": started, "ok": False, "error": None, "path": None}

    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: UnrealEditor-Cmd not found: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "run_force_universal.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["BS_MASTER_FORCE"] = "1"
        cmd = [
            str(UE_CMD),
            str(PROJECT_ROOT / "BS_GodFile.uproject"),
            f"-ExecutePythonScript={Path(__file__).as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-nosplash",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"UNIVERSAL_HEADLESS launching UE -> {log}")
        rc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env).returncode
        print(f"UNIVERSAL_HEADLESS exit={rc} (grep log for UNIVERSAL_RESULT)")
        return rc

    try:
        result = _run_build()
        report.update(result)
        report["ok"] = True
        print(f"UNIVERSAL_RESULT ok path={result.get('path')}")
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        print(f"UNIVERSAL_FAILED {exc}")
        print(report["traceback"])
        try:
            import unreal

            unreal.log_error(f"[run_force_universal] FAILED: {exc}")
            unreal.log_error(report["traceback"])
        except Exception:
            pass
        return 1
    finally:
        report["finished"] = datetime.now(timezone.utc).isoformat()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

