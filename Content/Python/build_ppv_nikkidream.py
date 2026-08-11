"""Build/configure a PPV_NikkiDream post-process volume ACTOR in the current level.

NOTE: PostProcessVolume CANNOT be a Blueprint parent class (UE throws a blocking
modal - that froze the editor previously). So this spawns/configures a
PostProcessVolume ACTOR directly in the currently-open level (intended:
zenforesttest, user-approved) instead of creating a Blueprint. Idempotent: reuses
an existing PPV_NikkiDream actor if present.

Stacks the project's existing PP materials as blendables + UDS-aware native
settings. Exposure overrides are left OFF so Ultra Dynamic Sky keeps driving
exposure/fog; this volume only adds bloom/vignette/CA/grain/grade on top.

Run inside the editor (Monolith run_python) with zenforesttest open:
  import build_ppv_nikkidream as b; b.build()
"""
from __future__ import annotations

BLENDABLES = [
    "/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline",
    "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst",
    "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",
]


def build() -> str:
    import unreal
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ppv = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "PPV_NikkiDream":
            ppv = a
            break
    if ppv is None:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label("PPV_NikkiDream")
    ppv.set_editor_property("unbound", True)     # affect the whole level
    ppv.set_editor_property("priority", 1.0)
    s = ppv.get_editor_property("settings")

    def ov(name, val):
        s.set_editor_property(f"override_{name}", True)
        s.set_editor_property(name, val)

    ov("bloom_intensity", 0.7)
    ov("vignette_intensity", 0.35)
    ov("scene_fringe_intensity", 1.2)      # chromatic aberration
    ov("film_grain_intensity", 0.12)
    ov("color_saturation", unreal.Vector4(1.05, 1.05, 1.08, 1.0))
    ov("color_contrast", unreal.Vector4(1.04, 1.04, 1.06, 1.0))
    ov("color_gain_shadows", unreal.Vector4(0.96, 0.97, 1.04, 1.0))     # lavender/teal shadows
    ov("color_gain_highlights", unreal.Vector4(1.04, 1.00, 0.98, 1.0))  # warm-rose highlights

    arr = []
    for mp in BLENDABLES:
        mm = unreal.EditorAssetLibrary.load_asset(mp)
        if mm:
            arr.append(unreal.WeightedBlendable(1.0, mm))
    s.set_editor_property("weighted_blendables", unreal.WeightedBlendables(arr))
    ppv.set_editor_property("settings", s)

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.save_current_level()
    msg = f"PPV_NikkiDream actor configured in current level | blendables={len(arr)} | unbound"
    print(msg)
    return msg


if __name__ == "__main__":
    build()
