"""Storybook + toon outline post-process audit.

Updated 2026-08-01: M_PP_ToonOutline + M_PP_StorybookVines(_Inst) were quarantined
(Content/_QuarantinePostProcess_20260801/) and consolidated into one material,
M_PP_StorybookOutline -- see Docs/Handoffs/PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md.
This audit now checks for the merged material instead of the old two-material
stack; the blend-order check no longer applies since there's one outline
material, not two in a required order.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "storybook_outline_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

LEVELS = (
    "/Game/EnvSandbox/_Template/L_Template",
    "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
)

PP_ASSETS = (
    "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline",
)
MPC_AUDIO = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"


def _graph_non_empty(material) -> bool:
    import unreal

    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(material) or []
        return len(exprs) > 3
    except Exception:
        return False


def _ppv_blendable_order(eas) -> dict:
    import unreal

    for actor in eas.get_all_level_actors() or []:
        if not isinstance(actor, unreal.PostProcessVolume):
            continue
        s = actor.get_editor_property("settings")
        try:
            weighted = s.get_editor_property("weighted_blendables")
            arr = weighted.get_editor_property("array") if weighted else []
            names = []
            for entry in arr or []:
                mat = entry.get_editor_property("object") if hasattr(entry, "get_editor_property") else None
                if mat:
                    names.append(mat.get_name())
            return {"ppv": actor.get_actor_label(), "blendables": names}
        except Exception as exc:
            return {"ppv": actor.get_actor_label(), "error": str(exc)}
    return {"ppv": None, "blendables": []}


def run_audit() -> dict:
    import unreal

    assets: dict[str, dict] = {}
    issues: list[dict] = []
    for base in PP_ASSETS:
        leaf = base.rsplit("/", 1)[-1]
        path = f"{base}.{leaf}"
        entry = {"exists": unreal.EditorAssetLibrary.does_asset_exist(path)}
        if entry["exists"]:
            mat = unreal.load_asset(path)
            entry["graph_non_empty"] = _graph_non_empty(mat) if mat else False
            if mat and not entry["graph_non_empty"]:
                issues.append({"id": "empty_pp_graph", "asset": leaf, "severity": "warn"})
        else:
            issues.append({"id": "missing_pp_asset", "asset": leaf, "severity": "critical"})
        assets[leaf] = entry

    mpc_ok = unreal.EditorAssetLibrary.does_asset_exist(MPC_AUDIO)
    if not mpc_ok:
        issues.append({"id": "missing_mpc_audio", "severity": "warn"})

    level_pp: list[dict] = []
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            continue
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        les.load_level(level)
        pp_info = _ppv_blendable_order(eas)
        names = pp_info.get("blendables") or []
        order_ok = any("StorybookOutline" in n for n in names) if names else False
        if not order_ok:
            issues.append({
                "id": "ppv_missing_storybook_outline",
                "level": level,
                "severity": "warn",
                "blendables": names,
            })
        level_pp.append({"level": level, **pp_info, "order_ok": order_ok})

    critical = sum(1 for i in issues if i.get("severity") == "critical")
    passed = critical == 0 and assets.get("M_PP_StorybookOutline", {}).get("graph_non_empty", False)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "assets": assets,
        "mpc_portfolio_audio": mpc_ok,
        "level_post_process": level_pp,
        "issues": issues,
        "critical_count": critical,
        "passed": passed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_storybook_outline.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode
    report = run_audit()
    print(f"STORYBOOK_OUTLINE passed={report.get('passed')}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
