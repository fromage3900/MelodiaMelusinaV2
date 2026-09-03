"""Create a dedicated light proof level for the interactable music sequencer."""

from __future__ import annotations

import json


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Sequencer"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_MusicStepSequencer"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_MusicStepSequencer"
PROFILE_PATH = f"{LEVEL_DIR}/DA_MusicStepGridProfile"


def _set_if_present(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _resolve_class(unreal, name: str):
    cls = getattr(unreal, name, None)
    if cls is not None:
        return cls
    return unreal.load_class(None, f"/Script/BS_GodFile.{name}")


def _spawn_or_reuse(unreal, eas, existing, cls, label: str, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
    actor = existing.get(label)
    if actor:
        return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(label)
    existing[label] = actor
    return actor


def build_level() -> dict:
    import unreal

    if not unreal.EditorAssetLibrary.does_directory_exist(LEVEL_DIR):
        unreal.EditorAssetLibrary.make_directory(LEVEL_DIR)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        if not les.new_level(LEVEL_PATH):
            raise RuntimeError(f"Could not create {LEVEL_PATH}")
    elif not les.load_level(LEVEL_PATH):
        raise RuntimeError(f"Could not load {LEVEL_PATH}")

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("Build the music sequencer graph and profile before creating its proof level")

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (eas.get_all_level_actors() or [])}
    grid_class = _resolve_class(unreal, "PCGMusicStepGrid")
    if grid_class is None:
        raise RuntimeError("PCGMusicStepGrid class is unavailable; compile/reload the C++ module first")
    grid = _spawn_or_reuse(unreal, eas, existing, grid_class, "PCG Music Step Sequencer", (0.0, 0.0, 0.0))
    _set_if_present(grid, "profile", profile)
    _set_if_present(grid, "music_graph", graph)

    pcg_component = grid.get_component_by_class(unreal.PCGComponent)
    if pcg_component:
        if hasattr(pcg_component, "set_graph"):
            pcg_component.set_graph(graph)
        else:
            _set_if_present(pcg_component, "graph", graph)
        if hasattr(pcg_component, "generate"):
            pcg_component.generate(True)
        elif hasattr(pcg_component, "generate_local"):
            pcg_component.generate_local(True)

    floor = _spawn_or_reuse(unreal, eas, existing, unreal.StaticMeshActor, "Music Sequencer Floor", (0.0, 0.0, -20.0))
    floor.static_mesh_component.set_editor_property(
        "static_mesh", unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    )
    floor.set_actor_scale3d(unreal.Vector(16.0, 4.0, 0.1))

    sun = _spawn_or_reuse(unreal, eas, existing, unreal.DirectionalLight, "Music Sequencer Key Light", (0.0, 0.0, 500.0), (-35.0, -35.0, 0.0))
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    _set_if_present(sun_component, "intensity", 4.0)
    _set_if_present(sun_component, "light_color", unreal.Color(214, 228, 255, 255))
    fill = _spawn_or_reuse(unreal, eas, existing, unreal.PointLight, "Music Sequencer Warm Fill", (0.0, -260.0, 240.0))
    fill_component = fill.get_component_by_class(unreal.PointLightComponent)
    _set_if_present(fill_component, "intensity", 1700.0)
    _set_if_present(fill_component, "attenuation_radius", 850.0)
    _set_if_present(fill_component, "light_color", unreal.Color(255, 180, 120, 255))

    _spawn_or_reuse(unreal, eas, existing, unreal.PlayerStart, "Music Sequencer Player Start", (0.0, -520.0, 120.0), (0.0, 90.0, 0.0))
    _spawn_or_reuse(unreal, eas, existing, unreal.CineCameraActor, "Music Sequencer Overview Camera", (0.0, -900.0, 600.0), (-25.0, 90.0, 0.0))
    les.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_pads": 64,
        "interaction": "walk across lanes to emit step/lane/MIDI events",
    }
    unreal.log(f"[PCG Music Sequencer] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
