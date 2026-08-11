"""Set ABP_Melusina target skeleton via Python in editor."""
import unreal

abp = unreal.load_asset("/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina")
skel = unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton")
print(f"Loaded ABP: {abp}")
print(f"Loaded Skeleton: {skel}")

abp.set_editor_property("target_skeleton", skel)
print(f"Target skeleton set: {abp.get_editor_property('target_skeleton').get_name()}")

unreal.EditorAssetLibrary.save_asset(abp)
print("Saved.")
