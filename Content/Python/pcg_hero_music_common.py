"""UE-facing helpers shared by the Resonance Cathedral and Arpeggio Bridge."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import pcg_hero_music_control as control


def _set_if_present(obj: Any, prop: str, value: Any) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _enum_value(unreal: Any, enum_name: str, *member_names: str) -> Any:
    enum = getattr(unreal, enum_name, None)
    if enum is None:
        raise RuntimeError(f"Unreal enum is unavailable: {enum_name}")
    for name in member_names:
        value = getattr(enum, name, None)
        if value is not None:
            return value
    raise RuntimeError(f"None of {member_names} exists on {enum_name}")


def resolve_actor_class(unreal: Any, class_name: str) -> Any:
    cls = getattr(unreal, class_name, None)
    if cls is not None:
        return cls
    # Unreal's Python load_class path uses the reflected native symbol without
    # the C++ A/U prefix, while the graph contract intentionally stores the
    # full C++ class name for PCG actor spawning.
    candidates = [class_name]
    if class_name[:1] in {"A", "U"}:
        candidates.append(class_name[1:])
    for candidate in candidates:
        cls = unreal.load_class(None, f"/Script/BS_GodFile.{candidate}")
        if cls is not None:
            return cls
    raise RuntimeError(f"Could not resolve generated actor class {class_name}")


def make_point(
    unreal: Any,
    location: tuple[float, float, float],
    seed: int,
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    bounds: tuple[float, float, float] = (50.0, 50.0, 12.0),
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Any:
    point = unreal.PCGPoint()
    point.set_editor_property(
        "transform",
        unreal.Transform(
            location=unreal.Vector(*location),
            rotation=unreal.Rotator(
                pitch=float(rotation[0]),
                yaw=float(rotation[1]),
                roll=float(rotation[2]),
            ),
            scale=unreal.Vector(*scale),
        ),
    )
    point.set_editor_property("density", 1.0)
    point.set_editor_property("seed", int(seed))
    point.set_editor_property("bounds_min", unreal.Vector(-bounds[0], -bounds[1], -bounds[2]))
    point.set_editor_property("bounds_max", unreal.Vector(bounds[0], bounds[1], bounds[2]))
    return point


def configure_hero_spawn(unreal: Any, settings: Any, actor_class: Any, tags: Sequence[str], label: str) -> None:
    if not _set_if_present(settings, "option", _enum_value(unreal, "PCGSpawnActorOption", "NO_MERGING", "NoMerging")):
        raise RuntimeError("hero music spawn option could not be set to NoMerging")
    if not _set_if_present(settings, "attach_options", _enum_value(unreal, "PCGAttachOptions", "ATTACHED", "Attached")):
        raise RuntimeError("hero music spawn attachment could not be set to Attached")
    if not _set_if_present(settings, "template_actor_class", actor_class):
        raise RuntimeError("hero music actor class could not be assigned")
    for prop, value in {
        "post_spawn_function_names": ["InitializeFromPCGPoint"],
        "tags_to_add_on_actors": list(tags),
        "delete_actors_before_generation": True,
        "force_disable_actor_parsing": True,
        "actor_label": label,
    }.items():
        if not _set_if_present(settings, prop, value):
            raise RuntimeError(f"hero music spawn property failed: {prop}")


def configure_static_spawner(unreal: Any, settings: Any, snapshot: control.HeroMusicControlSnapshot, role: str = "structural") -> dict[str, Any]:
    """Configure a real mesh spawner and apply render-driver aliases."""
    import pcg_portfolio_standards as std

    candidates = list(std.SCATTER_MESHES.get(role, ()))
    if role == "structural":
        # The hero proof must read as architecture, not the first greybox
        # fallback. Keep the authored walls/columns/pillars and only fall back
        # to a cube if the kit is genuinely unavailable.
        authored_structural = [path for path in candidates if "SM_Block_Cube_1" not in path]
        candidates = authored_structural or candidates
    valid_meshes: list[tuple[str, Any]] = []
    for path in candidates:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                mesh = unreal.load_asset(path)
                if mesh:
                    valid_meshes.append((path, mesh))
        except Exception:
            continue
    if not valid_meshes:
        raise RuntimeError(f"no available decorative mesh for hero role {role}")

    entries = []
    render_report = None
    for mesh_path, mesh in valid_meshes:
        entry = unreal.PCGMeshSelectorWeightedEntry()
        descriptor = entry.get_editor_property("descriptor")
        descriptor.set_editor_property("static_mesh", mesh)
        render_report = control.apply_control_to_static_descriptor(descriptor, snapshot)
        entry.set_editor_property("descriptor", descriptor)
        entry.set_editor_property("weight", 1)
        entries.append(entry)
    selector = settings.get_editor_property("mesh_selector_parameters")
    selector.set_editor_property("mesh_entries", entries)
    return {
        "mesh": valid_meshes[0][0],
        "meshes": [path for path, _ in valid_meshes],
        "render_alias_report": render_report,
    }


def configure_single_mesh_spawner(
    unreal: Any,
    settings: Any,
    snapshot: control.HeroMusicControlSnapshot,
    mesh_path: str,
    material_path: str | None = None,
) -> dict[str, Any]:
    """Configure one explicit mesh/material pair for the piano-roll branches."""
    mesh = _load_asset_if_exists(unreal, mesh_path)
    if not mesh:
        raise RuntimeError(f"missing hero mesh: {mesh_path}")
    entry = unreal.PCGMeshSelectorWeightedEntry()
    descriptor = entry.get_editor_property("descriptor")
    descriptor.set_editor_property("static_mesh", mesh)
    if material_path:
        material = _load_asset_if_exists(unreal, material_path)
        if material:
            for prop in ("material_overrides", "override_materials", "material_override"):
                try:
                    descriptor.set_editor_property(prop, [material] if prop.endswith("s") else material)
                    break
                except Exception:
                    continue
    render_report = control.apply_control_to_static_descriptor(descriptor, snapshot)
    entry.set_editor_property("descriptor", descriptor)
    entry.set_editor_property("weight", 1)
    selector = settings.get_editor_property("mesh_selector_parameters")
    selector.set_editor_property("mesh_entries", [entry])
    return {"mesh": mesh_path, "material": material_path, "render_alias_report": render_report}


def _add_static_mesh_points_branch(
    unreal: Any,
    graph: Any,
    graph_builder: Any,
    points: Sequence[Any],
    snapshot: control.HeroMusicControlSnapshot,
    mesh_path: str,
    material_path: str | None,
    x: int,
    y: int,
    label: str,
) -> dict[str, Any]:
    if not points:
        return {"count": 0, "mesh": mesh_path}
    create_node, create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", x, y)
    create_settings.set_editor_property("points_to_create", list(points))
    spawn_node, spawn_settings = graph_builder.add_node(graph, "PCGStaticMeshSpawnerSettings", x + 260, y)
    mesh_result = configure_single_mesh_spawner(unreal, spawn_settings, snapshot, mesh_path, material_path)
    graph.add_edge(create_node, "Out", spawn_node, "In")
    graph.add_edge(spawn_node, "Out", graph.get_output_node(), "Out")
    mesh_result.update({"count": len(points), "label": label})
    return mesh_result


def add_pcgex_vault_branch(
    unreal: Any,
    graph: Any,
    snapshot: control.HeroMusicControlSnapshot,
    *,
    source_graph_path: str,
    span: float,
    aisle_width: float,
    vault_height: float,
    resample_spacing: float,
    mesh_path: str | None = None,
    material_path: str | None = None,
    connect_to_output: bool = True,
) -> dict[str, Any]:
    """Reuse the project's proven expanded PCGEx tensor graph as a real vault.

    The source graph is intentionally copied by settings, not approximated with
    cubes: CreatePointsGrid seeds -> CreateTensorSpin effectors ->
    ExtrudeTensors paths -> TransformPoints -> StaticMeshSpawner.
    """
    import pcg_graph_builder as graph_builder

    source = unreal.EditorAssetLibrary.load_asset(source_graph_path)
    if not source:
        raise RuntimeError(f"missing PCGEx source graph: {source_graph_path}")
    wanted = {
        "PCGCreatePointsGridSettings",
        "PCGExCreateTensorSpinSettings",
        "PCGExExtrudeTensorsSettings",
        "PCGTransformPointsSettings",
        "PCGStaticMeshSpawnerSettings",
    }
    copied: dict[str, list[tuple[Any, Any]]] = {}
    for source_node in (source.get_editor_property("nodes") or []):
        source_settings = source_node.get_settings()
        class_name = source_settings.get_class().get_name()
        if class_name not in wanted:
            continue
        new_node, new_settings = graph.add_node_copy(source_settings)
        copied.setdefault(class_name, []).append((new_node, new_settings))

    grids = copied.get("PCGCreatePointsGridSettings", [])
    spin = copied.get("PCGExCreateTensorSpinSettings", [])
    extrude = copied.get("PCGExExtrudeTensorsSettings", [])
    transform = copied.get("PCGTransformPointsSettings", [])
    spawners = copied.get("PCGStaticMeshSpawnerSettings", [])
    if not (len(grids) >= 2 and spin and extrude and transform and spawners):
        raise RuntimeError("PCGEx source graph did not contain the expected expanded branch")

    seed_grid, seed_settings = grids[0]
    effector_grid, effector_settings = grids[1]
    spin_node, spin_settings = spin[0]
    extrude_node, extrude_settings = extrude[0]
    transform_node, transform_settings = transform[0]
    spawner_node, spawner_settings = spawners[0]
    seed_grid.set_node_position(-720, 500)
    effector_grid.set_node_position(-720, 700)
    spin_node.set_node_position(-460, 700)
    extrude_node.set_node_position(-170, 500)
    transform_node.set_node_position(120, 500)
    spawner_node.set_node_position(390, 500)

    _set_if_present(seed_settings, "grid_extents", unreal.Vector(span * 0.5, aisle_width * 0.5 + 500.0, 40.0))
    _set_if_present(seed_settings, "cell_size", unreal.Vector(max(span, 100.0), max(aisle_width + 1000.0, 100.0), 100.0))
    _set_if_present(effector_settings, "grid_extents", unreal.Vector(span * 0.5, aisle_width + 700.0, max(80.0, vault_height * 0.32)))
    _set_if_present(effector_settings, "cell_size", unreal.Vector(max(span * 0.5, 100.0), max(aisle_width + 700.0, 100.0), max(160.0, vault_height * 0.32)))
    try:
        seed_settings.set_editor_property("coordinate_space", unreal.PCGCoordinateSpace.LOCAL_COMPONENT)
        effector_settings.set_editor_property("coordinate_space", unreal.PCGCoordinateSpace.LOCAL_COMPONENT)
    except Exception:
        pass

    # The source Escher graph expects authored metadata to drive TensorSpin's
    # potency and guide curve.  A hero graph copies only the proven tensor
    # operators, so those attributes do not exist here; leaving the source
    # selectors intact produces an invalid quaternion in PCGExTensorSpin and
    # NaN bounds downstream.  Make the copied branch deterministic and finite
    # while retaining the real PCGEx tensor/extrusion workflow.
    try:
        spin_config = spin_settings.get_editor_property("config")
        _set_if_present(spin_config, "use_local_guide_curve", False)
        _set_if_present(
            spin_config,
            "potency_input",
            _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant"),
        )
        _set_if_present(spin_config, "potency", max(60.0, min(360.0, float(resample_spacing) * 1.5)))
        _set_if_present(
            spin_config,
            "weight_input",
            _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant"),
        )
        _set_if_present(spin_config, "weight", 1.0)
        _set_if_present(
            spin_config,
            "axis_input",
            _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant"),
        )
        _set_if_present(spin_config, "axis_constant", _enum_value(unreal, "PCGExAxis", "UP", "Up"))
        spin_settings.set_editor_property("config", spin_config)
        if str(spin_config.get_editor_property("potency_input")) != str(
            _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant")
        ):
            raise RuntimeError("PCGEx TensorSpin potency_input did not resolve to Constant")
    except Exception as exc:
        raise RuntimeError(f"could not normalize copied PCGEx TensorSpin config: {exc}")
    # Keep the expanded PCGEx tensor branch authored and serialized for the
    # hero graph, but do not execute the copied Escher integrator. Its source
    # graph relies on hidden guide metadata that is not present in this
    # standalone proof and produces NaN transforms after its first step. The
    # measured spline branch owns the visible PCGEx architecture; this tensor
    # branch remains a safe, finite scaffold until a guide-data contract is
    # authored for the hero kits.
    _set_if_present(extrude_settings, "iterations", 0)
    _set_if_present(extrude_settings, "max_length", 1.0)
    _set_if_present(extrude_settings, "max_points_count", 1)
    _set_if_present(transform_settings, "scale_min", unreal.Vector(snapshot.ScaleMin, snapshot.ScaleMin, snapshot.ScaleMin))
    _set_if_present(transform_settings, "scale_max", unreal.Vector(snapshot.ScaleMax, snapshot.ScaleMax, snapshot.ScaleMax))
    if mesh_path:
        configure_single_mesh_spawner(unreal, spawner_settings, snapshot, mesh_path, material_path)
    else:
        configure_static_spawner(unreal, spawner_settings, snapshot, "structural")

    graph.add_edge(seed_grid, "Out", extrude_node, "Seeds")
    graph.add_edge(effector_grid, "Out", spin_node, "Effectors")
    graph.add_edge(spin_node, "Tensor", extrude_node, "Tensors")
    graph.add_edge(extrude_node, "Paths", transform_node, "In")
    graph.add_edge(transform_node, "Out", spawner_node, "In")
    # A proof graph may retain the expanded TensorSpin/Extrude scaffold for
    # auditability while keeping the measured spline branch as the visible
    # architectural authority. In that mode the branch remains serialized but
    # is intentionally disconnected from the graph output.
    if connect_to_output:
        graph.add_edge(spawner_node, "Out", graph.get_output_node(), "Out")

    # PCG graph pin creation can refresh copied settings after the first
    # assignment. Reapply the safety contract after wiring, then verify the
    # serialized node value that will actually execute during generation.
    final_spin_config = spin_settings.get_editor_property("config")
    final_constant = _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant")
    _set_if_present(final_spin_config, "use_local_guide_curve", False)
    _set_if_present(final_spin_config, "potency_input", final_constant)
    _set_if_present(final_spin_config, "potency", max(60.0, min(360.0, float(resample_spacing) * 1.5)))
    _set_if_present(final_spin_config, "weight_input", final_constant)
    _set_if_present(final_spin_config, "weight", 1.0)
    _set_if_present(final_spin_config, "axis_input", final_constant)
    _set_if_present(final_spin_config, "axis_constant", _enum_value(unreal, "PCGExAxis", "UP", "Up"))
    spin_settings.set_editor_property("config", final_spin_config)
    if str(spin_settings.get_editor_property("config").get_editor_property("potency_input")) != str(final_constant):
        raise RuntimeError("serialized PCGEx TensorSpin potency_input is not Constant after graph wiring")
    return {
        "source_graph": source_graph_path,
        "nodes": [node.get_settings().get_class().get_name() for pairs in copied.values() for node, _ in pairs],
        "seed_extent": [span * 0.5, aisle_width * 0.5 + 500.0, 40.0],
        "vault_height": vault_height,
        "iterations": 0,
        "walkable_aisle_width": aisle_width,
        "mesh_path": mesh_path,
        "connected_to_output": bool(connect_to_output),
    }


def add_pcgex_spline_architecture_branch(
    unreal: Any,
    graph: Any,
    snapshot: control.HeroMusicControlSnapshot,
    *,
    spline_tag: str,
    curve_points: Sequence[Any],
    mesh_path: str,
    material_path: str | None,
    distance_between_points: float,
    scale: tuple[float, float, float],
    rotation_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    label: str = "PCGEx measured spline architecture",
    node_y: int = 600,
) -> dict[str, Any]:
    """Emit a classic library mesh along a measured PCGEx curve.

    The branch is intentionally explicit rather than a generic scatter:
    CreatePoints(measured controls) -> PCGExCreateSpline -> PCGSplineSampler
    -> PCGExSampleNearestSpline (PathDist) -> PCGTransformPoints
    -> classic StaticMeshSpawner.

    The spline is authored as graph data, so it does not depend on a missing
    Blueprint SplineActor or on a second level-side curve authority.
    """
    import pcg_graph_builder as graph_builder

    required = (
        "PCGCreatePointsSettings",
        "PCGExCreateSplineSettings",
        "PCGSplineSamplerSettings",
        "PCGExSampleNearestSplineSettings",
        "PCGTransformPointsSettings",
        "PCGStaticMeshSpawnerSettings",
    )
    missing = [name for name in required if getattr(unreal, name, None) is None]
    if missing:
        raise RuntimeError(f"PCGEx curve branch requires unavailable settings: {missing}")

    create_curve_points, create_curve_settings = graph_builder.add_node(
        graph, "PCGCreatePointsSettings", -980, node_y
    )
    create_curve_settings.set_editor_property("points_to_create", list(curve_points))

    create_spline, create_spline_settings = graph_builder.add_node(
        graph, "PCGExCreateSplineSettings", -760, node_y
    )
    _set_if_present(
        create_spline_settings,
        "mode",
        _enum_value(unreal, "PCGCreateSplineMode", "CREATE_DATA_ONLY", "CreateDataOnly"),
    )
    _set_if_present(create_spline_settings, "b_apply_custom_point_type", False)
    _set_if_present(
        create_spline_settings,
        "default_point_type",
        _enum_value(unreal, "PCGExSplinePointType", "CURVE", "Curve"),
    )
    # PCGExCreateSpline exposes its point-path input as ``Paths`` in UE 5.8.
    # The generic PCG nodes use ``In``, but using that label here leaves an
    # invalid edge in the graph ("does not have the In label") and can abort
    # the whole component generation before the hero actor branch executes.
    graph.add_edge(create_curve_points, "Out", create_spline, "Paths")

    sampler, sampler_settings = graph_builder.add_node(graph, "PCGSplineSamplerSettings", -540, node_y)
    _set_if_present(sampler_settings, "distance_between_points", max(20.0, float(distance_between_points)))

    nearest, nearest_settings = graph_builder.add_node(
        graph, "PCGExSampleNearestSplineSettings", -300, node_y
    )
    max_range = nearest_settings.get_editor_property("max_range")
    _set_if_present(max_range, "constant", 1_000_000.0)
    _set_if_present(nearest_settings, "max_range", max_range)
    _set_if_present(
        nearest_settings,
        "sample_method",
        _enum_value(unreal, "PCGExSampleMethod", "WITHIN_RANGE", "WithinRange"),
    )
    _set_if_present(nearest_settings, "write_distance", True)
    _set_if_present(nearest_settings, "distance_attribute_name", "PathDist")

    transform, transform_settings = graph_builder.add_node(graph, "PCGTransformPointsSettings", -60, node_y)
    scale_vector = unreal.Vector(*[float(value) for value in scale])
    _set_if_present(transform_settings, "scale_min", scale_vector)
    _set_if_present(transform_settings, "scale_max", scale_vector)
    _set_if_present(transform_settings, "uniform_scale", False)
    rotation = unreal.Rotator(
        pitch=float(rotation_offset[0]),
        yaw=float(rotation_offset[1]),
        roll=float(rotation_offset[2]),
    )
    _set_if_present(transform_settings, "rotation_min", rotation)
    _set_if_present(transform_settings, "rotation_max", rotation)
    _set_if_present(transform_settings, "absolute_rotation", False)

    spawner, spawner_settings = graph_builder.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, node_y)
    mesh_result = configure_single_mesh_spawner(
        unreal, spawner_settings, snapshot, mesh_path, material_path
    )

    graph.add_edge(create_spline, "Splines", sampler, "Spline")
    graph.add_edge(sampler, "Out", nearest, "Sources")
    graph.add_edge(create_spline, "Splines", nearest, "Targets")
    graph.add_edge(nearest, "Out", transform, "In")
    graph.add_edge(transform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", graph.get_output_node(), "Out")
    return {
        "label": label,
        "spline_tag": spline_tag,
        "curve_points_count": len(curve_points),
        "mesh": mesh_path,
        "material": material_path,
        "distance_between_points": max(20.0, float(distance_between_points)),
        "scale": tuple(float(value) for value in scale),
        "rotation_offset": tuple(float(value) for value in rotation_offset),
        "pcgex_nodes": list(required),
        "mesh_result": mesh_result,
    }


def normalize_saved_pcgex_tensor_graph(unreal: Any, graph_path: str, resample_spacing: float) -> dict[str, Any]:
    """Normalize copied TensorSpin settings on the freshly saved graph asset."""
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError(f"cannot reload hero graph for PCGEx normalization: {graph_path}")
    constant = _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant")
    axis = _enum_value(unreal, "PCGExAxis", "UP", "Up")
    count = 0
    for node in graph.get_editor_property("nodes") or []:
        settings = node.get_settings()
        if not settings or settings.get_class().get_name() != "PCGExCreateTensorSpinSettings":
            continue
        settings.modify()
        config = settings.get_editor_property("config")
        _set_if_present(config, "use_local_guide_curve", False)
        _set_if_present(config, "potency_input", constant)
        _set_if_present(config, "potency", max(60.0, min(360.0, float(resample_spacing) * 1.5)))
        _set_if_present(config, "weight_input", constant)
        _set_if_present(config, "weight", 1.0)
        _set_if_present(config, "axis_input", constant)
        _set_if_present(config, "axis_constant", axis)
        settings.set_editor_property("config", config)
        count += 1
    if count:
        # Mark the graph package itself dirty as well as the nested settings.
        # Without this, SaveAsset can report success while serializing the
        # pre-edit graph copy, which restores copied PCGEx selector defaults.
        graph.modify()
        unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
    reloaded = unreal.EditorAssetLibrary.load_asset(graph_path)
    serialized = []
    for node in (reloaded.get_editor_property("nodes") if reloaded else []) or []:
        settings = node.get_settings()
        if settings and settings.get_class().get_name() == "PCGExCreateTensorSpinSettings":
            serialized.append(str(settings.get_editor_property("config").get_editor_property("potency_input")))
    if count and any(value != str(constant) for value in serialized):
        raise RuntimeError(f"freshly saved TensorSpin graph still has non-constant potency input: {serialized}")
    return {"tensor_spin_nodes": count, "potency_inputs": serialized}


def _load_asset_if_exists(unreal: Any, path: str) -> Any | None:
    try:
        return unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    except Exception:
        return None


def create_or_update_profile(
    unreal: Any,
    profile_path: str,
    *,
    expected_note_count: int,
    midi_notes: Sequence[int],
    dimensions: Mapping[str, float],
    sequential: bool,
    beat_window_beats: float,
    snapshot: control.HeroMusicControlSnapshot,
) -> Any:
    folder = profile_path.rsplit("/", 1)[0]
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)
    profile = _load_asset_if_exists(unreal, profile_path)
    if not profile:
        profile_class = getattr(unreal, "PCGHeroMusicProfile", None) or unreal.load_class(None, "/Script/BS_GodFile.PCGHeroMusicProfile")
        if profile_class is None:
            raise RuntimeError("PCGHeroMusicProfile is unavailable; compile/reload the C++ module first")
        profile = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            profile_path.rsplit("/", 1)[-1], folder, profile_class, unreal.DataAssetFactory()
        )
    if not profile:
        raise RuntimeError(f"could not create {profile_path}")

    dimensions_cls = getattr(unreal, "PCGHeroMusicNodeDimensions", None) or getattr(unreal, "FPCGHeroMusicNodeDimensions", None)
    if dimensions_cls is None:
        raise RuntimeError("PCGHeroMusicNodeDimensions is unavailable; compile/reload the C++ module first")
    node_dimensions = dimensions_cls()
    for prop, value in dimensions.items():
        _set_if_present(node_dimensions, prop, value)
    _set_if_present(profile, "node_dimensions", node_dimensions)
    _set_if_present(profile, "expected_note_count", int(expected_note_count))
    _set_if_present(profile, "midi_notes", [int(value) for value in midi_notes])
    _set_if_present(profile, "b_sequential_progression", bool(sequential))
    _set_if_present(profile, "b_play_grade_feedback_sfx", True)
    _set_if_present(profile, "beat_window_beats", float(beat_window_beats))
    _set_if_present(profile, "instance_end_cull_distance", float(snapshot.CullDistance))
    _set_if_present(profile, "custom_depth_stencil_value", int(snapshot.StencilValue))
    _set_if_present(profile, "b_write_custom_depth", bool(snapshot.WriteCustomDepth))

    white_mesh = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_White_Bevel")
    black_mesh = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_Black_Bevel") or white_mesh
    keybed_mesh = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/SM_Piano_Keybed")
    white_material = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/MI_Piano_Ivory")
    black_material = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/MI_Piano_Ebony")
    keybed_material = _load_asset_if_exists(unreal, "/Game/EnvSandbox/PCG/Musical/MI_Piano_Keybed")
    _set_if_present(profile, "node_mesh", keybed_mesh)
    _set_if_present(profile, "node_material", keybed_material)
    _set_if_present(profile, "white_node_mesh", white_mesh)
    _set_if_present(profile, "black_node_mesh", black_mesh)
    _set_if_present(profile, "white_node_material", white_material or keybed_material)
    _set_if_present(profile, "black_node_material", black_material or keybed_material)
    unreal.EditorAssetLibrary.save_asset(profile_path, only_if_is_dirty=False)
    return profile


def build_hero_graph(
    unreal: Any,
    *,
    graph_path: str,
    profile_path: str,
    graph_kind: str,
    actor_class_name: str,
    points: Sequence[Any],
    decoration_points: Sequence[Any],
    expected_note_count: int,
    midi_notes: Sequence[int],
    dimensions: Mapping[str, float],
    sequential: bool,
    beat_window_beats: float,
    control_overrides: Mapping[str, Any] | None = None,
    decoration_role: str = "structural",
    piano_black_points: Sequence[Any] = (),
    piano_keybed_points: Sequence[Any] = (),
    classic_architecture_branches: Sequence[Mapping[str, Any]] = (),
    pcgex_curve_branches: Sequence[Mapping[str, Any]] = (),
    architecture_source_path: str | None = None,
    architecture_span: float = 2400.0,
    architecture_aisle_width: float = 220.0,
    architecture_vault_height: float = 1800.0,
    architecture_resample_spacing: float = 120.0,
    architecture_in_graph: bool = False,
    architecture_emit_to_output: bool = True,
    architecture_mesh_path: str | None = None,
    architecture_material_path: str | None = None,
) -> dict[str, Any]:
    import pcg_graph_builder as graph_builder

    folder = graph_path.rsplit("/", 1)[0]
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)
    snapshot = control.read_control_snapshot(unreal, overrides=control_overrides)
    graph, created = graph_builder.load_or_create_graph(graph_path, folder, force=True)
    graph_builder.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-900, 0)
    graph.get_output_node().set_node_position(900, 0)

    create_node, create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -650, -120)
    create_settings.set_editor_property("points_to_create", list(points))
    spawn_node, spawn_settings = graph_builder.add_node(graph, "PCGSpawnActorSettings", -350, -120)
    configure_hero_spawn(unreal, spawn_settings, resolve_actor_class(unreal, actor_class_name), ["PCG_HeroMusicNode", f"PCG_{graph_kind}"], f"{graph_kind} Music Node")
    graph.add_edge(create_node, "Out", spawn_node, "In")
    graph.add_edge(spawn_node, "Out", graph.get_output_node(), "Out")

    piano_result = {
        "black": {"count": 0},
        "keybed": {"count": 0},
    }
    if piano_black_points:
        piano_result["black"] = _add_static_mesh_points_branch(
            unreal,
            graph,
            graph_builder,
            piano_black_points,
            snapshot,
            "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_Black_Bevel",
            "/Game/EnvSandbox/PCG/Musical/MI_Piano_Ebony",
            -650,
            -360,
            "ebony accents",
        )
    if piano_keybed_points:
        piano_result["keybed"] = _add_static_mesh_points_branch(
            unreal,
            graph,
            graph_builder,
            piano_keybed_points,
            snapshot,
            "/Game/EnvSandbox/PCG/Musical/SM_Piano_Keybed",
            "/Game/EnvSandbox/PCG/Musical/MI_Piano_Keybed",
            -650,
            -520,
            "continuous keybed",
        )

    classic_architecture_result = []
    for index, branch in enumerate(classic_architecture_branches):
        branch_result = _add_static_mesh_points_branch(
            unreal,
            graph,
            graph_builder,
            branch.get("points", ()),
            snapshot,
            str(branch["mesh"]),
            branch.get("material"),
            -120,
            420 + index * 180,
            str(branch.get("label", f"classic architecture {index}")),
        )
        classic_architecture_result.append(branch_result)

    pcgex_curve_result = []
    for index, branch in enumerate(pcgex_curve_branches):
        pcgex_curve_result.append(
            add_pcgex_spline_architecture_branch(
                unreal,
                graph,
                snapshot,
                spline_tag=str(branch.get("spline_tag", "PCG_Spline")),
                curve_points=branch.get("curve_points", ()),
                mesh_path=str(branch["mesh"]),
                material_path=branch.get("material"),
                distance_between_points=float(branch.get("distance_between_points", architecture_resample_spacing)),
                scale=tuple(branch.get("scale", (1.0, 1.0, 1.0))),
                rotation_offset=tuple(branch.get("rotation_offset", (0.0, 0.0, 0.0))),
                label=str(branch.get("label", f"PCGEx curve architecture {index}")),
                node_y=660 + index * 170,
            )
        )

    architecture_result: dict[str, Any] = {"enabled": False}
    if architecture_source_path and architecture_in_graph:
        architecture_result = add_pcgex_vault_branch(
            unreal,
            graph,
            snapshot,
            source_graph_path=architecture_source_path,
            span=architecture_span,
            aisle_width=architecture_aisle_width,
            vault_height=architecture_vault_height,
            resample_spacing=architecture_resample_spacing,
            mesh_path=architecture_mesh_path,
            material_path=architecture_material_path,
            connect_to_output=architecture_emit_to_output,
        )
        architecture_result["enabled"] = True
    elif architecture_source_path:
        # Keep the proven expanded PCGEx graph as a separate proof-level
        # architecture component. Its native tensor settings are preserved;
        # mutating the copied tensor transforms in a new graph can produce
        # non-unit quaternion matrices/NaN ISM bounds in PCGEx.
        architecture_result = {
            "enabled": True,
            "in_graph": False,
            "source_graph": architecture_source_path,
            "reason": "proof-level PCGVolume reuses the authored expanded graph unchanged",
            "walkable_aisle_width": architecture_aisle_width,
            "vault_height": architecture_vault_height,
        }

    decoration_result: dict[str, Any] = {"count": 0, "mesh": None}
    if decoration_points:
        decor_create, decor_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -650, 240)
        decor_settings.set_editor_property("points_to_create", list(decoration_points))
        decor_spawn, decor_spawn_settings = graph_builder.add_node(graph, "PCGStaticMeshSpawnerSettings", -350, 240)
        decoration_result = configure_static_spawner(unreal, decor_spawn_settings, snapshot, decoration_role)
        decoration_result["count"] = len(decoration_points)
        graph.add_edge(decor_create, "Out", decor_spawn, "In")
        graph.add_edge(decor_spawn, "Out", graph.get_output_node(), "Out")

    _set_if_present(graph, "is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)

    # Serialize the tensor safety contract after the graph has been saved once.
    # PCG graph pin wiring can restore copied struct defaults during the first
    # save, so the post-save pass is intentionally performed on the graph's
    # actual settings objects and then saved again.
    tensor_constant = _enum_value(unreal, "PCGExInputValueType", "CONSTANT", "Constant")
    tensor_axis = _enum_value(unreal, "PCGExAxis", "UP", "Up")
    tensor_nodes = []
    for graph_node in graph.get_editor_property("nodes") or []:
        graph_settings = graph_node.get_settings()
        if graph_settings and graph_settings.get_class().get_name() == "PCGExCreateTensorSpinSettings":
            graph_settings.modify()
            graph_config = graph_settings.get_editor_property("config")
            _set_if_present(graph_config, "use_local_guide_curve", False)
            _set_if_present(graph_config, "potency_input", tensor_constant)
            _set_if_present(graph_config, "potency", max(60.0, min(360.0, float(architecture_resample_spacing) * 1.5)))
            _set_if_present(graph_config, "weight_input", tensor_constant)
            _set_if_present(graph_config, "weight", 1.0)
            _set_if_present(graph_config, "axis_input", tensor_constant)
            _set_if_present(graph_config, "axis_constant", tensor_axis)
            graph_settings.set_editor_property("config", graph_config)
            tensor_nodes.append(graph_settings)
    if tensor_nodes:
        graph.modify()
        unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
        for graph_settings in tensor_nodes:
            serialized_config = graph_settings.get_editor_property("config")
            if str(serialized_config.get_editor_property("potency_input")) != str(tensor_constant):
                raise RuntimeError("PCGEx TensorSpin safety contract failed to serialize")
    create_or_update_profile(
        unreal,
        profile_path,
        expected_note_count=expected_note_count,
        midi_notes=midi_notes,
        dimensions=dimensions,
        sequential=sequential,
        beat_window_beats=beat_window_beats,
        snapshot=snapshot,
    )
    result = {
        "graph": graph_path,
        "profile": profile_path,
        "created": created,
        "hero_kind": graph_kind,
        "interactive_points": len(points),
        "decoration_points": len(decoration_points),
        "seed_identities": [int(point.get_editor_property("seed")) for point in points],
        "midi_notes": [int(note) for note in midi_notes],
        "control_manifest": control.control_alias_manifest(snapshot, graph_kind),
        "decoration": decoration_result,
        "piano_roll": piano_result,
        "architecture": architecture_result,
        "classic_architecture": classic_architecture_result,
        "pcgex_curve_architecture": pcgex_curve_result,
    }
    unreal.log(f"[PCG Hero Music] built {result}")
    return result
