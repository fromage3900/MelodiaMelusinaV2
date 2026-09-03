"""Apply / refresh Zen material instances only.

Editor:
  py Content/Python/apply_zen_instances.py

Headless:
  python Content/Python/apply_zen_instances.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zen_instances.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue() -> int:
    import unreal
    from apply_theme_instances import build_theme_instances
    from zen_instances import ZEN_INSTANCES

    # Patch theme list for this run only
    import theme_instances as ti

    baroque = [s for s in ti.THEME_INSTANCES if s["name"].startswith("MI_Baroque_")]
    ti.THEME_INSTANCES[:] = baroque + list(ZEN_INSTANCES)

    unreal.log("=== APPLY ZEN INSTANCES ===")
    instances, master_wired, violations = build_theme_instances()
    zen_only = [row for row in instances if row["instance"].startswith("MI_Zen_")]
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER_PATH,
        "master_wired": master_wired,
        "violations_after": violations,
        "zen_count": len(zen_only),
        "instances": zen_only,
        "texture_pack": "/Game/Textures/70_Japanese_Ornament_Alphas_vfxMed",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ZenInstances] {len(zen_only)} zen MIs -> {REPORT}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    print(f"ZEN_INSTANCES_OK count={len(zen_only)} clean={not violations.get('banned') and not violations.get('unwired')}")
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: UE not found at {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "zen_instances.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/apply_zen_instances.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
