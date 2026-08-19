"""What landscape material do the dreamprint stack levels use?"""
from __future__ import annotations

import unreal

LEVELS = (
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream",
)

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for level in LEVELS:
    leaf = level.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
        print(leaf, "MISSING")
        continue
    les.load_level(level)
    mats = set()
    for actor in eas.get_all_level_actors() or []:
        if type(actor).__name__ != "Landscape":
            continue
        for comp in actor.get_components_by_class(unreal.LandscapeComponent) or []:
            try:
                lm = comp.get_editor_property("landscape_material")
                if lm:
                    mats.add(str(lm.get_path_name()).split(".")[0])
            except Exception:
                pass
    print(leaf, sorted(mats) or ["(no landscape)"])