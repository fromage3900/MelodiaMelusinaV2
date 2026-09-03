"""Build ornamental architecture PCG graphs — dedicated scatter for hero and detail pieces.

This creates standalone graphs for the 15 procedural ornamental meshes:
- PCG_OrnamentalArch (hero/large pieces: rose window, oculus, spiral stair, vault ribs)
- PCG_OrnamentalDetail (secondary pieces: capitals, corbels, moldings, etc.)

Run in-editor:
  py Content/Python/build_pcg_ornamental.py
  py Content/Python/build_pcg_ornamental.py --force
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
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_ornamental_build.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def build_ornamental_hero(*, force: bool = False) -> tuple[str, dict]:
    """Build scatter graph for large ornamental hero pieces."""
    import unreal

    target = std.GRAPH_ORNAMENTAL_ARCH
    folder = target.rsplit("/", 1)[0]
    graph, _ = gb.load_or_create_graph(target, folder, force=force)
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-800, 0)
    out.set_node_position(600, 0)

    # Volume sampler at hero scale (low density for large pieces)
    sampler, s_smp = gb.add_node(graph, "PCGVolumeSamplerSettings", -500, 0)
    s_smp.set_editor_property("voxel_size", unreal.Vector(600, 600, 600))
    s_smp.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", sampler, "Volume")

    # Transform with ornamental scale range
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -100, 0)
    gb.apply_transform(xform_s, scale_min=0.8, scale_max=1.5, jitter=15.0)
    graph.add_edge(sampler, "Out", xform, "In")

    # Spawner for hero pieces
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    if not gb.configure_spawner(spawner_s, "ornamental_hero", std.MI_GREYBOX_ROCK):
        raise RuntimeError("ornamental_hero spawner failed")
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(target, only_if_is_dirty=False)
    return target, {"role": "ornamental_hero", "density": "low", "scale": (0.8, 1.5)}


def build_ornamental_detail(*, force: bool = False) -> tuple[str, dict]:
    """Build scatter graph for detail ornamental pieces."""
    import unreal

    target = std.GRAPH_ORNAMENTAL_DETAIL
    folder = target.rsplit("/", 1)[0]
    graph, _ = gb.load_or_create_graph(target, folder, force=force)
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-800, 0)
    out.set_node_position(600, 0)

    # Volume sampler at higher density for detail layer
    sampler, s_smp = gb.add_node(graph, "PCGVolumeSamplerSettings", -500, 0)
    s_smp.set_editor_property("voxel_size", unreal.Vector(300, 300, 300))
    s_smp.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", sampler, "Volume")

    # Transform with smaller scale range
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -100, 0)
    gb.apply_transform(xform_s, scale_min=0.5, scale_max=1.2, jitter=25.0)
    graph.add_edge(sampler, "Out", xform, "In")

    # Spawner for detail pieces
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    if not gb.configure_spawner(spawner_s, "ornamental_detail", std.MI_GREYBOX_ROCK):
        raise RuntimeError("ornamental_detail spawner failed")
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(target, only_if_is_dirty=False)
    return target, {"role": "ornamental_detail", "density": "medium", "scale": (0.5, 1.2)}


def build_all(*, force: bool = False) -> dict:
    import unreal

    gb.ensure_directories()
    force = force or os.environ.get("BS_PCG_FORCE", "").lower() in ("1", "true", "yes")
    force = force or "--force" in sys.argv or "--rebuild" in sys.argv

    hero_path, hero_meta = build_ornamental_hero(force=force)
    detail_path, detail_meta = build_ornamental_detail(force=force)

    graphs_ok = all(
        unreal.EditorAssetLibrary.does_asset_exist(p)
        for p in (hero_path, detail_path)
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "build_pcg_ornamental.py",
        "passed": graphs_ok,
        "graphs": {
            "hero": {"path": hero_path, **hero_meta},
            "detail": {"path": detail_path, **detail_meta},
        },
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[PCGOrnamental] passed={report['passed']} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal
        report = build_all()
        print(f"PCG_ORNAMENTAL_OK passed={report['passed']}")
        return 0 if report["passed"] else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        os.environ.setdefault("BS_PCG_FORCE", "1")
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/build_pcg_ornamental.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())