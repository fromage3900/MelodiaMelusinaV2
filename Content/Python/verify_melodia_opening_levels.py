"""Validate the authored Melodia opening-map contract without modifying maps."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


LEVEL_DIR = "/Game/Melodia/Levels/Opening"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Melodia" / "opening_level_verification.json"

REQUIRED = {
    "L_Melodia_Dreamstate": {
        "Dreamstate_PlayerStart",
        "Dreamstate_BifrostBridge",
        "Dreamstate_OpeningState",
        "Dreamstate_FirstDissonanceBeat",
        "Dreamstate_WakePortal",
    },
    "L_MelusinaMorning": {
        "Morning_PlayerStart",
        "Morning_RoomShell",
        "Morning_SirMelodious_STATIC_INTRO",
        "Morning_OpeningState",
    },
}

GREYBOX_REQUIRED = {
    "L_Melodia_Dreamstate": {
        "GB_Dream_StartTerrace",
        "GB_Dream_MidTerrace",
        "GB_Dream_WakeTerrace",
        "GB_Dream_WakeTorii",
        "GB_Dream_DissonanceFocus",
        "PCG_MelodiaOpening_Dream_Atmosphere",
    },
    "L_MelusinaMorning": {
        "GB_Morning_WakeRug",
        "GB_Morning_ResonancePlinth",
        "GB_Morning_ExitArch",
        "PCG_MelodiaOpening_Morning_Dressing",
    },
}

LIGHTING_REQUIRED = {
    "L_Melodia_Dreamstate": {
        "LT_Melodia_Dream_Pillar_0",
        "LT_Melodia_Dream_Wake",
        "LT_Melodia_Dream_Dissonance",
    },
    "L_MelusinaMorning": {
        "LT_Melodia_Morning_Bed",
        "LT_Melodia_Morning_Sir",
        "LT_Melodia_Morning_Exit",
    },
}


def _verify_level(level_name: str, required_labels: set[str]) -> dict:
    path = f"{LEVEL_DIR}/{level_name}"
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(path):
        raise RuntimeError(f"Could not load {path}")

    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    missing = sorted(required_labels - set(by_label))
    if missing:
        raise RuntimeError(f"{level_name} missing required actors: {missing}")

    greybox_missing = sorted(GREYBOX_REQUIRED[level_name] - set(by_label))
    if greybox_missing:
        raise RuntimeError(f"{level_name} missing required greybox actors: {greybox_missing}")

    lighting_missing = sorted(LIGHTING_REQUIRED[level_name] - set(by_label))
    if lighting_missing:
        raise RuntimeError(f"{level_name} missing required lighting actors: {lighting_missing}")

    result = {"path": path, "actors": sorted(by_label), "valid": not missing, "greybox_actor_count": len(GREYBOX_REQUIRED[level_name]), "lighting_actor_count": len(LIGHTING_REQUIRED[level_name])}
    if level_name == "L_Melodia_Dreamstate":
        portal = by_label["Dreamstate_WakePortal"]
        destination = str(portal.get_editor_property("destination_level_name"))
        if destination != "/Game/ZenForestTest":
            raise RuntimeError(f"Dreamstate portal destination is incorrect: {destination}")
        scalar = by_label["Dreamstate_OpeningState"].get_editor_property("dissonance").get_editor_property("songcraft_scalar")
        if scalar >= 1.0:
            raise RuntimeError(f"Dreamstate Dissonance scalar must be below 1.0, got {scalar}")
        bond = by_label["Dreamstate_OpeningState"].get_editor_property("resonance_bond")
        if bond.is_songcraft_empowered():
            raise RuntimeError("Songcraft must not be empowered before Sir Melodious reunites with Melusina")
        beat = by_label["Dreamstate_FirstDissonanceBeat"]
        if "MelodiaDissonanceBeat" not in beat.get_class().get_name():
            raise RuntimeError("Dreamstate Dissonance actor is the wrong class")
        result.update({"portal_destination": destination, "songcraft_scalar": scalar, "songcraft_empowered": False, "dissonance_beat": beat.get_class().get_name()})
    else:
        sir = by_label["Morning_SirMelodious_STATIC_INTRO"]
        presentation_meshes = sir.get_editor_property("presentation_meshes")
        missing_meshes = [component.get_name() for component in presentation_meshes if not component.get_editor_property("skeletal_mesh_asset")]
        if missing_meshes:
            raise RuntimeError(f"Sir Melodious presentation components lack source meshes: {missing_meshes}")
        mesh_paths = [component.get_editor_property("skeletal_mesh_asset").get_path_name() for component in presentation_meshes]
        if not any("SK_SirMelodious_Rigged" in path for path in mesh_paths):
            raise RuntimeError("Bedroom Sir Melodious actor is not using the canonical rigged mesh")
        reunion_trigger = sir.get_component_by_class(unreal.SphereComponent)
        if not reunion_trigger:
            raise RuntimeError("Bedroom Sir Melodious actor is missing its reunion approach trigger")
        reunion_light = sir.get_component_by_class(unreal.PointLightComponent)
        if not reunion_light:
            raise RuntimeError("Bedroom Sir Melodious actor is missing its reunion visual cue")
        if not sir.get_editor_property("depart_after_reunion"):
            raise RuntimeError("Bedroom Sir Melodious departure beat is disabled")
        departure_destination = str(sir.get_editor_property("departure_destination_level"))
        if departure_destination != "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate":
            raise RuntimeError(f"Sir Melodious departure destination is incorrect: {departure_destination}")
        result.update({"sir_melodious_class": sir.get_class().get_name(), "sir_melodious_mesh_count": len(presentation_meshes), "sir_melodious_meshes": mesh_paths, "sir_reunion_trigger": reunion_trigger.get_name(), "sir_reunion_light": reunion_light.get_name(), "departure_destination": departure_destination})
    return result


def main():
    result = {name: _verify_level(name, labels) for name, labels in REQUIRED.items()}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaOpening] Verified opening maps -> {REPORT}")


if __name__ == "__main__":
    main()
