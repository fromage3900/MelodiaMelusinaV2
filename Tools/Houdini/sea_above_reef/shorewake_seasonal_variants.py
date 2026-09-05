#!/usr/bin/env python
"""Seasonal Shorewake garment variants — Spring/Summer/Autumn/Winter (2026-09-02).

Expands the universal garment system into SEASONS. Reuses the proven garment-
refresh recipe (charmeuse satin + per-layer lace/eyelet/dot + painterly nacre
albedo), re-keyed to four seasonal palettes, keeping the SAME Chladni mode
vocabulary per garment layer so a season is a palette + mood swap on the same
harmonic garment, never a parallel garment system.

Per season, the full 10-layer kit (8 maps/layer = 80 maps): BaseColor/Normal/
Height/AO/Roughness/Metal/Iridescence/Sheen. Plus a season contact sheet.

Seasons + palettes:
  Spring  — blossom: fresh cream base, sakura blush, petal-pink accent, spring-leaf
  Summer  — ocean: seafoam base, aqua blush, sun-gold accent, heat shimmer
  Autumn  — ember: warm cream, amber blush, burnt-orange/gold-leaf accent, bonfire
  Winter  — ice: pale frost base, lavender-ice blush, silver-star accent, deep freeze

Texture-only (no audio reader); single-writer contract respected. Deterministic,
seed-locked, sha256 manifest per season. Run via venv python.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_seasonal_variants.py [--size 2048]
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
import shorewake_garment_refresh as g  # noqa: E402  (reuse charmeuse/lace/smoothstep)

OUT = PROJECT / "Saved/Audit/melusina_lookdev/garment_refresh/seasons"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = int(sys.argv[sys.argv.index("--size") + 1] if "--size" in sys.argv else 2048)

LAYERS = [
    "M_Bodice_Torso", "M_Bodice_Front", "M_Bodice_Side", "M_Bodice_Upper",
    "M_Collar", "M_Shoulder_Trim", "M_Shoulder_Ornament", "M_Sleeve",
    "M_Underskirt", "M_Skirt_Full",
]

# Season -> (base, blush, accent, node_glow, roughness, mood_warp)
SEASONS = {
    "Spring": {
        "base": (250, 245, 235), "blush": (255, 225, 230), "accent": (255, 190, 205),
        "glow": (255, 220, 240), "rough": 0.30,
        "warp": 0.012, "lace_irl": 0.25, "sheen": 0.35, "desc": "blossom — fresh cream, sakura blush",
    },
    "Summer": {
        "base": (235, 248, 244), "blush": (180, 230, 220), "accent": (255, 216, 150),
        "glow": (160, 240, 255), "rough": 0.26,
        "warp": 0.020, "lace_irl": 0.30, "sheen": 0.42, "desc": "ocean — seafoam, aqua, sun-gold",
    },
    "Autumn": {
        "base": (245, 238, 226), "blush": (235, 205, 175), "accent": (230, 130, 60),
        "glow": (255, 190, 90), "rough": 0.34,
        "warp": 0.016, "lace_irl": 0.22, "sheen": 0.30, "desc": "ember — warm cream, burnt-orange",
    },
    "Winter": {
        "base": (238, 242, 250), "blush": (215, 220, 240), "accent": (210, 230, 255),
        "glow": (170, 200, 255), "rough": 0.22,
        "warp": 0.010, "lace_irl": 0.35, "sheen": 0.45, "desc": "ice — pale frost, lavender, silver-star",
    },
}


def season_layer(season_name, layer, rng):
    """Rebuild one layer in a season's palette (same mode, same structure)."""
    s = SEASONS[season_name]
    base = np.array(s["base"], float) / 255.0
    blush = np.array(s["blush"], float) / 255.0
    accent = np.array(s["accent"], float) / 255.0
    glow = np.array(s["glow"], float) / 255.0
    rough0 = s["rough"]
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)

    # ---- structure is season-invariant: charmeuse + per-layer lace/ornament ----
    if layer == "M_Bodice_Ornament":
        layer = "M_Shoulder_Ornament"
    if layer in ("M_Collar",):
        h0 = g.charmeuse_satin(rng, layer)
        lc = g.lace_overlay(rng, "floral")
        h = np.clip(h0 + lc * 0.45, 0, 1)
        opacity = np.clip(lc * 0.95 + 0.08, 0, 1)
        extra = lc
    elif layer in ("M_Shoulder_Ornament",):
        h0 = g.charmeuse_satin(rng, layer)
        lc = g.lace_overlay(rng, "dotgrid")
        h = np.clip(h0 + lc * 0.6, 0, 1)
        opacity = np.clip(0.6 + 0.4 * (lc > 0.45).astype(float), 0, 1)
        extra = lc
    elif layer in ("M_Shoulder_Trim",):
        h0 = g.charmeuse_satin(rng, layer)
        lc = g.lace_overlay(rng, "eyelet")
        h = np.clip(h0 + lc * 0.35, 0, 1)
        opacity = np.clip(0.7 + 0.3 * lc, 0, 1)
        extra = lc
    else:
        h = g.charmeuse_satin(rng, layer)
        opacity = np.ones((SIZE, SIZE), np.float32)
        extra = None

    # season mood: a coarse periodic warp over the structure (heat shimmer /
    # floral scatter / ember flicker / frost crystal) — subtle, structure-invariant
    warp = s["warp"] * np.sin(x * 0.003 + y * 0.0025)
    h = np.clip(h + warp * 0.5, 0, 1)

    # normal from height
    n = rc.normal_from_height(h, strength=1.8)

    # albedo — season tint + nacre, with season wash
    s1 = 0.035 * np.sin(x * 0.018 + y * 0.012)[..., None]
    s2 = 0.025 * np.sin(x * 0.009 - y * 0.022)[..., None]
    s3 = 0.018 * np.sin((x + y) * 0.006)[..., None]
    albedo = base[None, None] + s1 + s2 + s3
    if extra is not None:
        ivory = np.array([0.98, 0.96, 0.92])
        albedo = albedo * (1 - extra[..., None] * 0.45) + ivory[None, None] * extra[..., None] * 0.95
    albedo = np.clip(albedo, 0, 1)

    # roughness — season base
    rough = np.where(h > 0.62, rough0 - 0.09, rough0 + 0.07)
    rough += np.sin(x * 0.002 + y * 0.0015) * 0.10
    rough = np.clip(rough, 0.12, 0.88)

    # metal — cloth 0; season accent silver-thread on laced layers
    metal = np.zeros((SIZE, SIZE), np.float32)
    if extra is not None:
        metal = np.clip((extra - 0.65) * 3, 0, 1) * 0.15

    # iridescence — nacre + season sheen; lace boosts
    iri = np.clip((h - 0.5) * 1.8, 0, 1) * (0.70 + 0.30 * np.sin(x * 0.02 + y * 0.001))
    if extra is not None:
        iri = np.clip(iri + s["lace_irl"] * extra, 0, 1)
    iri = np.clip(iri, 0, 1)

    # sheen — season strength
    sheen = np.clip((1.0 - np.abs(h - 0.72) * 3.5) * s["sheen"] / 0.4 * 0.4 + s["sheen"] * 0.6, 0, 1)

    # AO — cavity
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    h_blur = np.asarray(hb, np.float32) / 255.0
    ao = 1.0 - 0.65 * (h_blur - h)

    return {"h": h, "n": n, "a": albedo, "r": rough, "m": metal,
            "iri": iri, "sheen": sheen, "ao": ao, "op": opacity}


