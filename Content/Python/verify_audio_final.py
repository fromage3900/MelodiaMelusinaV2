"""Final verification: confirm all new audio assets exist."""
import unreal

checks = [
    "/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover",
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full",
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Inst",
    "/Game/Melodia/Audio/SFX/A_UI_Bubble",
    "/Game/Melodia/Audio/Mix/SoundClasses/SCL_Master",
    "/Game/Melodia/Audio/Mix/SoundClasses/SCL_Music",
    "/Game/Melodia/Audio/Mix/SoundClasses/SCL_Voice",
    "/Game/Melodia/Audio/Mix/Submixes/SUBMIX_Music",
    "/Game/Melodia/Audio/Mix/Submixes/SUBMIX_Voice",
]
for c in checks:
    print(f"{'EXISTS' if unreal.EditorAssetLibrary.does_asset_exist(c) else 'MISSING'} {c}")

ui_count = len(unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Audio/SFX/UI", recursive=True, include_folder=False))
bgm_count = len(unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Audio/BGM", recursive=True, include_folder=False))
print(f"UI_BLIPS: {ui_count}")
print(f"BGM_ASSETS: {bgm_count}")
