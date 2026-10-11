"""Piano walkway: bend a piano key layout along a spline and build/place the PCG graph, keyboard actor and rails.

Pure math (no unreal import) lives in the first half so it can be unit-tested outside the editor
(Content/Python/Tests/test_piano_walkway.py). The editor half builds a PCG graph of authored points
(PCGCreatePoints, LOCAL_COMPONENT -> PCGSpawnActor for keys, PCGStaticMeshSpawner for rails), because PCG re-seeds
points and a deterministic instrument layout must not depend on a sampler.

Key identity (MIDI order) follows distance along the spline: set APCGPianoKeyboard.OrderPathActor to the actor that
carries the spline (build_walkway does this).

Editor use:
    import pcg_piano_walkway as w
    w.build_walkway(spline_actor_label="WC_PianoWalkway_WestRim", biome="MorningMeadow", whites=21)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

from pcg_piano_layout import PianoDimensions, build_layout, is_black_midi

Vec = tuple[float, float, float]
FrameFn = Callable[[float], tuple[Vec, Vec]]  # distance -> (world position, unit tangent)


@dataclass(frozen=True)
class WalkwayKey:
    key_index: int
    midi_note: int
    is_black: bool
    position: Vec   # world, key centre
    yaw: float      # degrees
    pitch: float    # degrees
    width: float
    depth: float
    height: float
    seed: int
    distance: float  # along the path


def _norm(v: Vec) -> Vec:
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def yaw_pitch(tangent: Vec) -> tuple[float, float]:
    t = _norm(tangent)
    yaw = math.degrees(math.atan2(t[1], t[0]))
    pitch = math.degrees(math.atan2(t[2], math.hypot(t[0], t[1])))
    return yaw, pitch


def right_vector(tangent: Vec) -> Vec:
    """Horizontal right-hand side of the direction of travel (up = +Z)."""
    t = _norm((tangent[0], tangent[1], 0.0))
    return (t[1], -t[0], 0.0)


def whites_for_length(path_length: float, dims: PianoDimensions, margin: float = 0.0) -> int:
    pitch = dims.white_width + dims.inter_key_gap
    return max(1, int((path_length - 2.0 * margin) // pitch))


def midi_range_for_whites(whites: int, first_midi: int = 48) -> tuple[int, int]:
    """First/last MIDI note so the range holds exactly `whites` white keys, starting and ending on a white key."""
    if is_black_midi(first_midi):
        first_midi += 1
    count = 0
    midi = first_midi
    last = first_midi
    while count < whites and midi <= 127:
        if not is_black_midi(midi):
            count += 1
            last = midi
        midi += 1
    return first_midi, last


def map_layout_to_path(
    frame: FrameFn,
    first_midi: int,
    last_midi: int,
    dims: PianoDimensions,
    ground: Callable[[float, float, float], float] | None = None,
    margin: float = 0.0,
) -> list[WalkwayKey]:
    """Bend the straight keyboard layout (x along, y across) onto the path. `ground(x, y, z_hint)` snaps keys to terrain."""
    specs = build_layout(first_midi, last_midi, dims)
    xs = [s.x - s.width * 0.5 for s in specs]
    x_min = min(xs)
    keys: list[WalkwayKey] = []
    for spec in specs:
        dist = spec.x - x_min + margin
        pos, tangent = frame(dist)
        right = right_vector(tangent)
        # spec.y is the lateral offset across the walkway (black keys sit toward one side, as on a keyboard).
        x = pos[0] + right[0] * spec.y
        y = pos[1] + right[1] * spec.y
        base_z = ground(x, y, pos[2]) if ground else pos[2]
        z = base_z + spec.z
        yaw, pitch = yaw_pitch(tangent)
        if ground:
            # follow the terrain slope under the key (the spline is authored flat; the ground is not)
            tn = _norm((tangent[0], tangent[1], 0.0))
            half = spec.width * 0.5
            ahead = ground(x + tn[0] * half, y + tn[1] * half, base_z)
            behind = ground(x - tn[0] * half, y - tn[1] * half, base_z)
            pitch = math.degrees(math.atan2(ahead - behind, spec.width))
        keys.append(
            WalkwayKey(
                key_index=spec.key_index, midi_note=spec.midi_note, is_black=spec.is_black,
                position=(x, y, z), yaw=yaw, pitch=pitch,
                width=spec.width, depth=spec.depth, height=spec.height, seed=spec.seed, distance=dist,
            )
        )
    return keys


GOLDEN_ANGLE_DEG = 137.50776405


def path_heat(s: float, length: float) -> float:
    """0..1 heat along the path (three slow swells plus a rise toward the end): drives key lift, like a PCGEx heat map."""
    t = s / max(length, 1.0)
    return max(0.0, min(1.0, 0.5 + 0.35 * math.sin(2.0 * math.pi * 3.0 * t) + 0.25 * t))


def _octave_groups(first_midi: int, last_midi: int) -> list[list[int]]:
    groups: dict[int, list[int]] = {}
    for m in range(first_midi, last_midi + 1):
        groups.setdefault(m // 12, []).append(m)
    return [groups[k] for k in sorted(groups)]


def map_layout_to_pattern(frame: FrameFn, length: float, first_midi: int, last_midi: int, dims: PianoDimensions,
                          pattern: str = "mixed", heat_lift: float = 70.0, ring_white: float = 250.0, key_scale: float = 2.2,
                          margin: float = 900.0) -> list[WalkwayKey]:
    """Walkable key patterns on the spline: every octave becomes one rosette (mandala ring or phyllotaxis spiral) centred
    on the path, long axes radial. Black keys sit ON the white petals (base at the white top, over the petal overlap).
    Heights follow path_heat. No ground snapping: the walkway floats."""
    groups = _octave_groups(first_midi, last_midi)
    n = len(groups)
    spacing = max(1.0, (length - 2.0 * margin) / max(n, 1))
    keys: list[WalkwayKey] = []
    key_index = 0
    for g, notes in enumerate(groups):
        s_c = margin + (g + 0.5) * spacing
        c_pos, c_tan = frame(s_c)
        right = right_vector(c_tan)
        path_yaw, _ = yaw_pitch(c_tan)
        lift = heat_lift * path_heat(s_c, length)
        mode = pattern if pattern != "mixed" else ("mandala" if g % 2 == 0 else "phyllotaxis")
        whites = [m for m in notes if not is_black_midi(m)]
        for m in notes:
            black = is_black_midi(m)
            if mode == "mandala":
                nw = max(len(whites), 1)
                if black:
                    k = whites.index(m - 1) if (m - 1) in whites else 0
                    theta = (k + 0.5) * 360.0 / 7.0
                    radius = (ring_white - 30.0) * key_scale
                else:
                    theta = whites.index(m) * 360.0 / 7.0
                    radius = ring_white * key_scale
            else:   # phyllotaxis: Vogel spiral, order by pitch
                j = notes.index(m)
                theta = j * GOLDEN_ANGLE_DEG
                radius = 230.0 * key_scale * math.sqrt(j + 0.6)
            ct, st = math.cos(math.radians(theta)), math.sin(math.radians(theta))
            u, v = ct * radius, st * radius                       # along, across
            x = c_pos[0] + c_tan[0] * u + right[0] * v
            y = c_pos[1] + c_tan[1] * u + right[1] * v
            z = c_pos[2] + lift + key_scale * (dims.white_height + dims.black_height * 0.5 if black else dims.white_height * 0.5)
            w, d, h = [key_scale * q for q in ((dims.black_width, dims.black_depth, dims.black_height) if black else (dims.white_width, dims.white_depth, dims.white_height))]
            keys.append(WalkwayKey(key_index=key_index, midi_note=m, is_black=black, position=(x, y, z), yaw=path_yaw + theta - 90.0,
                                   pitch=0.0, width=w, depth=d, height=h, seed=(m << 8) | (key_index & 0xFF), distance=s_c + key_index * 0.01))
            key_index += 1
    return keys



def rail_points(frame: FrameFn, path_length: float, lateral: float, segment: float = 200.0,
                ground: Callable[[float, float, float], float] | None = None) -> list[tuple[Vec, float, float]]:
    """Rail segment start points (position, yaw, pitch) down one side. lateral > 0 = right side."""
    out = []
    count = int(path_length // segment)
    for k in range(count):
        pos, tangent = frame(k * segment)
        right = right_vector(tangent)
        x = pos[0] + right[0] * lateral
        y = pos[1] + right[1] * lateral
        z = ground(x, y, pos[2]) if ground else pos[2]
        yaw, pitch = yaw_pitch(tangent)
        out.append(((x, y, z), yaw, pitch))
    return out


# --------------------------------------------------------------------------------------------------------------------
# Biome variants (data only; materials are instances of M_Master_Toon_Universal made in the editor)
# --------------------------------------------------------------------------------------------------------------------

BIOMES = {
    # name: (first_midi, hue offset, hue span, ivory rim, ebony rim, ivory tint, ebony tint)
    "MorningMeadow": dict(hue_offset=0.00, hue_span=1.00, ivory_tint=(0.95, 0.92, 0.84), ivory_rim=(1.0, 0.80, 0.95),
                          ebony_tint=(0.50, 0.50, 0.50), ebony_rim=(0.65, 0.55, 1.0)),
    "SeaAboveReef": dict(hue_offset=0.45, hue_span=0.35, ivory_tint=(0.86, 0.96, 0.95), ivory_rim=(0.35, 0.95, 0.85),
                         ebony_tint=(0.30, 0.42, 0.50), ebony_rim=(0.25, 0.70, 1.0)),
    "SakuraGarden": dict(hue_offset=0.88, hue_span=0.18, ivory_tint=(1.0, 0.92, 0.94), ivory_rim=(1.0, 0.62, 0.80),
                         ebony_tint=(0.45, 0.30, 0.38), ebony_rim=(1.0, 0.45, 0.65)),
    "FarawayFabric": dict(hue_offset=0.72, hue_span=0.22, ivory_tint=(0.92, 0.88, 0.97), ivory_rim=(0.78, 0.60, 1.0),
                          ebony_tint=(0.35, 0.30, 0.50), ebony_rim=(0.60, 0.40, 1.0)),
}


# --------------------------------------------------------------------------------------------------------------------
# Editor half
# --------------------------------------------------------------------------------------------------------------------

WALKWAY_FOLDER = "/Game/Melodia/PCG/Walkways"
MI_FOLDER = "/Game/EnvSandbox/Materials/Instances/PianoPath"
RAIL_FOLDER = "/Game/EnvSandbox/PCG/Musical/Rails"
RAIL_MESH = RAIL_FOLDER + "/SM_MusicRail_2m"
RAIL_MATERIAL = MI_FOLDER + "/MI_GoldenRail_Toon"
BASE_PROFILE = "/Game/EnvSandbox/PCG/Musical/DA_PianoKeyRun_2OctProfile"
WALKWAY_DIMS = PianoDimensions(white_width=110.0, white_depth=360.0, white_height=30.0, black_width=64.0,
                               black_depth=220.0, black_height=36.0, inter_key_gap=4.0, keybed_top=0.0)


def import_rail_mesh(fbx_path: str, asset_name: str = "SM_MusicRail_2m") -> str:
    """Import a baked rail segment FBX as a static mesh (no materials, no collision)."""
    import unreal
    if not unreal.EditorAssetLibrary.does_directory_exist(RAIL_FOLDER):
        unreal.EditorAssetLibrary.make_directory(RAIL_FOLDER)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", RAIL_FOLDER)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_animations", False)
    opts.static_mesh_import_data.set_editor_property("combine_meshes", True)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    path = f"{RAIL_FOLDER}/{asset_name}"
    mesh = unreal.load_asset(path)
    if mesh:
        unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        unreal.EditorAssetLibrary.save_asset(path)
    return path


def _find_actor(unreal, label: str):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def _spline_frame(unreal, spline) -> tuple[FrameFn, float]:
    length = spline.get_spline_length()
    world = unreal.SplineCoordinateSpace.WORLD

    def frame(dist: float):
        d = max(0.0, min(dist, length))
        p = spline.get_location_at_distance_along_spline(d, world)
        t = spline.get_direction_at_distance_along_spline(d, world)
        return (p.x, p.y, p.z), (t.x, t.y, t.z)

    return frame, length


def _ground_fn(unreal, world, ignore):
    def ground(x: float, y: float, z_hint: float) -> float:
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, z_hint + 1500.0), unreal.Vector(x, y, z_hint - 3000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, True)
        if hit is not None and hit.to_tuple()[0]:
            return hit.to_tuple()[5].z
        return z_hint
    return ground


def _point(unreal, local: Vec, yaw: float, pitch: float, width: float, depth: float, height: float, seed: int):
    p = unreal.PCGPoint()
    p.set_editor_property("transform", unreal.Transform(
        location=unreal.Vector(*local), rotation=unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw),
        scale=unreal.Vector(1.0, 1.0, 1.0)))
    p.set_editor_property("density", 1.0)
    p.set_editor_property("seed", int(seed))
    p.set_editor_property("bounds_min", unreal.Vector(-width * 0.5, -depth * 0.5, -height * 0.5))
    p.set_editor_property("bounds_max", unreal.Vector(width * 0.5, depth * 0.5, height * 0.5))
    return p


def ensure_profile(biome: str):
    """Duplicate the 2-octave profile into DA_PianoWalkway_<biome> and apply the biome look. Returns the asset path."""
    import unreal
    cfg = BIOMES[biome]
    if not unreal.EditorAssetLibrary.does_directory_exist(WALKWAY_FOLDER):
        unreal.EditorAssetLibrary.make_directory(WALKWAY_FOLDER)
    path = f"{WALKWAY_FOLDER}/DA_PianoWalkway_{biome}"
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.duplicate_asset(BASE_PROFILE, path)
    prof = unreal.load_asset(path)
    dims = prof.get_editor_property("dimensions")
    for prop, value in dict(white_key_width=WALKWAY_DIMS.white_width, white_key_depth=WALKWAY_DIMS.white_depth,
                            white_key_height=WALKWAY_DIMS.white_height, black_key_width=WALKWAY_DIMS.black_width,
                            black_key_depth=WALKWAY_DIMS.black_depth, black_key_height=WALKWAY_DIMS.black_height,
                            inter_key_gap=WALKWAY_DIMS.inter_key_gap).items():
        try:
            dims.set_editor_property(prop, float(value))
        except Exception:
            pass
    prof.set_editor_property("dimensions", dims)
    prof.set_editor_property("press_hue_offset", float(cfg["hue_offset"]))
    prof.set_editor_property("press_hue_span", float(cfg["hue_span"]))
    for prop, name in (("white_key_material", f"MI_PianoKey_{biome}_Ivory"), ("black_key_material", f"MI_PianoKey_{biome}_Ebony")):
        mi = unreal.load_asset(f"{MI_FOLDER}/{name}")
        if mi:
            prof.set_editor_property(prop, mi)
    unreal.EditorAssetLibrary.save_asset(path)
    return path


def build_walkway(spline_actor_label: str, biome: str = "MorningMeadow", whites: int | None = None,
                  first_midi: int = 48, name: str | None = None, rails: bool = True, rail_offset: float = 40.0,
                  pattern: str | None = "mixed", snap_ground: bool = False):
    """Create (or rebuild) a piano walkway along the spline carried by the labelled actor. Returns a summary dict."""
    import unreal
    import pcg_graph_builder as gb
    import build_pcg_piano as bp

    name = name or spline_actor_label
    spline_actor = _find_actor(unreal, spline_actor_label)
    if spline_actor is None:
        raise RuntimeError(f"no actor labelled {spline_actor_label}")
    spline = spline_actor.get_component_by_class(unreal.SplineComponent)
    frame, length = _spline_frame(unreal, spline)
    dims = WALKWAY_DIMS
    whites = whites or whites_for_length(length, dims)
    first, last = midi_range_for_whites(whites, first_midi)

    # drop previous copies of this walkway
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    tag = unreal.Name(f"Walkway.{name}")
    for a in eas.get_all_level_actors():
        if tag in a.tags:
            eas.destroy_actor(a)
    world = unreal.EditorLevelLibrary.get_editor_world()
    ignore = [a for a in eas.get_all_level_actors() if unreal.Name("PCG_PianoKey") in a.tags or isinstance(a, unreal.PCGPianoKeyboard)]
    ground = _ground_fn(unreal, world, ignore) if snap_ground else None

    keys = (map_layout_to_pattern(frame, length, first, last, dims, pattern) if pattern else map_layout_to_path(frame, first, last, dims, ground=ground))
    start_pos, _ = frame(0.0)
    origin = (start_pos[0], start_pos[1], ground(start_pos[0], start_pos[1], start_pos[2]) if ground else start_pos[2])

    def local(p: Vec) -> Vec:
        return (p[0] - origin[0], p[1] - origin[1], p[2] - origin[2])

    graph_path = f"{WALKWAY_FOLDER}/PCG_PianoWalkway_{name}"
    if not unreal.EditorAssetLibrary.does_directory_exist(WALKWAY_FOLDER):
        unreal.EditorAssetLibrary.make_directory(WALKWAY_FOLDER)
    graph, _created = gb.load_or_create_graph(graph_path, WALKWAY_FOLDER, force=True)
    gb.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-800, 0)
    out = graph.get_output_node()
    out.set_node_position(900, 0)

    local_space = getattr(getattr(unreal, "PCGCoordinateSpace", None), "LOCAL_COMPONENT", None)
    for is_black, y_pos in ((False, -160), (True, 160)):
        group = [k for k in keys if k.is_black == is_black]
        create, cs = gb.add_node(graph, "PCGCreatePointsSettings", -500, y_pos)
        cs.set_editor_property("points_to_create", [
            _point(unreal, local(k.position), k.yaw, k.pitch, k.width, k.depth, k.height, k.seed) for k in group])
        if local_space is not None:
            bp._set_if_present(cs, "coordinate_space", local_space)
        spawn, ss = gb.add_node(graph, "PCGSpawnActorSettings", -120, y_pos)
        bp._configure_spawn_settings(
            unreal, ss, bp._resolve_actor_class(unreal, "PCGPianoBlackKey" if is_black else "PCGPianoWhiteKey"),
            "PCG_PianoBlack" if is_black else "PCG_PianoWhite", "Walkway Black Key" if is_black else "Walkway White Key")
        graph.add_edge(create, "Out", spawn, "In")
        graph.add_edge(spawn, "Out", out, "Out")

    rail_count = 0
    AAA = "/Game/Melodia/Meshes/MusicRail_AAA"
    # (mesh, material instance): AAA frame + scrolling notes when the kit is imported, else the legacy joined rail
    layers = ([(f"{AAA}/SM_MusicRail_AAA_Frame_2m", RAIL_MATERIAL), (f"{AAA}/SM_MusicRail_AAA_Notes_2m", MI_FOLDER + "/MI_ScoreNotes_Glow")]
              if unreal.EditorAssetLibrary.does_asset_exist(f"{AAA}/SM_MusicRail_AAA_Frame_2m") else [(RAIL_MESH, RAIL_MATERIAL)])
    if rails and unreal.EditorAssetLibrary.does_asset_exist(layers[0][0]):
        lateral = dims.white_depth * 0.5 + rail_offset
        pts = []
        for side in (1.0, -1.0):
            pts += rail_points(frame, length, side * lateral, 200.0, ground)
        for li, (mesh_path, mat_path) in enumerate(layers):
            rail_create, rcs = gb.add_node(graph, "PCGCreatePointsSettings", -500, 420 + 300 * li)
            rcs.set_editor_property("points_to_create", [
                _point(unreal, local(p), yaw, pitch, 200.0, 10.0, 105.0, 7000 + i) for i, (p, yaw, pitch) in enumerate(pts)])
            if local_space is not None:
                bp._set_if_present(rcs, "coordinate_space", local_space)
            rail_spawn, rss = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", -120, 420 + 300 * li)
            entry = unreal.PCGMeshSelectorWeightedEntry()
            desc = entry.get_editor_property("descriptor")
            desc.set_editor_property("static_mesh", unreal.load_asset(mesh_path))
            mat = unreal.load_asset(mat_path)
            if mat:
                for prop in ("override_materials", "material_overrides"):
                    try:
                        desc.set_editor_property(prop, [mat])
                        break
                    except Exception:
                        continue
            try:
                desc.set_editor_property("component_tags", [unreal.Name("MelodiaCymatic"), unreal.Name("MelodiaSeasonal")])
            except Exception:
                pass
            entry.set_editor_property("descriptor", desc)
            entry.set_editor_property("weight", 1)
            rss.get_editor_property("mesh_selector_parameters").set_editor_property("mesh_entries", [entry])
            graph.add_edge(rail_create, "Out", rail_spawn, "In")
            graph.add_edge(rail_spawn, "Out", out, "Out")
        rail_count = len(pts) * len(layers)
    bp._set_if_present(graph, "is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(graph_path)

    profile_path = ensure_profile(biome)
    prof = unreal.load_asset(profile_path)
    prof.set_editor_property("first_midi_note", first)
    prof.set_editor_property("last_midi_note", last)
    unreal.EditorAssetLibrary.save_asset(profile_path)

    kb = eas.spawn_actor_from_class(unreal.PCGPianoKeyboard, unreal.Vector(*origin))
    kb.set_actor_label(f"Piano Walkway ({name})")
    kb.tags = [tag, unreal.Name("Portfolio"), unreal.Name("PianoWalkway")]
    kb.set_editor_property("profile", prof)
    kb.set_editor_property("piano_graph", unreal.load_asset(graph_path))
    kb.set_editor_property("keyboard_id", unreal.Name(f"Walkway_{name}"))
    kb.set_editor_property("order_path_actor", spline_actor)
    # bounds: local bounding box of every generated point + margin
    all_local = [local(k.position) for k in keys]
    lo = [min(p[i] for p in all_local) for i in range(3)]
    hi = [max(p[i] for p in all_local) for i in range(3)]
    box = kb.get_editor_property("generation_bounds")
    box.set_relative_location(unreal.Vector((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2), False, False)
    box.set_box_extent(unreal.Vector((hi[0] - lo[0]) / 2 + 600, (hi[1] - lo[1]) / 2 + 600, (hi[2] - lo[2]) / 2 + 600), True)
    comp = kb.get_component_by_class(unreal.PCGComponent)
    comp.set_graph(unreal.load_asset(graph_path))
    comp.generate(True)
    summary = dict(keyboard=kb.get_name(), keys=len(keys), whites=whites, first_midi=first, last_midi=last,
                   path_length_cm=round(length), rails=rail_count, graph=graph_path, profile=profile_path,
                   origin=[round(v) for v in origin])
    unreal.log(f"[PianoWalkway] {summary}")
    return summary
