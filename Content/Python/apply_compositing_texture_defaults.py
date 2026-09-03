"""Wire compositing library textures onto universal masters + all MI_* instances.

Safe pass — does not load bulk SDF masters or rewire _PROJECT paths.

Editor (Output Log):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_compositing_texture_defaults.py"

Shell:
  python Content/Python/apply_compositing_texture_defaults.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "compositing_texture_defaults.json"
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

    unreal.log("=== COMPOSITING TEXTURE DEFAULTS ===")
    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "masters": {},
        "instances": {},
    }

    for base in SAFE_MASTERS:
        path = f"{base}.{base.rsplit('/', 1)[-1]}"
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            unreal.log_warning(f"[CompositingDefaults] missing {base}")
            continue
        mat = unreal.load_asset(path)
        if not mat:
            continue
        wired = catalog.apply_master_defaults(mat, base, force=True)
        lib.save_package(mat)
        report["masters"][base] = wired
        unreal.log(f"[CompositingDefaults] master {base}: {len(wired)} textures")

    instance_wires = catalog.refresh_starter_instance_textures()
    report["instances"] = instance_wires
    report["instance_scope"] = "starters_only"
    report["instance_count"] = len(instance_wires)
    report["instance_textures_set"] = sum(len(v) for v in instance_wires.values())

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(
        f"[CompositingDefaults] {report['instance_count']} instances, "
        f"{report['instance_textures_set']} texture params -> {REPORT}"
    )
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/repair_crash_assets.py")], check=False)
    subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/portfolio_texture_catalog.py")], check=False)
    log = PROJECT_ROOT / "Saved" / "Logs" / "compositing_texture_defaults.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/apply_compositing_texture_defaults.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    print(f"Compositing texture defaults -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
