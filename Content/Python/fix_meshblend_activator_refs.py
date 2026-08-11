"""Rewire MeshBlend activator material-function refs to portfolio MF_MeshBlend_Activator_Index_0.

Fixes 11 EnvSandbox SDF/hybrid masters that still point at the non-existent Melodia parent
`/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index`, and retargets local
`MF_MeshBlend_Activator_Index_0/1` copies off Art paths where possible.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_meshblend_activator_refs.py"

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript=".../fix_meshblend_activator_refs.py"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "meshblend_activator_fix.json"

OLD_PARENT = "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index"
PORTFOLIO_MF_BAD = "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index"
OLD_PARENT_0 = "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index_0"
OLD_PARENT_1 = "/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index_1"
PLUGIN_MF_0 = "/MeshBlend/Materials/MF_MeshBlend_Activator_Index_0"
PLUGIN_MF_1 = "/MeshBlend/Materials/MF_MeshBlend_Activator_Index_1"
PORTFOLIO_MF_0 = "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_0"
PORTFOLIO_MF_1 = "/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_1"

SDF_MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_HybridStone_SDF",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_Baroque",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_GildedFiligree",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_GildedStucco",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_GothicArchitecture",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_GothicArchitecture_Enhanced",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_OrnamentLayer",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_OrnamentLayer_Enhanced",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_RayMarch_Gothic",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_RoseWindow",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_TrueParallax",
    "/Game/EnvSandbox/Materials/Masters/M_SDF_Grass_Field",
]

LOCAL_FUNCTIONS = [
    PORTFOLIO_MF_0,
    PORTFOLIO_MF_1,
]


def _load_material_function(path: str):
    import unreal

    asset = unreal.load_asset(path)
    if asset and isinstance(asset, unreal.MaterialFunction):
        return asset
    return None


def _function_path(expr) -> str | None:
    mf = expr.get_editor_property("material_function")
    if not mf:
        return None
    return mf.get_path_name().split(".", 1)[0]


def _set_function_call(expr, mf_path: str) -> bool:
    import unreal

    mf = _load_material_function(mf_path)
    if not mf:
        unreal.log_warning(f"[MeshBlendFix] Missing material function: {mf_path}")
        return False
    expr.set_editor_property("material_function", mf)
    return True


def _iter_function_calls(owner) -> list:
    import unreal

    if isinstance(owner, unreal.Material):
        exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(owner))
    else:
        try:
            exprs = list(
                unreal.MaterialEditingLibrary.get_material_function_expressions(owner)
            )
        except Exception:
            exprs = []
    calls: list = []
    for expr in exprs:
        if expr and "MaterialFunctionCall" in type(expr).__name__:
            calls.append(expr)
    return calls


def _fix_owner(owner, target_mf: str, report: dict, label: str) -> int:
    fixed = 0
    for expr in _iter_function_calls(owner):
        current = _function_path(expr)
        if current in (OLD_PARENT, OLD_PARENT_0, PLUGIN_MF_0, PORTFOLIO_MF_BAD) and target_mf == PORTFOLIO_MF_0:
            if _set_function_call(expr, PORTFOLIO_MF_0):
                fixed += 1
                report["changes"].append(
                    {"asset": label, "from": current, "to": PORTFOLIO_MF_0}
                )
        elif current in (OLD_PARENT, OLD_PARENT_1, PLUGIN_MF_1) and target_mf == PORTFOLIO_MF_1:
            if _set_function_call(expr, PORTFOLIO_MF_1):
                fixed += 1
                report["changes"].append(
                    {"asset": label, "from": current, "to": PORTFOLIO_MF_1}
                )
        elif current == OLD_PARENT:
            if _set_function_call(expr, PORTFOLIO_MF_0):
                fixed += 1
                report["changes"].append(
                    {"asset": label, "from": current, "to": PORTFOLIO_MF_0}
                )
    return fixed


def _save_and_recompile(owner, label: str) -> None:
    import unreal

    unreal.EditorAssetLibrary.save_loaded_asset(owner, only_if_is_dirty=False)
    if isinstance(owner, unreal.Material):
        unreal.MaterialEditingLibrary.recompile_material(owner)
    elif isinstance(owner, unreal.MaterialFunction):
        owner.post_edit_change()
    unreal.log(f"[MeshBlendFix] Saved {label}")


def fix_masters(report: dict) -> int:
    import unreal

    total = 0
    for path in SDF_MASTERS:
        material = unreal.load_asset(path)
        if not material or not isinstance(material, unreal.Material):
            report["errors"].append(f"Failed to load material: {path}")
            continue
        count = _fix_owner(material, PORTFOLIO_MF_0, report, path)
        if count:
            _save_and_recompile(material, path)
            total += count
    return total


def fix_local_functions(report: dict) -> int:
    total = 0
    for path in LOCAL_FUNCTIONS:
        mf = _load_material_function(path)
        if not mf:
            report["errors"].append(f"Failed to load material function: {path}")
            continue
        target = PORTFOLIO_MF_0 if path.endswith("_0") else PORTFOLIO_MF_1
        count = _fix_owner(mf, target, report, path)
        if count:
            _save_and_recompile(mf, path)
            total += count
        else:
            report["skipped"].append(
                {
                    "asset": path,
                    "reason": "No retargetable MaterialFunctionCall nodes (parent dep may be embedded)",
                }
            )
    return total


def replace_plugin_copies_if_needed(report: dict) -> int:
    import unreal

    """Replace portfolio MF copies with plugin originals when internal graph cannot be rewired."""
    replaced = 0
    pairs = [
        (PORTFOLIO_MF_0, PLUGIN_MF_0),
        (PORTFOLIO_MF_1, PLUGIN_MF_1),
    ]
    for dest, src in pairs:
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            report["errors"].append(f"Plugin source missing: {src}")
            continue
        if unreal.EditorAssetLibrary.duplicate_asset(src, dest):
            replaced += 1
            report["changes"].append({"asset": dest, "from": "duplicate", "to": src})
            mf = _load_material_function(dest)
            if mf:
                _save_and_recompile(mf, dest)
    return replaced


def _run_binary_patch_fallback() -> dict:
    from patch_meshblend_uasset_paths import main as patch_main

    patch_main()
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        report = _run_binary_patch_fallback()
        print(json.dumps(report, indent=2))
        return 0 if not report.get("errors") else 1

    import unreal

    report: dict = {
        "masters_fixed": 0,
        "functions_fixed": 0,
        "functions_replaced_from_plugin": 0,
        "changes": [],
        "errors": [],
        "skipped": [],
    }

    report["masters_fixed"] = fix_masters(report)
    report["functions_fixed"] = fix_local_functions(report)

    if report["masters_fixed"] == 0 and report["functions_fixed"] == 0:
        report["binary_patch"] = _run_binary_patch_fallback()

    if report["functions_fixed"] == 0 and not report.get("binary_patch"):
        report["functions_replaced_from_plugin"] = replace_plugin_copies_if_needed(report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    unreal.log(
        "[MeshBlendFix] "
        f"masters={report['masters_fixed']} "
        f"functions={report['functions_fixed']} "
        f"plugin_dup={report['functions_replaced_from_plugin']} "
        f"errors={len(report['errors'])}"
    )
    print(json.dumps(report, indent=2))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
