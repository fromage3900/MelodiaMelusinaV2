"""Build an interactable 16-step, 4-lane musical PCG sequencer.

Each generated pad is a gameplay actor. Walking over a pad emits a stable
step/lane/MIDI event, presses the pad with a spring return, and forwards the
event through the grid host for Blueprint, audio, or rhythm-game logic.
"""

from __future__ import annotations

from dataclasses import dataclass


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Sequencer"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_MusicStepSequencer"
PROFILE_PATH = f"{DEST_FOLDER}/DA_MusicStepGridProfile"
PAD_MESH_PATH = "/Engine/BasicShapes/Cube.Cube"
PAD_MATERIAL_PATH = "/Game/EnvSandbox/PCG/Musical/MI_Piano_Keybed"


@dataclass(frozen=True)
class StepSpec:
    step: int
    lane: int
    midi_note: int
    x: float
    y: float
    z: float
    seed: int


def _set_if_present(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _enum_value(unreal, enum_name: str, *member_names: str):
    enum = getattr(unreal, enum_name, None)
    if enum is None:
        raise RuntimeError(f"Unreal enum is unavailable: {enum_name}")
    for member_name in member_names:
        value = getattr(enum, member_name, None)
        if value is not None:
            return value
    raise RuntimeError(f"None of {member_names} exists on {enum_name}")


def _resolve_actor_class(unreal, class_name: str):
    cls = getattr(unreal, class_name, None)
    if cls is not None:
        return cls
    cls = unreal.load_class(None, f"/Script/BS_GodFile.{class_name}")
    if cls is None:
        raise RuntimeError(f"Could not resolve generated actor class {class_name}")
    return cls


def build_step_specs(steps: int = 16, lanes: int = 4, step_spacing: float = 86.0, lane_spacing: float = 96.0, pad_height: float = 12.0, lane_notes: tuple[int, ...] = (60, 62, 64, 67)) -> tuple[StepSpec, ...]:
    specs: list[StepSpec] = []
    for lane in range(lanes):
        midi_note = lane_notes[lane] if lane < len(lane_notes) else 60 + lane
        y = (lane - (lanes - 1) * 0.5) * lane_spacing
        for step in range(steps):
            x = (step - (steps - 1) * 0.5) * step_spacing
            specs.append(
                StepSpec(
                    step=step,
                    lane=lane,
                    midi_note=midi_note,
                    x=x,
                    y=y,
                    z=pad_height * 0.5,
                    seed=(lane << 8) | step,
                )
            )
    return tuple(specs)


def _make_point(unreal, spec: StepSpec, pad_width: float = 68.0, pad_depth: float = 68.0, pad_height: float = 12.0):
    point = unreal.PCGPoint()
    point.set_editor_property(
        "transform",
        unreal.Transform(
            location=unreal.Vector(spec.x, spec.y, spec.z),
            rotation=unreal.Rotator(0.0, 0.0, 0.0),
            scale=unreal.Vector(1.0, 1.0, 1.0),
        ),
    )
    point.set_editor_property("density", 1.0)
    point.set_editor_property("seed", int(spec.seed))
    point.set_editor_property("bounds_min", unreal.Vector(-pad_width * 0.5, -pad_depth * 0.5, -pad_height * 0.5))
    point.set_editor_property("bounds_max", unreal.Vector(pad_width * 0.5, pad_depth * 0.5, pad_height * 0.5))
    return point


def _configure_spawn_settings(unreal, settings, actor_class) -> None:
    if not _set_if_present(settings, "option", _enum_value(unreal, "PCGSpawnActorOption", "NO_MERGING", "NoMerging")):
        raise RuntimeError("PCGMusicStepSequencer spawn option could not be set to NoMerging")
    if not _set_if_present(settings, "attach_options", _enum_value(unreal, "PCGAttachOptions", "ATTACHED", "Attached")):
        raise RuntimeError("PCGMusicStepSequencer attach option could not be set to Attached")
    if not _set_if_present(settings, "template_actor_class", actor_class):
        raise RuntimeError("PCGMusicStepSequencer template actor class could not be assigned")
    for prop, value in {
        "post_spawn_function_names": ["InitializeFromPCGPoint"],
        "tags_to_add_on_actors": ["PCG_MusicStepPad", "PCG_MusicStepSequencer"],
        "delete_actors_before_generation": True,
        "force_disable_actor_parsing": True,
        "actor_label": "Music Step Pad",
    }.items():
        if not _set_if_present(settings, prop, value):
            raise RuntimeError(f"PCGMusicStepSequencer spawn property failed: {prop}")


def _create_or_update_profile(unreal):
    if unreal.EditorAssetLibrary.does_asset_exist(PROFILE_PATH):
        profile = unreal.load_asset(PROFILE_PATH)
    else:
        if not unreal.EditorAssetLibrary.does_directory_exist(DEST_FOLDER):
            unreal.EditorAssetLibrary.make_directory(DEST_FOLDER)
        profile_class = getattr(unreal, "PCGMusicStepGridProfile", None)
        if profile_class is None:
            profile_class = unreal.load_class(None, "/Script/BS_GodFile.PCGMusicStepGridProfile")
        if profile_class is None:
            raise RuntimeError("PCGMusicStepGridProfile is unavailable; compile/reload the C++ module first")
        profile = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_MusicStepGridProfile", DEST_FOLDER, profile_class, unreal.DataAssetFactory()
        )
    if not profile:
        raise RuntimeError(f"Could not create or load {PROFILE_PATH}")

    dimensions_cls = getattr(unreal, "PCGMusicStepGridDimensions", None)
    if dimensions_cls is None:
        dimensions_cls = getattr(unreal, "FPCGMusicStepGridDimensions", None)
    if dimensions_cls is None:
        raise RuntimeError("PCGMusicStepGridDimensions is unavailable")
    dimensions = dimensions_cls()
    for prop, value in {
        "steps": 16,
        "lanes": 4,
        "step_spacing": 86.0,
        "lane_spacing": 96.0,
        "pad_width": 68.0,
        "pad_depth": 68.0,
        "pad_height": 12.0,
        "press_depth": 5.0,
        "spring_stiffness": 1100.0,
        "spring_damping": 100.0,
        "press_trigger_height": 10.0,
    }.items():
        _set_if_present(dimensions, prop, value)
    _set_if_present(profile, "dimensions", dimensions)
    _set_if_present(profile, "first_midi_note", 60)
    _set_if_present(profile, "lane_midi_notes", [60, 62, 64, 67])
    _set_if_present(profile, "pad_mesh", unreal.load_asset(PAD_MESH_PATH))
    if unreal.EditorAssetLibrary.does_asset_exist(PAD_MATERIAL_PATH):
        _set_if_present(profile, "pad_material", unreal.load_asset(PAD_MATERIAL_PATH))
    unreal.EditorAssetLibrary.save_asset(PROFILE_PATH)
    return profile


