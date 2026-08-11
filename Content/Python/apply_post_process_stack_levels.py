"""Apply post-process outline stack to levels that lack blendables."""
from __future__ import annotations

import portfolio_scene_integration as scene

LEVELS = (
    "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
    "/Game/EnvSandbox/_Template/L_Template",
)


def main() -> int:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            continue
        les.load_level(level)
        ppv = scene.find_or_spawn_ppv(eas)
        names = scene.apply_post_process_stack(ppv)
        unreal.log(f"[ApplyPPStack] {level} blendables={names}")
        les.save_current_level()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
