#!/usr/bin/env python
"""Seasonal animated Shorewake variant flipbooks (2026-09-02).

Animation variants to close out the session: for each season, a seamless
8-frame animated flipbook of the season's garment fabric (iridescence/sheen/
normal crawl, no popping normals — same cadence as shorewake_animated_flipbook.py),
so each season can shimmer on loop and drive the dress's morph targets.

Per season, per frame (8), 6 maps: BaseColor/Normal/Iridescence/Sheen/Roughness/
Height. Structure is season-invariant; only palette + phase animate. Texture-only,
no audio reader. Deterministic SEED 20260902.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_seasonal_flipbook.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402
import shorewake_seasonal_variants as seas  # noqa: E402  (SEASONS palette reuse)

OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "garment_refresh" / "seasons" / "animated"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 1024
FRAMES = 8


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def satin_struct(rng):
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    wp = 7.0; wf = 7.0
    xb = x + np.sin((y * 0.00005) * 12) * 1.8
    offset = (y // wf) * 3
    warp = ((xb - offset * 2.1) % wp) < 5
    weft = ~warp
    over = warp * 0.96 + weft * 0.25
    fn = rng.normal(size=(SIZE, SIZE)) * 0.014
    return smoothstep(0.2, 0.85, np.clip(over + fn, 0, 1))


def season_frame(season, frame_i, h_struct):
    pal = seas.SEASONS[season]
    phase = (frame_i / FRAMES) * math.pi * 2.0
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    wash = np.sin(x * 0.002 + y * 0.0015 + phase * 0.65) * 0.03 \
        + np.cos(y * 0.003 - x * 0.001 + phase * 0.45) * 0.025
    h = np.clip(h_struct + 0.4 * wash, 0, 1)

    # normal — crawl, not pop
    dy, dx = np.gradient(h)
    dx *= 14.0; dy *= 14.0
    jx = np.sin(x * 0.07 + phase * 2.1 + y * 0.03) * 0.06
    jy = np.cos(y * 0.07 - phase * 1.7 + x * 0.02) * 0.06
    nx, ny, nz = -dx - jx, -dy - jy, np.ones_like(dx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([(nx / ln * 0.5 + 0.5), (ny / ln * 0.5 + 0.5),
                       (nz / ln * 0.5 + 0.5)], -1).astype(np.float32)

    # albedo — season palette + drifting wash
    base = np.array(pal["base"], float) / 255.0
    accent = np.array(pal["accent"], float) / 255.0
    drift = np.array([
        0.015 * math.sin(phase * 1.0),
        0.012 * math.sin(phase * 1.3 + 1.1),
        0.015 * math.cos(phase * 0.9 + 0.4),
    ])
    accent_f = np.clip(accent + drift, 0, 1)
    s1 = 0.035 * np.sin(x * 0.018 + y * 0.012 + phase * 1.2)[..., None]
    s2 = 0.025 * np.sin(x * 0.009 - y * 0.022 - phase * 0.9)[..., None]
    s3 = 0.018 * np.sin((x + y) * 0.006 + phase * 0.75)[..., None]
    albedo = np.clip(base[None, None] + s1 + s2 + s3, 0, 1)
    albedo += np.random.default_rng(SEED + frame_i).normal(size=(SIZE, SIZE, 3)) * 0.008
    albedo = np.clip(albedo, 0, 1)

    # iridescence — season nacre + crawl
    iri = np.clip((h - 0.5) * 1.8, 0, 1) * (0.70 + 0.30 * np.sin(x * 0.02 + phase * 1.4 + y * 0.001))
    band = 0.12 * np.sin(x * 0.030 - y * 0.018 + phase * 1.2) + 0.08 * np.sin((x + y) * 0.012 + phase * 0.6)
    iri = np.clip(iri + band + 0.06 * math.sin(phase * 0.9), 0, 1)

    # sheen — season strength breathe
    sh0 = pal["sheen"]
    sheen = np.clip((1.0 - np.abs(h - 0.72) * 3.5) * 0.4 + 0.35 + 0.10 * math.sin(phase * 1.1), 0, 1)

    # roughness — season base + wash crawl
    rough = np.where(h > 0.62, pal["rough"] - 0.09, pal["rough"] + 0.07)
    rough += np.sin(x * 0.002 + y * 0.0015 + phase * 0.5) * 0.08
    rough = np.clip(rough, 0.12, 0.88)

    height = np.clip(h, 0, 1)
    return albedo, normal, iri, sheen, rough, height


def main():
    for season in seas.SEASONS:
        rng = np.random.default_rng(SEED)
        h_struct = satin_struct(rng)
        files = []
        for f in range(FRAMES):
            albedo, normal, iri, sheen, rough, height = season_frame(season, f, h_struct)
            p = f"{season}_Frame{f:02d}"
            files += [
                rc.save_image(OUT / f"T_Season_{p}_BaseColor.png", albedo, "rgb"),
                rc.save_image(OUT / f"T_Season_{p}_Normal.png", normal, "rgb"),
                rc.save_image(OUT / f"T_Season_{p}_Iridescence.png", iri, "gray"),
                rc.save_image(OUT / f"T_Season_{p}_Sheen.png", sheen, "gray"),
                rc.save_image(OUT / f"T_Season_{p}_Roughness.png", rough, "gray"),
                rc.save_image(OUT / f"T_Season_{p}_Height.png", height, "gray"),
            ]
        names = [Path(f).name for f in files]
        rc.write_manifest(
            OUT / f"season_{season.lower()}_animated_manifest.json",
            f"melodia.shorewake_seasonal_{season.lower()}_animated.v1",
            SEED,
            {"season": season, "size": SIZE, "frames": FRAMES,
             "loop": "seamless phase 0==2pi",
             "recipe": "season palette + animated wash/crawl, crawl not pop, "
                       "same mode vocabulary",
             "audio_contract": "texture-only; no audio reader"},
            names,
        )
        print(f"[season-anim] {season}: {len(files)} maps")
    print(f"[season-anim] done -> {OUT}")


if __name__ == "__main__":
    main()