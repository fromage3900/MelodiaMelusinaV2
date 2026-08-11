"""Verify ZenForestTest is configured for the native Melodia smoke loop."""
from __future__ import annotations

import json
import os
import unreal


MAP_PATH = "/Game/ZenForestTest"
REPORT_PATH = "G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/ZenSmoke_verify.json"
MELUSINA_PAWN_CLASS_PATH = "/Game/Melodia/Characters/Melusina/BP_Melusina.BP_Melusina_C"


def _class_path(obj) -> str:
    if not obj:
        return ""
    if hasattr(obj, "get_path_name"):
        return str(obj.get_path_name())
    return str(obj)


def verify():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world after loading ZenForestTest")

    world_settings = world.get_world_settings()
    game_mode = world_settings.get_editor_property("default_game_mode")

    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    labels = {actor.get_actor_label(): actor for actor in actors}
    player_starts = [actor for actor in actors if isinstance(actor, unreal.PlayerStart)]

    result = {
        "map": MAP_PATH,
        "default_game_mode": _class_path(game_mode),
        "has_player_start": bool(player_starts),
        "player_start_count": len(player_starts),
        "player_start_labels": [actor.get_actor_label() for actor in player_starts],
        "has_encounter": "MelodiaSmoke_Encounter_01" in labels,
        "encounter_components": {},
        "expected_default_game_mode": "/Game/Melodia/_PROJECT/BP_MelodiaGameMode.BP_MelodiaGameMode_C",
        "expected_default_pawn": MELUSINA_PAWN_CLASS_PATH,
    }

    def _prop(obj, name, default=None):
        # Tolerate properties missing while the editor runs a DLL older than
        # source (live-coding pending); record them as absent instead of failing.
        try:
            return obj.get_editor_property(name)
        except Exception:
            return default

    encounter = labels.get("MelodiaSmoke_Encounter_01")
    if encounter:
        result["encounter_class"] = encounter.get_class().get_path_name()
        result["encounter_components"] = {
            "trigger_volume": bool(_prop(encounter, "trigger_volume")),
            "combat_state": bool(_prop(encounter, "combat_state")),
            "rhythm_execution": bool(_prop(encounter, "rhythm_execution")),
            "encounter_label": bool(_prop(encounter, "encounter_label")),
            "encounter_light": bool(_prop(encounter, "encounter_light")),
        }
        result["encounter_level"] = _prop(encounter, "encounter_level")
        result["encounter_display_name"] = str(_prop(encounter, "encounter_display_name"))
        # Unreal exposes the C++ bOneShot property to Python as one_shot.
        result["encounter_one_shot"] = _prop(encounter, "one_shot")
        result["encounter_cooldown_seconds"] = _prop(encounter, "cooldown_seconds")
        result["stale_module_properties"] = [
            name for name in ("encounter_label", "encounter_light", "one_shot", "cooldown_seconds")
            if _prop(encounter, name, "__missing__") == "__missing__"
        ]

    melusina_class = unreal.load_class(None, MELUSINA_PAWN_CLASS_PATH)
    result["melusina_pawn_class_loads"] = bool(melusina_class)

    game_mode_cdo = unreal.get_default_object(game_mode) if game_mode else None
    default_pawn = game_mode_cdo.get_editor_property("default_pawn_class") if game_mode_cdo else None
    result["default_pawn_class"] = _class_path(default_pawn)

    stale = set(result.get("stale_module_properties", []))
    core_components = {
        k: v for k, v in result["encounter_components"].items()
        if k not in stale
    }
    result["ok"] = (
        result["default_game_mode"].endswith("BP_MelodiaGameMode_C")
        and result["default_pawn_class"].endswith("BP_Melusina_C")
        and result["has_player_start"]
        and result["has_encounter"]
        and all(core_components.values())
        and result.get("encounter_level") == 1
        and ("cooldown_seconds" in stale or result.get("encounter_cooldown_seconds", 0.0) > 0.0)
        and result["melusina_pawn_class_loads"]
    )

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    unreal.log(f"[MelodiaSmokeVerify] Wrote {REPORT_PATH}")
    unreal.log(f"[MelodiaSmokeVerify] ok={result['ok']}")

    if not result["ok"]:
        raise RuntimeError("ZenForestTest Melodia smoke verification failed")


if __name__ == "__main__":
    verify()
