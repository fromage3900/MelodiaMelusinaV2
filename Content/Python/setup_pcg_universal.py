"""Build universal PCG graphs under /Game/EnvSandbox/PCG/Universal/.

  python Content/Python/setup_pcg_universal.py
  python Content/Python/setup_pcg_universal.py --force
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_graph_builder as gb
import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_universal_build.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def build_foliage(
    *,
    force: bool = False,
    density: float | None = None,
    voxel_cm: float | None = None,
    grass_mi: str | None = None,
    use_surface_tag: bool = False,
    transform_jitter: float = 0.0,
    apply_exclusion: bool = False,
    graph_path: str | None = None,
) -> tuple[str, dict]:
    target = graph_path or std.GRAPH_FOLIAGE
    folder = target.rsplit("/", 1)[0]
    graph, _ = gb.load_or_create_graph(target, folder, force=force)
    meta = gb.wire_scatter_chain(
        graph,
        voxel_cm=float(voxel_cm if voxel_cm is not None else std.DEFAULT_VOXEL_CM),
        grass_mi=grass_mi or std.MI_GREYBOX_GRASS,
        use_surface_tag=use_surface_tag,
        density_mult=float(density if density is not None else std.DEFAULT_DENSITY),
        transform_jitter=transform_jitter,
        spacing_prune=True,
        apply_exclusion=apply_exclusion,
    )
    import unreal
    unreal.EditorAssetLibrary.save_asset(target, only_if_is_dirty=False)
    return target, meta



def build_style_graphs(*, force: bool = False) -> dict:
    """Build expanded universal/style PCG layers from STYLE_PRESETS."""
    import unreal

    results: dict = {}
    for key, cfg in std.STYLE_PRESETS.items():
        graph_path = cfg["graph"]
        folder = graph_path.rsplit("/", 1)[0]
        graph, _ = gb.load_or_create_graph(graph_path, folder, force=force)
        scale = cfg.get("scale", (std.GRASS_SCALE_MIN, std.GRASS_SCALE_MAX))
        meta = gb.wire_scatter_chain(
            graph,
            voxel_cm=float(cfg.get("voxel_cm", std.DEFAULT_VOXEL_CM)),
            grass_mi=cfg.get("material") or std.MI_GREYBOX_GRASS,
            use_surface_tag=bool(cfg.get("use_surface_tag", False)),
            density_mult=float(cfg.get("density", std.DEFAULT_DENSITY)),
            transform_jitter=float(cfg.get("transform_jitter", 0.0)),
            spacing_prune=True,
            apply_exclusion=bool(cfg.get("spawn_exclusion", False)),
            role=cfg.get("role", "grass"),
            scale_min=float(scale[0]),
            scale_max=float(scale[1]),
        )
        unreal.EditorAssetLibrary.save_asset(graph_path, only_if_is_dirty=False)
        results[key] = {
            "path": graph_path,
            "label": cfg.get("label", key),
            "seed": cfg.get("seed"),
            "notes": cfg.get("notes"),
            **meta,
        }
    return results

def build_rock(*, force: bool = False) -> tuple[str, dict]:
    import unreal

    graph, _ = gb.load_or_create_graph(std.GRAPH_ROCK, std.DIR_UNIVERSAL, force=force)
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-800, 0)
    out.set_node_position(800, 0)

    sampler, sampler_settings = gb.add_node(graph, "PCGVolumeSamplerSettings", -500, 0)
    voxel = float(std.DEFAULT_VOXEL_CM) * 1.4
    sampler_settings.set_editor_property("voxel_size", unreal.Vector(voxel, voxel, voxel))
    sampler_settings.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", sampler, "Volume")

    xform, xform_settings = gb.add_node(graph, "PCGTransformPointsSettings", -100, 0)
    gb.apply_transform(xform_settings, scale_min=std.ROCK_SCALE_MIN, scale_max=std.ROCK_SCALE_MAX, jitter=15.0)
    graph.add_edge(sampler, "Out", xform, "In")

    spawner, spawner_settings = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    if not gb.configure_spawner(spawner_settings, "rock", std.MI_GREYBOX_ROCK):
        raise RuntimeError("rock spawner failed")
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(std.GRAPH_ROCK, only_if_is_dirty=False)
    return std.GRAPH_ROCK, {"role": "rock", "voxel_cm": voxel}


def build_exclusion_subgraph(*, force: bool = False) -> tuple[str, dict]:
    """Exclusion subgraph â€” tag filter passthrough documenting PCG_Exclude intent."""
    import unreal

    graph, _ = gb.load_or_create_graph(std.GRAPH_EXCLUSION, std.DIR_SUBGRAPHS, force=force)
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-400, 0)
    out.set_node_position(400, 0)

    tag_cls = getattr(unreal, "PCGFilterByTagSettings", None)
    wired = False
    if tag_cls:
        filt, filt_s = gb.add_node(graph, "PCGFilterByTagSettings", 0, 0)
        try:
            filt_s.set_editor_property("filter_mode", unreal.PCGFilterByTagFilterMode.Exclude)
            filt_s.set_editor_property("tag", std.TAG_EXCLUDE)
        except Exception:
            graph.add_edge(inp, "In", out, "Out")
        else:
            graph.add_edge(inp, "In", filt, "In")
            graph.add_edge(filt, "Out", out, "Out")
            wired = True
    else:
        graph.add_edge(inp, "In", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(std.GRAPH_EXCLUSION, only_if_is_dirty=False)
    pcgex_cls = gb.find_pcgex_class("falloff") or gb.find_pcgex_class("distance")
    return std.GRAPH_EXCLUSION, {
        "passthrough": not wired,
        "tag_filter": wired,
        "pcgex_candidate": pcgex_cls,
    }


def build_wall_detail(*, force: bool = False) -> tuple[str, dict]:
    """Phase 3 â€” spline wall scatter stub."""
    import unreal

    graph, _ = gb.load_or_create_graph(std.GRAPH_WALL, std.DIR_UNIVERSAL, force=force)
    inp = graph.get_input_node()
    out = graph.get_output_node()
    graph.add_edge(inp, "In", out, "Out")
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(std.GRAPH_WALL, only_if_is_dirty=False)
    return std.GRAPH_WALL, {"phase": 3, "note": "spline scatter deferred"}


MELODIA_GROUND_COVER = "/Game/_PROJECT/PCG/Collections/PCGCol_Environment_GroundCover"
MELODIA_ROCKS = "/Game/_PROJECT/PCG/Collections/PCGCol_Environment_Rocks"


def build_collections(*, force: bool = False) -> dict:
    portfolio = gb.duplicate_scatter_kit(
        std.SMC_PORTFOLIO, MELODIA_GROUND_COVER, force=force,
    )
    greybox = gb.duplicate_scatter_kit(
        std.SMC_GREYBOX, MELODIA_ROCKS, force=force,
    )
    sakura = gb.duplicate_scatter_kit(
        std.SMC_SAKURA, MELODIA_GROUND_COVER, force=force,
    )
    return {"portfolio": portfolio, "greybox": greybox, "sakura": sakura}


def build_all(*, force: bool = False) -> dict:
    import unreal

    gb.ensure_directories()
    force = force or os.environ.get("BS_PCG_FORCE", "").lower() in ("1", "true", "yes")
    force = force or "--force" in sys.argv or "--rebuild" in sys.argv

    foliage_path, foliage_meta = build_foliage(force=force)
    rock_path, rock_meta = build_rock(force=force)
    excl_path, excl_meta = build_exclusion_subgraph(force=force)
    wall_path, wall_meta = build_wall_detail(force=force)
    style_graphs = build_style_graphs(force=force)
    collections = build_collections(force=force)

    import setup_pcg_greybox as grey
    greybox_presets = grey.build_preset_graphs(force=force)

    graphs_ok = all(
        unreal.EditorAssetLibrary.does_asset_exist(p)
        for p in (
            foliage_path, rock_path, excl_path, wall_path,
            std.GRAPH_GREYBOX_MINIMAL, std.GRAPH_GREYBOX_STANDARD,
            *(entry["path"] for entry in style_graphs.values()),
        )
    )
    collections_ok = all(
        collections[k].get("exists") or collections[k].get("method") == "manifest_only"
        for k in ("portfolio", "greybox", "sakura")
        if isinstance(collections.get(k), dict)
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "setup_pcg_universal.py",
        "graphs_ok": graphs_ok,
        "collections_ok": collections_ok,
        "passed": graphs_ok,
        "graphs": {
            "foliage": {"path": foliage_path, **foliage_meta},
            "rock": {"path": rock_path, **rock_meta},
            "exclusion": {"path": excl_path, **excl_meta},
            "wall": {"path": wall_path, **wall_meta},
        },
        "style_graphs": style_graphs,
        "collections": collections,
        "greybox_presets": greybox_presets,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[PCGUniversal] passed={report['passed']} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = build_all()
        print(f"PCG_UNIVERSAL_OK passed={report['passed']}")
        return 0 if report["passed"] else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        os.environ.setdefault("BS_PCG_FORCE", "1")
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_universal.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())



