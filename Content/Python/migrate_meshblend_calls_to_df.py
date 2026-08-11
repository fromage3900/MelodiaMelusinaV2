"""Replace resolvable legacy MeshBlend activator calls with native DF contact calls."""
from __future__ import annotations
import json
from pathlib import Path
import unreal
TARGET = "/Game/EnvSandbox/Materials/Functions/MF_DF_ContactBlend"
MANIFEST = Path(unreal.Paths.project_saved_dir()) / "Audit" / "meshblend_material_call_inventory.json"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "meshblend_to_df_migration.json"
PROTECTED = ()
def main() -> None:
    target = unreal.EditorAssetLibrary.load_asset(TARGET)
    if not target:
        raise RuntimeError(f"Missing target function {TARGET}")
    source = json.loads(MANIFEST.read_text(encoding="utf-8"))
    migrated, skipped, failed = [], [], []
    by_asset = {}
    for row in source.get("legacy_calls", []):
        by_asset.setdefault(row["asset"], []).append(row)
    for path, rows in by_asset.items():
        if any(marker in path for marker in PROTECTED):
            skipped.append({"asset": path, "reason": "protected_or_archival"})
            continue
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not asset:
            failed.append({"asset": path, "reason": "load_failed"})
            continue
        try:
            expressions = (unreal.MaterialEditingLibrary.get_material_expressions(asset) if isinstance(asset, unreal.Material) else unreal.MaterialEditingLibrary.get_material_function_expressions(asset)) or []
            wanted = {row["expression"] for row in rows}
            changed = 0
            for expression in expressions:
                if expression.get_name() not in wanted or not isinstance(expression, unreal.MaterialExpressionMaterialFunctionCall):
                    continue
                expression.set_editor_property("material_function", target)
                changed += 1
            if changed:
                if isinstance(asset, unreal.Material):
                    unreal.MaterialEditingLibrary.recompile_material(asset)
                unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
                migrated.append({"asset": path, "calls": changed})
        except Exception as exc:
            failed.append({"asset": path, "reason": str(exc)})
    result = {"target": TARGET, "migrated_assets": migrated, "migrated_asset_count": len(migrated), "migrated_call_count": sum(x["calls"] for x in migrated), "skipped": skipped, "failed": failed}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MeshBlendToDF] migrated {result['migrated_call_count']} calls in {len(migrated)} assets; skipped={len(skipped)} failed={len(failed)} -> {OUT}")
    if failed:
        raise RuntimeError(f"Migration failures: {len(failed)}")
if __name__ == "__main__":
    main()