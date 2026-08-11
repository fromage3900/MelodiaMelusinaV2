"""Apply V5 premium outline to ZenForestTest's PPV.

ZenForestTest was deliberately NOT saved after the premium outline pass,
so its PPV_NikkiDream still carries MI_StorybookOutline_GameplayStandard
from the canonical nikki_render_post_process setup.

This script:
  1. Loads ZenForestTest
  2. Updates PPV_NikkiDream to use MI_Outline_PremiumV3_Hero at weight 1.0
  3. Saves the level

Run in-editor with ZenForestTest loaded:
    import apply_zenforest_v5_outline as z; z.run()
"""
from __future__ import annotations

LEVEL = "/Game/ZenForestTest"
OUTLINE_INSTANCE = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_Outline_PremiumV3_Hero"
GRADE_INSTANCE = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero"
SKY_INSTANCE = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StarryNight_Hero"
PPV_LABEL = "PPV_NikkiDream"
PRIORITY = 10.0


def run() -> str:
    import unreal
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if not les.load_level(LEVEL):
        raise RuntimeError(f"Failed to load {LEVEL}")

    ppv = next((a for a in eas.get_all_level_actors() or []
                if a.get_actor_label() == PPV_LABEL), None)
    if not ppv:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label(PPV_LABEL)
        ppv.set_editor_property("unbound", True)
        ppv.set_editor_property("priority", PRIORITY)

    def load(path):
        return unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None

    mats = []
    for path in (OUTLINE_INSTANCE, GRADE_INSTANCE, SKY_INSTANCE):
        mat = load(path)
        if mat:
            mats.append(unreal.WeightedBlendable(1.0, mat))
        else:
            print(f"  [WARN] Missing: {path}")

    settings = ppv.get_editor_property("settings")
    settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(mats))
    ppv.set_editor_property("settings", settings)

    les.save_current_level()
    msg = f"ZenForestTest PPV updated | {len(mats)} blendables | outline={OUTLINE_INSTANCE}"
    print(msg)
    return msg


if __name__ == "__main__":
    run()
