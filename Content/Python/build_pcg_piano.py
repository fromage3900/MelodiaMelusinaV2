"""Build the reusable PCG piano keyboard graph and its profile asset.

Run in the Unreal Editor Python environment after the BS_GodFile module has
compiled:

    import build_pcg_piano as piano
    piano.build_piano_graph(force=True)

The graph deliberately uses authored point arrays rather than a volume sampler:
the piano is a deterministic instrument layout, and this avoids the project's
known zero-output VolumeSampler behavior while retaining native PCG spawning.
"""

from __future__ import annotations

from pcg_piano_layout import PianoDimensions, build_layout, split_layout


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_PianoKeyboard"
PROFILE_PATH = f"{DEST_FOLDER}/DA_PianoKeyboardProfile"
WHITE_MESH_PATH = f"{DEST_FOLDER}/SM_PianoKey_White_Bevel"
BLACK_MESH_PATH = f"{DEST_FOLDER}/SM_PianoKey_Black_Bevel"
KEYBED_MESH_PATH = f"{DEST_FOLDER}/SM_Piano_Keybed"
WHITE_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Ivory"
BLACK_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Ebony"
KEYBED_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Keybed"


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


def _make_point(unreal, spec):
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
    point.set_editor_property(
        "bounds_min", unreal.Vector(-spec.width * 0.5, -spec.depth * 0.5, -spec.height * 0.5)
    )
    point.set_editor_property(
        "bounds_max", unreal.Vector(spec.width * 0.5, spec.depth * 0.5, spec.height * 0.5)
    )
    return point


def _resolve_actor_class(unreal, class_name: str):
    cls = getattr(unreal, class_name, None)
    if cls is not None:
        return cls
    cls = unreal.load_class(None, f"/Script/BS_GodFile.{class_name}")
    if cls is None:
        raise RuntimeError(f"Could not resolve generated actor class {class_name}")
    return cls


def _configure_spawn_settings(unreal, settings, actor_class, tag: str, label: str) -> None:
    no_merging = _enum_value(unreal, "PCGSpawnActorOption", "NO_MERGING", "NoMerging")
    attached = _enum_value(unreal, "PCGAttachOptions", "ATTACHED", "Attached")
    if not _set_if_present(settings, "option", no_merging):
        raise RuntimeError("PCGSpawnActorSettings.option could not be set to NoMerging")
    if not _set_if_present(settings, "attach_options", attached):
        raise RuntimeError("PCGSpawnActorSettings.attach_options could not be set to Attached")

    if hasattr(settings, "set_template_actor_class"):
        settings.set_template_actor_class(actor_class)
    elif not _set_if_present(settings, "template_actor_class", actor_class):
        raise RuntimeError("PCGSpawnActorSettings template actor class could not be assigned")

    required = {
        "post_spawn_function_names": ["InitializeFromPCGPoint"],
        "tags_to_add_on_actors": [tag, "PCG_PianoKey"],
        "delete_actors_before_generation": True,
        "force_disable_actor_parsing": True,
        "actor_label": label,
    }
    for prop, value in required.items():
        if not _set_if_present(settings, prop, value):
            raise RuntimeError(f"PCGSpawnActorSettings.{prop} could not be set")


