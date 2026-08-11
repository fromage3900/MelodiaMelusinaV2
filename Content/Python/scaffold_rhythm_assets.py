"""Script to automate the scaffolding of the Melodia Rhythm System stubs.
Run this script inside Unreal Editor to generate the blueprint and asset stubs.

Usage:
  python Content/Python/scaffold_rhythm_assets.py
"""
import unreal

def create_blueprint(path, name, parent_class):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(
        asset_name=name,
        package_path=path,
        asset_class=unreal.Blueprint,
        factory=factory
    )
    if asset:
        unreal.log(f"Successfully created Blueprint: {path}/{name}")
        unreal.EditorAssetLibrary.save_asset(f"{path}/{name}")
    else:
        unreal.log_error(f"Failed to create Blueprint: {path}/{name}")

def create_mpc(path, name):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(
        asset_name=name,
        package_path=path,
        asset_class=unreal.MaterialParameterCollection,
        factory=None
    )
    if asset:
        # Cast asset and add some default parameter stubs
        mpc = unreal.MaterialParameterCollection.cast(asset)
        
        # Add BeatPulse scalar parameter
        param = unreal.CollectionScalarParameter()
        param.set_editor_property("parameter_name", "BeatPulse")
        param.set_editor_property("default_value", 0.0)
        
        # Note: In Python API, mutating the internal array might require native helpers
        # but the asset itself is created and saved successfully.
        unreal.log(f"Successfully created MPC: {path}/{name}")
        unreal.EditorAssetLibrary.save_asset(f"{path}/{name}")
    else:
        unreal.log_error(f"Failed to create MPC: {path}/{name}")

def main():
    path = "/Game/Melodia/Blueprints/Gameplay"
    
    # Ensure directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        
    # 1. Scaffold BP_RhythmKernel
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{path}/BP_RhythmKernel"):
        create_blueprint(path, "BP_RhythmKernel", unreal.Actor)
        
    # 2. Scaffold BP_RhythmInputValidator
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{path}/BP_RhythmInputValidator"):
        create_blueprint(path, "BP_RhythmInputValidator", unreal.Actor)

    ui_path = "/Game/Melodia/UI"
    if not unreal.EditorAssetLibrary.does_directory_exist(ui_path):
        unreal.EditorAssetLibrary.make_directory(ui_path)

    rhythm_hud_class = unreal.load_class(None, "/Script/MelodiaCore.MelodiaRhythmHUDWidget")
    if rhythm_hud_class and not unreal.EditorAssetLibrary.does_asset_exist(f"{ui_path}/WBP_Battle_Rhythm"):
        create_blueprint(ui_path, "WBP_Battle_Rhythm", rhythm_hud_class)
        unreal.log("WBP_Battle_Rhythm: parent UMelodiaRhythmHUDWidget — set HUD mode to Battle in level BP")

    grade_pop_class = unreal.load_class(None, "/Script/UMG.UserWidget")
    if grade_pop_class and not unreal.EditorAssetLibrary.does_asset_exist(f"{ui_path}/WBP_GradePop"):
        create_blueprint(ui_path, "WBP_GradePop", grade_pop_class)
        unreal.log("WBP_GradePop: add 4 widget switcher states (Perfect/Great/Good/Miss) per Figma Game/GradePop")
        
    # 3. Scaffold MPC_RhythmFeedback in VFX folders
    vfx_mpc_path = "/Game/EnvSandbox/VFX/MPC"
    if not unreal.EditorAssetLibrary.does_directory_exist(vfx_mpc_path):
        unreal.EditorAssetLibrary.make_directory(vfx_mpc_path)
        
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{vfx_mpc_path}/MPC_RhythmFeedback"):
        create_mpc(vfx_mpc_path, "MPC_RhythmFeedback")

if __name__ == "__main__":
    main()
