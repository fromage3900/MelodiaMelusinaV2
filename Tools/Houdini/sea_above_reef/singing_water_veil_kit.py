#!/usr/bin/env python
"""Cymatic Singing Water Veil — PBR kit + height-awake placement (2026-09-02).

Deterministic cymatic ocean-silk fabric for the Sea Above water lands. Pure
numpy+Pillow (venv), bakes a 9-map copernicus contract (BaseColor/Normal/Height/
Roughness/Metallic/Iridescence/Emissive/ORM/Opacity) per water-zone Chladni
mode, plus a bounded heightfield PNG of the "veil surface" for downstream WPO
or parallax. Pairs with shorewake_cymatic_garment.py (same mode language) —
the garment and the water sing the same harmonics (Shorelistener: the world is
water). Texture-only (no audio reader), single-writer contract respected.

Files -> Saved/Audit/melusina_lookdev/singing_water/cymatic/
  T_SingingWater_<Zone>_<Map>.png            (per-zone 9-map set)
  T_SingingWater_VeilHeight_4K.png           (veil surface heightfield, cymatic)
  singing_water_cymatic_manifest.json        (seed 20260902, sha256/file)

Zone->Chladni mode map mirrors the water-ecosystem manifest (same modes as the
fabric garment). Run via venv python.

Height-awake note: the heightfield is authored in water-space; the placement
plan (specs/water_veil/singing_water_veil_placements.json) carries the
CanonicalLandscape surface height per point so the editor raycast-snaps.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/singing_water_veil_kit.py
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

OUT = PROJECT / "Saved/Audit/melusina_lookdev/singing_water/cymatic"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 2048

# Water zone -> Chladni mode (identical to the fabric garment mode table so the
# garment and water share harmonic language).
MODE_BY_ZONE = {
    "SheetVeil":   (2, 4),
    "SingingFall": (4, 9),
    "HearthPool":  (1, 2),
    "TideSeam":    (6, 7),
}
PAL = {
    "deep":   (6, 40, 66),     # deep ocean
    "mid":    (34, 120, 150),  # seafoam-cyan
    "foam":   (215, 245, 240),
    "sing":   (150, 220, 255),  # cymatic node light on the water
    "rough":  0.12,
}


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def chladni(s, m, n, phase=0.0):
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) / s
    p1 = np.sin(m * np.pi * x + phase)
    p2 = np.sin(m * np.pi * y + phase * 0.3)
    p3 = np.sin(n * np.pi * x + phase * 0.7)
    p4 = np.sin(n * np.pi * y + phase)
    return np.clip(np.abs(p1 * p2 - p3 * p4), 0, 1)


def ocean_base(rng):
    """Deterministic ocean-silk macro field: broad swell + fine ripple."""
    s = SIZE
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    swell = np.sin(x * 0.0015) * np.cos(y * 0.0012) * 0.30
    swell += np.sin((x + y) * 0.0008) * 0.15
    ripple = np.sin(x * 0.05 + y * 0.04) * 0.02 + np.cos(y * 0.06 - x * 0.03) * 0.02
    fn = rng.normal(size=(s, s)) * 0.012
    h = np.clip(0.5 + swell + ripple + fn, 0, 1)
    return smoothstep(0.15, 0.85, h)


def build_zone(rng, zone):
    s = SIZE
    m, n = MODE_BY_ZONE[zone]
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    base = np.array(PAL["foam"], float) / 255.0
    deep = np.array(PAL["deep"], float) / 255.0
    mid = np.array(PAL["mid"], float) / 255.0
    sing = np.array(PAL["sing"], float) / 255.0

    h_ocean = ocean_base(rng)
    ch = smoothstep(0.35, 0.9, chladni(s, m, n))
    # the sung standing-wave lines ride over the swell
    h = np.clip(h_ocean + 0.42 * ch, 0, 1)

    # normal — height-derived, OpenGL Y+
    nrm = rc.normal_from_height(h, strength=1.6)

    # albedo — foam->mid->deep vertical, node glow on sung lines
    t = h
    albedo = foam_mix(mid, deep, t)
    albedo = albedo * (1 - 0.65 * ch[..., None]) + sing[None, None] * 0.40 * ch[..., None]
    albedo = np.clip(albedo, 0, 1)
    albedo += np.random.default_rng(SEED + 1).normal(size=(s, s, 3)) * 0.008
    albedo = np.clip(albedo, 0, 1)

    # roughness — foam soft, sung lines glossy
    rough = np.where(h > 0.7, 0.06, 0.22)
    rough += np.sin(x * 0.003 + y * 0.002) * 0.06
    rough = np.clip(rough, 0.03, 0.6)

    # metal — water 0, occasional spume glint
    metal = np.clip((ch - 0.75) * 3.0, 0, 1) * 0.25

    # iridescence — ocean nacre + sung sheen
    iri = np.clip((h - 0.45) * 1.6, 0, 1) * (0.6 + 0.4 * np.sin(x * 0.005 + y * 0.005))
    iri = np.clip(iri + 0.35 * ch, 0, 1)

    # emissive — the singing lines glow (audio-reactive-ready, no reader)
    emissive = smoothstep(0.78, 0.99, ch)[..., None] * sing[None, None] * 0.9

    # AO — cavity
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    hb_a = np.asarray(hb, np.float32) / 255.0
    ao = 1.0 - 0.5 * (hb_a - h)
    orm = np.stack([ao, rough, metal], -1).astype(np.float32)
    op = np.ones((s, s), np.float32)

    return {"h": h, "n": nrm, "a": albedo, "r": rough, "m": metal,
            "iri": iri, "e": emissive, "ao": ao, "orm": orm, "op": op}


def foam_mix(mid, deep, t):
    return mid[None, None] * (1 - t[..., None]) + deep[None, None] * t[..., None]


def main():
    zones = list(MODE_BY_ZONE.keys())
    rng = np.random.default_rng(SEED)
    files = []
    for zone in zones:
        m = build_zone(rng, zone)
        files += [
            rc.save_image(OUT / f"T_SingingWater_{zone}_BaseColor.png", m["a"], "rgb"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Normal.png", m["n"], "rgb"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Height.png", m["h"], "gray"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Roughness.png", m["r"], "gray"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Metallic.png", m["m"], "gray"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Iridescence.png", m["iri"], "gray"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Emissive.png", m["e"], "rgb"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_ORM.png", m["orm"], "rgb"),
            rc.save_image(OUT / f"T_SingingWater_{zone}_Opacity.png", m["op"], "gray"),
        ]
        print(f"[swv] {zone} mode({MODE_BY_ZONE[zone][0]},{MODE_BY_ZONE[zone][1]}): 9 maps")

    # veil heightfield (4K, bounded) for WPO/parallax downstream
    hvoll = np.zeros((4096, 4096), np.float32)
    # compose the four zones as a quadrant field (cymatic standing wave pitches)
    m, n = 3, 5
    qy, qx = np.mgrid[0:4096, 0:4096].astype(np.float32)
    u = qx / 4096.0
    v = qy / 4096.0
    hvoll = 0.5 + 0.5 * chladni(4096, m, n)
    hvoll = smoothstep(0.2, 0.8, hvoll)
    files.append(rc.save_image(OUT / "T_SingingWater_VeilHeight_4K.png", hvoll, "gray"))

    names = [Path(f).name for f in files]
    rc.write_manifest(
        OUT / "singing_water_cymatic_manifest.json",
        "melodia.singing_water_cymatic.v1",
        SEED,
        {
            "size": SIZE,
            "zones": zones,
            "modes": {z: list(MODE_BY_ZONE[z]) for z in zones},
            "veil_height_res": 4096,
            "recipe": "ocean-silk macro swell + per-zone Chladni standing-wave nodal "
                      "lines; cymatic node glow on emissive/iridescence/foam; "
                      "height-derived normal (OpenGL Y+); audio-reactive-READY "
                      "(no reader; single MPC writer untouched)",
            "height_contract": "placed on CanonicalLandscape (never created) via "
                               "paired placement plan; height-awake raycast",
        },
        names,
    )
    print(f"[swv] {len(files)} maps -> {OUT}")


if __name__ == "__main__":
    main()