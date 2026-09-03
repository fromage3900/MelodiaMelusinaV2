"""Inventory resolvable legacy MeshBlend material-function calls."""
from __future__ import annotations
import json
from pathlib import Path
import unreal
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "meshblend_material_call_inventory.json"
def main() -> None:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    rows = []
    load_failures = []
    for data in registry.get_assets_by_path("/Game", recursive=True):
        class_name = str(data.asset_class_path.asset_name)
        if class_name not in {"Material", "MaterialFunction", "MaterialFunctionMaterialLayer", "MaterialFunctionMaterialLayerBlend"}:
            continue
        path = str(data.package_name)
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not asset:
            load_failures.append(path)
            continue
        try:
            if isinstance(asset, unreal.Material):
                expressions = unreal.MaterialEditingLibrary.get_material_expressions(asset) or []
            elif isinstance(asset, unreal.MaterialFunction):
                expressions = unreal.MaterialEditingLibrary.get_material_function_expressions(asset) or []
            else:
                continue
        except Exception:
            continue
        for expression in expressions:
            if not isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
                continue
            function = expression.get_editor_property("material_function")
            function_path = function.get_path_name() if function else ""
            if "MeshBlend" not in function_path and "MeshBlend" not in expression.get_name():
                continue
            rows.append({"asset": path, "expression": expression.get_name(), "function": function_path, "inputs": list(unreal.MaterialEditingLibrary.get_material_expression_input_names(expression) or []), "outputs": list(unreal.MaterialEditingLibrary.get_material_expression_output_names(expression) or [])})
    report = {"legacy_calls": rows, "legacy_call_count": len(rows), "load_failures": load_failures}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MeshBlendCallAudit] {len(rows)} resolvable calls -> {OUT}")
if __name__ == "__main__":
    main()