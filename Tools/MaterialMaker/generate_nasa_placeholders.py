#!/usr/bin/env python3
"""Generate procedural NASA_Refs placeholder maps (public-domain style stand-ins).

Run once after clone if real NASA downloads are not bundled:

  py Tools/MaterialMaker/generate_nasa_placeholders.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent / "NASA_Refs"
SIZE = 1024


def _save(img: Image.Image, name: str) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / name
    img.save(path, quality=92)
    print(f"  {path.name}")


def blue_marble() -> None:
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            u, v = x / SIZE, y / SIZE
            ocean = 0.15 + 0.25 * math.sin(u * 12) * math.cos(v * 8)
            land = max(0.0, math.sin(u * 20 + 1.2) * math.cos(v * 16 - 0.5) * 0.35)
            cloud = 0.15 * max(0, math.sin(u * 40 + v * 30))
            r = int(255 * min(1, ocean * 0.3 + land * 0.55 + cloud + 0.05))
            g = int(255 * min(1, ocean * 0.55 + land * 0.45 + cloud + 0.08))
            b = int(255 * min(1, ocean * 0.85 + land * 0.2 + cloud + 0.12))
            px[x, y] = (r, g, b)
    _save(img.filter(ImageFilter.GaussianBlur(1)), "blue_marble_4k.jpg")


def hubble_nebula() -> None:
    img = Image.new("RGB", (SIZE, SIZE))
    px = img.load()
    rng = random.Random(42)
    for y in range(SIZE):
        for x in range(SIZE):
            u, v = x / SIZE - 0.5, y / SIZE - 0.5
            d = math.sqrt(u * u + v * v)
            r = int(255 * max(0, 0.9 - d * 1.8) ** 1.2 * (0.4 + 0.6 * math.sin(d * 30)))
            g = int(255 * max(0, 0.5 - d) * (0.3 + 0.4 * math.cos(d * 22 + 1)))
            b = int(255 * max(0, 0.7 - d * 1.2) * (0.5 + 0.3 * rng.random()))
            px[x, y] = (min(255, r + 40), min(255, g + 20), min(255, b + 80))
    _save(img.filter(ImageFilter.GaussianBlur(2)), "hubble_carina_4k.jpg")


def elevation_map(name: str, seed: int) -> None:
    img = Image.new("L", (SIZE, SIZE))
    px = img.load()
    rng = random.Random(seed)
    for y in range(SIZE):
        for x in range(SIZE):
            u, v = x / SIZE, y / SIZE
            n = sum(math.sin((u * s + rng.random()) * math.pi * 2) * math.cos((v * s) * math.pi * 2) / s for s in (2, 4, 8, 16))
            val = int(128 + 80 * n)
            px[x, y] = max(0, min(255, val))
    _save(img.filter(ImageFilter.GaussianBlur(1)), name)


def star_csv() -> None:
    path = ROOT / "star_bright.csv"
    ROOT.mkdir(parents=True, exist_ok=True)
    # Subset of well-known bright stars (public catalog coordinates)
    rows = [
        ("Sirius", 101.287, -16.716, -1.46),
        ("Canopus", 95.988, -52.696, -0.74),
        ("Arcturus", 213.915, 19.182, -0.05),
        ("Vega", 279.235, 38.784, 0.03),
        ("Capella", 79.172, 45.998, 0.08),
        ("Rigel", 78.634, -8.202, 0.13),
        ("Procyon", 114.825, 5.225, 0.34),
        ("Betelgeuse", 88.793, 7.407, 0.42),
        ("Altair", 297.695, 8.868, 0.76),
        ("Aldebaran", 68.980, 16.509, 0.85),
        ("Spica", 201.298, -11.161, 0.97),
        ("Antares", 247.352, -26.432, 1.06),
        ("Pollux", 116.329, 28.026, 1.14),
        ("Fomalhaut", 344.413, -29.622, 1.16),
        ("Deneb", 310.358, 45.280, 1.25),
        ("Regulus", 152.093, 11.967, 1.35),
        ("Castor", 113.650, 31.888, 1.58),
        ("Bellatrix", 81.283, 6.350, 1.64),
        ("Elnath", 81.573, 28.607, 1.65),
        ("Miaplacidus", 138.300, -69.717, 1.67),
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = __import__("csv").writer(fh)
        w.writerow(["name", "ra_deg", "dec_deg", "mag"])
        w.writerows(rows)
    print(f"  {path.name}")


def main() -> None:
    print("Generating NASA_Refs placeholders...")
    blue_marble()
    hubble_nebula()
    elevation_map("moon_lro_elevation_2k.png", 7)
    elevation_map("mars_mola_2k.png", 13)
    star_csv()
    print("Done. Run preprocess_nasa_stars.py next.")


if __name__ == "__main__":
    main()
