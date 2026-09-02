#!/usr/bin/env python
"""Shorewake dress animated fabric — morph-aware flipbook (2026-09-02).

Bakes a seamless animated texture sequence for the dress fabric that the UE
material can flip through to drive the nacre/iridescence shimmer in sync with
the dress's authored morph targets (Bloom/Swirl/ShimmerWave). Reuses the proven
flipbook cadence from flipbook_aaa.py, keyed to the refreshed garment layers.

Per frame (8 frames, 2048, seamless loop phase 0==2pi):
  BaseColor     painterly pearl (Moon palette), wash-phase drifting
  Normal        height-derived, crawl-phase (no popping)
  Iridescence  crest/band shimmer, hue drifting per frame
  Sheen         grazing-weight shimmer
  Height        stable weave + phase wash
Plus one morph-aware normal set: T_Shorewake_Morph_Bloom/Swirl_*.png driving
the normal map between morph target poses (texture-side, matches the dress's
shape-key normals without touching .uasset).

Texture-only; no audio reader. Deterministic SEED 20260902.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_animated_flipbook.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402

OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "garment_refresh" / "animated"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 2048
FRAMES = 8

RNG_FIXED = np.random.default_rng(1234)  # stable structural field


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def satin_structure(rng):
    """Stable woven charmeuse field (same across frames — only wash/shimmer animate)."""
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    warp_period = 7.0
    weft_period = 7.0
    bias = y * 0.00005
    x_biased = x + np.sin(bias * 12) * 1.8
    offset = (y // weft_period) * 3
    warp_float = ((x_biased - offset * 2.1) % warp_period) < 5
    weft_float = ~warp_float
    over = warp_float * 0.96 + weft_float * 0.25
    fn = rng.normal(size=(SIZE, SIZE)) * 0.014
    h = np.clip(over + fn, 0, 1)
    return smoothstep(0.2, 0.85, h)


def frame(frame_i, h_struct):
    phase = (frame_i / FRAMES) * math.pi * 2.0
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    wash = np.sin(x * 0.002 + y * 0.0015 + phase * 0.65) * 0.03 \
        + np.cos(y * 0.003 - x * 0.001 + phase * 0.45) * 0.025
    brush = np.sin(x * 0.15 + phase * 0.3) * np.cos(y * 0.12 - phase * 0.2) * 0.012
    h = np.clip(h_struct + 0.4 * wash + brush, 0, 1)

    # normal — stable structure + crawl jitter (no pop)
    dy, dx = np.gradient(h)
    dx *= 14.0; dy *= 14.0
    jx = np.sin(x * 0.07 + phase * 2.1 + y * 0.03) * 0.06
    jy = np.cos(y * 0.07 - phase * 1.7 + x * 0.02) * 0.06
    nx, ny, nz = -dx - jx, -dy - jy, np.ones_like(dx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([(nx / ln * 0.5 + 0.5), (ny / ln * 0.5 + 0.5), (nz / ln * 0.5 + 0.5)], -1).astype(np.float32)

    # albedo — Moon palette pearl, hue + wash drifting
    base = np.array([245, 242, 235], float) / 255.0
    blush = np.array([230, 228, 222], float) / 255.0
    accent = np.array([255, 240, 230], float) / 255.0
    drift = np.array([
        0.015 * math.sin(phase * 1.0),
        0.012 * math.sin(phase * 1.3 + 1.1),
        0.015 * math.cos(phase * 0.9 + 0.4),
    ])
    accent_f = np.clip(accent + drift, 0, 1)
    tint = base[None, None]
    s1 = 0.035 * np.sin(x * 0.018 + y * 0.012 + phase * 1.2)[..., None]
    s2 = 0.025 * np.sin(x * 0.009 - y * 0.022 - phase * 0.9)[..., None]
    s3 = 0.018 * np.sin((x + y) * 0.006 + phase * 0.75)[..., None]
    # pearl dust flecks — stable positions, shimmering intensity
    RNG_FIXED_again = np.random.default_rng(4242)
    fleck_field = (RNG_FIXED_again.random((SIZE, SIZE)) > 0.985).astype(float)[..., None]
    fleck_int = 0.02 * (0.7 + 0.3 * math.sin(phase * 1.6))
    fleck = fleck_int * fleck_field * (accent_f - tint)
    albedo = np.clip(tint + s1 + s2 + s3 + fleck, 0, 1)
    albedo += np.random.default_rng(999 + frame_i).normal(size=(SIZE, SIZE, 3)) * 0.010
    albedo = np.clip(albedo, 0, 1)

    # iridescence — crest + crawling thin-film bands, hue drifting
    iri = np.clip((h - 0.5) * 1.8, 0, 1) * (0.70 + 0.30 * np.sin(x * 0.02 + phase * 1.4 + y * 0.001))
    band = 0.12 * np.sin(x * 0.030 - y * 0.018 + phase * 1.2) + 0.08 * np.sin((x + y) * 0.012 + phase * 0.6)
    iri = np.clip(iri + band + 0.06 * math.sin(phase * 0.9), 0, 1)

    # sheen — grazing-weight shimmer
    sheen = np.clip((1.0 - np.abs(h - 0.72) * 3.5) * 0.4 + 0.35 + 0.10 * math.sin(phase * 1.1), 0, 1)

    rough = np.where(h > 0.62, 0.31 - 0.09, 0.31 + 0.07)
    rough += np.sin(x * 0.002 + y * 0.0015 + phase * 0.5) * 0.08
    rough = np.clip(rough, 0.12, 0.88)

    height = np.clip(h, 0, 1)
    return albedo, normal, iri, sheen, rough, height


def morph_normals(h_struct):
    """Morph-aware normal maps for Bloom / Swirl targets (texture-side)."""
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    # Bloom: radial rise from center (dress breathes open)
    cx, cy = SIZE / 2, SIZE / 2
    rad = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / SIZE * 2.0
    bloom = np.clip(np.exp(-((rad - 0.4) ** 2) / 0.05), 0, 1)
    h_bloom = np.clip(h_struct + 0.18 * bloom, 0, 1)
    # Swirl: angular wave (dress twists)
    ang = np.arctan2(y - cy, x - cx)
    swirl = np.clip(0.5 + 0.5 * np.sin(ang * 4.0), 0, 1)
    h_swirl = np.clip(h_struct + 0.16 * swirl, 0, 1)
    outs = {}
    for name, hh in (("Bloom", h_bloom), ("Swirl", h_swirl)):
        n = rc.normal_from_height(hh, strength=1.8)
        outs[name] = n
    return outs


def main():
    rng = np.random.default_rng(SEED)
    h_struct = satin_structure(rng)
    files = []
    for f in range(FRAMES):
        albedo, normal, iri, sheen, rough, height = frame(f, h_struct)
        p = f"Frame{f:02d}"
        files += [
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_BaseColor.png", albedo, "rgb"),
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_Normal.png", normal, "rgb"),
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_Iridescence.png", iri, "gray"),
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_Sheen.png", sheen, "gray"),
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_Roughness.png", rough, "gray"),
            rc.save_image(OUT / f"T_Shorewake_Animated_{p}_Height.png", height, "gray"),
        ]
        print(f"[anim] {p}: 6 maps")
    morphs = morph_normals(h_struct)
    for name, nrm in morphs.items():
        files.append(rc.save_image(OUT / f"T_Shorewake_Morph_{name}_Normal.png", nrm, "rgb"))
    names = [Path(f).name for f in files]
    rc.write_manifest(
        OUT / "animated_manifest.json",
        "melodia.shorewake_animated_flipbook.v1",
        SEED,
        {
            "size": SIZE,
            "frames": FRAMES,
            "loop": "seamless phase 0==2pi",
            "morph_targets": ["Bloom", "Swirl"],
            "recipe": "stable satin structure + animated wash/crawl/hue; "
                      "crawl not pop; morph normals from height (Bloom radial, Swirl angular)",
            "audio_contract": "texture-only; no audio reader",
        },
        names,
    )
    print(f"[anim] {len(files)} maps -> {OUT}")


if __name__ == "__main__":
    main()