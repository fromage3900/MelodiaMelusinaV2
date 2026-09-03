#!/usr/bin/env python
"""Per-panel ID map for the Shorewake dress (48 flat colors, luminance-ordered).

Rasterizes the 48-slot mesh's faces into UV space with a unique flat color per
panel (SW_Dress_P01..P48). This is the Substance hand-paint masking map:
one merged texture set + ID color extraction == per-panel control.

Inputs : bake/night_pkg_2026-08-31/face_uv_data.npz (from slotted export)
Outputs: bake/night_pkg_2026-08-31/
           T_DressShorewake_PanelID_4K.png      (sRGB ID map)
           T_DressShorewake_PanelID_legend.png  (swatch sheet)
           panel_id_manifest.json               (colors + coverage census)

Run: python Tools/Houdini/sea_above_reef/shorewake_panel_id_map.py
"""
import colorsys
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[3]
PKG = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "bake" / "night_pkg_2026-08-31"
RES = 4096
SEED = 20260831

data = np.load(PKG / "face_uv_data.npz")
loop_uv = data["loop_uv"].astype(np.float64)
loop_total = data["loop_total"]
mat_idx = data["material_index"]
slot_names = json.loads(str(data["slot_names"]))
n_slots = len(slot_names)

# --- 48 unique colors, luminance-ordered P01 -> P48 ---------------------------
rng = np.random.default_rng(SEED)
colors = []
while len(colors) < n_slots:
    h = rng.random()
    s = 0.55 + 0.45 * rng.random()
    v = 0.55 + 0.45 * rng.random()
    rgb = tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v))
    if all(sum(abs(a - b) for a, b in zip(rgb, prev)) > 90 for prev in colors):
        colors.append(rgb)
lum = [0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for c in colors]
order = np.argsort(lum)  # dark -> light
colors = [colors[i] for i in order]
slot_colors = {slot_names[i]: colors[i] for i in range(n_slots)}

# --- rasterize -----------------------------------------------------------------
# loops are contiguous per polygon; build per-face loop slices
starts = np.concatenate([[0], np.cumsum(loop_total)[:-1]])
img = Image.new("RGB", (RES, RES), (0, 0, 0))
draw = ImageDraw.Draw(img)
for f in range(len(loop_total)):
    s, e = starts[f], starts[f] + loop_total[f]
    uvf = loop_uv[s:e]
    pts = [(float(u) * (RES - 1), float((1.0 - v)) * (RES - 1)) for u, v in uvf]
    draw.polygon(pts, fill=slot_colors[slot_names[mat_idx[f]]])

id_png = PKG / "T_DressShorewake_PanelID_4K.png"
img.save(id_png)

# --- coverage census -----------------------------------------------------------
arr = np.asarray(img)
flat = arr.reshape(-1, 3)
cov = {}
for i, name in enumerate(slot_names):
    c = np.array(slot_colors[name], dtype=np.uint8)
    px = int(np.count_nonzero(np.all(flat == c, axis=1)))
    cov[name] = {"color": list(slot_colors[name]), "px": px,
                 "pct": round(100.0 * px / flat.shape[0], 3)}
unassigned_pct = round(100.0 * int(np.count_nonzero(np.all(flat == 0, axis=1))) / flat.shape[0], 3)

# --- legend sheet ---------------------------------------------------------------
LEG_W, CELL_H = 1400, 64
LEG_H = 60 + n_slots * CELL_H + 30
leg = Image.new("RGB", (LEG_W, LEG_H), (24, 24, 28))
ld = ImageDraw.Draw(leg)
try:
    font = ImageFont.truetype("arial.ttf", 26)
    font_s = ImageFont.truetype("arial.ttf", 20)
except Exception:
    font = ImageFont.load_default()
    font_s = font
ld.text((20, 12), "Shorewake Dress Panel ID Legend — SW_Dress_P01..P48 (luminance-ordered)",
        fill=(240, 240, 240), font=font)
for i, name in enumerate(slot_names):
    y = 60 + i * CELL_H
    ld.rectangle([20, y, 80, y + CELL_H - 10], fill=slot_colors[name])
    ld.text((100, y + 12), f"{name}   RGB{slot_colors[name]}   {cov[name]['pct']}%",
            fill=(220, 220, 220), font=font_s)
leg.save(PKG / "T_DressShorewake_PanelID_legend.png")

manifest = {
    "schema": "melodia.shorewake_panel_id.v1",
    "seed": SEED,
    "resolution": RES,
    "slot_count": n_slots,
    "slot_names": slot_names,
    "colors": {k: list(v) for k, v in slot_colors.items()},
    "coverage": cov,
    "unassigned_black_pct": unassigned_pct,
    "mapping_source": "face_uv_data.npz (frozen 48-slot blend, slotted export)",
    "outputs": ["T_DressShorewake_PanelID_4K.png", "T_DressShorewake_PanelID_legend.png"],
}
(PKG / "panel_id_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
zero_cov = [k for k, v in cov.items() if v["px"] == 0]
print("ID_MAP " + json.dumps({
    "slots": n_slots, "zero_coverage_panels": zero_cov,
    "unassigned_black_pct": unassigned_pct,
    "min_pct": min(v["pct"] for v in cov.values()),
    "max_pct": max(v["pct"] for v in cov.values()),
}))
