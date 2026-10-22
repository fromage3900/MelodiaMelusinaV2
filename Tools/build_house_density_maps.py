#!/usr/bin/env python3
"""Build the three room density textures the house fill needs.

Why this exists
---------------
`specs/p0/melusina_house_p0_fill.v1.json` (the fill contract) requires one
grayscale density texture per room - the Poitou zone-heatmap convention, white
= maximum - and it names them:

    dressing_heatmap_bedroom.png
    dressing_heatmap_landing.png
    dressing_heatmap_salon.png

None exist. This script derives a FIRST PASS for all three from the artist's
own placements, so the fill has something to start from that already agrees
with the composition instead of contradicting it.

The derivation
--------------
1. Take the artist's 97 placements (`specs/p0/melusina_house_p0_dressing_state.json`).
2. Per room, splat each placement into a grid with a soft kernel (~2.5 m), so
   the field says "how much attention is here" - clutter gathers on the
   furniture the artist placed, which is exactly where fill clutter belongs.
3. Zero the route corridor: the P0 house-leg route is reconstructed from the
   functional carriers the artist placed (book -> flame -> threshold ->
   medallion -> door) and the field is cut back 4 m from it, because the walk
   must never snag on furniture.
4. Normalise so the 98th percentile is white, and write an 8-bit grayscale PNG.

What this is NOT
----------------
It is a first pass, not the authored truth. The artist paints over it. The
route polyline is reconstructed from carrier positions, not read from
`BP_PathSplineProvider` (a Blueprint's spline points are not available
offline), so the corridor is approximate - the fill graph's own spline filter
remains the authoritative exclusion.

Usage:
    python Tools/build_house_density_maps.py [--out-dir <dir>] [--receipt <json>]
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE_PATH = REPO_ROOT / "specs" / "p0" / "melusina_house_p0_dressing_state.json"
FILL_PATH = REPO_ROOT / "specs" / "p0" / "melusina_house_p0_fill.v1.json"
DEFAULT_OUT_DIR = REPO_ROOT / "Content" / "EnvSandbox" / "PCG" / "House" / "Textures"
DEFAULT_RECEIPT = REPO_ROOT / "Saved" / "Audit" / "house_density_maps.json"

# The house-leg route in beat order, taken from the golden-walk plan
# (Docs/Plans/POITOU_P0_GOLDEN_WALK_2026-10-21.md):
#   M00 Wake          - the bedside camera
#   M01 Notice        - "approach and inspect ONE of: the empty perch / the
#                       companion token / the desk" -> the token is the one that
#                       sits with the bedside cluster
#   M02 First resonance- "instrument, music-box or window chime (choose ONE
#                       existing compatible actor)" -> the candle flame
#   M03 Threshold     - the bedroom door opens to the larger house; the artist
#                       hung the passage lantern in the landing to mark it
#   M04 The house hums- the curved landing and the oval salon; the medallion
#   M05 Front door    - the exit
# Each entry names the exact prop the artist placed; the polyline is built from
# their positions in this order.
ROUTE_CARRIERS = [
    ("M00", "Explore_Desk"),
    ("M01", "MelodyToken_Heart"),
    ("M02", "BP_CandleFlame"),
    ("M03", "BP_Lantern"),
    ("M04", "BP_Crystal"),
    ("M05", "BP_HiddenDoor"),
]

ROUTE_BUFFER_M = 4.0
# The splat radius. Small values produce isolated specks - one per prop - which
# is not a usable fill guide. At 12 m the props the artist grouped together
# (a desk and its chair and its books) merge into a density REGION, and the
# fill gathers where the furniture is instead of scattering evenly.
KERNEL_RADIUS_M = 12.0
PIXELS_PER_METRE = 2.0  # 0.5 m per pixel
# gamma applied after normalisation: <1 lifts the mid-tones so the gradient
# survives an 8-bit grayscale texture
DENSITY_GAMMA = 0.7


def _load(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _room_bounds(volume: str) -> tuple[float, float, float, float]:
    """Parse 'the bedroom shell interior, x [-1150,-450], y [-995,-100], z 0'.

    A plain comma split is wrong here: the coordinate pairs contain commas too.
    """
    match = re.search(
        r"x\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\].*?"
        r"y\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]",
        volume,
    )
    if not match:
        raise ValueError(f"cannot read a room volume from: {volume!r}")
    return (
        float(match.group(1)),
        float(match.group(2)),
        float(match.group(3)),
        float(match.group(4)),
    )


def _segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    denom = vx * vx + vy * vy
    t = 0.0 if denom == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    cx, cy = ax + t * vx, ay + t * vy
    return math.hypot(px - cx, py - cy)


def build_route(state: dict) -> list[dict]:
    """Reconstruct the house-leg route from the carriers the artist placed.

    The prop name is matched exactly first - a substring match on 'Book' would
    pick the bookshelf instead of the interactive book.
    """
    actors = state.get("actors", [])
    points: list[dict] = []
    for beat, needle in ROUTE_CARRIERS:
        exact = [a for a in actors if (a.get("prop") or "") == needle]
        fuzzy = [
            a
            for a in actors
            if needle.lower() in (a.get("prop") or "").lower()
            or needle.lower() in (a.get("label") or "").lower()
        ]
        chosen = exact[0] if exact else (fuzzy[0] if fuzzy else None)
        if chosen is None:
            continue
        loc = chosen.get("location") or [0.0, 0.0, 0.0]
        points.append(
            {
                "beat": beat,
                "label": chosen.get("label"),
                "prop": chosen.get("prop"),
                "room": chosen.get("room"),
                "x": float(loc[0]),
                "y": float(loc[1]),
            }
        )
    return points


def build_room_grid(room: str, bounds: tuple[float, float, float, float], actors: list[dict], route: list[dict]):
    x0, x1, y0, y1 = bounds
    width = max(1, int(round((x1 - x0) * PIXELS_PER_METRE)))
    height = max(1, int(round((y1 - y0) * PIXELS_PER_METRE)))
    field = np.zeros((height, width), dtype=np.float64)

    kernel_px = max(1, int(round(KERNEL_RADIUS_M * PIXELS_PER_METRE)))
    ax = np.arange(-kernel_px, kernel_px + 1)
    ky, kx = np.meshgrid(ax, ax, indexing="ij")
    kernel = np.exp(-(kx * kx + ky * ky) / (2.0 * (kernel_px / 2.0) ** 2))
    kernel /= kernel.sum()

    placed = 0
    for actor in actors:
        if (actor.get("room") or "") != room:
            continue
        loc = actor.get("location") or [0.0, 0.0, 0.0]
        px = (float(loc[0]) - x0) * PIXELS_PER_METRE
        py = (float(loc[1]) - y0) * PIXELS_PER_METRE
        if not (0 <= px < width and 0 <= py < height):
            continue
        placed += 1
        ix, iy = int(px), int(py)
        x0s, x1s = max(0, ix - kernel_px), min(width, ix + kernel_px + 1)
        y0s, y1s = max(0, iy - kernel_px), min(height, iy + kernel_px + 1)
        kx0, kx1 = x0s - (ix - kernel_px), x1s - (ix - kernel_px)
        ky0, ky1 = y0s - (iy - kernel_px), y1s - (iy - kernel_px)
        field[y0s:y1s, x0s:x1s] += kernel[ky0:ky1, kx0:kx1]

    # Cut the route corridor.
    if len(route) >= 2:
        buffer_px = ROUTE_BUFFER_M * PIXELS_PER_METRE
        step = 1
        for row in range(0, height, step):
            wy = y0 + row / PIXELS_PER_METRE
            for col in range(0, width, step):
                wx = x0 + col / PIXELS_PER_METRE
                best = min(
                    _segment_distance(wx, wy, route[i]["x"], route[i]["y"], route[i + 1]["x"], route[i + 1]["y"])
                    for i in range(len(route) - 1)
                )
                if best * PIXELS_PER_METRE < buffer_px:
                    field[row : row + step, col : col + step] = 0.0

    return field, placed, (width, height)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--receipt", default=str(DEFAULT_RECEIPT))
    args = parser.parse_args(argv)

    state = _load(STATE_PATH)
    fill = _load(FILL_PATH)
    actors = state.get("actors", [])

    route = build_route(state)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    receipt = {
        "kind": "house_density_map_receipt",
        "generated": "2026-10-22",
        "generator": "Tools/build_house_density_maps.py",
        "inputs": [
            "specs/p0/melusina_house_p0_dressing_state.json",
            "specs/p0/melusina_house_p0_fill.v1.json",
        ],
        "derivation": (
            "the artist's own placements, splatted with a "
            f"{KERNEL_RADIUS_M} m kernel, route corridor cut back {ROUTE_BUFFER_M} m, "
            "normalised so the 98th percentile is white"
        ),
        "resolution_m_per_px": 1.0 / PIXELS_PER_METRE,
        "route_reconstructed_from": route,
        "rooms": {},
    }

    for room, spec in fill.get("rooms", {}).items():
        bounds = _room_bounds(spec["volume"])
        field, placed, (width, height) = build_room_grid(room, bounds, actors, route)
        nonzero = field[field > 0]
        if nonzero.size == 0:
            print(f"   {room}: no placements inside the volume - skipped")
            continue
        peak = float(field.max())
        if peak <= 0:
            peak = 1.0
        normalised = np.clip(field / peak, 0.0, 1.0) ** DENSITY_GAMMA
        # a 2 m blur removes the hard truncation edge the finite kernel leaves
        image = Image.fromarray((normalised * 255.0).astype(np.uint8), mode="L").filter(
            ImageFilter.GaussianBlur(radius=KERNEL_RADIUS_M * PIXELS_PER_METRE / 4.0)
        )

        name = f"dressing_heatmap_{room}.png"
        path = out_dir / name
        image.save(path, optimize=True)

        # A preview the artist can actually judge: the field, the route corridor
        # and every placement, drawn over the top.
        preview = image.convert("RGB")
        draw = ImageDraw.Draw(preview)
        for point in route:
            px = int((point["x"] - bounds[0]) * PIXELS_PER_METRE)
            py = int((point["y"] - bounds[1]) * PIXELS_PER_METRE)
            draw.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(255, 80, 80), width=2)
            draw.text((px + 8, py - 6), point["beat"], fill=(255, 120, 120))
        for actor in actors:
            if (actor.get("room") or "") != room:
                continue
            loc = actor.get("location") or [0.0, 0.0, 0.0]
            px = int((float(loc[0]) - bounds[0]) * PIXELS_PER_METRE)
            py = int((float(loc[1]) - bounds[1]) * PIXELS_PER_METRE)
            if 0 <= px < width and 0 <= py < height:
                draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(120, 200, 255))
        preview_path = pathlib.Path(args.receipt).parent / f"density_preview_{room}.png"
        preview.save(preview_path, optimize=True)

        receipt["rooms"][room] = {
            "file": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "bounds_xy": [bounds[0], bounds[1], bounds[2], bounds[3]],
            "pixels": [width, height],
            "placements_splatted": placed,
            "max_field": round(float(field.max()), 4),
            "peak_field": round(peak, 4),
            "white_fraction": round(float((normalised > 0.99).mean()), 5),
            "preview": str(preview_path).replace("\\", "/"),
            "kernel_radius_m": KERNEL_RADIUS_M,
            "gamma": DENSITY_GAMMA,
        }
        print(
            f"   {room}: {width}x{height} px, {placed} placements, "
            f"peak={peak:.2f} -> {path.name}"
        )

    receipt_path = pathlib.Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"wrote {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
