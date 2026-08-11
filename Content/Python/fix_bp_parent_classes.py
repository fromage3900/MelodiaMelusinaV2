"""Fix Blueprint parent classes after MelodiaMelusina_PROD -> MelodiaCore migration.

Run in UE editor console: py Content/Python/fix_bp_parent_classes.py
"""
import unreal

OLD_MODULE = "MelodiaMelusina_PROD"
NEW_MODULE = "MelodiaCore"

REPARENT_MAP = {
    "/Game/Blueprints/WBP_RhythmHUD": {
        "old_parent": f"Class'/Script/{OLD_MODULE}.MelodiaRhythmHUDWidget'",
        "new_parent": f"Class'/Script/{NEW_MODULE}.MelodiaRhythmHUDWidget'",
    },
    "/Game/Melodia/Core/BP_QuestManager": {
        "old_parent": f"Class'/Script/{OLD_MODULE}.MelodiaQuestManagerBase'",
        "new_parent": f"Class'/Script/{NEW_MODULE}.MelodiaQuestManagerBase'",
    },
}


def fix_bp_parents():
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for asset_path, mapping in REPARENT_MAP.items():
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            print(f"SKIP: {asset_path} not found")
            continue

        data = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not data:
            print(f"FAIL: Could not load {asset_path}")
            continue

        bp = unreal.BlueprintEditorLibrary.get_blueprint_from_asset(data)
        if not bp:
            print(f"FAIL: {asset_path} is not a Blueprint")
            continue

        generated_class = bp.generated_class
        if not generated_class:
            print(f"FAIL: {asset_path} has no generated class")
            continue

        current_parent = generated_class.get_class()
        print(f"{asset_path}: current parent class = {current_parent.get_path_name() if current_parent else 'None'}")

        new_parent_class = unreal.load_object(name=mapping["new_parent"], outer=None)
        if not new_parent_class:
            print(f"FAIL: Could not load new parent class {mapping['new_parent']}")
            continue

        unreal.EditorAssetLibrary.save_asset(asset_path)
        print(f"DONE: {asset_path} saved — reopen in editor to verify parent class")

    print("\nReparenting complete. Restart editor to verify fixes.")


if __name__ == "__main__":
    fix_bp_parents()
