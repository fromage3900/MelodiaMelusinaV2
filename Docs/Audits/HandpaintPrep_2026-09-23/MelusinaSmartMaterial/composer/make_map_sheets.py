#!/usr/bin/env python
"""Assemble the Mr. Sheep texture-map contact sheet from Painter exports.

Rows = variants (Verse, Inversion, ...), columns = PBR maps actually
exported. Thumbnails downscaled with LANCZOS; row/col captions; prints
per-cell mean brightness as an honest non-black sanity check.

Usage:
  python make_map_sheets.py --exports <variants dir> --out <png path>
"""
from __future__ import annotations

import argparse
import os
from datetime import date

from PIL import Image, ImageDraw, ImageFont

CREAM = (245, 236, 215)
ACCENT = (255, 201, 120)
DARK = (24, 20, 34)
PANEL = (32, 27, 46)

COL_ORDER = ["BaseColor", "Emissive", "Roughness", "Metallic",
             "Height", "Normal", "Ambient Occlusion", "Opacity"]


def _font(size):
    for cand in ("C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/segoeui.ttf"):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


def find_map(files, key):
    """Match 'choralsheep_BaseColor.png' style names for a channel key."""
    token = key.replace(" ", "")
    for f in files:
        stem = os.path.splitext(f)[0].lower()
        if stem.endswith("_" + key.lower().replace(" ", "")) or \
           stem.endswith(key.lower().replace(" ", "")):
            return f
        if token.lower() in stem.replace("_", "").replace("-", ""):
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exports", required=True,
                    help="dir containing one subdir per variant")
    ap.add_argument("--out", required=True)
    ap.add_argument("--thumb", type=int, default=256)
    args = ap.parse_args()

    variants = sorted(d for d in os.listdir(args.exports)
                      if os.path.isdir(os.path.join(args.exports, d)))
    if not variants:
        raise SystemExit("no variant dirs under %s" % args.exports)

    per_variant = {}
    cols = []
    for v in variants:
        d = os.path.join(args.exports, v)
        files = [f for f in os.listdir(d) if f.lower().endswith(".png")]
        maps = {}
        for key in COL_ORDER:
            hit = find_map(files, key)
            if hit:
                maps[key] = os.path.join(d, hit)
                if key not in cols:
                    cols.append(key)
        per_variant[v] = maps
        print("%-12s maps: %s" % (v, sorted(maps)))
    cols = [c for c in COL_ORDER if c in cols]
    print("columns:", cols)

    tw = args.thumb
    margin, cap = 18, 40
    W = margin + (tw + margin) * (len(cols) + 1)
    H = 150 + (tw + cap + margin) * len(variants)
    page = Image.new("RGB", (W, H), DARK)
    dr = ImageDraw.Draw(page)
    dr.rectangle([0, 0, W, 108], fill=PANEL)
    dr.text((margin, 16), "MR. SHEEP — SMS Composer — texture map sheet",
            font=_font(32), fill=CREAM)
    dr.text((margin, 60),
            "%s — %d variants x %d maps — Painter 11.1.1 — Melodia/Melusina"
            % (date.today().isoformat(), len(variants), len(cols)),
            font=_font(19), fill=ACCENT)

    stats = {}
    for ci, col in enumerate(cols):
        x = margin + (tw + margin) * (ci + 1)
        dr.text((x + 4, 118), col, font=_font(20), fill=CREAM)
    for ri, v in enumerate(variants):
        y = 150 + (tw + cap + margin) * ri
        dr.text((margin + 2, y + tw // 2 - 12), v, font=_font(22), fill=CREAM)
        for ci, col in enumerate(cols):
            x = margin + (tw + margin) * (ci + 1)
            p = per_variant[v].get(col)
            if not p:
                dr.rectangle([x, y, x + tw, y + tw], outline=(80, 70, 96))
                dr.text((x + 8, y + 8), "missing", font=_font(16),
                        fill=(150, 140, 170))
                continue
            img = Image.open(p).convert("RGB")
            small = img.resize((tw, tw), Image.LANCZOS)
            page.paste(small, (x, y))
            px = list(small.convert("L").getdata())
            mean = sum(px) / len(px)
            stats.setdefault(col, []).append(round(mean, 1))
            if mean < 2.0:
                print("WARN all-black?", v, col, mean)
    page.save(args.out)
    print("wrote", args.out)
    for col, vals in stats.items():
        print("%-18s mean-brightness per variant: %s" % (col, vals))


if __name__ == "__main__":
    main()
