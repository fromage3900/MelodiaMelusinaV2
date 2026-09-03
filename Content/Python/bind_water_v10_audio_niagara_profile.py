"""Guarded text-injection manifest for the project-owned Water v10 profile.

Run only after a normal editor restart has loaded the latest C++ reflection:
    unreal.EditorAssetLibrary.load_asset(...)

The script writes profile references and budgets only. It never edits engine or
third-party assets and refuses to save when a required project asset is absent.
"""

import json
import unreal


PROFILE_PATH = "/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default"

ASSET_FIELDS = {
    "ContactDataChannel": "/Game/EnvSandbox/Water/v10/NDC_MelodiaWaterContact",
    "ContactSystem": "/Game/EnvSandbox/Water/v10/NS_MelodiaWaterContact",
    "RippleSystem": "/Game/Melodia/VFX/NS_Melusina_Ripple",
    "SplashSystem": "/Game/Melodia/VFX/NS_Melusina_Splash",
    "FluidSystem": "/Game/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP2D_Pool",
    "SurfaceMovementMetaSound": "/Game/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceMovement",
    "SurfaceEntryMetaSound": "/Game/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceEntry",
    "UnderwaterBubbleMetaSound": "/Game/EnvSandbox/Water/v10/Audio/MS_Water_UnderwaterBubble",
    "WaterImpactMetaSound": "/Game/EnvSandbox/Water/v10/Audio/MS_Water_Impact",
    "ReemergenceMetaSound": "/Game/EnvSandbox/Water/v10/Audio/MS_Water_Reemergence",
    "AudioConcurrency": "/Game/EnvSandbox/Water/v10/Audio/SC_WaterV10_AudioConcurrency",
    "AudioAttenuation": "/Game/EnvSandbox/Water/v10/Audio/SA_WaterV10_3D_Attenuation",
    "QuantumReactionSystem": "/Game/Melodia/VFX/NS_Melusina_ChaosDrift",
    "QuantumEntropySystem": "/Game/Melodia/VFX/NS_Melusina_EntropyDust",
}


def main():
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not profile:
        raise RuntimeError("Missing Water v10 profile: %s" % PROFILE_PATH)

    missing_properties = []
    missing_assets = []
    loaded = {}
    for field, asset_path in ASSET_FIELDS.items():
        try:
            profile.get_editor_property(field)
        except Exception:
            missing_properties.append(field)
            continue
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not asset:
            missing_assets.append(asset_path)
            continue
        loaded[field] = asset

    if missing_properties:
        raise RuntimeError(
            "Reflection is stale; restart the editor before binding: %s"
            % ", ".join(missing_properties)
        )
    if missing_assets:
        raise RuntimeError("Missing required project assets: %s" % ", ".join(missing_assets))

    for field, asset in loaded.items():
        profile.set_editor_property(field, asset)
    profile.set_editor_property("bUseQuantumReactionVFX", True)
    profile.set_editor_property("MaxAudioEventsPerSecond", 8)
    profile.set_editor_property("MaxAudioVoices", 4)
    profile.set_editor_property("MaxQuantumReactionEventsPerSecond", 2)
    profile.set_editor_property("MaxContactsPerSecond", 60)
    profile.set_editor_property("Provenance", "Project-owned water-v10 audio + Nikki quantum Niagara bridge; source waves remain referenced.")
    unreal.EditorAssetLibrary.save_asset(PROFILE_PATH)

    print(json.dumps({
        "ok": True,
        "profile": PROFILE_PATH,
        "bound_fields": sorted(loaded.keys()),
        "budgets": {
            "MaxAudioEventsPerSecond": 8,
            "MaxAudioVoices": 4,
            "MaxQuantumReactionEventsPerSecond": 2,
        },
    }, indent=2))


main()
