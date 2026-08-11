"""Shared PCG graph construction utilities for portfolio scripts."""
from __future__ import annotations

import pcg_portfolio_standards as std


def ensure_directories() -> None:
    import unreal

    for path in std.ALL_PORTFOLIO_DIRS:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            unreal.EditorAssetLibrary.make_directory(path)


def clear_graph_nodes(graph) -> None:
    """Remove every node from a PCG graph before a rebuild.

    NOTE: PCGGraph.remove_nodes() is a no-op in this engine build (confirmed
    2026-07-02: a rebuilt graph kept its old nodes alongside the new ones,
    silently doubling instance counts). Do not use it. Per-node removal via
    get_editor_property("nodes") + remove_node() is the proven-working path.
    """
    for node in list(graph.get_editor_property("nodes")):
        try:
            graph.remove_node(node)
        except Exception:
            pass


def add_node(graph, settings_class_name: str, x: int, y: int):
    import unreal

    cls = getattr(unreal, settings_class_name, None)
    if cls is None:
        raise RuntimeError(f"PCG settings class missing: {settings_class_name}")
    node, settings = graph.add_node_of_type(cls)
    node.set_node_position(x, y)
    return node, settings


def find_pcgex_class(fragment: str) -> str | None:
    import unreal

    frag = fragment.lower()
    for name in dir(unreal):
        if "pcgex" in name.lower() and frag in name.lower() and name.endswith("Settings"):
            return name
    return None


def load_or_create_graph(asset_path: str, folder: str, *, force: bool = False):
    import unreal

    # A freshly reopened editor can have the package on disk before the
    # AssetRegistry has indexed its folder. Refresh this narrow path so a
    # rebuild never mistakes an existing PCG graph for a missing asset.
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([folder], True)
    except Exception:
        pass
    name = asset_path.rsplit("/", 1)[-1]
    # load_asset can resolve a package directly even while the registry is
    # still catching up after editor startup; prefer that authoritative result.
    existing = None
    try:
        existing = unreal.load_asset(asset_path)
    except Exception:
        existing = None
    exists = existing is not None or unreal.EditorAssetLibrary.does_asset_exist(asset_path)
    if exists and not force:
        return unreal.load_asset(asset_path), False
    if exists and force:
        try:
            from material_lib import close_open_material_editors
            close_open_material_editors((name,))
        except Exception:
            pass
        graph = existing or unreal.load_asset(asset_path)
        if graph:
            clear_graph_nodes(graph)
        return graph, True
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)
    factory = unreal.PCGGraphFactory()
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    graph = tools.create_asset(name, folder, unreal.PCGGraph, factory)
    if not graph:
        raise RuntimeError(f"failed to create PCG graph at {folder}/{name}")
    return graph, True


def duplicate_scatter_kit(
    dest_path: str,
    source_path: str | None = None,
    *,
    force: bool = False,
) -> dict:
    """Clone Melodia PCGCol_* into SMC_* kit path when source exists."""
    import unreal

    folder = dest_path.rsplit("/", 1)[0]
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    if unreal.EditorAssetLibrary.does_asset_exist(dest_path) and not force:
        return {"path": dest_path, "exists": True, "method": "existing"}

    if force and unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        return {"path": dest_path, "exists": True, "method": "existing", "skipped_force": True}

    if source_path and unreal.EditorAssetLibrary.does_asset_exist(source_path):
        ok = unreal.EditorAssetLibrary.duplicate_asset(source_path, dest_path)
        return {
            "path": dest_path,
            "exists": bool(ok) and unreal.EditorAssetLibrary.does_asset_exist(dest_path),
            "method": "duplicate",
            "source": source_path,
        }

    # Document intended meshes when no Melodia source is available.
    manifest = {
        "kit": dest_path,
        "meshes": {role: std.resolve_mesh(role) for role in std.SCATTER_MESHES},
    }
    return {"path": dest_path, "exists": False, "method": "manifest_only", "manifest": manifest}


