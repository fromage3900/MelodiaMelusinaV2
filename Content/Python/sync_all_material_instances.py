"""Re-apply all portfolio material instance families after master rebuilds.

Headless:
  python Content/Python/sync_all_material_instances.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sync_all_instances.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def run_sync() -> dict:
    import unreal

    results: list[dict] = []
    ok = True

    def step(name: str, fn) -> None:
        nonlocal ok
        try:
            fn()
            results.append({"step": name, "ok": True})
            unreal.log(f"[SyncAll] {name} OK")
        except Exception as exc:
            ok = False
            results.append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[SyncAll] {name} failed: {exc}")

    step("starters", lambda: __import__("apply_starter_instances").build_starter_instances())
    step("sakura", lambda: __import__("setup_sakura_instances").build())
    step("zen", lambda: __import__("apply_zen_instances")._run_in_ue())
    step("trimsheet", lambda: __import__("setup_trimsheet_instances").build())
    step("cloth_catalog", lambda: __import__("cloth_trim_textures").main())
    step("baroque", lambda: __import__("apply_theme_instances")._run_in_ue())
    step("landscape_instances", lambda: __import__("setup_landscape_height_blend").build(force=False))
    step("grand_water_instances", lambda: __import__("setup_master_water").build())

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": results,
        "all_ok": ok and all(r["ok"] for r in results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = run_sync()
        print(f"SYNC_ALL_OK all_ok={report['all_ok']} -> {REPORT}")
        return 0 if report["all_ok"] else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "sync_all_instances.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/sync_all_material_instances.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