def _create_or_update_profile(unreal, dimensions: PianoDimensions, force: bool):
    if unreal.EditorAssetLibrary.does_asset_exist(PROFILE_PATH):
        profile = unreal.load_asset(PROFILE_PATH)
    else:
        if not unreal.EditorAssetLibrary.does_directory_exist(DEST_FOLDER):
            unreal.EditorAssetLibrary.make_directory(DEST_FOLDER)
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        profile_class = getattr(unreal, "PCGPianoKeyboardProfile", None)
        if profile_class is None:
            profile_class = unreal.load_class(None, "/Script/BS_GodFile.PCGPianoKeyboardProfile")
        if profile_class is None:
            raise RuntimeError("PCGPianoKeyboardProfile is unavailable; compile the C++ module first")
        profile = tools.create_asset(
            "DA_PianoKeyboardProfile",
            DEST_FOLDER,
            profile_class,
            unreal.DataAssetFactory(),
        )

    if not profile:
        raise RuntimeError(f"Could not create or load {PROFILE_PATH}")

    dimensions_struct_cls = getattr(unreal, "PCGPianoKeyboardDimensions", None)
    if dimensions_struct_cls is None:
        dimensions_struct_cls = getattr(unreal, "FPCGPianoKeyboardDimensions", None)
    if dimensions_struct_cls is None:
        raise RuntimeError("PCGPianoKeyboardDimensions is unavailable; compile the C++ module first")

    values = {
        "first_midi_note": 21,
        "last_midi_note": 108,
        "dimensions": dimensions_struct_cls(),
    }
    dims = values["dimensions"]
    dim_values = {
        "white_key_width": dimensions.white_width,
        "white_key_depth": dimensions.white_depth,
        "white_key_height": dimensions.white_height,
        "black_key_width": dimensions.black_width,
        "black_key_depth": dimensions.black_depth,
        "black_key_height": dimensions.black_height,
        "inter_key_gap": dimensions.inter_key_gap,
    }
    for prop, value in dim_values.items():
        _set_if_present(dims, prop, float(value))
    values["dimensions"] = dims
    for prop, value in values.items():
        _set_if_present(profile, prop, value)

    mesh_paths = {
        "white_key_mesh": WHITE_MESH_PATH,
        "black_key_mesh": BLACK_MESH_PATH,
        "keybed_mesh": KEYBED_MESH_PATH,
    }
    for prop, path in mesh_paths.items():
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            _set_if_present(profile, prop, unreal.load_asset(path))

    material_paths = {
        "white_key_material": WHITE_MATERIAL_PATH,
        "black_key_material": BLACK_MATERIAL_PATH,
        "keybed_material": KEYBED_MATERIAL_PATH,
    }
    for prop, path in material_paths.items():
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            _set_if_present(profile, prop, unreal.load_asset(path))

    unreal.EditorAssetLibrary.save_asset(PROFILE_PATH)
    return profile


def build_piano_graph(force: bool = True, create_profile: bool = True) -> dict:
    import unreal
    import pcg_graph_builder as graph_builder

    dimensions = PianoDimensions()
    specs = build_layout()
    white_specs, black_specs = split_layout(specs)
    if (len(specs), len(white_specs), len(black_specs)) != (88, 52, 36):
        raise AssertionError("full piano layout must contain 88 notes, 52 white keys, and 36 black keys")

    graph, created = graph_builder.load_or_create_graph(GRAPH_PATH, DEST_FOLDER, force=force)
    graph_builder.clear_graph_nodes(graph)
    input_node = graph.get_input_node()
    output_node = graph.get_output_node()
    input_node.set_node_position(-800, 0)
    output_node.set_node_position(800, 0)

    white_create, white_create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -500, -160)
    black_create, black_create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -500, 160)
    white_create_settings.set_editor_property("points_to_create", [_make_point(unreal, spec) for spec in white_specs])
    black_create_settings.set_editor_property("points_to_create", [_make_point(unreal, spec) for spec in black_specs])

    local_space = getattr(getattr(unreal, "PCGCoordinateSpace", None), "LOCAL", None)
    if local_space is not None:
        _set_if_present(white_create_settings, "coordinate_space", local_space)
        _set_if_present(black_create_settings, "coordinate_space", local_space)

    white_spawn, white_spawn_settings = graph_builder.add_node(graph, "PCGSpawnActorSettings", -120, -160)
    black_spawn, black_spawn_settings = graph_builder.add_node(graph, "PCGSpawnActorSettings", -120, 160)
    _configure_spawn_settings(
        unreal,
        white_spawn_settings,
        _resolve_actor_class(unreal, "PCGPianoWhiteKey"),
        "PCG_PianoWhite",
        "Piano White Key",
    )
    _configure_spawn_settings(
        unreal,
        black_spawn_settings,
        _resolve_actor_class(unreal, "PCGPianoBlackKey"),
        "PCG_PianoBlack",
        "Piano Black Key",
    )

    graph.add_edge(white_create, "Out", white_spawn, "In")
    graph.add_edge(black_create, "Out", black_spawn, "In")
    graph.add_edge(white_spawn, "Out", output_node, "Out")
    graph.add_edge(black_spawn, "Out", output_node, "Out")
    _set_if_present(graph, "is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH)

    profile = _create_or_update_profile(unreal, dimensions, force) if create_profile else None
    result = {
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH if profile else None,
        "created": created,
        "total_points": len(specs),
        "white_points": len(white_specs),
        "black_points": len(black_specs),
        "strategy": "PCGCreatePoints -> PCGSpawnActor(NoMerging) -> InitializeFromPCGPoint",
    }
    unreal.log(f"[PCG Piano] built {result}")
    return result


if __name__ == "__main__":
    print(build_piano_graph())
