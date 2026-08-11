"""Export scene statistics (triangle count, draw calls) for portfolio.

Run in-editor:
  py Content/Python/stats_exporter.py

Output:
  Saved/Portfolio/Stats/portfolio_stats_manifest.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import portfolio_output_layout as portfolio_fs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "Stats" / "portfolio_stats_manifest.json"


def export_stats() -> dict:
    """Export basic scene statistics."""
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not eas:
        raise RuntimeError("EditorActorSubsystem unavailable — run inside Unreal Editor")

    triangle_count = 0
    draw_calls = 0
    actor_count = 0

    all_actors = eas.get_all_level_actors() or []
    for actor in all_actors:
        try:
            if not actor.is_a(unreal.StaticMeshActor.static_class()):
                continue
        except Exception:
            continue

        actor_count += 1
        comp = actor.static_mesh_component
        if comp:
            mesh = comp.get_static_mesh()
            if mesh:
                try:
                    # Get render data for triangle count
                    render_data = mesh.get_render_data()
                    if render_data:
                        triangle_count += render_data.get_triangle_count()
                except Exception:
                    pass

    # Estimate draw calls (rough approximation)
    draw_calls = actor_count  # Conservative estimate

    report = {
        "triangle_count": triangle_count,
        "draw_calls": draw_calls,
        "actor_count": actor_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return report


def write_stats(*, output_path: Path | None = None) -> Path:
    import unreal

    portfolio_fs.ensure_portfolio_layout()
    portfolio_fs.organize_portfolio_outputs()
    out = output_path or OUTPUT_PATH
    report = export_stats()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[StatsExporter] wrote {out}")
    return out


def main() -> None:
    path = write_stats()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
