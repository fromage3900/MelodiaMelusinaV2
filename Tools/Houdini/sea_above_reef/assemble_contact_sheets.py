"""Assemble labeled contact sheets from the Blender render QA output.

Runs in SYSTEM Python (Pillow lives here, not in Blender's interpreter):
  python Tools/Houdini/sea_above_reef/assemble_contact_sheets.py

Reads Saved/Audit/sea_above/renders/{meshes,textures/flat,textures/sphere}/*.png
and writes:
  _SHEET_Meshes.png
  _SHEET_Textures_Flat.png
  _SHEET_Textures_Spheres.png
  _SHEET_OVERVIEW.png   (everything, small cells - the one-look sheet)
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reef_common import PROJECT_ROOT  # noqa: E402

RENDERS = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "renders"
CELL = 264          # thumbnail box (image 256 + label strip)
LABEL_H = 22
COLS = 5
BG = (26, 30, 34)
FG = (215, 220, 216)


def _load_fit(path, box):
    img = Image.open(path).convert("RGB")
    img.thumbnail((box, box), Image.LANCZOS)
    canvas = Image.new("RGB", (box, box), (18, 20, 23))
    canvas.paste(img, ((box - img.width) // 2, (box - img.height) // 2))
    return canvas


def sheet(items, title, out_path, cell=CELL, cols=COLS):
    if not items:
        print(f"[sheets] {title}: nothing to assemble, skipped")
        return
    rows = (len(items) + cols - 1) // cols
    header = 34
    board = Image.new("RGB", (cols * cell + 16, header + rows * (cell + LABEL_H) + 16), BG)
    d = ImageDraw.Draw(board)
    d.text((10, 9), title, fill=FG)
    for idx, (path, label) in enumerate(items):
        x = 8 + (idx % cols) * cell
        y = header + (idx // cols) * (cell + LABEL_H)
        board.paste(_load_fit(path, cell - 8), (x + 4, y))
        d.text((x + 6, y + cell - 4 - LABEL_H + 18), label[:cols * 8], fill=FG)
    board.save(str(out_path), format="PNG")
    print(f"[sheets] {out_path.name} ({len(items)} cells)")


def main():
    groups = {
        "_SHEET_Meshes.png": sorted((RENDERS / "meshes").glob("*.png")) if (RENDERS / "meshes").exists() else [],
        "_SHEET_Textures_Flat.png": sorted((RENDERS / "textures" / "flat").glob("**/*.png")) if (RENDERS / "textures" / "flat").exists() else [],
        "_SHEET_Textures_Spheres.png": sorted((RENDERS / "textures" / "sphere").glob("**/*.png")) if (RENDERS / "textures" / "sphere").exists() else [],
    }
    for name, paths in groups.items():
        items = [(p, p.stem) for p in paths]
        sheet(items, name.replace("_SHEET_", "").replace(".png", ""),
              RENDERS / name)
    # overview: everything small
    all_items = []
    for paths in groups.values():
        all_items += [(p, p.stem) for p in paths]
    sheet(all_items, "REEF OVERVIEW - all renders", RENDERS / "_SHEET_OVERVIEW.png",
          cell=176, cols=6)


if __name__ == "__main__":
    main()
