"""Assemble 48 silhouette PNGs into a labeled grid contact sheet.

The Blender render step produced panel_NN_SW_Dress_PXX.png for NN=01..48.
This just tiles them 8x6 with white labels (venv python has PIL).
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/silhouette_out")
COLS, ROWS = 8, 6
CELL = 300
MARGIN = 100
W = COLS * CELL + MARGIN * 2
H = ROWS * CELL + MARGIN * 2


def panel_num(name: str) -> int:
    return int("".join(c for c in name if c.isdigit()))


def main():
    pngs = sorted((OUT).glob("panel_*_*.png"),
                  key=lambda p: panel_num(p.stem))
    if len(pngs) != 48:
        raise SystemExit(f"expected 48 panels, found {len(pngs)}")
    sheet = Image.new("RGB", (W, H), (12, 12, 18))
    draw = ImageDraw.Draw(sheet)
    entries = []
    for i, p in enumerate(pngs):
        r, c = divmod(i, COLS)
        x0 = MARGIN + c * CELL
        y0 = MARGIN + r * CELL
        img = Image.open(p).convert("RGBA")
        # pad cell to keep aspect, center
        cell = Image.new("RGBA", (CELL, CELL), (12, 12, 18, 255))
        img.thumbnail((CELL - 16, CELL - 16))
        cell.alpha_composite(img, ((CELL - img.width) // 2, (CELL - img.height) // 2))
        sheet.paste(cell, (x0, y0))
        label = p.stem.replace("panel_NN_", "").replace(".png", "")
        label = p.stem.split("_", 2)[-1]
        draw.text((x0 + 8, y0 + 8), label, fill=(255, 255, 255))
        entries.append({"slot": i, "panel": label, "png": p.name})
    sheet.save(OUT / "SILHOUETTE_GRID_48.png")
    manifest = {
        "schema": "melodia.shorewake_silhouette_grid.v1",
        "grid": {"cols": COLS, "rows": ROWS, "cell": CELL},
        "sheet": "SILHOUETTE_GRID_48.png",
        "panels": entries,
    }
    (OUT / "silhouette_grid_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"grid -> {OUT / 'SILHOUETTE_GRID_48.png'} ({len(entries)} panels)")


if __name__ == "__main__":
    main()