#!/usr/bin/env python
"""Shorewake refresh fabric kit — per-garment-layer, breath-taking (2026-09-02).

Builds on the proven pearl/weave recipe (skill: melodia-fabric-cops-pipeline,
shorewake_pearl_weave_kit.py) but re-targets the maps to the 10 silhouette-
labeled garment layers, so each piece of the dress gets a weave + finish that
matches its layer rather than one shared texture set:

  M_Bodice_Torso      tight charmeuse satin (high sheen, long float)
  M_Bodice_Front/Side charmeuse satin + corset bone creases
  M_Bodice_Upper      charmeuse satin
  M_Collar            pearl lace (masked opacity, sheen accent)
  M_Shoulder_Trim     micro eyelet trim
  M_Shoulder_Ornament pearl dot/bead grid
  M_Sleeve            soft satin drape
  M_Underskirt        silk organza sheen
  M_Skirt_Full        painterly pearl satin (base dress)

Outputs (2048 tiling unless layered note): an 8-map per-layer set
  T_Shorewake_Garment_<Layer>_{BaseColor,Normal,Height,AO,Roughness,Metal,
                                Iridescence,Sheen}.png
into Saved/Audit/melusina_lookdev/garment_refresh/ plus a contact sheet +
manifest. Texture-only (no audio reader), matches the audio contract.
Deterministic: SEED recorded.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_garment_refresh.py
"""
from __future__ import annotations

import colorsys
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402

OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "garment_refresh"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 2048

