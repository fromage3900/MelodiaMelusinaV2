"""PCG corridor carve proof — sandbox only (Step 1 of the room-shell plan).

Duplicates the staged PCG_Core_PathCarve (GetSpline -> SampleNearestSpline ->
AttributeFiltering) into /Game/EnvSandbox/PCG/Tests/, prepends a fixed grid and
appends two spawners (kept=Cube on InsideFilter, culled=Sphere on OutsideFilter),
then generates a PCGVolume crossed by a tagged spline actor and counts instances
per mesh. The ONLY variable between runs is GetSpline.components_must_overlap_self.

Run inside the editor (Monolith run_python) with the sandbox map open:
  import build_pcg_carve_test as t; print(t.run(overlap=True))
  import build_pcg_carve_test as t; print(t.run(overlap=False))

SAFETY: refuses unless the open editor world is L_PCG_CarveHouse_Test. Never
touches Morning, the staged graph, or any production asset. Writes only:
  /Game/EnvSandbox/PCG/Tests/PCG_Carve_Test (graph copy)
  TEST_Carve_Spine / TEST_Carve_Volume (actors in the test map)
  Saved/Audit/pcg_corridor_roomshell/carve_test_<variant>.json (receipt)
"""
from __future__ import annotations

import json
import os

TEST_MAP = "/Game/EnvSandbox/PCG/Tests/L_PCG_CarveHouse_Test"
STAGED = "/Game/Melodia/PCG/Core/PCG_Core_PathCarve"
TEST_GRAPH = "/Game/EnvSandbox/PCG/Tests/PCG_Carve_Test"
SPINE_LABEL = "TEST_Carve_Spine"
VOLUME_LABEL = "TEST_Carve_Volume"
KEPT_MESH = "/Engine/BasicShapes/Cube"
CULLED_MESH = "/Engine/BasicShapes/Sphere"

RECEIPT_DIR = os.path.join("Saved", "Audit", "pcg_corridor_roomshell")


def _label(a) -> str:
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def _actors():
    import unreal
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return eas, list(eas.get_all_level_actors())


def _find(actors, label):
    for a in actors:
        if _label(a) == label:
            return a
    return None


def _spawner_entry(mesh_path: str):
    import unreal
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        raise RuntimeError(f"mesh missing: {mesh_path}")
    entry = unreal.PCGMeshSelectorWeightedEntry()
    desc = entry.get_editor_property("descriptor")
    desc.set_editor_property("static_mesh", mesh)
    entry.set_editor_property("descriptor", desc)
    entry.set_editor_property("weight", 1)
    return entry


def _set_spawner_mesh(spawner_settings, mesh_path: str) -> None:
    import unreal
    selector = spawner_settings.get_editor_property("mesh_selector_parameters")
    selector.set_editor_property("mesh_entries", [_spawner_entry(mesh_path)])


def _remove_edge(graph, from_node, from_pin: str, to_node, to_pin: str) -> bool:
    try:
        return bool(graph.remove_edge(from_node, from_pin, to_node, to_pin))
    except Exception:
        return False


