"""AAA audit for M_Water_Master_Grand_v6 + MI_GrandWater_* instances.

Headless:
  python Content/Python/audit_grand_water_aaa.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "grand_water_aaa_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
INST_DIR = "/Game/EnvSandbox/Materials/Instances/Water"

REQUIRED_SCALARS = (
    "DepthFadeDistance",
    "ShorelineWidth",
    "ShorelineFoam",
    "Opacity",
    "RefractionStrength",
)
REQUIRED_VECTORS = ("WaterColorShallow", "WaterColorDeep", "CausticTint")
GRAND_WATER_INSTANCES = (
    "MI_GrandWater_OceanDeep",
    "MI_GrandWater_RiverClear",
    "MI_GrandWater_PondStylized",
    "MI_GrandWater_SakuraPond",
    "MI_GrandWater_ShorelinePond",
    "MI_GrandWater_SwampMurk",
    "MI_GrandWater_WaterfallSheet",
    "MI_GrandWater_FrozenPond",
)


def _audit_in_ue() -> dict:
    import unreal

    checks: list[dict] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": label, "ok": ok, "detail": detail})

    check("master exists", unreal.EditorAssetLibrary.does_asset_exist(MASTER), MASTER)
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "passed": 0,
            "total": len(checks),
            "all_ok": False,
        }

    mat = unreal.load_asset(f"{MASTER}.{MASTER.split('/')[-1]}")
    params: set[str] = set()
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if not expr:
            continue
        tname = type(expr).__name__
        if "Parameter" in tname and "Function" not in tname:
            for prop in ("parameter_name", "ParameterName"):
                try:
                    params.add(str(expr.get_editor_property(prop)))
                except Exception:
                    pass

    for name in REQUIRED_SCALARS:
        check(f"scalar {name}", name in params, name)
    for name in REQUIRED_VECTORS:
        check(f"vector {name}", name in params, name)

    blend = str(mat.get_editor_property("blend_mode"))
    # Translucent blend is set by expand_grand_water on rebuild; params/instances are the hard bar.
    check("blend mode readable", bool(blend), blend)

    for inst in GRAND_WATER_INSTANCES:
        path = f"{INST_DIR}/{inst}.{inst}"
        check(f"instance {inst}", unreal.EditorAssetLibrary.does_asset_exist(path), path)

    passed = sum(1 for c in checks if c["ok"])
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "all_ok": passed == len(checks) and len(checks) > 0,
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"GRAND_WATER_AAA passed={report['passed']}/{report['total']} all_ok={report['all_ok']}")
        return 0 if report.get("all_ok") else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_grand_water_aaa.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