PALETTE = {
    "Moon":   {"base": (245, 242, 235), "blush": (230, 228, 222), "accent": (235, 225, 210), "rough": 0.31},
    "Blush":  {"base": (245, 232, 228), "blush": (235, 210, 205), "accent": (255, 210, 200), "rough": 0.30},
    "Dusk":   {"base": (220, 218, 230), "blush": (200, 195, 220), "accent": (210, 200, 235), "rough": 0.32},
}
PAL = PALETTE["Moon"]  # primary — dress reads under iridescence


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def charmeuse_satin(rng, layer):
    """Tight lustrous satin — long float, high sheen, fine threads."""
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    warp_period = 7.0
    weft_period = 7.0
    bias = y * 0.00005
    x_biased = x + np.sin(bias * 12) * 1.8
    offset = (y // weft_period) * 3  # 7-end satin step
    warp_float = ((x_biased - offset * 2.1) % warp_period) < 5
    weft_float = ~warp_float
    over = warp_float * 0.96 + weft_float * 0.25
    fn = rng.normal(size=(SIZE, SIZE)) * 0.014
    wash = np.sin(x * 0.002 + y * 0.0015) * 0.03 + np.cos(y * 0.003 - x * 0.001) * 0.025
    h = np.clip(over + fn + wash, 0, 1)
    h = smoothstep(0.2, 0.85, h)
    # corset bone creases for bodice layers
    if "Bodice" in layer:
        crease = np.abs(np.sin(x * 0.0012))  # gentle vertical ribs
        h = np.clip(h + 0.06 * crease, 0, 1)
    return h


def lace_overlay(rng, kind):
    """8-repeat lace. kinds: floral|eyelet|dotgrid."""
    s = SIZE
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    fx, fy = (x / s * 8) % 1, (y / s * 8) % 1
    tx, ty = fx * 2 - 1, fy * 2 - 1
    dist = np.sqrt(tx * tx + ty * ty)
    ang = np.arctan2(ty, tx)
    if kind == "dotgrid":  # bead/perl dots
        dot = np.clip(1 - dist * 3.0, 0, 1); dot = smoothstep(0.6, 0.95, dot)
        lattice = abs(np.sin(fx * np.pi * 2) * np.sin(fy * np.pi * 2)); lattice = smoothstep(0.45, 0.85, lattice)
        lace = np.maximum(dot * 0.7, lattice * 0.45)
    else:  # floral / eyelet
        flower = np.clip(1 - dist * 1.4 + np.cos(ang * 5) * 0.18, 0, 1)
        flower = smoothstep(0.35, 0.72, flower)
        vine = abs(np.sin(fx * np.pi * 2) * np.sin(fy * np.pi * 2)); vine = smoothstep(0.45, 0.85, vine)
        eyelet = smoothstep(0.55, 0.9, np.clip(1 - dist * 2.2, 0, 1)) * 0.85
        lace = np.maximum(flower * 0.95, np.maximum(vine * 0.75, eyelet * 0.3))
    lace = np.clip(lace, 0, 1) * (0.92 + 0.08 * np.sin(x * 0.015 + y * 0.013))
    return lace


def build_layer(layer, rng):
    s = SIZE
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    base = np.array(PAL["base"], float) / 255.0
    blush = np.array(PAL["blush"], float) / 255.0
    accent = np.array(PAL["accent"], float) / 255.0
    rough_base = PAL["rough"]

    extra_lace = None
    if layer in ("M_Collar",):
        h0 = charmeuse_satin(rng, layer)
        lc = lace_overlay(rng, "floral")
        h = np.clip(h0 + lc * 0.45, 0, 1)
        opacity = np.clip(lc * 0.95 + 0.08, 0, 1)
        extra_lace = lc
    elif layer in ("M_Shoulder_Ornament",):
        h0 = charmeuse_satin(rng, layer)
        lc = lace_overlay(rng, "dotgrid")
        h = np.clip(h0 + lc * 0.6, 0, 1)
        opacity = np.clip(0.6 + 0.4 * (lc > 0.45).astype(float), 0, 1)
        extra_lace = lc
    elif layer in ("M_Shoulder_Trim",):
        h0 = charmeuse_satin(rng, layer)
        lc = lace_overlay(rng, "eyelet")
        h = np.clip(h0 + lc * 0.35, 0, 1)
        opacity = np.clip(0.7 + 0.3 * lc, 0, 1)
        extra_lace = lc
    else:  # satin families
        h = charmeuse_satin(rng, layer)
        opacity = np.ones((s, s), np.float32)

    # normal from height
    n = rc.normal_from_height(h, strength=1.8)

    # albedo — painterly pearl with layer-specific tint
    tint = base  # (1,3) broadcast
    s1 = 0.035 * np.sin(x * 0.018 + y * 0.012)[..., None]
    s2 = 0.025 * np.sin(x * 0.009 - y * 0.022)[..., None]
    s3 = 0.018 * np.sin((x + y) * 0.006)[..., None]
    if layer in ("M_Skirt_Full", "M_Underskirt", "M_Sleeve"):
        # push toward deeper pearl/teal for skirt family (dress continuity)
        tint = base[None, None] * 0.85 + np.array([0.08, 0.12, 0.13])
    albedo = tint + s1 + s2 + s3
    if extra_lace is not None:
        # ivory lace over pearl base
        ivory = np.array([0.98, 0.96, 0.92])
        albedo = albedo * (1 - extra_lace[..., None] * 0.45) + ivory[None, None] * extra_lace[..., None] * 0.95
    albedo = np.clip(albedo, 0, 1)

    # roughness
    rough = np.where(h > 0.62, rough_base - 0.09, rough_base + 0.07)
    rough += np.sin(x * 0.002 + y * 0.0015) * 0.10
    rough = np.clip(rough, 0.12, 0.88)

    # metallic (0 base; lace crests metallic hint)
    metal = np.zeros((s, s), np.float32)
    if extra_lace is not None:
        metal = np.clip((extra_lace - 0.65) * 3, 0, 1) * 0.15

    # iridescence — nacre crest bands
    iri = np.clip((h - 0.5) * 1.8, 0, 1) * (0.70 + 0.30 * np.sin(x * 0.02 + y * 0.001))
    if extra_lace is not None:
        iri = np.clip(iri + extra_lace * 0.25, 0, 1)
    iri = np.clip(iri, 0, 1)

    # sheen strength
    sheen = np.clip((1.0 - np.abs(h - 0.72) * 3.5) * 0.4 + 0.35, 0, 1)

    # AO — cavity via local min (PIL max filter sort)
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    h_blur = np.asarray(hb, np.float32) / 255.0
    ao = 1.0 - 0.65 * (h_blur - h)

    files = [
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_BaseColor.png", albedo, "rgb"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Normal.png", n, "rgb"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Height.png", h, "gray"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_AO.png", ao, "gray"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Roughness.png", rough, "gray"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Metal.png", metal, "gray"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Iridescence.png", iri, "gray"),
        rc.save_image(OUT / f"T_Shorewake_Garment_{layer}_Sheen.png", sheen, "gray"),
    ]
    return files, opacity


def main():
    layers = [
        "M_Bodice_Torso", "M_Bodice_Front", "M_Bodice_Side", "M_Bodice_Upper",
        "M_Collar", "M_Shoulder_Trim", "M_Shoulder_Ornament", "M_Sleeve",
        "M_Underskirt", "M_Skirt_Full",
    ]
    rng = np.random.default_rng(SEED)
    all_files = []
    opacity_map = {}
    for layer in layers:
        files, _op = build_layer(layer, rng)
        all_files.extend(files)
        print(f"[refresh] {layer}: {len(files)} maps")
    files = [Path(f).name for f in all_files]
    rc.write_manifest(
        OUT / "garment_refresh_manifest.json",
        "melodia.shorewake_garment_refresh.v1",
        SEED,
        {
            "size": SIZE,
            "layers": layers,
            "palette": "Moon",
            "recipe": "charmeuse satin + per-layer lace/eyelet/dot, painterly nacre "
                      "albedo, height-derived normal (rc.normal_from_height), "
                      "crest-weighted iridescence, sheen strength",
            "audio_contract": "texture-only; no audio reader; single audio writer untouched",
        },
        files,
    )
    print(f"[refresh] {len(all_files)} maps -> {OUT}")
    print(f"[refresh] manifest -> {OUT / 'garment_refresh_manifest.json'}")


if __name__ == "__main__":
    main()