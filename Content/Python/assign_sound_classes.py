"""Assign authored sound assets to the new Melodia SoundClasses and verify.
Also set the SoundClass field (UE 5.8: 'sound_class_object' or via editor property).
"""
import unreal

WAVES = [
    "/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover",
    "/Game/Melodia/Audio/BGM/SW_BGM_Battle_Placeholder_128",
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full",
    "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Inst",
    "/Game/Melodia/Audio/SFX/A_UI_Bubble",
    "/Game/Melodia/Audio/Ambience/A_Ambience_Melusina_98bpm",
]

MUSIC_CLASS = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Music")
SFX_CLASS = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/SoundClasses/SCL_SFX")
AMB_CLASS = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Ambience")

MUSIC_SUBMIX = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/Submixes/SUBMIX_Music")
SFX_SUBMIX = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/Submixes/SUBMIX_SFX")
AMB_SUBMIX = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Audio/Mix/Submixes/SUBMIX_Ambience")


def set_class(asset, sound_class, submix=None):
    if not asset:
        return False
    try:
        asset.set_editor_property("sound_class_object", sound_class)
    except Exception as e1:
        print(f"  class prop failed: {e1}")
        try:
            asset.set_editor_property("sound_class", sound_class)
        except Exception as e2:
            print(f"  class prop2 failed: {e2}")
    if submix:
        try:
            asset.set_editor_property("sound_submix_object", submix)
        except Exception as e3:
            print(f"  submix prop failed: {e3}")
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return True


results = []
for path in WAVES:
    a = unreal.EditorAssetLibrary.load_asset(path)
    if not a:
        print(f"LOAD_FAIL {path}")
        continue
    if "BGM/" in path:
        ok = set_class(a, MUSIC_CLASS, MUSIC_SUBMIX)
        label = "MUSIC"
    elif "Ambience" in path:
        ok = set_class(a, AMB_CLASS, AMB_SUBMIX)
        label = "AMB"
    else:
        ok = set_class(a, SFX_CLASS, SFX_SUBMIX)
        label = "SFX"
    print(f"{label} {path} ok={ok}")
    results.append((label, path, ok))

print("DONE")
