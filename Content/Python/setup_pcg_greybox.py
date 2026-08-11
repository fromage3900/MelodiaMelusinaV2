"""Apply greybox PCG presets to any level with a tagged ground plane.

  py Content/Python/setup_pcg_greybox.py
  py Content/Python/setup_pcg_greybox.py --level L_Template --preset minimal
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std
import pcg_validate_helpers as vh

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _set_tag(actor, tag: str) -> None:
    import unreal

    try:
        tags = list(actor.tags)
        if tag not in tags:
            tags.append(tag)
            actor.tags = tags
    except Exception:
        pass


def _ensure_ground_tag(eas, ground_label: str = "Ground") -> bool:
    import unreal

    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == ground_label:
            _set_tag(actor, std.TAG_GROUND)
            return True
        tags = list(getattr(actor, "tags", []) or [])
        if std.TAG_GROUND in tags:
            return True
    return False


def _destroy_prefix(eas, prefix: str) -> None:
    for actor in list(eas.get_all_level_actors()):
        label = actor.get_actor_label()
        if label == prefix or label.startswith(prefix):
            eas.destroy_actor(actor)


def _ensure_ground_plane(eas) -> bool:
    """Spawn tagged Ground plane when the level has no PCG_Ground actor."""
    import unreal

    if _ensure_ground_tag(eas):
        return True
    plane = "/Engine/BasicShapes/Plane.Plane"
    mi_path = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow"
    actor = eas.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, -20), unreal.Rotator(0, 0, 0),
    )
    if not actor:
        return False
    actor.set_actor_label("Ground")
    actor.set_actor_scale3d(unreal.Vector(40, 40, 1))
    sm = actor.static_mesh_component
    sm.set_static_mesh(unreal.load_asset(plane))
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        sm.set_material(0, unreal.load_asset(mi_path))
    _set_tag(actor, std.TAG_GROUND)
    return True


def _spawn_volume(eas, label: str, graph_path: str, seed: int = 1001) -> tuple[object, object]:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(graph_path):
        import setup_pcg_universal as uni
        uni.build_all(force=True)
    graph = unreal.load_asset(graph_path)
    cx, cy, cz = std.PCG_VOLUME_CENTER
    sx, sy, sz = std.PCG_VOLUME_SCALE
    vol = eas.spawn_actor_from_class(
        unreal.PCGVolume,
        unreal.Vector(cx, cy, cz),
        unreal.Rotator(0, 0, 0),
    )
    vol.set_actor_label(label)
    vol.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    comp = vol.get_component_by_class(unreal.PCGComponent)
    gb.assign_pcg_graph(comp, graph)
    gb.configure_pcg_component(comp, seed=seed, activated=True)
    return vol, comp


def _spawn_exclusion_from_scene(eas) -> list[str]:
    import unreal

    cube = "/Engine/BasicShapes/Cube.Cube"
    spawned: set[str] = set()
    existing = {a.get_actor_label() for a in eas.get_all_level_actors() or []}

    def _spawn_guide(suffix: str, loc, scale) -> None:
        guide = f"{std.ACTOR_EXCLUDE_PREFIX}{suffix}"
        if guide in spawned or guide in existing:
            spawned.add(guide)
            return
        box = eas.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(0, 0, 0),
        )
        if not box:
            return
        box.set_actor_label(guide)
        box.set_actor_scale3d(unreal.Vector(*scale))
        _set_tag(box, std.TAG_EXCLUDE)
        comp = box.static_mesh_component
        comp.set_static_mesh(unreal.load_asset(cube))
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_visibility(False, True)
        spawned.add(guide)

    path_seen = pond_seen = False
    for actor in list(eas.get_all_level_actors()):
        label = actor.get_actor_label()
        tags = list(getattr(actor, "tags", []) or [])
        if std.TAG_PATH in tags or label.startswith("PathStone_"):
            if not path_seen:
                loc = actor.get_actor_location()
                _spawn_guide("Path", (loc.x, loc.y, loc.z + 8), (16, 3, 2))
                path_seen = True
        elif std.TAG_POND in tags or "Pond" in label:
            if not pond_seen:
                loc = actor.get_actor_location()
                _spawn_guide("Pond", (loc.x, loc.y, loc.z + 4), (8, 6, 2))
                pond_seen = True

    if "Path" not in spawned:
        _spawn_guide("Path", (-700, -20, 8), (16, 3, 2))
    if "Pond" not in spawned:
        _spawn_guide("Pond", (600, -400, 8), (8, 6, 2))
    return sorted(spawned)


def build_preset_graphs(*, force: bool = False) -> dict:
    """Bake Minimal/Standard preset graphs under PCG/Greybox/."""
    import unreal

    gb.ensure_directories()
    results: dict = {}
    for preset, graph_path in (
        ("minimal", std.GRAPH_GREYBOX_MINIMAL),
        ("standard", std.GRAPH_GREYBOX_STANDARD),
    ):
        cfg = std.PRESETS[preset]
        graph, _ = gb.load_or_create_graph(graph_path, std.DIR_GREYBOX, force=force)
        meta = gb.wire_scatter_chain(
            graph,
            voxel_cm=cfg.get("voxel_cm", std.DEFAULT_VOXEL_CM),
            grass_mi=std.MI_GREYBOX_GRASS,
            use_surface_tag=bool(cfg.get("use_surface_tag")),
            density_mult=cfg.get("density", std.DEFAULT_DENSITY),
            transform_jitter=float(cfg.get("transform_jitter", 0.0)),
            spacing_prune=True,
            apply_exclusion=bool(cfg.get("spawn_exclusion")),
        )
        unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
        results[preset] = {"path": graph_path, **meta}
    return results


def _foliage_graph_for_preset(preset: str) -> str:
    if preset == "minimal":
        return std.GRAPH_GREYBOX_MINIMAL
    if preset == "standard":
        return std.GRAPH_GREYBOX_STANDARD
    cfg = std.PRESETS.get(preset, {})
    return cfg.get("foliage_graph", std.GRAPH_FOLIAGE)


def apply_greybox_pcg(
    level: str,
    preset: str = "standard",
    ground_label: str = "Ground",
    generate: bool = True,
    grass_mi: str | None = None,
) -> dict:
    import unreal
    import setup_pcg_universal as uni

    cfg = std.PRESETS.get(preset, std.PRESETS["standard"])
    level_asset = f"{level}.{level.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
        raise RuntimeError(f"level missing: {level}")

    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    except Exception as exc:
        return {"passed": False, "error": f"LevelEditorSubsystem unavailable: {exc}"}
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    except Exception as exc:
        return {"passed": False, "error": f"EditorActorSubsystem unavailable: {exc}"}
    try:
        les.load_level(level)
    except Exception as exc:
        return {"passed": False, "error": f"load_level failed: {exc}"}

    _destroy_prefix(eas, std.ACTOR_GROUND_COVER)
    _destroy_prefix(eas, std.ACTOR_ROCKS)
    _destroy_prefix(eas, std.ACTOR_EXCLUDE_PREFIX)

    ground_ok = _ensure_ground_plane(eas)
    exclusions: list[str] = []
    if cfg.get("spawn_exclusion"):
        exclusions = _spawn_exclusion_from_scene(eas)

    foliage_meta: dict = {}
    foliage_graph = _foliage_graph_for_preset(preset)
    if preset == "showcase":
        foliage_graph, foliage_meta = uni.build_foliage(
            force=True,
            density=cfg.get("density", std.DEFAULT_DENSITY),
            voxel_cm=cfg.get("voxel_cm", std.DEFAULT_VOXEL_CM),
            grass_mi=grass_mi or std.MI_SAKURA_GRASS,
            use_surface_tag=bool(cfg.get("use_surface_tag")),
            transform_jitter=float(cfg.get("transform_jitter", 0.0)),
            apply_exclusion=bool(cfg.get("spawn_exclusion")),
            graph_path=foliage_graph,
        )
        foliage_meta = {"path": foliage_graph, **foliage_meta}
    else:
        foliage_meta = build_preset_graphs(force=True).get(preset, {})
        foliage_graph = _foliage_graph_for_preset(preset)

    foliage_vol, foliage_comp = _spawn_volume(
        eas, std.ACTOR_GROUND_COVER, foliage_graph, seed=std.SEED_FOLIAGE,
    )
    gb.fit_volume_to_ground(foliage_vol, eas, preset=preset)
    ism_foliage = 0
    gen_ok = False
    if generate:
        try:
            vh.generate_and_wait(foliage_comp, force=True)
            gen_ok = True
            ism_foliage = max(vh.count_ism(foliage_vol), vh.count_world_ism())
        except Exception as exc:
            unreal.log_error(f"[GreyboxPCG] generate failed: {exc}")

    ism_rocks = 0
    if cfg.get("spawn_rocks"):
        rock_vol, rock_comp = _spawn_volume(
            eas, std.ACTOR_ROCKS, std.GRAPH_ROCK, seed=std.SEED_ROCKS,
        )
        gb.fit_volume_to_ground(rock_vol, eas, preset=preset)
        if generate:
            try:
                vh.generate_and_wait(rock_comp, force=True)
                ism_rocks = vh.count_ism(rock_vol)
            except Exception:
                pass

    lo, hi = cfg.get("ism_band", std.ISM_BAND_PORTFOLIO)
    total_ism = ism_foliage + ism_rocks
    ism_pass = vh.within_bounds(ism_foliage, lo, hi) if ism_foliage > 0 else None
    structural_pass = ground_ok and gen_ok if generate else ground_ok
    les.save_current_level()
    return {
        "level": level,
        "preset": preset,
        "ground_tagged": ground_ok,
        "exclusion_guides": exclusions,
        "foliage_graph_meta": foliage_meta,
        "ism_foliage": ism_foliage,
        "ism_rocks": ism_rocks,
        "ism_total": total_ism,
        "ism_band": [lo, hi],
        "generated": gen_ok,
        "structural_pass": structural_pass,
        "ism_pass": ism_pass,
        "passed": structural_pass and (ism_pass if ism_pass is not None else True),
        "graphs": {
            "foliage": foliage_graph,
            "rock": std.GRAPH_ROCK if cfg.get("spawn_rocks") else None,
        },
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_greybox.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    level = std.LEVEL_TEMPLATE
    preset = "standard"
    for i, arg in enumerate(sys.argv):
        if arg == "--level" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            level = name if name.startswith("/Game/") else f"/Game/EnvSandbox/{name}"
        if arg == "--preset" and i + 1 < len(sys.argv):
            preset = sys.argv[i + 1].lower()

    result = apply_greybox_pcg(level, preset=preset, generate="--no-generate" not in sys.argv)
    out = PROJECT_ROOT / "Saved" / "Audit" / "pcg_greybox_apply.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "setup_pcg_greybox.py",
        "ok": result.get("passed", False),
        **result,
    }, indent=2), encoding="utf-8")
    print(f"GREYBOX_PCG preset={preset} passed={result['passed']} ism={result['ism_total']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