def build_sequencer_graph(force: bool = True, create_profile: bool = True) -> dict:
    import unreal
    import pcg_graph_builder as graph_builder

    specs = build_step_specs()
    if len(specs) != 64:
        raise AssertionError("music step sequencer must contain 64 pads")

    graph, created = graph_builder.load_or_create_graph(GRAPH_PATH, DEST_FOLDER, force=force)
    graph_builder.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-700, 0)
    graph.get_output_node().set_node_position(700, 0)
    create_node, create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -300, 0)
    create_settings.set_editor_property("points_to_create", [_make_point(unreal, spec) for spec in specs])
    local_space = getattr(getattr(unreal, "PCGCoordinateSpace", None), "LOCAL", None)
    if local_space is not None:
        _set_if_present(create_settings, "coordinate_space", local_space)

    spawn_node, spawn_settings = graph_builder.add_node(graph, "PCGSpawnActorSettings", 200, 0)
    _configure_spawn_settings(unreal, spawn_settings, _resolve_actor_class(unreal, "PCGMusicStepPad"))
    graph.add_edge(create_node, "Out", spawn_node, "In")
    graph.add_edge(spawn_node, "Out", graph.get_output_node(), "Out")
    _set_if_present(graph, "is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH)

    profile = _create_or_update_profile(unreal) if create_profile else None
    result = {
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH if profile else None,
        "created": created,
        "steps": 16,
        "lanes": 4,
        "pad_points": len(specs),
        "lane_midi_notes": [60, 62, 64, 67],
        "interaction": "player overlap -> spring pad press -> step/lane/MIDI event",
    }
    unreal.log(f"[PCG Music Sequencer] built {result}")
    return result


if __name__ == "__main__":
    print(build_sequencer_graph())