def assign_pcg_graph(comp, graph) -> None:
    """Assign a PCG graph to a component (UE 5.8 graph property is editor-protected)."""
    import unreal

    if hasattr(comp, "set_graph"):
        comp.set_graph(graph)
        return

    gi_cls = getattr(unreal, "PCGGraphInstance", None)
    if gi_cls is not None:
        inst = unreal.new_object(gi_cls, comp)
        for prop in ("graph", "pcg_graph", "parent"):
            try:
                inst.set_editor_property(prop, graph)
                break
            except Exception:
                continue
        for prop in ("graph_instance", "GraphInstance"):
            try:
                comp.set_editor_property(prop, inst)
                return
            except Exception:
                continue

    for prop in ("graph", "Graph"):
        try:
            comp.set_editor_property(prop, graph)
            return
        except Exception:
            continue

    raise RuntimeError("could not assign PCG graph to component")


def configure_pcg_component(comp, *, seed: int | None = None, activated: bool = True) -> None:
    import unreal

    if seed is not None:
        for prop in ("seed", "Seed"):
            try:
                comp.set_editor_property(prop, int(seed))
                break
            except Exception:
                continue
    if activated:
        for prop in ("b_is_active", "b_activated", "is_active", "activated"):
            try:
                comp.set_editor_property(prop, True)
                break
            except Exception:
                continue


def configure_spawner(spawner_settings, role: str, material_path: str | None) -> bool:
    """Configure spawner with weighted entries from SCATTER_MESHES."""
    import unreal

    if not spawner_settings:
        unreal.log_error(f"[PCG] configure_spawner: spawner_settings is None for role {role}")
        return False
    resolved: list[str] = []
    for path in std.SCATTER_MESHES.get(role, []):
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                resolved.append(path)
        except Exception:
            continue
    if not resolved:
        single = std.resolve_mesh(role)
        if not single:
            unreal.log_warning(f"[PCG] no mesh for role {role}")
            return False
        resolved = [single]

    entries = []
    weight = max(1, 4 - len(resolved))
    for mesh_path in resolved:
        mesh = unreal.load_asset(mesh_path)
        if not mesh:
            continue
        entry = unreal.PCGMeshSelectorWeightedEntry()
        desc = entry.get_editor_property("descriptor")
        desc.set_editor_property("static_mesh", mesh)
        if material_path and unreal.EditorAssetLibrary.does_asset_exist(material_path):
            mat = unreal.load_asset(material_path)
            if mat:
                for prop in ("material_overrides", "override_materials", "material_override"):
                    try:
                        desc.set_editor_property(prop, [mat] if prop.endswith("s") else mat)
                        break
                    except Exception:
                        continue
        entry.set_editor_property("descriptor", desc)
        entry.set_editor_property("weight", weight)
        entries.append(entry)
        weight = max(1, weight - 1)

    if not entries:
        unreal.log_warning(f"[PCG] spawner has no valid entries for role {role}")
        return False
    try:
        selector = spawner_settings.get_editor_property("mesh_selector_parameters")
        selector.set_editor_property("mesh_entries", entries)
    except Exception as exc:
        unreal.log_warning(f"[PCG] spawner mesh_selector_parameters failed for role {role}: {exc}")
        return False
    return True


def get_graph_from_component(comp):
    """Resolve assigned PCG graph from a component (UE 5.8 graph instance path)."""
    import unreal

    for prop in ("graph", "Graph"):
        try:
            graph = comp.get_editor_property(prop)
            if graph:
                return graph
        except Exception:
            continue
    for prop in ("graph_instance", "GraphInstance"):
        try:
            inst = comp.get_editor_property(prop)
            if not inst:
                continue
            for inner in ("graph", "pcg_graph", "parent"):
                try:
                    graph = inst.get_editor_property(inner)
                    if graph:
                        return graph
                except Exception:
                    continue
        except Exception:
            continue
    if hasattr(comp, "get_graph"):
        try:
            return comp.get_graph()
        except Exception:
            pass
    return None


def graph_package_path(comp) -> str | None:
    graph = get_graph_from_component(comp)
    if not graph:
        return None
    return str(graph.get_path_name()).split(".")[0]


