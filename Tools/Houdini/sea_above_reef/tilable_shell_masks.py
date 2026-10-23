"""Tilable shell-pattern masks for LV_SeaAbove_Prototype (Sea Above reef suite).

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_ShellMask_Nautilus.png   log-spiral chamber shells on a 4x4 grid
  T_SeaAbove_ShellMask_Scallop.png    full-bleed periodic rib pattern
  T_SeaAbove_ShellMask_Conch.png      diagonal periodic bands + knobby modulate
  T_SeaAbove_ShellMask_SandDollar.png 5-fold petaloid motif grid
  _ShellMasks_ContactSheet.png        2x2 sheet of all four

Tiling proof: grid motifs are drawn per-cell with parameters taken from a seeded
4x4 lattice (the whole canvas is one period); full-bleed patterns use integer
frequencies + periodic warp. WrappedDraw guards any motif that touches a cell edge.

Pillow is required (vector motif drawing). Run:
  python Tools/Houdini/sea_above_reef/tilable_shell_masks.py
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

rc.require_pil()
from PIL import Image, ImageDraw  # noqa: E402

SIZE = 1024
GRID = 4          # motif cells per axis (canvas = one period)
SEED = 20260828
MASK_ON = 255     # mask value where shell material shows
MASK_EDGE = 128   # soft edge / chamber lines


def _cell_params(seed, gi, gj, count):
    """Per-cell variation drawn from a GRID x GRID lattice (periodic by design)."""
    rng = np.random.default_rng(seed * 1000 + gi * GRID + gj)
    return [rng.uniform(0, 1) for _ in range(count)], rng


def draw_nautilus(draw, cx, cy, scale, rot, rng):
    """Log-spiral shell with chamber septa, fully inside its cell."""
    b = 0.18
    pts = []
    for i in range(160):
        t = i / 159.0 * 5.0 * math.pi
        r = scale * math.exp(b * t) / math.exp(b * 5.0 * math.pi)
        pts.append((cx + r * math.cos(t + rot), cy + r * math.sin(t + rot)))
    draw.line(pts, fill=MASK_ON, width=max(2, int(scale * 0.06)))
    # inner offset spiral + septa
    pts2 = [(cx + (x - cx) * 0.62, cy + (y - cy) * 0.62) for (x, y) in pts]
    draw.line(pts2, fill=MASK_EDGE, width=max(1, int(scale * 0.04)))
    for k in range(7):
        t = k / 7.0 * 5.0 * math.pi
        r = scale * math.exp(b * t) / math.exp(b * 5.0 * math.pi)
        x = cx + r * math.cos(t + rot)
        y = cy + r * math.sin(t + rot)
        draw.line([(cx, cy), (x, y)], fill=MASK_EDGE, width=max(1, int(scale * 0.025)))


def draw_sanddollar(draw, cx, cy, scale, rot, rng):
    """5-fold petaloid marks + rim dots."""
    for k in range(5):
        a = rot + k * (2.0 * math.pi / 5.0)
        px, py = cx + 0.30 * scale * math.cos(a), cy + 0.30 * scale * math.sin(a)
        petal = [(px + 0.16 * scale * math.cos(a) * s + 0.07 * scale * math.sin(a) * q,
                  py + 0.16 * scale * math.sin(a) * s - 0.07 * scale * math.cos(a) * q)
                 for (s, q) in [(-1, -0.4), (-0.4, -0.75), (0.4, -0.75), (1, 0),
                                (0.4, 0.75), (-0.4, 0.75), (-1, 0.4)]]
        draw.polygon(petal, fill=MASK_ON)
    rim = int(scale * 0.48)
    for k in range(24):
        a = k / 24.0 * 2.0 * math.pi
        draw.ellipse([cx + rim * math.cos(a) - 2, cy + rim * math.sin(a) - 2,
                      cx + rim * math.cos(a) + 2, cy + rim * math.sin(a) + 2],
                     fill=MASK_EDGE)


def nautilus_sheet(size, seed):
    cell = size // GRID
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    margin = 0.18
    for gi in range(GRID):
        for gj in range(GRID):
            (rot01, scale01), _ = _cell_params(seed, gi, gj, 2)
            cx = gj * cell + cell // 2
            cy = gi * cell + cell // 2
            scale = cell * (0.5 - margin) * (0.8 + 0.4 * scale01)
            rot = rot01 * 2.0 * math.pi
            draw_nautilus(d, cx, cy, scale, rot, None)
    return np.asarray(img, np.float32) / 255.0


def sanddollar_sheet(size, seed):
    cell = size // GRID
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    for gi in range(GRID):
        for gj in range(GRID):
            (rot01, scale01), _ = _cell_params(seed + 7, gi, gj, 2)
            cx = gj * cell + cell // 2
            cy = gi * cell + cell // 2
            scale = cell * 0.62 * (0.85 + 0.3 * scale01)
            rot = rot01 * 2.0 * math.pi
            draw_sanddollar(d, cx, cy, scale, rot, None)
    return np.asarray(img, np.float32) / 255.0


def scallop_fullbleed(size, seed):
    """Full-bleed rib pattern: periodic stripes with periodic warp + dot rows."""
    rng = np.random.default_rng(seed + 11)
    warp = rc.fbm(size, 8, 3, rng, gain=0.5)
    ribs = rc.tileable_sine(size, 14, 4, phase=0.0, warp=warp, warp_amp=0.9)
    mask = np.clip((ribs - 0.30) / 0.70, 0, 1) ** 1.4
    # hinge dot rows at integer periods
    dots = rc.tileable_sine(size, 14, 4, phase=math.pi / 2, warp=warp, warp_amp=0.9)
    dots_mask = np.clip((dots - 0.82) / 0.18, 0, 1)
    out = np.clip(mask * 0.85 + dots_mask * 0.6, 0, 1)
    return out.astype(np.float32)


def conch_fullbleed(size, seed):
    """Diagonal periodic bands modulated by wrapped knobs (voronoi bulges)."""
    rng = np.random.default_rng(seed + 23)
    bands = rc.tileable_sine(size, 5, 9, phase=0.35)
    knobs = rc.periodic_voronoi_f1(size, 16, 0.9, rng)
    bulge = np.clip(1.0 - knobs * 2.2, 0, 1) ** 1.5
    out = np.clip(bands * 0.65 + bulge * 0.55, 0, 1) ** 1.2
    return out.astype(np.float32)


def main():
    out = rc.ensure_out_dir()
    seed = SEED
    size = SIZE
    if not rc.IS_BLENDER:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        ap.add_argument("--size", type=int, default=SIZE)
        args = ap.parse_args()
        seed, size = args.seed, args.size

    masks = {
        "T_SeaAbove_ShellMask_Nautilus": nautilus_sheet(size, seed),
        "T_SeaAbove_ShellMask_Scallop": scallop_fullbleed(size, seed),
        "T_SeaAbove_ShellMask_Conch": conch_fullbleed(size, seed),
        "T_SeaAbove_ShellMask_SandDollar": sanddollar_sheet(size, seed),
    }

    files = []
    for name, arr in masks.items():
        p = rc.save_image(out / f"{name}.png", arr, "gray")
        files.append({"name": name, "path": str(p), "kind": "gray",
                      "size": int(size), "seed": seed})
        print(f"[shells] wrote {p.name}")

    # 2x2 contact sheet (PIL)
    sheet = Image.new("L", (size * 2, size * 2), 24)
    order = list(masks.values())
    for i, arr in enumerate(order):
        tile = Image.fromarray((arr * 255).round().astype(np.uint8), mode="L")
        sheet.paste(tile, ((i % 2) * size, (i // 2) * size))
    sheet_path = out / "_ShellMasks_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    files.append({"name": sheet_path.stem, "path": str(sheet_path),
                  "kind": "contact_sheet", "size": size * 2, "seed": seed})
    print(f"[shells] wrote {sheet_path.name}")

    manifest = rc.write_manifest(
        out / "shell_masks_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "tilable_shell_masks.py",
            "runtime": "python+PIL",
            "grid": GRID,
            "tiling": "4x4 motif lattice (whole canvas = one period) / integer-freq full-bleed",
        },
        files,
    )
    print(f"[shells] manifest -> {manifest}")


if __name__ == "__main__":
    main()
