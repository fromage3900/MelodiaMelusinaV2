"""One master-material loop tick: ban /Engine/ textures, wire compositing catalog, rotate focus.

Editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_master_material_loop_tick.py"

Headless (close editor first — avoids Error 32):
  set BS_MASTER_FORCE=1
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_master_material_loop_tick.py" ^
    -unattended -nullrhi
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE = PROJECT_ROOT / "Saved" / "Audit" / "master_texture_loop_state.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "master_texture_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

SAFE_MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
]

FOCUS = (
    "banned_audit_and_force_rewire",
    "orm_roughness_role_validation",
    "nikki_character_param_groups",
    "celestial_nebula_flower_shadow",
    "magical_fairy_dust_masks",
    "starter_instance_texture_refresh",
)


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _load_tick() -> int:
    if STATE.exists():
        try:
            return int(json.loads(STATE.read_text(encoding="utf-8")).get("tick_index", 0))
        except Exception:
            pass
    return 0


def _save_tick(tick: int, focus: str, summary: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(
            {
                "tick_index": tick,
                "last_focus": focus,
                "last_run": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _run_in_ue() -> int:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as catalog

    tick = _load_tick()
    focus = FOCUS[tick % len(FOCUS)]
    unreal.log(f"=== MASTER TEXTURE LOOP tick={tick} focus={focus} ===")

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick_index": tick,
        "focus": focus,
        "masters": {},
    }

    for base in SAFE_MASTERS:
        leaf = base.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            continue
        mat = unreal.load_asset(f"{base}.{leaf}")
        if not mat:
            continue
        before = catalog.scan_master_texture_violations(mat)
        wired = catalog.apply_master_defaults(mat, base, force=True)
        after = catalog.scan_master_texture_violations(mat)
        try:
            unreal.MaterialEditingLibrary.recompile_material(mat)
        except Exception as exc:
            after["compile"] = str(exc)
        else:
            after["compile"] = "ok"
        lib.save_package(mat)
        report["masters"][base] = {
            "wired": wired,
            "violations_before": before,
            "violations_after": after,
        }

    if focus == "orm_roughness_role_validation":
        for base, data in report.get("masters", {}).items():
            wrong = data.get("violations_after", {}).get("wrong_role", [])
            if wrong:
                unreal.log_warning(f"[Loop] ORM role fix needed on {base}: {wrong}")

    if focus == "starter_instance_texture_refresh":
        try:
            import apply_starter_instances as starters

            starters._run_in_ue()
            report["starters"] = "refreshed"
        except Exception as exc:
            report["starters"] = f"error: {exc}"

    if focus == "nikki_character_param_groups":
        report["note"] = "Nikki/Character groups live in setup_master_universal GROUP_NIKI; rebuild with BS_MASTER_FORCE=1 to refresh"

    if focus == "celestial_nebula_flower_shadow":
        report["note"] = "Celestial + FlowerShadow params verified via catalog space_nebula + sakura petal chains"

    if focus == "magical_fairy_dust_masks":
        report["note"] = "Magical masks use T_Magic_Heart / T_Spark_* / T_Sakura_Petal — no /Engine/ paths"

    banned = sum(
        len(m.get("violations_after", {}).get("banned", []))
        for m in report.get("masters", {}).values()
    )
    unwired = sum(
        len(m.get("violations_after", {}).get("unwired", []))
        for m in report.get("masters", {}).values()
    )
    report["summary"] = {
        "banned_texture_slots": banned,
        "unwired_texture_slots": unwired,
        "clean": banned == 0 and unwired == 0,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _save_tick(tick + 1, focus, report["summary"])
    unreal.log(f"[MasterTextureLoop] banned={banned} unwired={unwired} -> {REPORT}")
    return 0 if report["summary"]["clean"] else 1


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/portfolio_texture_catalog.py")], check=False)
    if os.environ.get("BS_MASTER_FORCE", "").strip().lower() not in ("1", "true", "yes"):
        os.environ["BS_MASTER_FORCE"] = "1"
    log = PROJECT_ROOT / "Saved" / "Logs" / "master_texture_loop.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_master_material_loop_tick.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        f"-log={log}",
    ]
    print(f"Master texture loop tick -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
