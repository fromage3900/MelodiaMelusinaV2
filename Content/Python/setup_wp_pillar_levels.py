"""Create 4 World Partition pillar levels with portfolio pipeline scaffold.

Levels (WP-native, MeshTerrain-ready):
  L_WP_SakuraDream      — MeadowFalloff PCG + warm daylight
  L_WP_SpaceCathedral   — Escher PCG + cool volumetrics
  L_WP_BaroqueGrotto    — Cave/strata PCG + enclosed wet mood
  L_WP_CosmicOrrery     — Orbit scatter PCG + night cosmic mood

Each level gets:
  - GeometryScript terrain block-in (tagged MeshTerrain_Seed — replace with UE 5.8
    MeshTerrain actor in-editor; no Python authoring API exists yet)
  - Per-pillar lighting mood + NikkiDream PPV
  - Portfolio hero cameras (Portfolio_Hero tag)
  - PCG volume wired to pillar graph

Run in-editor (one pillar):
  py Content/Python/setup_wp_pillar_levels.py --pillar SakuraDream

Run all pillars in-editor:
  py Content/Python/setup_wp_pillar_levels.py --all

If levels were created before the WP fix (world_partition=false in audit), recreate once:
  py Content/Python/setup_wp_pillar_levels.py --all --recreate-wp

Headless (editor closed):
  py Content/Python/run_wp_pillar_levels_cmd.py
  py Content/Python/run_wp_pillar_levels_cmd.py --pillar SpaceCathedral
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std
import render_exporter as rex

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "wp_pillar_levels.json"
LEVEL_DIR = "/Game/EnvSandbox/Environments/WP"
SCRATCH_LEVEL = f"{LEVEL_DIR}/_WPPillar_BuildScratch"
TERRAIN_DIR = "/Game/EnvSandbox/Meshes/WPTerrains"
HERO_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
COSMIC_GRAPH = "/Game/EnvSandbox/PCG/Styles/Cosmic/PCG_Cosmic_OrbitScatter"
ESCHER_DECKS = "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherDecks"
PENROSE_SHRINE = "/Game/EnvSandbox/PCG/Styles/Escher/PCG_PenroseShrine"
FLOATING_STAIRWAYS = "/Game/EnvSandbox/PCG/Styles/Escher/PCG_FloatingStairways"
BRIDGE_ARCHIPELAGO = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BridgeArchipelago"
CATHEDRAL_NAVE = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_CathedralNave"
GREYBOX_BLOCKOUT = "/Game/EnvSandbox/PCG/Universal/PCG_GreyboxBlockout"
BAROQUE_COLONNADE = "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BaroqueColonnade"

UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

TAG_MESH_TERRAIN_SEED = "MeshTerrain_Seed"
TAG_GROUND = std.TAG_GROUND


@dataclass(frozen=True)
class PillarConfig:
    key: str
    level_name: str
    hero_material: str
    noise_layers: tuple[tuple[float, float], ...]
    sun_rot: tuple[float, float]
    sun_color: tuple[float, float, float]
    sun_intensity: float
    fog_color: tuple[float, float, float]
    fog_density: float
    pcg_mode: str
    pcg_graphs: tuple[str, ...]
    camera_offset: tuple[float, float, float]


PILLARS: dict[str, PillarConfig] = {
    "SakuraDream": PillarConfig(
        key="SakuraDream",
        level_name="L_WP_SakuraDream",
        hero_material=f"{HERO_DIR}/MI_NikkiHero_SakuraDream",
        noise_layers=((400.0, 0.00008), (120.0, 0.0004)),
        sun_rot=(-35.0, 210.0),
        sun_color=(1.0, 0.85, 0.80),
        sun_intensity=6.5,
        fog_color=(0.95, 0.75, 0.85),
        fog_density=0.015,
        pcg_mode="meadow_falloff",
        pcg_graphs=(std.GRAPH_MEADOW_BLOOM, std.GRAPH_BLOSSOM_PATH, std.GRAPH_SAKURA_GROVE, std.GRAPH_PETAL_DRIFT),
        camera_offset=(-8000.0, -7000.0, 3200.0),
    ),
    "SpaceCathedral": PillarConfig(
        key="SpaceCathedral",
        level_name="L_WP_SpaceCathedral",
        hero_material=f"{HERO_DIR}/MI_NikkiHero_SpaceCathedral",
        noise_layers=((450.0, 0.00006), (150.0, 0.0004)),
        sun_rot=(-20.0, 250.0),
        sun_color=(0.85, 0.72, 0.98),
        sun_intensity=5.5,
        fog_color=(0.62, 0.55, 0.90),
        fog_density=0.018,
        pcg_mode="escher",
        # Live-tested greybox spine. Experimental Escher rooms stay out of the
        # first pass because they require special inputs or can occlude traversal.
        pcg_graphs=(std.GRAPH_ROCK, std.GRAPH_GARDEN_RUINS, FLOATING_STAIRWAYS, std.GRAPH_GREYBOX_STANDARD, BRIDGE_ARCHIPELAGO),
        camera_offset=(-10000.0, -8500.0, 4500.0),
    ),
    "BaroqueGrotto": PillarConfig(
        key="BaroqueGrotto",
        level_name="L_WP_BaroqueGrotto",
        hero_material=f"{HERO_DIR}/MI_NikkiHero_BaroqueCastle",
        noise_layers=((380.0, 0.0001), (150.0, 0.0004)),
        sun_rot=(-15.0, 300.0),
        sun_color=(0.75, 0.55, 0.70),
        sun_intensity=4.0,
        fog_color=(0.65, 0.42, 0.72),
        fog_density=0.022,
        pcg_mode="cave_strata",
        pcg_graphs=(std.GRAPH_ROCK, std.GRAPH_WALL_MOSS, std.GRAPH_WALL_LICHEN, std.GRAPH_WALL_IVY, std.GRAPH_GARDEN_RUINS),
        camera_offset=(-6000.0, -5500.0, 2800.0),
    ),
    "CosmicOrrery": PillarConfig(
        key="CosmicOrrery",
        level_name="L_WP_CosmicOrrery",
        hero_material=f"{HERO_DIR}/MI_NikkiHero_CosmicOrrery",
        noise_layers=((500.0, 0.00005), (150.0, 0.0003)),
        sun_rot=(-10.0, 180.0),
        sun_color=(0.62, 0.48, 0.92),
        sun_intensity=2.5,
        fog_color=(0.28, 0.18, 0.48),
        fog_density=0.015,
        pcg_mode="cosmic_orbit",
        pcg_graphs=(COSMIC_GRAPH, std.GRAPH_LANTERN_GROVE, std.GRAPH_GARDEN_RUINS),
        camera_offset=(-9000.0, -9000.0, 5000.0),
    ),
}


def _parse_args() -> dict:
    pillar = ""
    run_all = "--all" in sys.argv
    recreate_wp = "--recreate-wp" in sys.argv
    verify_only = "--verify" in sys.argv
    for index, arg in enumerate(sys.argv):
        if arg == "--pillar" and index + 1 < len(sys.argv):
            pillar = sys.argv[index + 1]
    return {"pillar": pillar, "all": run_all, "recreate_wp": recreate_wp, "verify": verify_only}


def _get_editor_world():
    import unreal

    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            world = ues.get_editor_world()
            if world:
                return world
    except Exception:
        pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _level_disk_paths(level_path: str) -> list[Path]:
    rel = level_path.removeprefix("/Game/")
    base = PROJECT_ROOT / "Content" / rel.replace("/", "\\")
    return [base.with_suffix(ext) for ext in (".umap", ".uasset")]


def _external_actors_dir(level_path: str) -> Path:
    rel = level_path.removeprefix("/Game/").replace("/", "\\")
    return PROJECT_ROOT / "Content" / "__ExternalActors__" / rel


def _package_on_disk(level_path: str) -> bool:
    return any(p.is_file() for p in _level_disk_paths(level_path))


def _refresh_asset_registry(level_folder: str) -> None:
    import unreal

    try:
        unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous([level_folder], True)
    except Exception:
        pass


def _park_editor_on_scratch(les) -> None:
    """Unload the target level package before purge (avoids ghost in-memory world)."""
    import unreal

    if not unreal.EditorAssetLibrary.does_directory_exist(LEVEL_DIR):
        unreal.EditorAssetLibrary.make_directory(LEVEL_DIR)
    if _package_on_disk(SCRATCH_LEVEL) and unreal.EditorAssetLibrary.does_asset_exist(SCRATCH_LEVEL):
        les.load_level(SCRATCH_LEVEL)
        return
    les.new_level(SCRATCH_LEVEL, is_partitioned_world=False)


def _purge_level_package(level_path: str) -> dict:
    """Remove level package from asset registry and disk.

    EditorAssetLibrary.delete_asset alone is not enough: levels are .umap packages and
    FPackageName::DoesPackageExist still sees them, so new_level() returns false.
    """
    import shutil
    import unreal

    purge: dict = {"level": level_path, "delete_asset": False, "disk_removed": [], "external_actors_removed": False}
    if unreal.EditorAssetLibrary.does_asset_exist(level_path):
        purge["delete_asset"] = bool(unreal.EditorAssetLibrary.delete_asset(level_path))
    for path in _level_disk_paths(level_path):
        if path.is_file():
            path.unlink()
            purge["disk_removed"].append(str(path))
    ext_dir = _external_actors_dir(level_path)
    if ext_dir.is_dir():
        shutil.rmtree(ext_dir, ignore_errors=True)
        purge["external_actors_removed"] = True
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, False)
    except Exception:
        pass
    return purge


def _is_world_partitioned(world, level_path: str | None = None) -> bool:
    """True if the current editor world is a World Partition level.

    FIXED 2026-07-09: the previous implementation was a guaranteed false
    negative on UE 5.8 -- `World.get_world_partition()` does not exist in the
    Python API and neither do any `*enable_world_partition*` properties on
    WorldSettings (verified live; both raised and were swallowed). That made
    the 07-09 audit report world_partition=false for levels that were in fact
    WP-native. Detection now uses (1) the on-disk __ExternalActors__ folder for
    the level (definitive OFPA/WP marker) and (2) a WorldPartitionBlueprintLibrary
    call that only succeeds in WP worlds.
    """
    import unreal

    if not world:
        return False
    if level_path:
        ext = _external_actors_dir(level_path)
        if ext.is_dir() and any(ext.rglob("*.uasset")):
            return True
    try:
        bounds = unreal.WorldPartitionBlueprintLibrary.get_editor_world_bounds()
        if bounds and bounds.is_valid:
            return True
    except Exception:
        pass
    return False


def _ensure_wp_level(les, level_path: str, *, recreate: bool = False) -> dict:
    """Create or load a WP-native level.

    UE 5.8: LevelEditorSubsystem.new_level(path, is_partitioned_world=True).
    After --recreate-wp purge, disk absence is the source of truth (registry can lie).
    """
    import unreal

    info: dict = {"level": level_path, "recreate": recreate}
    on_disk = _package_on_disk(level_path)
    in_registry = unreal.EditorAssetLibrary.does_asset_exist(level_path)

    if recreate and (on_disk or in_registry):
        _park_editor_on_scratch(les)
        info["purge"] = _purge_level_package(level_path)
        _refresh_asset_registry(LEVEL_DIR)
        time.sleep(0.25)
        on_disk = _package_on_disk(level_path)
        in_registry = unreal.EditorAssetLibrary.does_asset_exist(level_path)
        info["deleted_existing"] = True

    if not on_disk:
        if in_registry:
            unreal.EditorAssetLibrary.delete_asset(level_path)
            _refresh_asset_registry(LEVEL_DIR)
            time.sleep(0.1)
        ok = les.new_level(level_path, is_partitioned_world=True)
        world = _get_editor_world()
        info.update({
            "created": True,
            "new_level_ok": ok,
            "method": "new_level(is_partitioned_world=True)",
            "world_partition": _is_world_partitioned(world, level_path),
        })
        if not ok:
            info["error"] = (
                "new_level returned false — check Saved/Logs for LevelEditorSubsystem::NewLevel errors"
            )
        return info

    les.load_level(level_path)
    world = _get_editor_world()
    wp = _is_world_partitioned(world, level_path)
    if not wp:
        wp = _enable_world_partition()
        world = _get_editor_world()
        wp = wp or _is_world_partitioned(world, level_path)
    info.update({
        "created": False,
        "world_partition": wp,
        "method": "load_existing",
        "on_disk": True,
    })
    if not wp:
        info["fix"] = "Re-run with --recreate-wp to replace this map with a WP-native level."
    return info


def _set_tag(actor, tag: str) -> None:
    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _enable_world_partition() -> bool:
    """Fallback: toggle WP on a legacy non-partitioned map (prefer is_partitioned_world=True on create)."""
    import unreal

    world = _get_editor_world()
    if not world:
        return False
    try:
        ws = world.get_world_settings()
        for prop in ("b_enable_world_partition", "enable_world_partition", "bEnableWorldPartition"):
            try:
                ws.set_editor_property(prop, True)
                return _is_world_partitioned(_get_editor_world())
            except Exception:
                continue
    except Exception as exc:
        unreal.log_warning(f"[WPPillar] WP enable failed: {exc}")
    return False


def _terrain_mesh(name: str, layers: tuple[tuple[float, float], ...], *, force: bool = False) -> str:
    """Author (or re-author) the pillar terrain static mesh.

    FIXED 2026-07-09: the deprecated `apply_perlin_noise_to_mesh` squares the
    frequency parameter (engine deprecation note confirms it), so configured
    frequencies like 0.00008 collapsed to ~0 and every pillar terrain came out
    flat (Z extent 0.21cm instead of the configured 380-500cm magnitude).
    `apply_perlin_noise_to_mesh2` applies frequency correctly (verified live:
    Z extent ~470cm at magnitude 400). Existing flat meshes are auto-rebuilt.
    """
    import unreal

    asset_path = f"{TERRAIN_DIR}/SM_Terrain_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        rebuild = force
        if not rebuild:
            try:
                existing = unreal.EditorAssetLibrary.load_asset(asset_path)
                box = existing.get_bounding_box()  # Box has min/max, no get_size()
                rebuild = (box.max.z - box.min.z) < 50.0  # flat legacy mesh from the squared-frequency bug
            except Exception:
                rebuild = True  # can't prove it's good -> rebuild
        if not rebuild:
            return asset_path
        unreal.EditorAssetLibrary.delete_asset(asset_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(TERRAIN_DIR):
        unreal.EditorAssetLibrary.make_directory(TERRAIN_DIR)
    dm = unreal.new_object(unreal.DynamicMesh)
    prim_opts = unreal.GeometryScriptPrimitiveOptions()
    xform = unreal.Transform()
    unreal.GeometryScript_Primitives.append_rectangle_xy(
        dm, prim_opts, xform, 20000.0, 20000.0, 128, 128)
    for layer_index, (mag, freq) in enumerate(layers):
        opts = unreal.GeometryScriptPerlinNoiseOptions()
        base = unreal.GeometryScriptPerlinNoiseLayerOptions()
        base.set_editor_property("magnitude", mag)
        base.set_editor_property("frequency", freq)
        base.set_editor_property("frequency_shift", unreal.Vector(0, 0, 0))
        base.set_editor_property("random_seed", hash(name) % 10000 + layer_index)
        opts.set_editor_property("base_layer", base)
        sel = unreal.GeometryScriptMeshSelection()
        unreal.GeometryScript_MeshDeformers.apply_perlin_noise_to_mesh2(dm, sel, opts)
    unreal.GeometryScript_Normals.recompute_normals(
        dm, unreal.GeometryScriptCalculateNormalsOptions())
    out = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dm, asset_path, out)
    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return asset_path


def _ensure_cosmic_orbit_graph(*, force: bool = False) -> str:
    target = COSMIC_GRAPH
    folder = target.rsplit("/", 1)[0]
    graph, _ = gb.load_or_create_graph(target, folder, force=force)
    gb.wire_scatter_chain(
        graph,
        voxel_cm=420.0,
        grass_mi=std.MI_GREYBOX_GRASS,
        use_surface_tag=False,
        density_mult=0.12,
        transform_jitter=55.0,
        spacing_prune=True,
        apply_exclusion=False,
        role="decor",
        scale_min=0.5,
        scale_max=2.0,
    )
    import unreal

    unreal.EditorAssetLibrary.save_asset(target, only_if_is_dirty=False)
    return target


def _ensure_pcg_graphs(cfg: PillarConfig, *, force: bool = False) -> list[str]:
    import setup_pcg_universal as uni

    ready: list[str] = []
    if cfg.pcg_mode == "meadow_falloff":
        import unreal

        uni.build_style_graphs(force=force)
        for graph_path in cfg.pcg_graphs:
            preset_key = {
                std.GRAPH_MEADOW_BLOOM: "meadow_bloom",
                std.GRAPH_BLOSSOM_PATH: "blossom_path",
                std.GRAPH_SAKURA_GROVE: "sakura_grove",
                std.GRAPH_PETAL_DRIFT: "sakura_petal_drift",
            }.get(graph_path)
            if preset_key and preset_key in std.STYLE_PRESETS:
                preset = std.STYLE_PRESETS[preset_key]
                graph, _ = gb.load_or_create_graph(graph_path, graph_path.rsplit("/", 1)[0], force=force)
                gb.wire_scatter_chain(
                    graph,
                    voxel_cm=preset["voxel_cm"],
                    grass_mi=preset["material"] or std.MI_GREYBOX_GRASS,
                    use_surface_tag=preset["use_surface_tag"],
                    density_mult=preset["density"],
                    transform_jitter=preset["transform_jitter"],
                    spacing_prune=True,
                    apply_exclusion=preset["spawn_exclusion"],
                    role=preset["role"],
                    scale_min=preset["scale"][0],
                    scale_max=preset["scale"][1],
                )
                import unreal
                unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
            elif not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
                # Graph doesn't exist and no style preset — try generic scatter chain
                graph, _ = gb.load_or_create_graph(graph_path, graph_path.rsplit("/", 1)[0], force=force)
                gb.wire_scatter_chain(
                    graph, voxel_cm=240.0, grass_mi=std.MI_GREYBOX_GRASS,
                    density_mult=0.25, spacing_prune=True, role="grass",
                )
                unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
            ready.append(graph_path)
    elif cfg.pcg_mode == "escher":
        # The greybox pass intentionally uses catalogued graphs that can run
        # from a plain volume. Experimental Escher room/gravity builders need
        # authored inputs and are kept out of this production lane.
        import unreal
        for graph_path in cfg.pcg_graphs:
            if unreal.EditorAssetLibrary.does_asset_exist(graph_path):
                ready.append(graph_path)
    elif cfg.pcg_mode == "cave_strata":
        uni.build_rock(force=force)
        ready.insert(0, std.GRAPH_ROCK)
        wall_detail = __import__("build_pcg_wall_detail", fromlist=["build_wall_moss", "build_wall_lichen", "build_wall_ivy"])
        wall_detail.build_wall_moss()
        ready.append(std.GRAPH_WALL_MOSS)
        for graph_path in cfg.pcg_graphs:
            if graph_path == std.GRAPH_ROCK or graph_path == std.GRAPH_WALL_MOSS:
                continue
            elif graph_path == std.GRAPH_WALL_LICHEN:
                wall_detail.build_wall_lichen()
                ready.append(std.GRAPH_WALL_LICHEN)
            elif graph_path == std.GRAPH_WALL_IVY:
                wall_detail.build_wall_ivy()
                ready.append(std.GRAPH_WALL_IVY)
            elif graph_path == std.GRAPH_GARDEN_RUINS:
                uni.build_style_graphs(force=force)
                ready.append(std.GRAPH_GARDEN_RUINS)
    elif cfg.pcg_mode == "cosmic_orbit":
        ready.append(_ensure_cosmic_orbit_graph(force=force))
        for graph_path in cfg.pcg_graphs[1:]:
            if graph_path == std.GRAPH_LANTERN_GROVE:
                uni.build_style_graphs(force=force)
                ready.append(std.GRAPH_LANTERN_GROVE)
            elif graph_path == std.GRAPH_GARDEN_RUINS:
                uni.build_style_graphs(force=force)
                ready.append(std.GRAPH_GARDEN_RUINS)
    return ready


def _spawn_actor(eas, existing: dict, cls, label: str, loc=(0, 0, 0), rot=(0, 0, 0)):
    import unreal

    if label in existing:
        return existing[label]
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
    r = unreal.Rotator()
    r.set_editor_property("pitch", rot[0])
    r.set_editor_property("yaw", rot[1])
    r.set_editor_property("roll", rot[2] if len(rot) > 2 else 0.0)
    actor.set_actor_rotation(r, False)
    actor.set_actor_label(label)
    # WP editor builds must keep authored route/PCG anchors in the persistent
    # layer; otherwise reopening the map unloads them and leaves nav bounds
    # over empty terrain.
    try:
        actor.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass
    existing[label] = actor
    return actor


def _spawn_hero_cameras(eas, existing: dict, offset: tuple[float, float, float]) -> list[str]:
    import unreal

    labels: list[str] = []
    specs = (
        ("Cam_Hero_Establishing", rex.TAG_HERO, offset, (-18.0, 42.0)),
        ("Cam_Hero_Materials", rex.TAG_HERO, (offset[0] * 0.6, offset[1] * 0.5, offset[2] * 0.7), (-12.0, 30.0)),
        ("Cam_Breakdown_Shader", rex.TAG_BREAKDOWN, (offset[0] * 0.45, offset[1] * 0.35, offset[2] * 0.5), (-10.0, 25.0)),
    )
    cine_cls = unreal.CineCameraActor.static_class()
    for label, tag, loc, rot in specs:
        cam = _spawn_actor(eas, existing, cine_cls, label, loc, rot)
        _set_tag(cam, tag)
        labels.append(label)
    return labels


# Universal graphs whose scatter chains are surface-sampler based. Vanilla
# PCGSurfaceSamplerSettings yields 0 points on StaticMeshActor terrain (proven
# live 2026-07-09 -- it is landscape-oriented), so on WP pillar levels these are
# substituted with per-pillar variants that mesh-sample SM_Terrain_<Pillar>
# directly via PCGMeshSamplerSettings (proven working the same session).
# basename -> (role, sampling_radius_cm, (scale_min, scale_max), max_samples)
WP_MESH_SCATTER_ROLES: dict[str, tuple[str, float, tuple[float, float], int]] = {
    "PCG_MeadowBloom": ("grass", 260.0, (0.5, 1.2), 3000),
    "PCG_BlossomPath": ("flower", 430.0, (0.6, 1.1), 1200),
    "PCG_SakuraGrove": ("petal", 700.0, (0.9, 1.6), 500),
    "PCG_Sakura_PetalDrift": ("petal", 380.0, (0.5, 1.0), 1500),
    "PCG_RockScatter": ("rock", 650.0, (0.7, 1.8), 700),
    "PCG_WallMoss": ("moss", 420.0, (0.4, 0.9), 1200),
    "PCG_WallLichen": ("moss", 520.0, (0.3, 0.7), 900),
    "PCG_WallIvy": ("moss", 600.0, (0.4, 1.0), 700),
    "PCG_GardenRuins": ("ruin", 1400.0, (0.8, 1.3), 120),
    # These graphs are specialized in their original contexts, but their
    # first-pass WP role is a bounded architectural greybox scatter. Mapping
    # them here prevents the graph from sampling the entire terrain asset.
    "PCG_FloatingStairways": ("ruin", 800.0, (0.8, 1.3), 100),
    "PCG_Greybox_Standard": ("ruin", 500.0, (0.8, 1.2), 80),
    "PCG_LanternGrove": ("lantern", 1600.0, (0.9, 1.1), 80),
}
WP_GRAPH_DIR = "/Game/EnvSandbox/PCG/Styles/WP"


def _wp_variant_graph(cfg: PillarConfig, graph_path: str, terrain_mesh_path: str) -> str:
    """Build (or reuse) the per-pillar mesh-sampled variant of a surface graph."""
    import unreal
    import pcg_graph_builder as gb

    basename = graph_path.rsplit("/", 1)[-1]
    spec = WP_MESH_SCATTER_ROLES.get(basename)
    if spec is None:
        return graph_path
    role, radius, (smin, smax), max_samples = spec
    variant_path = f"{WP_GRAPH_DIR}/PCG_WP_{cfg.key}_{basename.removeprefix('PCG_')}"
    graph, created = gb.load_or_create_graph(variant_path, WP_GRAPH_DIR, force=True)
    gb.wire_mesh_scatter_chain(
        graph,
        terrain_mesh_path=terrain_mesh_path,
        role=role,
        material_path=cfg.hero_material if role in ("grass", "moss") else None,
        sampling_radius_cm=radius,
        max_samples=max_samples,
        scale_min=smin,
        scale_max=smax,
        transform_jitter=15.0,
    )
    unreal.EditorAssetLibrary.save_asset(variant_path, only_if_is_dirty=False)
    return variant_path


def _spawn_pcg_volumes(
    eas, existing: dict, cfg: PillarConfig, graphs: list[str],
    terrain_mesh_path: str | None = None,
) -> list[dict]:
    import unreal
    import pcg_validate_helpers as vh

    volumes: list[dict] = []
    cx, cy, cz = std.PCG_VOLUME_CENTER
    sx, sy, sz = std.PCG_VOLUME_SCALE
    for index, graph_path in enumerate(graphs):
        if not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
            volumes.append({"graph": graph_path, "error": "missing"})
            continue
        if terrain_mesh_path:
            graph_path = _wp_variant_graph(cfg, graph_path, terrain_mesh_path)
        label = f"PCG_{cfg.key}_{index}"
        graph = unreal.load_asset(graph_path)
        vol = _spawn_actor(
            eas, existing, unreal.PCGVolume, label,
            (cx, cy + index * 400, cz), (0, 0, 0),
        )
        vol.set_actor_scale3d(unreal.Vector(sx * 2.2, sy * 2.2, sz * 2.5))
        comp = vol.get_component_by_class(unreal.PCGComponent)
        gb.assign_pcg_graph(comp, graph)
        gb.configure_pcg_component(comp, seed=std.SEED_FOLIAGE + index * 111, activated=True)
        # Existing WP actors may retain generated ISMs from an older volume
        # footprint. Clear them before kicking the async rebuild so a resized
        # greybox volume cannot appear to occupy the previous terrain-scale
        # bounds.
        try:
            comp.cleanup(True)
        except Exception as exc:
            unreal.log_warning(f"[WPPillar] PCG cleanup failed for {label}: {exc}")
        # KICK ONLY (fixed 2026-07-09): PCG generation is async and Python holds
        # the game thread, so any same-call wait/count always reads 0 (the old
        # generate_and_wait pattern produced last night's false ISM=0 audit).
        # Counting happens in a separate invocation: `--verify` / verify().
        try:
            vh_ = vh  # keep import used
            comp.generate(True)
        except Exception as exc:
            volumes.append({"graph": graph_path, "label": label, "error": str(exc)})
            continue
        volumes.append({"graph": graph_path, "label": label, "ism": None, "generate_kicked": True})
    return volumes


def verify(pillar_key: str, *, save_report: bool = True) -> dict:
    """Second-pass ISM count for a pillar level (run AFTER build(), in a
    separate editor call so async PCG generation has had real ticks)."""
    import unreal

    cfg = PILLARS[pillar_key]
    level_path = f"{LEVEL_DIR}/{cfg.level_name}"
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    world = _get_editor_world()
    if not world or world.get_name() != cfg.level_name:
        les.load_level(level_path)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    try:
        wpbl = unreal.WorldPartitionBlueprintLibrary
        wpbl.load_actors([descriptor.guid for descriptor in wpbl.get_actor_descs()])
    except Exception:
        pass
    counts: dict[str, int] = {}
    total = 0
    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label()
        if not label.startswith(f"PCG_{cfg.key}_"):
            continue
        n = 0
        for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            try:
                n += int(c.get_instance_count())
            except Exception:
                pass
        counts[label] = n
        total += n
    expected_labels = [f"PCG_{cfg.key}_{index}" for index in range(len(cfg.pcg_graphs))]
    missing_volumes = [label for label in expected_labels if label not in counts]
    empty_volumes = [label for label in expected_labels if counts.get(label, 0) <= 0]
    unexpected_volumes = sorted(label for label in counts if label not in expected_labels)
    result = {
        "pillar": pillar_key,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "ism_per_volume": counts,
        "total_ism": total,
        "expected_volume_count": len(expected_labels),
        "missing_volumes": missing_volumes,
        "empty_volumes": empty_volumes,
        "unexpected_volumes": unexpected_volumes,
        "world_partition": _is_world_partitioned(_get_editor_world(), level_path),
    }
    result["passed"] = (
        result["world_partition"]
        and not missing_volumes
        and not empty_volumes
        and not unexpected_volumes
    )
    if save_report and REPORT.is_file():
        try:
            data = json.loads(REPORT.read_text(encoding="utf-8"))
            pillar_entry = data.get("pillars", {}).get(pillar_key)
            if pillar_entry is not None:
                pillar_entry["verify"] = result
                pillar_entry["world_partition"] = result["world_partition"]
                pillar_entry["total_ism"] = total
                pillar_entry["passed"] = result["passed"]
                REPORT.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            result["report_update_error"] = str(exc)
    return result


def _save_current_level(les, level_path: str) -> bool:
    import unreal

    try:
        les.save_current_level()
        return _package_on_disk(level_path)
    except Exception as exc:
        unreal.log_warning(f"[WPPillar] save_current_level failed: {exc}")
    world = _get_editor_world()
    if not world:
        return False
    try:
        unreal.EditorLoadingAndSavingUtils.save_map(world, level_path)
        return _package_on_disk(level_path)
    except Exception as exc:
        unreal.log_warning(f"[WPPillar] save_map failed: {exc}")
        return False


def build(pillar_key: str, *, save: bool = True, recreate_wp: bool = False) -> dict:
    import unreal
    import build_ppv_nikkidream as ppv

    if pillar_key not in PILLARS:
        raise ValueError(f"unknown pillar: {pillar_key}")
    cfg = PILLARS[pillar_key]
    report: dict = {"pillar": pillar_key, "started_at": datetime.now(timezone.utc).isoformat()}

    if not unreal.EditorAssetLibrary.does_directory_exist(LEVEL_DIR):
        unreal.EditorAssetLibrary.make_directory(LEVEL_DIR)

    level_path = f"{LEVEL_DIR}/{cfg.level_name}"
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_info = _ensure_wp_level(les, level_path, recreate=recreate_wp)
    report["level"] = level_path
    report["level_info"] = level_info
    report["world_partition"] = level_info.get("world_partition", False)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # WP levels stream actors out on load — without loading them first the
    # `existing` label lookup is empty and every build spawns duplicates
    # (found live 2026-07-09: 6 PCGVolumes in CosmicOrrery, 2 per label).
    try:
        wpbl = unreal.WorldPartitionBlueprintLibrary
        wpbl.load_actors([d.guid for d in wpbl.get_actor_descs()])
    except Exception:
        pass
    existing = {a.get_actor_label(): a for a in eas.get_all_level_actors() or []}

    mesh_path = _terrain_mesh(cfg.key, cfg.noise_layers)
    report["terrain_mesh"] = mesh_path
    terrain = _spawn_actor(eas, existing, unreal.StaticMeshActor, f"Terrain_{cfg.key}")
    smc = terrain.static_mesh_component
    smc.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset(mesh_path))
    hero = unreal.EditorAssetLibrary.load_asset(cfg.hero_material)
    if hero:
        smc.set_material(0, hero)
    _set_tag(terrain, TAG_MESH_TERRAIN_SEED)
    _set_tag(terrain, TAG_GROUND)
    report["mesh_terrain_note"] = (
        "GeometryScript terrain tagged MeshTerrain_Seed — replace with UE 5.8 "
        "MeshTerrain actor in-editor when ready."
    )

    sun = _spawn_actor(
        eas, existing, unreal.DirectionalLight, "Sun", (0, 0, 5000),
        (cfg.sun_rot[0], cfg.sun_rot[1], 0),
    )
    lc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_editor_property("intensity", cfg.sun_intensity)
    lc.set_editor_property(
        "light_color",
        unreal.Color(
            int(cfg.sun_color[0] * 255),
            int(cfg.sun_color[1] * 255),
            int(cfg.sun_color[2] * 255),
            255,
        ),
    )
    _spawn_actor(eas, existing, unreal.SkyLight, "Sky", (0, 0, 5000))
    _spawn_actor(eas, existing, unreal.SkyAtmosphere, "Atmosphere")
    fog = _spawn_actor(eas, existing, unreal.ExponentialHeightFog, "Fog")
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fc.set_editor_property("fog_density", cfg.fog_density)
    fc.set_editor_property(
        "fog_inscattering_luminance",
        unreal.LinearColor(*cfg.fog_color, 1.0),
    )

    report["ppv"] = ppv.build()
    report["cameras"] = _spawn_hero_cameras(eas, existing, cfg.camera_offset)

    graphs = _ensure_pcg_graphs(cfg, force=False)
    report["pcg_graphs"] = graphs
    report["pcg_volumes"] = _spawn_pcg_volumes(
        eas, existing, cfg, graphs, terrain_mesh_path=mesh_path
    )

    if save:
        report["saved"] = _save_current_level(les, level_path)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    level_ok = bool(report.get("level")) and not level_info.get("error")
    created_ok = level_info.get("new_level_ok", True) if level_info.get("created") else True
    # HONEST pass criteria (fixed 2026-07-09): the old check only verified that
    # steps ran, so the 07-09 audit reported passed=true with world_partition
    # false and every volume at ISM 0. Passing now requires the actual targets.
    # ISM counting is deferred to verify() (async generation can't be counted
    # in the same game-thread call). build() passing means structure is right;
    # verify() finalizes `passed` with the real ISM totals.
    report["needs_verify"] = True
    report["passed"] = (
        level_ok
        and created_ok
        and bool(report.get("saved"))
        and bool(graphs)
        and _package_on_disk(level_path)
        and bool(report.get("world_partition"))
    )
    return report


def build_all(*, save: bool = True, recreate_wp: bool = False) -> dict:
    results: dict[str, dict] = {}
    for key in PILLARS:
        import unreal

        unreal.log(f"[WPPillar] building {key}...")
        results[key] = build(key, save=save, recreate_wp=recreate_wp)
        time.sleep(2.0)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pillars": results,
        "passed": all(r.get("passed") for r in results.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            print(f"UnrealEditor-Cmd not found: {UE_CMD}")
            return 1
        script = (PROJECT_ROOT / "Content/Python/setup_wp_pillar_levels.py").as_posix()
        args = dict(_parse_args())
        pillar_arg = []
        if args["pillar"]:
            pillar_arg = ["--pillar", args["pillar"]]
        elif args["all"]:
            pillar_arg = ["--all"]
        if args["recreate_wp"]:
            pillar_arg.append("--recreate-wp")
        script_with_args = script if not pillar_arg else f"{script} {' '.join(pillar_arg)}"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={script_with_args}",
            "-stdout",
            "-unattended",
            "-nosplash",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    args = _parse_args()
    if args["verify"]:
        targets = [args["pillar"]] if args["pillar"] else list(PILLARS)
        results = {k: verify(k) for k in targets}
        print(json.dumps(results, indent=2))
        return 0 if all(r.get("passed") for r in results.values()) else 1
    if args["all"] or not args["pillar"]:
        summary = build_all(recreate_wp=args["recreate_wp"])
        print(json.dumps(summary, indent=2))
        return 0 if summary.get("passed") else 1
    report = build(args["pillar"], recreate_wp=args["recreate_wp"])
    print(json.dumps(report, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