def main():
    files = []
    sheets = []
    for season in SEASONS:
        rng = np.random.default_rng(SEED + abs(hash(season)) % 1000)
        s_files = []
        row = []
        for layer in LAYERS:
            mset = season_layer(season, layer, rng)
            prefix = f"T_Shorewake_Season_{season}_{layer}"
            s_files += [
                rc.save_image(OUT / f"{prefix}_BaseColor.png", mset["a"], "rgb"),
                rc.save_image(OUT / f"{prefix}_Normal.png", mset["n"], "rgb"),
                rc.save_image(OUT / f"{prefix}_Height.png", mset["h"], "gray"),
                rc.save_image(OUT / f"{prefix}_AO.png", mset["ao"], "gray"),
                rc.save_image(OUT / f"{prefix}_Roughness.png", mset["r"], "gray"),
                rc.save_image(OUT / f"{prefix}_Metal.png", mset["m"], "gray"),
                rc.save_image(OUT / f"{prefix}_Iridescence.png", mset["iri"], "gray"),
                rc.save_image(OUT / f"{prefix}_Sheen.png", mset["sheen"], "gray"),
            ]
            row.append(OUT / f"{prefix}_BaseColor.png")
        print(f"[season] {season}: {len(s_files)} maps")
        files.extend(s_files)
        # season contact sheet (all layer BaseColors in a row)
        try:
            from PIL import Image, ImageDraw
            cols, cell = len(row), 256
            W, H = cols * (cell + 8) + 24, cell + 40
            sheet = Image.new("RGB", (W, H), (12, 12, 16))
            draw = ImageDraw.Draw(sheet)
            for i, p in enumerate(row):
                if p.exists():
                    im = Image.open(p).convert("RGB").resize((cell, cell))
                    sheet.paste(im, (24 + i * (cell + 8), 24))
                    draw.text((24 + i * (cell + 8) + 4, 4), layer_short(LAYERS[i]), fill=(255, 255, 255))
            sheet.save(OUT / f"SEASON_{season}_CONTACT.png")
            sheets.append(f"SEASON_{season}_CONTACT.png")
        except Exception as e:
            print(f"[season] sheet warn: {e}")

    names = [Path(f).name for f in files]
    for season, pal in SEASONS.items():
        rc.write_manifest(
            OUT / f"season_{season.lower()}_manifest.json",
            f"melodia.shorewake_seasonal_{season.lower()}.v1",
            SEED,
            {
                "season": season,
                "season_desc": pal["desc"],
                "size": SIZE,
                "layers": LAYERS,
                "palette": {k: pal[k] for k in ("base", "blush", "accent", "glow", "rough")},
                "recipe": "reuses shorewake_garment_refresh charmeuse/lace structure with "
                          "season palette + mood warp; same Chladni mode vocabulary per layer",
                "audio_contract": "texture-only; no audio reader; single audio writer untouched",
            },
            [f for f in names if f.startswith(f"T_Shorewake_Season_{season}_")],
        )
    print(f"[season] {len(files)} maps -> {OUT}")
    print(f"[season] contact sheets: {sheets}")


def layer_short(name):
    return name.replace("M_", "").replace("_", " ").title()


if __name__ == "__main__":
    main()