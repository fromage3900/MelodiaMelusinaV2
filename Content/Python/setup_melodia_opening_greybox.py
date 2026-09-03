"""Author the first visual-slice greybox on the two Melodia opening maps.

This script owns only actors labelled GB_Dream_*, GB_Morning_*, and
PCG_MelodiaOpening_*. It is safe to rerun and deliberately reserves PCG
volumes without binding an unrelated biome graph to the authored opening.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
REPORT = ROOT / "Saved" / "Melodia" / "opening_greybox_setup.json"
LEVELS = {
    "dream": "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate",
    "morning": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
}
KIT = "/Game/EnvSandbox/Greybox_Kit"
MESH = {
    "cube": f"{KIT}/SM_Greybox_Cube_1m",
    "floor": f"{KIT}/SM_Greybox_Floor_4x4",
    "pillar": f"{KIT}/SM_Greybox_Column_05",
    "arch": f"{KIT}/SM_arch_06",
    "torii": f"{KIT}/SM_Greybox_Torii",
    "rock_a": f"{KIT}/SM_Greybox_Rock_A",
    "rock_b": f"{KIT}/SM_Greybox_Rock_B",
    "gem": f"{KIT}/SM_Greybox_Gem",
    "half_wall": f"{KIT}/SM_Greybox_HalfWall_4",
}


def _load(path: str):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"Required greybox mesh missing: {path}")
    return asset


def _clear(eas, prefixes):
    for actor in list(eas.get_all_level_actors()):
        if actor.get_actor_label().startswith(prefixes):
            eas.destroy_actor(actor)


def _spawn(eas, label, mesh_key, location, scale=(1, 1, 1), rotation=(0, 0, 0), tags=()):
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(_load(MESH[mesh_key]))
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.static_mesh_component.set_collision_profile_name("BlockAll")
    actor.tags = [unreal.Name(tag) for tag in tags]
    return actor


def _pcg_volume(eas, label, location, scale, tags):
    volume = eas.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(*location), unreal.Rotator())
    if not volume:
        raise RuntimeError(f"Could not spawn {label}")
    volume.set_actor_label(label)
    volume.set_actor_scale3d(unreal.Vector(*scale))
    volume.tags = [unreal.Name(tag) for tag in tags]
    # Intentionally unbound: this marks the authored envelope for the later
    # DreamIntensity graph rather than introducing an unrelated foliage graph.
    component = volume.get_component_by_class(unreal.PCGComponent)
    if component:
        component.set_editor_property("activated", False)
    return volume


def build_dream(eas):
    _clear(eas, ("GB_Dream_", "PCG_MelodiaOpening_Dream_"))
    made = []
    add = lambda *args, **kwargs: made.append(_spawn(eas, *args, **kwargs))
    route = ("Melodia", "Dreamstate", "PrimaryRoute")
    framing = ("Melodia", "Dreamstate", "Framing")
    # Two broad approach terraces make the bridge feel entered and exited, not
    # simply dropped into a void. The existing Venetian bridge remains central.
    add("GB_Dream_StartTerrace", "floor", (-900, 0, 0), (1.5, 1.2, 0.25), tags=route)
    add("GB_Dream_MidTerrace", "floor", (0, 0, 0), (1.15, 0.9, 0.22), tags=route)
    add("GB_Dream_WakeTerrace", "floor", (900, 0, 0), (1.5, 1.2, 0.25), tags=route)
    # Framing pillars become a visual metronome: stable -> strained -> portal.
    for index, x in enumerate((-600, -220, 220, 600)):
        height = 1.0 if abs(x) > 300 else 1.45
        for side in (-1, 1):
            add(f"GB_Dream_Pillar_{index}_{side}", "pillar", (x, side * 300, 95), (0.8, 0.8, height), tags=framing)
    add("GB_Dream_WakeTorii", "torii", (900, 0, 80), (1.4, 1.4, 1.4), rotation=(0, 90, 0), tags=("Melodia", "Dreamstate", "PortalFrame"))
    # Dissonance is readable before the gameplay trigger: broken side-rocks and
    # a small focal gem are non-blocking, asymmetric, and kept off the route.
    for index, (x, y, key, scale) in enumerate(((-90, -420, "rock_a", (0.8, 0.8, 0.8)), (80, 410, "rock_b", (0.7, 0.7, 0.7)), (220, -400, "rock_a", (0.55, 0.55, 0.55)))):
        add(f"GB_Dream_DissonanceRock_{index}", key, (x, y, 30), scale, tags=("Melodia", "Dissonance", "NoRouteBlock"))
    add("GB_Dream_DissonanceFocus", "gem", (0, 230, 115), (0.45, 0.45, 0.45), tags=("Melodia", "Dissonance", "Readability"))
    made.append(_pcg_volume(eas, "PCG_MelodiaOpening_Dream_Atmosphere", (0, 0, 240), (11, 8, 3), ("Melodia", "PCG", "Dreamstate", "Reserved_DreamIntensity")))
    return [actor.get_actor_label() for actor in made]


def build_morning(eas):
    _clear(eas, ("GB_Morning_", "PCG_MelodiaOpening_Morning_"))
    made = []
    add = lambda *args, **kwargs: made.append(_spawn(eas, *args, **kwargs))
    # These markers describe the bedroom's three readable verbs: wake, notice
    # the companion, and leave. They do not alter the imported room shell.
    add("GB_Morning_WakeRug", "floor", (-220, -40, 8), (0.55, 0.55, 0.05), tags=("Melodia", "Bedroom", "WakeZone"))
    add("GB_Morning_ResonancePlinth", "floor", (160, 130, 65), (0.35, 0.35, 0.18), tags=("Melodia", "Bedroom", "SirMelodious", "InteractionZone"))
    add("GB_Morning_ResonanceGem", "gem", (105, 155, 92), (0.18, 0.18, 0.18), tags=("Melodia", "Bedroom", "SirMelodious", "Readability"))
    for index, x in enumerate((-430, 430)):
        add(f"GB_Morning_ThresholdPillar_{index}", "pillar", (x, 240, 105), (0.5, 0.5, 0.9), tags=("Melodia", "Bedroom", "ExitFrame"))
    add("GB_Morning_ExitArch", "arch", (0, 315, 100), (1.1, 1.1, 1.1), rotation=(0, 90, 0), tags=("Melodia", "Bedroom", "ExitFrame"))
    made.append(_pcg_volume(eas, "PCG_MelodiaOpening_Morning_Dressing", (0, 0, 170), (4, 4, 2), ("Melodia", "PCG", "Bedroom", "Reserved_Dressing")))
    return [actor.get_actor_label() for actor in made]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results = {}
    for name, path in LEVELS.items():
        if not levels.load_level(path):
            raise RuntimeError(f"Could not load {path}")
        actors = build_dream(eas) if name == "dream" else build_morning(eas)
        levels.save_current_level()
        results[name] = {"level": path, "actors": actors}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaGreybox] Built opening compositions -> {REPORT}")


if __name__ == "__main__":
    main()
