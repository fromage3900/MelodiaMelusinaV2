"""Lightweight texture + instance integration (avoids loading all SDF masters).

Editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/integrate_instances_light.py"
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "integrate_instances_light.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

SAFE_MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
]


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue() -> int:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as catalog
    import setup_universal_instances as inst

    unreal.log("=== INTEGRATE INSTANCES LIGHT ===")
    wired_masters: dict = {}
    for base in SAFE_MASTERS:
        path = f"{base}.{base.rsplit('/', 1)[-1]}"
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            continue
        mat = unreal.load_asset(path)
        if not mat:
            continue
        wired_masters[base] = catalog.apply_master_defaults(mat, base, force=True)
        lib.save_package(mat)

    results = inst.build_instances()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master_wired": wired_masters,
        "instances": len(results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[IntegrateLight] {len(results)} instances -> {REPORT}")
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        return 1
    for script in (
        "repair_crash_assets.py",
    ):
        subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python" / script)], check=False)
    log = PROJECT_ROOT / "Saved" / "Logs" / "integrate_instances_light.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/integrate_instances_light.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
