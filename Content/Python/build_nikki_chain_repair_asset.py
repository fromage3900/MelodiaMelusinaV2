"""Build a non-destructive Universal Nikki-chain verification asset.

This intentionally does not clear or rewrite M_Master_Toon_Universal. The
existing force-rebuild wrapper can crash UE 5.8 while deleting rooted material
expressions, so this path asks the canonical builder to create a new,
project-owned comparison asset and then verifies all four Nikki function-call
references before any instance migration is considered.
"""
from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPAIR_NAME = "M_Master_Toon_Universal_NikkiChainRepairV2"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
REPAIR_PATH = f"{MASTER_DIR}/{REPAIR_NAME}"
REQUIRED = (
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiSparkle",
    "/Game/EnvSandbox/Materials/Functions/MF_NikkiIridescenceSheen",
)


def _asset_path(asset) -> str:
    try:
        return str(asset.get_path_name()).split(".", 1)[0]
    except Exception:
        return ""


def _function_paths(unreal, material) -> list[str]:
    found: list[str] = []
    expressions = unreal.MaterialEditingLibrary.get_material_expressions(material) or []
    for expression in expressions:
        if expression.get_class().get_name() != "MaterialExpressionMaterialFunctionCall":
            continue
        try:
            function = expression.get_editor_property("material_function")
        except Exception:
            try:
                function = expression.get_editor_property("function")
            except Exception:
                function = None
        path = _asset_path(function) if function else ""
        if path:
            found.append(path)
    return sorted(set(found))


def main() -> dict:
    import unreal

    # Force the editor-side asset registry to resolve the already-saved
    # function assets before the canonical builder evaluates its availability.
    # This is read-only and avoids the false "Nikki MF chain missing" result
    # seen during the first startup pass.
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass
    for path in REQUIRED:
        if not unreal.load_asset(path):
            raise RuntimeError(f"Required Nikki function did not load: {path}")

    repair = unreal.EditorAssetLibrary.load_asset(REPAIR_PATH)
    built = False
    if not repair:
        import setup_master_universal as builder

        builder = importlib.reload(builder)
        old_name = builder.MASTER_NAME
        try:
            builder.MASTER_NAME = REPAIR_NAME
            sys.argv = ["build_nikki_chain_repair_asset.py"]
            builder.build()
            built = True
        finally:
            builder.MASTER_NAME = old_name
        repair = unreal.EditorAssetLibrary.load_asset(REPAIR_PATH)

    if not repair:
        raise RuntimeError(f"Repair asset was not created: {REPAIR_PATH}")

    functions = _function_paths(unreal, repair)
    report = {
        "ok": all(path in functions for path in REQUIRED),
        "repair_asset": REPAIR_PATH,
        "built_this_run": built,
        "required_functions": list(REQUIRED),
        "function_calls": functions,
        "v9_touched": False,
        "v10_touched": False,
        "live_universal_touched": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / "Audit" / "nikki_chain_repair_asset.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[NikkiRepair] {json.dumps(report)}")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