def run(overlap: bool) -> dict:
    import unreal
    import pcg_graph_builder as gb

    EAL = unreal.EditorAssetLibrary
    ELL = unreal.EditorLevelLibrary

    world_path = str(ELL.get_editor_world().get_outer().get_path_name())
    if "L_PCG_CarveHouse_Test" not in world_path:
        return {"error": f"refusing: open world is {world_path}, not the sandbox test map"}

    # 1. Fresh copy of the staged carve graph (config rides along untouched).
    if EAL.does_asset_exist(TEST_GRAPH):
        EAL.delete_asset(TEST_GRAPH)
    if not EAL.duplicate_asset(STAGED, TEST_GRAPH):
        return {"error": f"duplicate_asset failed: {STAGED} -> {TEST_GRAPH}"}
    graph = EAL.load_asset(TEST_GRAPH)
    if graph is None:
        return {"error": "test graph copy failed to load"}

    by_class = {}
    for n in list(graph.nodes):
        by_class[n.get_settings().get_class().get_name()] = n
    get_spline = by_class.get("PCGGetSplineSettings")
    sampler = by_class.get("PCGExSampleNearestSplineSettings")
    filtr = by_class.get("PCGAttributeFilteringSettings")
    if not (get_spline and sampler and filtr):
        return {"error": f"staged nodes missing in copy: {sorted(by_class)}"}
    get_spline.get_settings().set_editor_property("components_must_overlap_self", bool(overlap))

    # 2. Prepend grid: Input.In -> Grid.In, Grid.Out -> Sampler.Sources.
    inp, outp = graph.get_input_node(), graph.get_output_node()
    removed = _remove_edge(graph, inp, "In", sampler, "Sources")
    grid, grid_s = gb.add_node(graph, "PCGCreatePointsGridSettings", -700, -200)
    grid_s.set_editor_property("grid_extents", unreal.Vector(1000.0, 1000.0, 50.0))
    grid_s.set_editor_property("cell_size", unreal.Vector(110.0, 110.0, 100.0))
    graph.add_edge(inp, "In", grid, "In")
    graph.add_edge(grid, "Out", sampler, "Sources")

    # 3. Append spawners: InsideFilter -> Cube, OutsideFilter -> Sphere.
    kept, kept_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 500, -200)
    culled, culled_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 500, 200)
    _set_spawner_mesh(kept_s, KEPT_MESH)
    _set_spawner_mesh(culled_s, CULLED_MESH)
    graph.add_edge(filtr, "InsideFilter", kept, "In")
    try:
        graph.add_edge(filtr, "OutsideFilter", culled, "In")
    except Exception as exc:
        return {"error": f"OutsideFilter pin missing on staged filter node: {exc}"}
    graph.add_edge(kept, "Out", outp, "Out")
    graph.add_edge(culled, "Out", outp, "Out")
    EAL.save_asset(TEST_GRAPH)

    # 4. Spline actor: plain Actor + instanced SplineComponent (SplineActor is
    # not exposed to Python in this build), 24 m spine through the volume.
    eas, actors = _actors()
    spine = _find(actors, SPINE_LABEL)
    if spine is None:
        spine = eas.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if spine is None:
            return {"error": "spine Actor spawn failed"}
        spine.set_actor_label(SPINE_LABEL)
        try:
            sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            handles = sub.k2_gather_subobject_data_for_instance(spine)
            params = unreal.AddNewSubobjectParams(parent_handle=handles[0],
                                                  new_class=unreal.SplineComponent,
                                                  blueprint_context=None)
            handle, fail = sub.add_new_subobject(params)
            if not fail.is_empty():
                return {"error": f"add SplineComponent to spine: {fail}"}
            sub.rename_subobject(handle, unreal.Text("Spine"))
        except Exception as exc:
            return {"error": f"spline component attach failed: {exc}"}
    else:
        actors = list(eas.get_all_level_actors())
    scomp = spine.get_component_by_class(unreal.SplineComponent)
    if scomp is None:
        return {"error": "SplineActor has no SplineComponent"}
    pts = [unreal.Vector(-1200, 0, 0), unreal.Vector(1200, 0, 0)]
    try:
        scomp.set_spline_points(pts, unreal.SplineCoordinateSpace.WORLD, True)
    except Exception:
        scomp.clear_spline_points(False)
        for p in pts:
            scomp.add_spline_point(p, unreal.SplineCoordinateSpace.WORLD, False)
        scomp.update_spline()
    try:
        scomp.set_editor_property("point_type", unreal.SplinePointType.Linear)
    except Exception:
        pass
    tags = [t for t in list(spine.get_editor_property("tags")) if str(t) not in ("PCG_Spline", "PathSpline")]
    tags += [unreal.Name("PCG_Spline"), unreal.Name("PathSpline")]
    spine.set_editor_property("tags", tags)
    spine.set_folder_path("Tests/Carve")

    # 5. Volume + generate.
    vol = _find(list(eas.get_all_level_actors()), VOLUME_LABEL)
    if vol is None:
        vol = ELL.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if vol is None:
            return {"error": "PCGVolume spawn failed"}
        vol.set_actor_label(VOLUME_LABEL)
    vol.set_actor_location(unreal.Vector(0, 0, 0), False, False)
    vol.set_actor_scale3d(unreal.Vector(10.0, 10.0, 2.0))
    vol.set_folder_path("Tests/Carve")
    comp = vol.get_component_by_class(unreal.PCGComponent)
    comp.set_graph(EAL.load_asset(TEST_GRAPH))
    try:
        comp.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    except Exception:
        pass
    try:
        comp.set_editor_property("seed", 424242)
    except Exception:
        pass
    try:
        unreal.SystemLibrary.execute_console_command(ELL.get_editor_world(), "pcg.FlushCache")
    except Exception:
        pass
    comp.generate(True)

    # 6. Count kept vs culled by mesh (PCG populates ISMCs asynchronously:
    # poll until the total stabilizes across two consecutive reads).
    import time
    last = (-1, -1)
    kept_n = culled_n = 0
    comps = 0
    for _ in range(30):
        time.sleep(0.5)
        k = c_ = 0
        ncomp = 0
        _, all_actors = _actors()
        for a in [vol] + [x for x in all_actors if x.get_class().get_name() == "PCGPartitionActor"]:
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                mesh = c.get_editor_property("static_mesh")
                if not mesh:
                    continue
                n = c.get_instance_count()
                if n == 0:
                    continue
                name = str(mesh.get_path_name())
                if "Cube" in name:
                    k += n
                    ncomp += 1
                elif "Sphere" in name:
                    c_ += n
                    ncomp += 1
        if (k, c_) == last and (k + c_) > 0:
            kept_n, culled_n, comps = k, c_, ncomp
            break
        last = (k, c_)
        kept_n, culled_n, comps = k, c_, ncomp
    total = kept_n + culled_n
    # Grid semantics (cell-centered): x/y -945..925 step 110 -> 18 each, one z
    # layer -> 324 points. Culled band |y| <= 700 -> 12 rows -> 216; kept 108.
    expected_total, expected_kept, expected_culled = 324, 108, 216
    carve_works = (
        total >= int(expected_total * 0.9)
        and abs(kept_n - expected_kept) <= expected_total * 0.15
        and abs(culled_n - expected_culled) <= expected_total * 0.15
    )
    verdict = "PASS" if carve_works else "FAIL"
    receipt = {
        "test": "pcg_carve_sandbox",
        "overlap_flag": bool(overlap),
        "graph": TEST_GRAPH,
        "kept_cube": kept_n,
        "culled_sphere": culled_n,
        "total": total,
        "expected": {"total": expected_total, "kept": expected_kept, "culled": expected_culled},
        "ism_components": comps,
        "verdict": verdict,
    }
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    variant = "overlap_true" if overlap else "overlap_false"
    with open(os.path.join(RECEIPT_DIR, f"carve_test_{variant}.json"), "w") as f:
        json.dump(receipt, f, indent=1)
    ELL.save_current_level()
    return receipt


