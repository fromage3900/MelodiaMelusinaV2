"""Audit the staged scale-world builder evidence without opening Unreal."""
from __future__ import annotations

import json
from pathlib import Path

from pcg_scale_world_pipeline import HERO_GRAPH_PATHS, WP_CELL_SIZE_CM, validate_grid
from pcg_visual_chunk_builder import validate_visual_world_plan


ROOT = Path(__file__).resolve().parents[2]
GRID_REPORT = ROOT / "Saved" / "Audit" / "pcg_scale_world_chunk_grid.json"
BUILD_REPORT = ROOT / "Saved" / "Audit" / "pcg_scale_world_build.json"
WORLD_PLAN_REPORT = ROOT / "Saved" / "Audit" / "pcg_visual_world_plan.json"
EXPECTED_STAGES = ("pcg", "hlod", "nav", "minimap")


def _read(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "present": False}
    try:
        return {"path": str(path), "present": True, "data": json.loads(path.read_text(encoding="utf-8"))}
    except Exception as exc:
        return {"path": str(path), "present": True, "error": str(exc)}


def audit() -> dict:
    grid_file = _read(GRID_REPORT)
    build_file = _read(BUILD_REPORT)
    plan_file = _read(WORLD_PLAN_REPORT)
    grid = grid_file.get("data", {})
    build = build_file.get("data", {})
    plan = plan_file.get("data", {})
    chunks = grid.get("chunks", []) if isinstance(grid, dict) else []
    stage_rows = build.get("stages", []) if isinstance(build, dict) else []
    by_stage = {row.get("name"): row for row in stage_rows if isinstance(row, dict)}

    chunk_errors = []
    if chunks:
        # Rehydrate enough of the serialized manifests for the canonical
        # validator while preserving the actual JSON as the evidence source.
        from pcg_scale_world_pipeline import ChunkManifest

        manifests = []
        for chunk in chunks:
            manifests.append(
                ChunkManifest(
                    world_seed=int(chunk["world_seed"]),
                    chunk_x=int(chunk["chunk_x"]),
                    chunk_y=int(chunk["chunk_y"]),
                    generator_version=str(chunk["generator_version"]),
                    chunk_size_cm=int(chunk["chunk_size_cm"]),
                    biome_id=str(chunk["biome_id"]),
                    pcg_graph_paths=tuple(chunk["pcg_graph_paths"]),
                    data_layer_assignments=tuple(chunk["data_layer_assignments"]),
                    hlod_layer_assignments=tuple(chunk["hlod_layer_assignments"]),
                    hero_slot_assignments=tuple(chunk["hero_slot_assignments"]),
                    border_signatures=tuple(sorted(chunk["border_signatures"].items())),
                    persistence_revision=int(chunk["persistence_revision"]),
                    generation_quality=int(chunk["generation_quality"]),
                    stable_seed=int(chunk["stable_seed"]),
                    world_origin_cm=tuple(chunk.get("world_origin_cm", (0, 0, 0))),
                    biome_band=str(chunk.get("biome_band", "stone_court")),
                    curve_seed=int(chunk.get("curve_seed", 0)),
                    walkable_corridor_cm=int(chunk.get("walkable_corridor_cm", 2400)),
                    seam_buffer_cm=int(chunk.get("seam_buffer_cm", 900)),
                    border_anchor_layout=tuple(
                        (side, tuple(sorted(values.items())))
                        for side, values in sorted(chunk.get("border_anchor_layout", {}).items())
                    ),
                )
            )
        chunk_errors = validate_grid(manifests)

    world_plan_errors = validate_visual_world_plan(plan) if plan_file.get("present") and isinstance(plan, dict) else ["world plan is missing or invalid"]
    plan_specs = plan.get("hero_volume_specs", []) if isinstance(plan, dict) else []
    plan_graphs = {spec.get("graph") for spec in plan_specs if isinstance(spec, dict)}

    stage_ok = all(
        name in by_stage
        and int(by_stage[name].get("return_code", 1)) == 0
        and Path(by_stage[name].get("log", "")).exists()
        for name in EXPECTED_STAGES
    )
    graph_contract = all(
        set(HERO_GRAPH_PATHS).issubset(set(chunk.get("pcg_graph_paths", [])))
        for chunk in chunks
    ) if chunks else False
    report = {
        "grid_report": grid_file,
        "build_report": build_file,
        "checks": {
            "grid_present": bool(grid_file.get("present")),
            "grid_ok": bool(grid.get("ok")) and not chunk_errors,
            "nine_chunks": len(chunks) == 9,
            "canonical_cell_size": all(int(c.get("chunk_size_cm", 0)) == WP_CELL_SIZE_CM for c in chunks),
            "hero_graphs_in_every_chunk": graph_contract,
            "world_plan_present": bool(plan_file.get("present")),
            "world_plan_ok": bool(plan.get("ok")) and not world_plan_errors,
            "reusable_graph_bindings": set(HERO_GRAPH_PATHS).issubset(plan_graphs),
            "shared_curve_seams": not any("curve anchor" in error for error in chunk_errors),
            "stage_report_present": bool(build_file.get("present")),
            "stage_report_is_execution": bool(build.get("stages")) and not bool(build.get("dry_run")),
            "pcg_hlod_nav_minimap_stages_ok": stage_ok,
            "production_maps_untouched": build.get("production_maps_touched") is False,
        },
        "chunk_errors": chunk_errors,
        "world_plan_errors": world_plan_errors,
        "stages": {name: by_stage.get(name) for name in EXPECTED_STAGES},
    }
    report["ok"] = all(report["checks"].values())
    return report


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)