def apply_transform(settings, *, scale_min: float, scale_max: float, jitter: float = 0.0) -> None:
    import unreal

    smin, smax = float(scale_min), float(scale_max)
    settings.set_editor_property("scale_min", unreal.Vector(smin, smin, smin))
    settings.set_editor_property("scale_max", unreal.Vector(smax, smax, smax))
    settings.set_editor_property("uniform_scale", True)
    settings.set_editor_property("rotation_min", unreal.Rotator(0, 0, 0))
    settings.set_editor_property("rotation_max", unreal.Rotator(0, 359.0, 0))
    settings.set_editor_property("absolute_rotation", False)
    if jitter > 0:
        try:
            settings.set_editor_property("translation_min", unreal.Vector(-jitter, -jitter, 0))
            settings.set_editor_property("translation_max", unreal.Vector(jitter, jitter, 0))
        except Exception:
            pass


def wire_scatter_chain(
    graph,
    *,
    voxel_cm: float,
    grass_mi: str,
    use_surface_tag: bool = False,
    density_mult: float = 1.0,
    transform_jitter: float = 0.0,
    spacing_prune: bool = True,
    apply_exclusion: bool = False,
    role: str = "grass",
    scale_min: float | None = None,
    scale_max: float | None = None,
) -> dict:
    """Build Input â†’ Sample â†’ [Exclusion] â†’ [Density] â†’ [Prune] â†’ Transform â†’ Spawner â†’ Output."""
    import unreal

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    chain_in = None
    if use_surface_tag:
        surf_cls = getattr(unreal, "PCGSurfaceSamplerSettings", None)
        if surf_cls:
            sampler, sampler_settings = add_node(graph, "PCGSurfaceSamplerSettings", -700, 0)
            try:
                sampler_settings.set_editor_property(
                    "points_per_squared_meter", max(0.008, 0.015 * density_mult)
                )
            except Exception:
                pass
            chain_in = sampler
        else:
            use_surface_tag = False

    if not use_surface_tag:
        sampler, sampler_settings = add_node(graph, "PCGVolumeSamplerSettings", -700, 0)
        voxel = float(voxel_cm)
        sampler_settings.set_editor_property("voxel_size", unreal.Vector(voxel, voxel, voxel))
        sampler_settings.set_editor_property("unbounded", False)
        chain_in = sampler

    graph.add_edge(inp, "In", chain_in, "Surface" if use_surface_tag else "Volume")
    prev = chain_in
    prev_pin = "Out"
    density_wired = False
    exclusion_wired = False
    prune_wired = False

    if apply_exclusion:
        exclusion_wired = _wire_exclusion_filter(graph, prev, prev_pin)
        if exclusion_wired:
            prev, prev_pin = exclusion_wired["node"], exclusion_wired["pin"]

    dens_cls = getattr(unreal, "PCGDensityFilterSettings", None)
    upper = max(0.04, min(0.95, density_mult * 0.85))
    if dens_cls:
        dens, dens_s = add_node(graph, "PCGDensityFilterSettings", -450, 0)
        try:
            dens_s.set_editor_property("lower_bound", 0.0)
            dens_s.set_editor_property("upper_bound", upper)
            dens_s.set_editor_property("b_invert_filter", False)
        except Exception:
            pass
        graph.add_edge(prev, prev_pin, dens, "In")
        prev, prev_pin = dens, "Out"
        density_wired = True

    prune_cls = getattr(unreal, "PCGSelfPruningSettings", None)
    if spacing_prune and prune_cls:
        prune, prune_s = add_node(graph, "PCGSelfPruningSettings", -250, 0)
        try:
            prune_s.set_editor_property("pruning_type", unreal.PCGSelfPruningType.LARGEST_TO_SMALLEST)
            prune_s.set_editor_property("radius_similarity_factor", 0.25)
            prune_s.set_editor_property(
                "comparison_source", unreal.PCGSelfPruningComparisonSource.Largest,
            )
        except Exception:
            pass
        try:
            prune_s.set_editor_property("radius", float(std.SPACING_PRUNE_RADIUS_CM))
        except Exception:
            pass
        graph.add_edge(prev, prev_pin, prune, "In")
        prev, prev_pin = prune, "Out"
        prune_wired = True

    xform, xform_settings = add_node(graph, "PCGTransformPointsSettings", -50, 0)
    apply_transform(
        xform_settings,
        scale_min=std.GRASS_SCALE_MIN if scale_min is None else float(scale_min),
        scale_max=std.GRASS_SCALE_MAX if scale_max is None else float(scale_max),
        jitter=float(transform_jitter),
    )
    graph.add_edge(prev, prev_pin, xform, "In")

    spawner, spawner_settings = add_node(graph, "PCGStaticMeshSpawnerSettings", 250, 0)
    if not configure_spawner(spawner_settings, role, grass_mi):
        raise RuntimeError(f"spawner configuration failed for role {role}")
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    return {
        "surface_sampler": use_surface_tag,
        "density_filter": density_wired,
        "spacing_prune": prune_wired,
        "pcgex_exclusion": exclusion_wired is not False and bool(exclusion_wired),
        "transform_jitter": float(transform_jitter),
        "role": role,
        "scale_min": std.GRASS_SCALE_MIN if scale_min is None else float(scale_min),
        "scale_max": std.GRASS_SCALE_MAX if scale_max is None else float(scale_max),
    }


