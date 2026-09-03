"""Remove disconnected probe nodes left by failed V10 editor-injection attempts."""
import json
from pathlib import Path
import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
NAMES = {
    "MaterialExpressionCustom_8",
    "MaterialExpressionCustom_9",
    "MaterialExpressionCustom_10",
}

material = unreal.EditorAssetLibrary.load_asset(MASTER)
removed = []
for expression in list(unreal.MaterialEditingLibrary.get_material_expressions(material) or []):
    if expression.get_name() in NAMES:
        unreal.MaterialEditingLibrary.delete_material_expression(material, expression)
        removed.append(expression.get_name())
unreal.MaterialEditingLibrary.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
report = {"ok": True, "master": MASTER, "removed": removed}
out = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_orphan_cleanup.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("[WaterV10] Orphan cleanup: " + json.dumps(report))
print(json.dumps(report, indent=2))
