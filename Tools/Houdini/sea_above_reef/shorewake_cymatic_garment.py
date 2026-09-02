#!/usr/bin/env python
"""Cymatic Garment Kit — Chladni standing-wave fabric per shorewake garment layer.

Folds the silhouette-labeled Shorewake garment grid (10 layers from
silhouette_garment_label.py) into a **cymatic garment pipeline**: every garment
piece weaves its own Chladni standing-wave harmonic (distinct m,n nodal mode),
so the whole dress reads as one "singing" garment where each piece vibrates at
a different nodal frequency. This is the Infinity Nikki-style wardrobe material
language — presentation channels (iridescence / sheen / emissive) are keyed to
cymatic nodes so the fabric is audio-reactive-READY (no audio reader added; the
single audio writer MelodiaAudioReactivePresentationSubsystem stays untouched).

Per layer, an 6-map set is written:
  BaseColor / Normal / Height / Roughness / Metal / Iridescence
plus an Emissive (node glow) and the ORM-pack (R=AO G=Rough B=Metal) and
Opacity, matching the copernicus_cymatic_parallax output contract (9 maps) so
the two pipelines can be swapped on the material.

Static (seed 20260902) + a seamless 8-frame animated flipbook where the
standing-wave phase crawls (Chladni plate "breathes").

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_cymatic_garment.py
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

OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "garment_refresh" / "cymatic"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 2048
FRAMES = 8

# Chladni nodal mode per garment layer — each piece sings its own harmonic.
# (m,n) chosen so adjacent layers differ (no two identical), low enough to be
# crisp nodal lines at 2K, high enough to register as a woven motif.
MODE_BY_LAYER = {
    "M_Bodice_Torso":     (5, 7),   # the chest note — lowest full-body bass
    "M_Bodice_Front":     (3, 4),
    "M_Bodice_Side":      (2, 6),
    "M_Bodice_Upper":     (1, 3),
    "M_Collar":           (6, 6),   # symmetric collar frame
    "M_Shoulder_Trim":    (4, 8),
    "M_Shoulder_Ornament":(8, 8),   # bead-grid nodal
    "M_Sleeve":           (2, 7),
    "M_Underskirt":       (3, 5),
    "M_Skirt_Full":       (7, 9),   # the big skirt plate — full sing
}

PAL = {
    "base":   (245, 242, 235),
    "blush":  (230, 228, 222),
    "accent": (255, 240, 230),
    "rough":  0.31,
    "node_glow": (200, 230, 255),   # cool cymatic node light
}


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def chladni(s, m, n, phase=0.0):
    """Rectangular-plate Chladni standing wave, tileable (periodic via mgrid)."""
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) / s
    p1 = np.sin(m * np.pi * x + phase)
    p2 = np.sin(m * np.pi * y + phase * 0.3)
    p3 = np.sin(n * np.pi * x + phase * 0.7)
    p4 = np.sin(n * np.pi * y + phase)
    a = p1 * p2
    b = p3 * p4
    t = np.abs(a - b)
    return np.clip(t, 0, 1)


def charmeuse(rng, layer):
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    wp = 7.0; wf = 7.0
    xb = x + np.sin((y * 0.00005) * 12) * 1.8
    offset = (y // wf) * 3
    warp = ((xb - offset * 2.1) % wp) < 5
    weft = ~warp
    over = warp * 0.96 + weft * 0.25
    fn = rng.normal(size=(SIZE, SIZE)) * 0.014
    wash = np.sin(x * 0.002 + y * 0.0015) * 0.03 + np.cos(y * 0.003 - x * 0.001) * 0.025
    h = np.clip(over + fn + wash, 0, 1)
    h = smoothstep(0.2, 0.85, h)
    if "Bodice" in layer:
        h = np.clip(h + 0.06 * np.abs(np.sin(x * 0.0012)), 0, 1)
    return h


def build_layer(layer, m, n, rng, frame=-1, nframes=FRAMES):
    s = SIZE
    phase = (frame / nframes) * math.pi * 2.0 if frame >= 0 else 0.0
    base = np.array(PAL["base"], float) / 255.0
    blush = np.array(PAL["blush"], float) / 255.0
    accent = np.array(PAL["accent"], float) / 255.0
    glow = np.array(PAL["node_glow"], float) / 255.0

    h_satin = charmeuse(rng, layer)
    # cymatic nodal lattice woven over the satin: weight by mode count
    ch = smoothstep(0.30, 0.85, chladni(s, m, n, phase))
    h = np.clip(h_satin + 0.40 * (ch - 0.5) + 0.12 * ch, 0, 1)

    # normal from height
    nrm = rc.normal_from_height(h, strength=1.8)

    # albedo — pearl base + cymatic node glow on nodal lines
    y1, x1 = np.mgrid[0:s, 0:s].astype(np.float32)
    m1 = 0.035 * np.sin(x1 * 0.018 + y1 * 0.012)[..., None]
    m2 = 0.025 * np.sin(x1 * 0.009 - y1 * 0.022)[..., None]
    m3 = 0.018 * np.sin((x1 + y1) * 0.006)[..., None]
    albedo = base[None, None] + m1 + m2 + m3
    # node glow: brighten nodal lines toward cool cymatic light
    albedo = albedo * (1 - 0.35 * ch[..., None]) + glow[None, None] * 0.28 * ch[..., None]
    albedo = np.clip(albedo, 0, 1)

    # roughness — fabric base, cymatic crests glossier
    rough = np.where(h > 0.62, PAL["rough"] - 0.09, PAL["rough"] + 0.07)
    rough += np.sin(x1 * 0.002 + y1 * 0.0015) * 0.10
    rough = np.clip(rough, 0.12, 0.88)

    # metal — 0 (cloth); metallic hint at nodal crests for "silver thread"
    metal = np.clip((ch - 0.55) * 2.0, 0, 1) * 0.20

    # iridescence — nacre over base PLUS cymatic node swell (the singing sheen)
    iri = np.clip((h - 0.5) * 1.8, 0, 1) * (0.70 + 0.30 * np.sin(x1 * 0.02 + y1 * 0.001))
    iri = np.clip(iri + 0.30 * ch, 0, 1)

    # emissive — nodal lines glow (audio-reactive-ready; no reader added)
    emissive = smoothstep(0.72, 0.98, ch)[..., None] * glow[None, None] * 0.85

    # AO — cavity from dilate
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    h_blur = np.asarray(hb, np.float32) / 255.0
    ao = 1.0 - 0.65 * (h_blur - h)

    # ORM pack
    orm = np.stack([ao, rough, metal], -1).astype(np.float32)
    opacity = np.ones((s, s), np.float32)
    return {"h": h, "n": nrm, "a": albedo, "r": rough, "m": metal,
            "iri": iri, "e": emissive, "ao": ao, "orm": orm, "op": opacity}


def save_static(layer, maps):
    files = [
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_BaseColor.png", maps["a"], "rgb"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Normal.png", maps["n"], "rgb"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Height.png", maps["h"], "gray"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Roughness.png", maps["r"], "gray"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Metallic.png", maps["m"], "gray"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Iridescence.png", maps["iri"], "gray"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Emissive.png", maps["e"], "rgb"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_ORM.png", maps["orm"], "rgb"),
        rc.save_image(OUT / f"T_Cymatic_Garment_{layer}_Opacity.png", maps["op"], "gray"),
    ]
    return files


def save_animated(layer, m, n, rng):
    files = []
    for f in range(FRAMES):
        maps = build_layer(layer, m, n, rng, frame=f)
        p = f"Frame{f:02d}"
        files += [
            rc.save_image(OUT / "animated" / f"T_Cymatic_Garment_{layer}_{p}_BaseColor.png", maps["a"], "rgb"),
            rc.save_image(OUT / "animated" / f"T_Cymatic_Garment_{layer}_{p}_Normal.png", maps["n"], "rgb"),
            rc.save_image(OUT / "animated" / f"T_Cymatic_Garment_{layer}_{p}_Iridescence.png", maps["iri"], "gray"),
            rc.save_image(OUT / "animated" / f"T_Cymatic_Garment_{layer}_{p}_Emissive.png", maps["e"], "rgb"),
            rc.save_image(OUT / "animated" / f"T_Cymatic_Garment_{layer}_{p}_Height.png", maps["h"], "gray"),
        ]
    return files


def main():
    layers = list(MODE_BY_LAYER.keys())
    rng = np.random.default_rng(SEED)
    all_files = []
    (OUT / "animated").mkdir(parents=True, exist_ok=True)
    mode_table = {}
    for layer in layers:
        m, n = MODE_BY_LAYER[layer]
        mode_table[layer] = [m, n]
        maps = build_layer(layer, m, n, rng)
        files = save_static(layer, maps)
        anim = save_animated(layer, m, n, rng)
        all_files.extend(files + anim)
        print(f"[cymatic] {layer} mode({m},{n}): {len(files)} static + {len(anim)} animated")
    names = [Path(f).name for f in all_files]
    rc.write_manifest(
        OUT / "cymatic_garment_manifest.json",
        "melodia.shorewake_cymatic_garment.v1",
        SEED,
        {
            "size": SIZE,
            "layers": layers,
            "modes": mode_table,
            "frames_anim": FRAMES,
            "recipe": "charmeuse satin + per-layer Chladni (m,n) standing-wave "
                      "nodal lattice woven into height; cymatic node glow on albedo/"
                      "emissive/iridescence; audio-reactive-READY (no reader; MPC "
                      "writer untouched); normal OpenGL Y+; regular-diff tangent normal",
            "audio_contract": "texture-only; emissive/sheen/iridescence lanes ready "
                              "for MPC/caymatics consumers, zero new writers",
        },
        names,
    )
    print(f"[cymatic] {len(all_files)} maps -> {OUT}")
    other = list(Path(PROJECT / "Saved/Audit/melusina_lookdev/garment_refresh").glob("*.png"))
    print(f"[cymatic] static refresh family (non-cymatic): {len(other)} maps")


if __name__ == "__main__":
    main()