#!/usr/bin/env python3
"""Chladni sheets -> mask textures (headless, deterministic).

Rasterizes foundry SVG sheets (nodal geometry only: circles/lines/polylines;
frame, caption and the center-dot marker are skipped) into square grayscale
mask PNGs - white nodal lines on black - for UE import as T_Chladni_* sources.

Usage (from repo root):
    python Tools/chladni_sheets_to_textures.py <sheet_dir> [--out DIR] [--size 1024]

Writes <out>/T_Chladni_<id>_Mask.png + <out>/chladni_textures_manifest.json.
Deterministic: same sheets -> byte-identical PNGs (supersample 2x + Lanczos).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tag(e):
    return e.tag.split("}")[-1]


def num(v, dflt=0.0):
    try:
        return float(v)
    except Exception:
        return dflt


def rasterize(svg_path, size, ss=2):
    px = size * ss
    img = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(img)
    scale = px / 240.0
    for e in ET.parse(svg_path).getroot().iter():
        t = tag(e)
        if t == "circle":
            cx, cy, r = num(e.get("cx")), num(e.get("cy")), num(e.get("r"))
            if r <= 3.0:
                continue  # skip the r=2.6 center-dot marker
            sw = max(1, int(round(num(e.get("stroke-width", "1.8")) * scale)))
            d.ellipse([cx * scale - r * scale - sw / 2, cy * scale - r * scale - sw / 2,
                       cx * scale + r * scale + sw / 2, cy * scale + r * scale + sw / 2],
                      outline=255, width=sw)
        elif t == "line":
            sw = max(1, int(round(num(e.get("stroke-width", "1.6")) * scale)))
            d.line([num(e.get("x1")) * scale, num(e.get("y1")) * scale,
                    num(e.get("x2")) * scale, num(e.get("y2")) * scale],
                   fill=255, width=sw)
        elif t == "polyline":
            pts = []
            for p in e.get("points", "").split():
                a, b = p.split(",")
                pts.append((num(a) * scale, num(b) * scale))
            if len(pts) > 1:
                d.line(pts, fill=255,
                       width=max(1, int(round(num(e.get("stroke-width", "1.8")) * scale))))
    return img.resize((size, size), Image.LANCZOS)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Chladni sheets -> mask textures")
    ap.add_argument("sheet_dir", help="Folder containing Chl_*.svg (+ .json) sheets")
    ap.add_argument("--out", default=os.path.join(ROOT, "Saved", "GeneratedTextures", "Chladni"))
    ap.add_argument("--size", type=int, default=1024)
    args = ap.parse_args(argv)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    entries = []
    for svg in sorted(glob.glob(os.path.join(args.sheet_dir, "Chl_*.svg"))):
        meta = {}
        jp = svg[:-4] + ".json"
        if os.path.exists(jp):
            with open(jp, encoding="utf-8") as fh:
                meta = json.load(fh)
        sheet_id = meta.get("id", os.path.basename(svg)[:-4])
        short = sheet_id[4:] if sheet_id.startswith("Chl_") else sheet_id
        png_name = f"T_Chladni_{short}_Mask.png"
        png_path = os.path.join(out_dir, png_name)
        img = rasterize(svg, args.size)
        img.save(png_path)
        with open(png_path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        entries.append({
            "id": sheet_id,
            "display_name": meta.get("display_name"),
            "rank": meta.get("rank"),
            "family": meta.get("family"),
            "geometry": meta.get("geometry"),
            "png": png_name,
            "size": args.size,
            "sha256": digest,
            "source_svg": os.path.relpath(svg, ROOT).replace("\\", "/"),
        })
        print(f"wrote {png_name}  ({meta.get('display_name')} rank={meta.get('rank')})")

    entries.sort(key=lambda e: -(e["rank"] or 0.0))
    manifest = {
        "generator": "Tools/chladni_sheets_to_textures.py",
        "source": os.path.relpath(args.sheet_dir, ROOT).replace("\\", "/"),
        "count": len(entries),
        "mask_convention": "white nodal lines on black; 240-unit sheet space; 2x supersampled + Lanczos",
        "ue_import_hints": {
            "srgb": False,
            "compression": "Grayscale (G8) or Default linear",
            "lod_group": "World",
            "note": "mask/pattern use; invert or tint in material",
        },
        "entries": entries,
    }
    mpath = os.path.join(out_dir, "chladni_textures_manifest.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"manifest: {mpath}  ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
