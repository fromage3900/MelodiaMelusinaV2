#!/usr/bin/env python3
"""Bright Star Catalog subset → star_mask.png for Material Maker image node.

MM has no CSV reader; run this before opening the celestial graph.

  py Tools/MaterialMaker/preprocess_nasa_stars.py
  py Tools/MaterialMaker/preprocess_nasa_stars.py --csv NASA_Refs/star_bright.csv --out NASA_Refs/star_mask.png --size 1024
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow required: pip install pillow") from exc

ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "NASA_Refs" / "star_bright.csv"
DEFAULT_OUT = ROOT / "NASA_Refs" / "star_mask.png"


def ra_dec_to_uv(ra_deg: float, dec_deg: float) -> tuple[float, float]:
    """Equirectangular UV for star catalog coordinates."""
    u = (ra_deg % 360.0) / 360.0
    v = (dec_deg + 90.0) / 180.0
    return u, max(0.0, min(1.0, v))


def load_stars(csv_path: Path) -> list[dict]:
    stars: list[dict] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            stars.append(
                {
                    "name": row.get("name", ""),
                    "ra_deg": float(row["ra_deg"]),
                    "dec_deg": float(row["dec_deg"]),
                    "mag": float(row.get("mag", "3.0")),
                }
            )
    return stars


def render_star_mask(stars: list[dict], size: int) -> Image.Image:
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    for star in stars:
        u, v = ra_dec_to_uv(star["ra_deg"], star["dec_deg"])
        x = int(u * (size - 1))
        y = int((1.0 - v) * (size - 1))
        # Brighter stars (lower mag) → larger points
        mag = star["mag"]
        radius = max(1, int(3.5 - mag * 0.6))
        brightness = int(max(80, min(255, 255 - mag * 25)))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=brightness)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess star CSV to star_mask.png")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--size", type=int, default=1024)
    args = parser.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"Missing CSV: {args.csv}")

    stars = load_stars(args.csv)
    if not stars:
        raise SystemExit(f"No stars in {args.csv}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    render_star_mask(stars, args.size).save(args.out)
    print(f"Wrote {len(stars)} stars -> {args.out} ({args.size}x{args.size})")


if __name__ == "__main__":
    main()