if __name__ == "__main__":
    print(run(overlap=True))


def run_wrapped(subgraph_path: str = None, overlap: bool = True, track_bounds: bool = True,
                volume_label: str = "TEST_Carve_Volume_Wrapped") -> dict:
    """Phase 2: consume a carve graph as a subgraph node (the exact
    pattern the biome core uses), proving the subgraph context works.
    Wrapper: Grid -> Subgraph(carve) -> Spawner(Cube) -> Out.
    Writes Saved/Audit/pcg_corridor_roomshell/carve_test_wrapped.json.
    """
    import time
    import unreal
    import pcg_graph_builder as gb

    EAL = unreal.EditorAssetLibrary
    ELL = unreal.EditorLevelLibrary
    WRAP_GRAPH = "/Game/EnvSandbox/PCG/Tests/PCG_Carve_Test_Wrapped"
    WRAP_VOLUME = volume_label
    sub_path = subgraph_path or STAGED

    world_path = str(ELL.get_editor_world().get_outer().get_path_name())
    if "L_PCG_CarveHouse_Test" not in world_path:
        return {"error": f"refusing: open world is {world_path}, not the sandbox test map"}

    if EAL.does_asset_exist(WRAP_GRAPH):
        EAL.delete_asset(WRAP_GRAPH)
    graph, _ = gb.load_or_create_graph(WRAP_GRAPH, "/Game/EnvSandbox/PCG/Tests", force=True)
    gb.clear_graph_nodes(graph)
    inp, outp = graph.get_input_node(), graph.get_output_node()

    grid, grid_s = gb.add_node(graph, "PCGCreatePointsGridSettings", -700, 0)
    grid_s.set_editor_property("grid_extents", unreal.Vector(1000.0, 1000.0, 50.0))
    grid_s.set_editor_property("cell_size", unreal.Vector(110.0, 110.0, 100.0))
    graph.add_edge(inp, "In", grid, "In")

    sub, sub_s = gb.add_node(graph, "PCGSubgraphSettings", -200, 0)
    # Never mutate STAGED during experiments: duplicate to a variant copy,
    # set the GetSpline actor-query flags there, and point the wrapper at it.
    VARIANT = "/Game/EnvSandbox/PCG/Tests/PCG_Carve_Variant"
    if EAL.does_asset_exist(VARIANT):
        EAL.delete_asset(VARIANT)
    if not EAL.duplicate_asset(sub_path, VARIANT):
        return {"error": f"variant duplicate failed: {sub_path} -> {VARIANT}"}
    staged = EAL.load_asset(VARIANT)
    if staged is None:
        return {"error": f"variant missing: {VARIANT}"}
    for n in list(staged.nodes):
        if n.get_settings().get_class().get_name() == "PCGGetSplineSettings":
            n.get_settings().set_editor_property("components_must_overlap_self", bool(overlap))
            try:
                n.get_settings().set_editor_property("track_actors_only_within_bounds", bool(track_bounds))
            except Exception as exc:
                return {"error": f"track_bounds set failed: {exc}"}
    EAL.save_asset(VARIANT)
    try:
        sub_s.set_editor_property("subgraph_override", staged)
    except Exception as exc:
        return {"error": f"subgraph_override bind failed: {exc}"}
    graph.add_edge(grid, "Out", sub, "In")

    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 300, 0)
    _set_spawner_mesh(spawner_s, KEPT_MESH)
    graph.add_edge(sub, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", outp, "Out")
    EAL.save_asset(WRAP_GRAPH)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    vol = _find(list(eas.get_all_level_actors()), WRAP_VOLUME)
    if vol is None:
        vol = ELL.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        if vol is None:
            return {"error": "wrapped PCGVolume spawn failed"}
        vol.set_actor_label(WRAP_VOLUME)
    vol.set_actor_location(unreal.Vector(0, 0, 0), False, False)
    vol.set_actor_scale3d(unreal.Vector(10.0, 10.0, 2.0))
    vol.set_folder_path("Tests/Carve")
    comp = vol.get_component_by_class(unreal.PCGComponent)
    comp.set_graph(EAL.load_asset(WRAP_GRAPH))
    try:
        comp.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    except Exception:
        pass
    try:
        unreal.SystemLibrary.execute_console_command(ELL.get_editor_world(), "pcg.FlushCache")
    except Exception:
        pass
    comp.generate(True)

    last = -1
    kept_n = 0
    for _ in range(30):
        time.sleep(0.5)
        k = 0
        for a in [vol] + [x for x in eas.get_all_level_actors()
                           if x.get_class().get_name() == "PCGPartitionActor"]:
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                mesh = c.get_editor_property("static_mesh")
                if mesh and "Cube" in str(mesh.get_path_name()):
                    k += c.get_instance_count()
        if k == last and k > 0:
            kept_n = k
            break
        last = k
        kept_n = k
    expected_kept = 108
    verdict = "PASS" if abs(kept_n - expected_kept) <= expected_kept * 0.15 else "FAIL"
    receipt = {"test": "pcg_carve_subgraph", "graph": WRAP_GRAPH, "subgraph": VARIANT,
               "overlap_flag": bool(overlap), "track_bounds": bool(track_bounds),
               "kept_cube": kept_n, "expected_kept": expected_kept, "verdict": verdict}
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    with open(os.path.join(RECEIPT_DIR, "carve_test_wrapped.json"), "w") as f:
        json.dump(receipt, f, indent=1)
    ELL.save_current_level()
    return receipt


def apply_to_staged(overlap: bool, track_bounds: bool) -> dict:
    """Apply a proven GetSpline flag combination to the staged
    PCG_Core_PathCarve (0 referencers — nothing live consumes it) and save.
    Call ONLY with a sandbox-proven combination."""
    import unreal

    EAL = unreal.EditorAssetLibrary
    staged = EAL.load_asset(STAGED)
    if staged is None:
        return {"error": f"staged graph missing: {STAGED}"}
    for n in list(staged.nodes):
        if n.get_settings().get_class().get_name() == "PCGGetSplineSettings":
            n.get_settings().set_editor_property("components_must_overlap_self", bool(overlap))
            n.get_settings().set_editor_property("track_actors_only_within_bounds", bool(track_bounds))
    EAL.save_asset(STAGED)
    return {"staged": STAGED, "overlap": bool(overlap), "track_bounds": bool(track_bounds), "saved": True}
