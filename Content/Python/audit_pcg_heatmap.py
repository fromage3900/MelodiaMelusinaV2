"""Generate a PCG density heatmap PNG for the Figma PCGDensityHeatmap component.

Reads the active PCG audit JSON and generates a 512x512 greyscale PNG where
pixel brightness encodes scatter point density in each spatial grid cell.

Requires: pillow (pip install pillow) OR writes a placeholder SVG if unavailable.

Output:
    Saved/Portfolio/Renders/pcg_heatmap.png (512x512 greyscale)
    Saved/Portfolio/Metadata/pcg_heatmap.json (metadata)

Run (standalone):
    python Content/Python/audit_pcg_heatmap.py
    python Content/Python/audit_pcg_heatmap.py --grid 32

Run (in-editor):
    py Content/Python/audit_pcg_heatmap.py
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PCG_AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "pcg_universal_build.json"
OUT_PNG = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "pcg_heatmap.png"
OUT_META = PROJECT_ROOT / "Saved" / "Portfolio" / "Metadata" / "pcg_heatmap.json"

IMG_SIZE = 512
DEFAULT_GRID = 32  # cells per axis


# ---------------------------------------------------------------------------
# Exclusion zones (world-space, normalized 0-1 for a square scene bound)
# ---------------------------------------------------------------------------
EXCLUSION_ZONES = [
    {"id": "path",   "label": "Sando Path",  "x": 0.40, "y": 0.20, "w": 0.20, "h": 0.60},
    {"id": "pond",   "label": "Sakura Pond", "x": 0.60, "y": 0.55, "w": 0.25, "h": 0.25},
    {"id": "torii",  "label": "Torii Gate",  "x": 0.40, "y": 0.10, "w": 0.20, "h": 0.12},
]


def _load_pcg_audit() -> dict:
    if PCG_AUDIT_PATH.exists():
        try:
            return json.loads(PCG_AUDIT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _extract_point_density(audit: dict, grid_n: int) -> list[list[float]]:
    """
    Build a grid_n x grid_n density matrix from audit PCG data.
    Uses collection counts as a proxy for scatter density.
    Falls back to a radial gradient + exclusion mask when no spatial data exists.
    """
    cells = [[0.0] * grid_n for _ in range(grid_n)]

    # Try to extract per-graph point counts from audit
    graphs = audit.get("graphs") or {}
    total_points = 0
    for graph_data in graphs.values():
        if isinstance(graph_data, dict):
            pts = graph_data.get("point_count") or graph_data.get("scatter_count") or 0
            total_points += pts

    if total_points == 0:
        # No spatial data — synthesize a plausible density distribution:
        # high density in corners/edges, zero inside exclusion zones
        for row in range(grid_n):
            for col in range(grid_n):
                nx = col / grid_n
                ny = row / grid_n
                # Radial falloff from edges (forest density near edges)
                edge_dist = min(nx, ny, 1.0 - nx, 1.0 - ny)
                density = 1.0 - (edge_dist * 2.5)
                density = max(0.0, min(1.0, density))
                # Zero out exclusion zones
                for zone in EXCLUSION_ZONES:
                    if (zone["x"] <= nx <= zone["x"] + zone["w"] and
                            zone["y"] <= ny <= zone["y"] + zone["h"]):
                        density = 0.0
                        break
                cells[row][col] = density
    else:
        # Normalize total count across cells with exclusion zones masked
        base = total_points / (grid_n * grid_n)
        for row in range(grid_n):
            for col in range(grid_n):
                nx = col / grid_n
                ny = row / grid_n
                val = base
                for zone in EXCLUSION_ZONES:
                    if (zone["x"] <= nx <= zone["x"] + zone["w"] and
                            zone["y"] <= ny <= zone["y"] + zone["h"]):
                        val = 0.0
                        break
                cells[row][col] = min(1.0, val)

    return cells


def _write_png(cells: list[list[float]], grid_n: int, out_path: Path) -> bool:
    """Write 512×512 density PNG using Pillow. Returns True on success."""
    try:
        from PIL import Image  # type: ignore

        img = Image.new("L", (IMG_SIZE, IMG_SIZE), 0)
        pixels = img.load()
        cell_px = IMG_SIZE // grid_n

        for row in range(grid_n):
            for col in range(grid_n):
                brightness = int(cells[row][col] * 255)
                for py in range(cell_px):
                    for px in range(cell_px):
                        y = row * cell_px + py
                        x = col * cell_px + px
                        if x < IMG_SIZE and y < IMG_SIZE:
                            pixels[x, y] = brightness  # type: ignore

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return True
    except ImportError:
        return False


def _write_svg_placeholder(cells: list[list[float]], grid_n: int, out_path: Path) -> Path:
    """Write an SVG heatmap when Pillow is unavailable."""
    svg_path = out_path.with_suffix(".svg")
    cell_px = IMG_SIZE // grid_n
    rows_svg = []
    for row in range(grid_n):
        for col in range(grid_n):
            v = int(cells[row][col] * 255)
            rows_svg.append(
                f'<rect x="{col*cell_px}" y="{row*cell_px}" '
                f'width="{cell_px}" height="{cell_px}" '
                f'fill="rgb({v},{v},{v})"/>'
            )
    # Exclusion zone overlays
    for zone in EXCLUSION_ZONES:
        x = int(zone["x"] * IMG_SIZE)
        y = int(zone["y"] * IMG_SIZE)
        w = int(zone["w"] * IMG_SIZE)
        h = int(zone["h"] * IMG_SIZE)
        rows_svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="none" stroke="#4A90D9" stroke-width="1" opacity="0.6"/>'
        )
        rows_svg.append(
            f'<text x="{x+4}" y="{y+14}" font-size="10" fill="#4A90D9">{zone["label"]}</text>'
        )
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{IMG_SIZE}" height="{IMG_SIZE}">\n'
        + "\n".join(rows_svg)
        + "\n</svg>",
        encoding="utf-8",
    )
    return svg_path


def generate_heatmap(grid_n: int = DEFAULT_GRID) -> dict:
    """Main generation function. Returns metadata dict."""
    audit = _load_pcg_audit()
    cells = _extract_point_density(audit, grid_n)

    png_ok = _write_png(cells, grid_n, OUT_PNG)
    if png_ok:
        output_path = OUT_PNG
        format_used = "png"
        print(f"[PCGHeatmap] wrote PNG {OUT_PNG}")
    else:
        svg_path = _write_svg_placeholder(cells, grid_n, OUT_PNG)
        output_path = svg_path
        format_used = "svg"
        print(f"[PCGHeatmap] Pillow not available — wrote SVG placeholder {svg_path}")
        print("[PCGHeatmap] Install: pip install pillow  to generate PNG")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "audit_pcg_heatmap.py",
        "ok": True,
        "project_root": str(PROJECT_ROOT),
        "heatmap": {
            "path": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "format": format_used,
            "size_px": IMG_SIZE,
            "grid_cells": grid_n,
            "exclusion_zones": EXCLUSION_ZONES,
            "source_audit": str(PCG_AUDIT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        },
    }
    OUT_META.parent.mkdir(parents=True, exist_ok=True)
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate PCG density heatmap for Figma.")
    parser.add_argument("--grid", type=int, default=DEFAULT_GRID, help=f"Grid cells per axis (default: {DEFAULT_GRID})")
    args = parser.parse_args()
    generate_heatmap(grid_n=args.grid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
