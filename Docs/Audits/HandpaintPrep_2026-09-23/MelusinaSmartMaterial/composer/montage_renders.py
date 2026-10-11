#!/usr/bin/env python
"""Montage the Mr. Sheep variant renders into a contact sheet (PIL).

Usage:
  python montage_renders.py --renders <dir of <Name>.png> --params \
      composer_params.json --out <png>
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date

from PIL import Image, ImageDraw, ImageFont

CREAM = (245, 236, 215)
ACCENT = (255, 201, 120)
DARK = (24, 20, 34)
PANEL = (32, 27, 46)


def _font(size):
    for cand in ("C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/segoeui.ttf"):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renders", required=True)
    ap.add_argument("--params", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=int, default=512)
    args = ap.parse_args()

    descs = {}
    if args.params and os.path.isfile(args.params):
        cfg = json.load(open(args.params, encoding="utf-8"))
        for v in cfg.get("variants", []):
            p = v.get("params", {})
            descs[v["name"]] = "%s | glow %.2f / engrave %.2f" % (
                v.get("desc", ""), p.get("score_glow_op", 0),
                p.get("score_engrave_op", 0))

    names = sorted(f[:-4] for f in os.listdir(args.renders)
                   if f.lower().endswith(".png"))
    if not names:
        raise SystemExit("no renders under %s" % args.renders)
    names = [n for n in names if n.lower() != "sheet"]

    cell = args.cell
    cols = min(3, len(names))
    rows = (len(names) + cols - 1) // cols
    margin, cap = 18, 52
    W = margin + cols * (cell + margin)
    H = 150 + rows * (cell + cap + margin)
    page = Image.new("RGB", (W, H), DARK)
    dr = ImageDraw.Draw(page)
    dr.rectangle([0, 0, W, 108], fill=PANEL)
    dr.text((margin, 16), "MR. SHEEP — SMS Composer — rendered variants",
            font=_font(32), fill=CREAM)
    dr.text((margin, 60),
            "%s — Cycles 4.5 headless — Melodia/Melusina"
            % date.today().isoformat(), font=_font(19), fill=ACCENT)
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x = margin + c * (cell + margin)
        y = 130 + r * (cell + cap + margin)
        img = Image.open(os.path.join(args.renders, name + ".png")).convert("RGB")
        page.paste(img.resize((cell, cell), Image.LANCZOS), (x, y))
        dr.text((x + 2, y + cell + 6), name, font=_font(24), fill=CREAM)
        if name in descs:
            dr.text((x + 2, y + cell + 30), descs[name], font=_font(15),
                    fill=(170, 160, 190))
    page.save(args.out)
    print("wrote", args.out, "(%d renders)" % len(names))


if __name__ == "__main__":
    main()