def _wire_exclusion_filter(graph, prev, prev_pin, corridor_cm: float = 700.0) -> dict | bool:
    """Carve scatter away from spline paths tagged PCG_Spline.

    REWRITTEN 2026-08-02. The previous implementation could never work:

      * it set ``actor_selector = unreal.PCGActorSelector.ByTag``, but
        ``actor_selector`` is a PCGActorSelectorSettings STRUCT whose fields are
        ``actor_filter`` / ``actor_selection`` / ``actor_selection_tag`` -- and whose
        ``actor_filter`` defaults to Self, so a tag search never scans the world at all;
      * it set a property named ``actor_tag`` that does not exist;
      * it wired PCGDifference's subtract input to a pin called "Subtract"; the real
        pin is "Differences";
      * its preferred branch, PCGFilterByTag, filters DATA BY TAG -- it has nothing to
        do with spatial proximity, so even on success it excluded the wrong thing;
      * every failure was swallowed by ``except: return False``, so callers recorded
        "exclusion wired" while nothing was culled.

    PCGDifference was abandoned rather than repaired. It depends on the spatial-data
    semantics of whatever PCGDataFromActor emits, which proved opaque: it culled nothing
    across two actor classes (StaticMeshActor, BlockingVolume) and three source modes,
    with verified genuine overlap.

    The replacement is numeric and was proven end-to-end: PCGExSampleNearestSpline writes
    a per-point distance to the nearest tagged spline, and a plain attribute filter keeps
    the points beyond ``corridor_cm``. Measured on PCG_Nikki_PhyllotaxisGarden_Walkable --
    threshold 1200 left 53 of 160 points with the closest survivor at 1203 uu; threshold
    700 left 97 with the closest at 707 uu. Zero points inside the corridor either time.

    This carves to the spline's actual ribbon rather than an actor's bounding box, and the
    corridor width is one number instead of a volume someone has to place by hand.
    """
    import unreal

    sample_cls = getattr(unreal, "PCGExSampleNearestSplineSettings", None)
    spline_cls = getattr(unreal, "PCGGetSplineSettings", None)
    filter_cls = getattr(unreal, "PCGAttributeFilteringSettings", None)
    if not (sample_cls and spline_cls and filter_cls):
        return False

    dist_attr = "PathDist"

    spline, spline_s = add_node(graph, "PCGGetSplineSettings", -760, 240)
    selector = spline_s.get_editor_property("actor_selector")
    # ALL_WORLD_ACTORS is mandatory: the default is Self, which silently finds nothing.
    selector.set_editor_property("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS)
    selector.set_editor_property("actor_selection", unreal.PCGActorSelection.BY_TAG)
    selector.set_editor_property("actor_selection_tag", std.TAG_SPLINE)
    selector.set_editor_property("select_multiple", True)
    spline_s.set_editor_property("actor_selector", selector)

    sample, sample_s = add_node(graph, "PCGExSampleNearestSplineSettings", -620, 0)
    # A very large max_range means every point samples successfully and carries a real
    # distance, so the filter -- not the sampler -- decides what is culled.
    max_range = sample_s.get_editor_property("max_range")
    max_range.set_editor_property("constant", 1_000_000.0)
    sample_s.set_editor_property("max_range", max_range)
    sample_s.set_editor_property("sample_method", unreal.PCGExSampleMethod.WITHIN_RANGE)
    sample_s.set_editor_property("write_distance", True)
    sample_s.set_editor_property("distance_attribute_name", dist_attr)

    filt, filt_s = add_node(graph, "PCGAttributeFilteringSettings", -480, 0)
    # The selector must be built from text. set_attribute_name() returns True but leaves
    # the selection as PROPERTY($Density); only import_text flips it to ATTRIBUTE.
    target = unreal.PCGAttributePropertyInputSelector()
    target.import_text(f"PCGBegin({dist_attr})PCGEnd")
    filt_s.set_editor_property("target_attribute", target)
    filt_s.set_editor_property("operator", unreal.PCGAttributeFilterOperator.GREATER)
    filt_s.set_editor_property("use_constant_threshold", True)
    threshold = filt_s.get_editor_property("attribute_types")
    threshold.set_editor_property("type", unreal.PCGMetadataTypes.DOUBLE)
    threshold.set_editor_property("double_value", float(corridor_cm))
    threshold.set_editor_property("float_value", float(corridor_cm))
    filt_s.set_editor_property("attribute_types", threshold)

    graph.add_edge(prev, prev_pin, sample, "Sources")
    graph.add_edge(spline, "Out", sample, "Targets")
    graph.add_edge(sample, "Out", filt, "In")
    # "InsideFilter" carries the points that PASS the test, i.e. those far from the path.
    return {"node": filt, "pin": "InsideFilter"}


def _set_actor_location(actor, loc) -> None:
    """UE 5.8 Python bindings differ between editor and commandlet builds."""
    import unreal

    v = loc if isinstance(loc, unreal.Vector) else unreal.Vector(*loc)
    for args in ((v, False, None, False), (v, False, False), (v, False), (v,)):
        try:
            actor.set_actor_location(*args)
            return
        except TypeError:
            continue
    actor.set_actor_location(v)


def fit_volume_to_ground(volume_actor, eas, *, preset: str | None = None) -> dict:
    """Scale/position PCG volume from tagged Ground actor bounds."""
    import unreal

    cfg = std.PRESETS.get(preset or "standard", std.PRESETS["standard"])
    scale = cfg.get("volume_scale", std.PCG_VOLUME_SCALE)
    center_z = float(cfg.get("volume_center_z", std.PCG_VOLUME_CENTER[2]))

    ground = None
    for actor in eas.get_all_level_actors() or []:
        tags = list(getattr(actor, "tags", []) or [])
        if std.TAG_GROUND in tags or actor.get_actor_label() == "Ground":
            ground = actor
            break

    if not ground:
        _set_actor_location(volume_actor, std.PCG_VOLUME_CENTER)
        try:
            volume_actor.set_actor_scale3d(unreal.Vector(*scale))
        except Exception as exc:
            unreal.log_warning(f"[PCG] fit_volume_to_ground scale failed: {exc}")
        return {"fitted": False, "reason": "no_ground", "scale": scale}

    try:
        origin, extent = ground.get_actor_bounds(False)
    except Exception as exc:
        unreal.log_warning(f"[PCG] get_actor_bounds failed on Ground: {exc}")
        _set_actor_location(volume_actor, std.PCG_VOLUME_CENTER)
        try:
            volume_actor.set_actor_scale3d(unreal.Vector(*scale))
        except Exception:
            pass
        return {"fitted": False, "reason": "bounds_failed", "scale": scale}
    sx = max(8.0, (extent.x * 2.0) / 100.0)
    sy = max(8.0, (extent.y * 2.0) / 100.0)
    sz = float(scale[2]) if len(scale) > 2 else 1.8
    _set_actor_location(volume_actor, (origin.x, origin.y, center_z))
    volume_actor.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    return {
        "fitted": True,
        "origin": [origin.x, origin.y, origin.z],
        "scale": [sx, sy, sz],
        "extent": [extent.x, extent.y, extent.z],
    }


