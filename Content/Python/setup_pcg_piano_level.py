"""Create a small, dedicated light-test level for the interactive PCG piano."""

from __future__ import annotations

import json


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_PianoKeyboard"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_PianoKeyboard"
PROFILE_PATH = f"{LEVEL_DIR}/DA_PianoKeyboardProfile"
KEYBED_MESH_PATH = f"{LEVEL_DIR}/SM_Piano_Keybed"
KEYBED_MATERIAL_PATH = f"{LEVEL_DIR}/MI_Piano_Keybed"


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
    if label in existing and existing[label]:
        actor = existing[label]
    else:
        actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(*rotation))
        actor.set_actor_label(label)
        existing[label] = actor
    return actor


def build_level() -> dict:
    import unreal

    for path in (LEVEL_DIR,):
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        if not les.new_level(LEVEL_PATH):
            raise RuntimeError(f"Could not create {LEVEL_PATH}")
    elif not les.load_level(LEVEL_PATH):
        raise RuntimeError(f"Could not load {LEVEL_PATH}")

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    keybed_mesh = unreal.EditorAssetLibrary.load_asset(KEYBED_MESH_PATH)
    keybed_material = unreal.EditorAssetLibrary.load_asset(KEYBED_MATERIAL_PATH)
    if not graph or not profile or not keybed_mesh:
        raise RuntimeError("Build piano assets and graph before creating the proof level")

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (eas.get_all_level_actors() or [])}

    keyboard_class = _resolve_class(unreal, "PCGPianoKeyboard")
    if keyboard_class is None:
        raise RuntimeError("PCGPianoKeyboard class is unavailable; compile the C++ module first")
    keyboard = _spawn_or_reuse(unreal, eas, existing, keyboard_class, "PCG Piano Keyboard", (0.0, 0.0, 0.0))
    _set_if_present(keyboard, "profile", profile)
    _set_if_present(keyboard, "piano_graph", graph)

    pcg_component = keyboard.get_component_by_class(unreal.PCGComponent)
    if pcg_component:
        if hasattr(pcg_component, "set_graph"):
            pcg_component.set_graph(graph)
        else:
            _set_if_present(pcg_component, "graph", graph)
        if hasattr(pcg_component, "generate"):
            pcg_component.generate(True)
        elif hasattr(pcg_component, "generate_local"):
            pcg_component.generate_local(True)

    # Keybed: the baked mesh is centered, so its top sits at Z=0.
    keybed = _spawn_or_reuse(unreal, eas, existing, unreal.StaticMeshActor, "Piano Keybed", (0.0, 0.0, -7.5))
    smc = keybed.static_mesh_component
    smc.set_editor_property("static_mesh", keybed_mesh)
    if keybed_material:
        smc.set_material(0, keybed_material)

    # Lightweight floor and neutral studio backdrop. BasicShapes/Cube is an
    # engine asset, so the level has no external content dependency.
    floor = _spawn_or_reuse(unreal, eas, existing, unreal.StaticMeshActor, "Piano Test Floor", (0.0, 0.0, -25.0))
    floor.static_mesh_component.set_editor_property(
        "static_mesh", unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    )
    floor.set_actor_scale3d(unreal.Vector(16.0, 5.0, 0.1))

    sun = _spawn_or_reuse(unreal, eas, existing, unreal.DirectionalLight, "Piano Key Light", (0.0, 0.0, 500.0), (-35.0, -35.0, 0.0))
    sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
    _set_if_present(sun_component, "intensity", 5.0)
    _set_if_present(sun_component, "light_color", unreal.Color(255, 242, 218, 255))

    skylight = _spawn_or_reuse(unreal, eas, existing, unreal.SkyLight, "Piano Sky Fill", (0.0, 0.0, 500.0))
    _set_if_present(skylight.get_component_by_class(unreal.SkyLightComponent), "intensity", 0.8)

    point = _spawn_or_reuse(unreal, eas, existing, unreal.PointLight, "Piano Warm Fill", (0.0, -180.0, 240.0))
    point_component = point.get_component_by_class(unreal.PointLightComponent)
    _set_if_present(point_component, "intensity", 1800.0)
    _set_if_present(point_component, "attenuation_radius", 750.0)
    _set_if_present(point_component, "light_color", unreal.Color(255, 192, 132, 255))

    player_start = _spawn_or_reuse(unreal, eas, existing, unreal.PlayerStart, "Piano Player Start", (0.0, -360.0, 110.0), (0.0, 90.0, 0.0))
    _set_if_present(player_start, "player_start_tag", "PianoTest")

    camera = _spawn_or_reuse(unreal, eas, existing, unreal.CineCameraActor, "Piano Overview Camera", (0.0, -720.0, 420.0), (-18.0, 90.0, 0.0))

    les.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "keyboard": "PCG Piano Keyboard",
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "generation": "kicked",
        "test_setup": "neutral studio, floor, warm fill, player start, overview camera",
    }
    unreal.log(f"[PCG Piano] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
