"""Full UE render capture orchestrator for portfolio artifacts.

This script runs capture steps sequentially (best-effort) and writes:
  Saved/Portfolio/Renders/renders_manifest.json

It does NOT modify exporter logic; it calls existing exporters and Monolith MCP
actions where available.

Run in-editor:
  py Content/Python/capture_portfolio_renders.py

Headless Cmd (RHI, optional Monolith via env):
  python Content/Python/generate_portfolio.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import portfolio_output_layout as portfolio_fs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDERS_ROOT = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "capture_portfolio_renders.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(message: str) -> None:
    line = f"[CapturePortfolioRenders] {message}"
    try:
        import unreal

        unreal.log(line)
    except ImportError:
        print(line)


def _try_monolith_ping() -> bool:
    try:
        import monolith_mcp_client as mono

        return bool(mono.ping(timeout=2.5))
    except Exception:
        return False


def _capture_material_grid() -> dict:
    """Capture a showcase grid from curated MI_Show_* instances via Monolith."""
    import starter_instances

    if not _try_monolith_ping():
        return {"ok": False, "skipped": True, "reason": "monolith_unavailable"}

    import monolith_mcp_client as mono

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = RENDERS_ROOT / "Materials" / f"grid_showcase_{ts}_2048x2048.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Monolith expects asset paths (materials or material instances) as strings.
    material_paths = [
        f"{starter_instances.SHOWCASE_DIR}/{entry['name']}.{entry['name']}"
        for entry in starter_instances.STARTER_INSTANCES
        if isinstance(entry, dict) and entry.get("name")
    ]

    try:
        result = mono.editor_query(
            "capture_material_grid",
            material_paths=material_paths,
            output_path=str(out),
            resolution=2048,
            preview_mesh="sphere",
        )
        return {"ok": True, "output_path": str(out), "result": result, "count": len(material_paths)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _capture_breakdown_overlays() -> dict:
    """Capture wireframe/uv_density passes for selected assets via Monolith.

    v1 behavior: if Monolith unavailable, skip.
    v1 selection: uses actors in scene_metadata.json filtered by 'GB_' label prefix.
    """
    if not _try_monolith_ping():
        return {"ok": False, "skipped": True, "reason": "monolith_unavailable"}

    meta_path = portfolio_fs.SCENE_METADATA_PATH
    if not meta_path.is_file():
        return {"ok": False, "skipped": True, "reason": "scene_metadata_missing"}

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "skipped": True, "reason": "scene_metadata_unreadable"}

    actors = meta.get("static_mesh_actors")
    if not isinstance(actors, list) or not actors:
        return {"ok": False, "skipped": True, "reason": "no_static_mesh_actors"}

    # Select a small set to avoid long capture runs.
    selected: list[str] = []
    for entry in actors:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "")
        mesh = entry.get("mesh")
        if not mesh:
            continue
        if label.startswith("GB_") or "GREYBOX" in label.upper():
            selected.append(str(mesh))
        if len(selected) >= 6:
            break

    if not selected:
        return {"ok": False, "skipped": True, "reason": "no_greybox_meshes_found"}

    import monolith_mcp_client as mono

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    outputs: list[dict] = []
    for asset_path in selected:
        stem = asset_path.rsplit("/", 1)[-1]
        for mode in ("wireframe", "uv_density"):
            out = RENDERS_ROOT / "Breakdown" / f"breakdown_{stem}_{mode}_{ts}_1024x1024.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                result = mono.editor_query(
                    "capture_with_overlay",
                    asset_path=asset_path,
                    mode=mode,
                    output_path=str(out),
                    resolution=1024,
                )
                outputs.append(
                    {
                        "ok": True,
                        "asset_path": asset_path,
                        "mode": mode,
                        "output_path": str(out),
                        "result": result,
                    }
                )
            except Exception as exc:
                outputs.append(
                    {
                        "ok": False,
                        "asset_path": asset_path,
                        "mode": mode,
                        "error": str(exc),
                    }
                )

    return {"ok": True, "count": len(outputs), "outputs": outputs}


def _capture_trim_sheets() -> dict:
    """Trim sheet capture placeholder for v1.

    We reserve the folder and manifest hooks. Actual trim capture may require
    dedicated preview meshes and vertex-color masking; this step is a no-op if
    Monolith isn't available.
    """
    if not _try_monolith_ping():
        return {"ok": False, "skipped": True, "reason": "monolith_unavailable"}
    return {"ok": True, "skipped": True, "reason": "trim_capture_not_implemented_v1"}


def run_all_captures() -> dict:
    """Sequential, best-effort capture run. Always writes renders_manifest.json."""
    import compile_render_plates as compiler
    import render_exporter as viewport

    portfolio_fs.ensure_portfolio_layout()
    portfolio_fs.organize_portfolio_outputs()

    steps: list[dict] = []

    def step(name: str, fn) -> dict:
        _log(f"START {name}")
        try:
            result = fn()
            steps.append({"step": name, "ok": True, "result": result})
            _log(f"OK {name}")
            return result if isinstance(result, dict) else {"result": result}
        except Exception as exc:
            steps.append({"step": name, "ok": False, "error": str(exc)})
            _log(f"FAIL {name}: {exc}")
            return {"ok": False, "error": str(exc)}

    export_result = step("render_exporter", viewport.export_renders)
    step("monolith_material_grid", _capture_material_grid)
    step("monolith_breakdown_overlays", _capture_breakdown_overlays)
    step("monolith_trim_sheets", _capture_trim_sheets)

    # Always (re)compile the manifest from disk + latest export_result.
    manifest = compiler.compile_renders_manifest(export_result=export_result, scan_disk=True)
    out_path = compiler.write_renders_manifest(manifest)
    portfolio_fs.organize_portfolio_outputs()

    report = {
        "generated_at": _now_iso(),
        "generated_by": "capture_portfolio_renders.py",
        "ok": True,
        "project_root": PROJECT_ROOT.as_posix(),
        "renders_manifest": str(out_path),
        "steps": steps,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(f"complete -> {out_path}")
    return report


def main() -> int:
    # Cmd can invoke Python before everything is fully ready.
    time.sleep(10)
    run_all_captures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

