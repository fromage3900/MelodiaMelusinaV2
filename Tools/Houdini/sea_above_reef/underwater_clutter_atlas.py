"""Underwater clutter: decal/sprite atlas + tilable floor-debris mask (Sea Above).

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_Clutter_Atlas.png   4x4 atlas of 512px RGBA decal sprites
  T_SeaAbove_ClutterFloor_Mask.png 1024 tilable scattered-debris mask
  _Clutter_Sprites_ContactSheet.png labeled sheet (individual sprites too)

Sprites (each deterministic from the suite seed):
  00 spiral shell   01 scallop      02 clam pair    03 starfish
  04 sea glass      05 pebble       06 barnacle cluster  07 seaweed sprig
  08 coral twig     09 bottle shard 10 bubble trio  11 driftwood twig

All sprites are authored as RGBA (straight alpha, 2x supersampled). The atlas is
the import target; individual sprites are QA copies. The floor mask is lattice-
periodic with wrapped ellipse placement -> seam-free.

Pillow is required. Run:
  python Tools/Houdini/sea_above_reef/underwater_clutter_atlas.py
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

SPRITE = 512
ATLAS_N = 4
SIZE = 1024          # floor mask
SEED = 20260828
SHELL_RGB = (214, 196, 168)
ACCENT_RGB = (150, 190, 185)
GLASS_RGB = (168, 216, 206)
WEED_RGB = (96, 148, 120)


def _new_sprite():
    img = Image.new("RGBA", (SPRITE, SPRITE), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _finish(img):
    return img.resize((SPRITE // 2, SPRITE // 2), Image.LANCZOS)


def spiral_shell(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    b = 0.16
    # body silhouette
    pts = []
    for i in range(200):
        t = i / 199.0 * 6.0 * math.pi
        r = 8 + 150 * math.exp(b * t) / math.exp(b * 6.0 * math.pi)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    d.line(pts, fill=SHELL_RGB + (255,), width=34, joint="curve")
    # lip + aperture
    d.ellipse([cx - 42, cy - 52, cx + 54, cy + 46], fill=SHELL_RGB + (255,))
    d.ellipse([cx - 26, cy - 36, cx + 38, cy + 30], fill=(60, 52, 44, 255))
    # bands
    for k in range(5):
        t = (k + 0.5) / 5.0 * 6.0 * math.pi
        r = 8 + 150 * math.exp(b * t) / math.exp(b * 6.0 * math.pi)
        d.line([(cx + r * math.cos(t) - 18, cy + r * math.sin(t) - 18),
                (cx + r * math.cos(t) + 18, cy + r * math.sin(t) + 18)],
               fill=ACCENT_RGB + (220,), width=6)
    return _finish(img)


def scallop(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2 + 90
    R = 170
    for k in range(9):
        a0 = math.pi + (k / 8.0) * math.pi
        a1 = math.pi + ((k + 0.7) / 8.0) * math.pi
        mid = (a0 + a1) / 2
        p0 = (cx + R * math.cos(a0), cy + R * math.sin(a0))
        p1 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
        d.polygon([(cx, cy), p0, (cx + R * 1.02 * math.cos(mid), cy + R * 1.02 * math.sin(mid)), p1],
                  fill=SHELL_RGB + (255,))
    d.ellipse([cx - 26, cy - 30, cx + 26, cy + 22], fill=(90, 76, 62, 255))
    return _finish(img)


def clam_pair(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    for s, dy in ((1, -34), (-1, 34)):
        d.polygon([(cx - 150 * s, cy + dy), (cx + 150 * s, cy + dy),
                   (cx + 110 * s, cy + dy - 66 * s), (cx - 110 * s, cy + dy - 66 * s)],
                  fill=SHELL_RGB + (255,))
        for k in range(5):
            x = cx - 120 * s + k * 55 * s
            d.line([(x, cy + dy - 6 * s), (x + 30 * s, cy + dy - 58 * s)],
                   fill=(150, 132, 108, 255), width=5)
    return _finish(img)


def starfish(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    arms, R, r = 5, 190, 60
    pts = []
    for i in range(arms * 2):
        a = i * math.pi / arms - math.pi / 2
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(224, 160, 120, 255))
    for k in range(14):
        a = k / 14.0 * 2 * math.pi
        d.ellipse([cx + 90 * math.cos(a) - 6, cy + 90 * math.sin(a) - 6,
                   cx + 90 * math.cos(a) + 6, cy + 90 * math.sin(a) + 6],
                  fill=(180, 118, 88, 255))
    return _finish(img)


def sea_glass(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    rng = np.random.default_rng(seed + 5)
    for k in range(3):
        px = cx - 120 + k * 120 + rng.uniform(-14, 14)
        s = rng.uniform(0.7, 1.05)
        shard = [(px - 62 * s, cy + 30 * s), (px + 10 * s, cy - 66 * s),
                 (px + 70 * s, cy + 6 * s), (px + 26 * s, cy + 78 * s)]
        d.polygon(shard, fill=GLASS_RGB + (210,))
        d.polygon([(px - 30 * s, cy + 12 * s), (px + 6 * s, cy - 30 * s),
                   (px + 34 * s, cy + 10 * s)], fill=(230, 248, 244, 160))
    return _finish(img)


def pebbles(seed):
    img, d = _new_sprite()
    rng = np.random.default_rng(seed + 6)
    for k in range(7):
        px = 70 + rng.uniform(0, SPRITE - 140)
        py = 90 + rng.uniform(0, SPRITE - 180)
        rx = 34 + rng.uniform(0, 46)
        ry = rx * rng.uniform(0.6, 0.9)
        g = int(120 + rng.uniform(0, 60))
        d.ellipse([px - rx, py - ry, px + rx, py + ry],
                  fill=(g, g + 12, g + 6, 255))
    return _finish(img)


def barnacle_cluster(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    rng = np.random.default_rng(seed + 7)
    for k in range(9):
        px = cx + rng.uniform(-120, 120)
        py = cy + rng.uniform(-100, 120)
        r = rng.uniform(18, 40)
        d.ellipse([px - r, py - r, px + r, py + r], outline=(232, 228, 216, 255), width=9)
        d.ellipse([px - r * 0.4, py - r * 0.4, px + r * 0.4, py + r * 0.4],
                  fill=(70, 84, 88, 255))
    return _finish(img)


def seaweed_sprig(seed):
    img, d = _new_sprite()
    base = (SPRITE / 2, SPRITE - 40)
    for k, lean in enumerate((-70, -20, 40, 95)):
        pts = []
        for i in range(30):
            t = i / 29.0
            x = base[0] + lean * t * t
            y = base[1] - (SPRITE - 110) * t
            w = 26 * (1.0 - 0.75 * t) * math.sin(math.pi * min(1.0, t * 1.15))
            pts.append((x, y, max(2, w)))
        for i in range(len(pts) - 1):
            d.line([pts[i][:2], pts[i + 1][:2]], fill=WEED_RGB + (235,), width=int(pts[i][2]))
    return _finish(img)


def coral_twig(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE - 120, SPRITE - 60

    def branch(x, y, ang, ln, w, depth):
        if depth == 0 or ln < 14:
            return
        x2, y2 = x + ln * math.cos(ang), y - ln * math.sin(ang)
        d.line([(x, y), (x2, y2)], fill=(226, 148, 128, 255), width=max(2, int(w)))
        branch(x2, y2, ang + 0.42, ln * 0.72, w * 0.72, depth - 1)
        branch(x2, y2, ang - 0.30, ln * 0.76, w * 0.72, depth - 1)

    branch(cx, cy, math.pi / 2, 120, 17, 5)
    return _finish(img)


def bottle_shard(seed):
    img, d = _new_sprite()
    cx, cy = SPRITE / 2, SPRITE / 2
    d.polygon([(cx - 90, cy + 60), (cx - 40, cy - 90), (cx + 96, cy - 40),
               (cx + 60, cy + 84)], fill=(150, 178, 168, 200))
    d.polygon([(cx - 40, cy + 20), (cx - 6, cy - 44), (cx + 52, cy - 6)],
              fill=(214, 236, 230, 150))
    return _finish(img)


def bubbles(seed):
    img, d = _new_sprite()
    for (bx, by, r) in ((SPRITE / 2, SPRITE / 2, 96), (SPRITE / 2 + 120, SPRITE / 2 - 90, 52),
                        (SPRITE / 2 - 110, SPRITE / 2 - 120, 34)):
        d.ellipse([bx - r, by - r, bx + r, by + r], outline=(210, 240, 236, 200), width=7)
        d.ellipse([bx - r * 0.55, by - r * 0.55, bx - r * 0.15, by - r * 0.15],
                  fill=(240, 252, 250, 120))
    return _finish(img)


def driftwood(seed):
    img, d = _new_sprite()
    d.line([(70, 400), (220, 300), (330, 320), (470, 210)], fill=(146, 118, 92, 255), width=26)
    d.line([(220, 300), (260, 220)], fill=(120, 96, 74, 255), width=14)
    for t in (0.3, 0.55, 0.8):
        x = 70 + t * 380
        y = 400 - t * 180
        d.line([(x, y), (x + 26, y - 8)], fill=(104, 84, 66, 255), width=6)
    return _finish(img)


def clutter_floor_mask(size, seed):
    """Tilable scattered-debris mask: lattice jitter positions + noise specks."""
    rng = np.random.default_rng(seed + 31)
    wd = rc.WrappedDraw(size, background=0)
    n = 12  # lattice: 12x12 jittered placements per tile -> whole canvas tiles
    cell = size / n
    for gy in range(n):
        for gx in range(n):
            if rng.uniform() > 0.42:
                continue
            px = (gx + rng.uniform(0.15, 0.85)) * cell
            py = (gy + rng.uniform(0.15, 0.85)) * cell
            rx = rng.uniform(3.0, 11.0)
            ry = rx * rng.uniform(0.5, 0.95)
            v = int(rng.uniform(90, 210))
            wd.ellipse([(px - rx, py - ry), (px + rx, py + ry)], fill=v)
    arr = np.asarray(wd.result(), np.float32) / 255.0
    specks = rc.fbm(size, 128, 2, np.random.default_rng(seed + 32), gain=0.55)
    speck_mask = np.clip((specks - 0.86) / 0.14, 0, 1)
    return np.clip(arr + speck_mask * 0.5, 0, 1).astype(np.float32)


def main():
    out = rc.ensure_out_dir()
    seed = SEED
    if not rc.IS_BLENDER:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        ap.add_argument("--size", type=int, default=SIZE, help="floor mask size")
        args = ap.parse_args()
        seed, size = args.seed, args.size
    else:
        size = SIZE

    sprites = [
        spiral_shell(seed), scallop(seed), clam_pair(seed), starfish(seed),
        sea_glass(seed), pebbles(seed), barnacle_cluster(seed), seaweed_sprig(seed),
        coral_twig(seed), bottle_shard(seed), bubbles(seed), driftwood(seed),
    ]
    names = ["SpiralShell", "Scallop", "ClamPair", "Starfish", "SeaGlass", "Pebbles",
             "BarnacleCluster", "SeaweedSprig", "CoralTwig", "BottleShard", "Bubbles",
             "Driftwood"]

    files = []
    for img, name in zip(sprites, names):
        p = out / f"T_SeaAbove_Clutter_{name}.png"
        img.save(str(p), format="PNG")
        files.append({"name": p.stem, "path": str(p), "kind": "rgba_sprite",
                      "size": img.size[0], "seed": seed})

    # atlas 4x4 (sprites are 256px after supersample-downscale)
    s = sprites[0].size[0]
    atlas = Image.new("RGBA", (s * ATLAS_N, s * ATLAS_N), (0, 0, 0, 0))
    for i, img in enumerate(sprites):
        atlas.paste(img, ((i % ATLAS_N) * s, (i // ATLAS_N) * s))
    atlas_path = out / "T_SeaAbove_Clutter_Atlas.png"
    atlas.save(str(atlas_path), format="PNG")
    files.append({"name": atlas_path.stem, "path": str(atlas_path), "kind": "rgba_atlas",
                  "size": atlas.size[0], "grid": [ATLAS_N, ATLAS_N],
                  "cell_px": s, "sprites": names, "seed": seed})
    print(f"[clutter] atlas -> {atlas_path.name} ({atlas.size[0]}px, {len(sprites)} sprites)")

    # labeled QA contact sheet (gray bg so alpha reads)
    sheet = Image.new("RGB", (s * ATLAS_N, s * ATLAS_N), (38, 44, 48))
    for i, img in enumerate(sprites):
        sheet.paste(img, ((i % ATLAS_N) * s, (i // ATLAS_N) * s), img)
    sheet_path = out / "_Clutter_Sprites_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    files.append({"name": sheet_path.stem, "path": str(sheet_path),
                  "kind": "contact_sheet", "size": s * ATLAS_N, "seed": seed})

    # floor mask
    floor = clutter_floor_mask(size, seed)
    fp = rc.save_image(out / "T_SeaAbove_ClutterFloor_Mask.png", floor, "gray")
    files.append({"name": fp.stem, "path": str(fp), "kind": "gray",
                  "size": int(size), "seed": seed, "tiling": "lattice-periodic"})
    print(f"[clutter] floor mask -> {fp.name}")

    manifest = rc.write_manifest(
        out / "clutter_atlas_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "underwater_clutter_atlas.py",
            "runtime": "python+PIL",
            "sprite_supersample": 2,
            "alpha": "straight, RGBA",
            "floor_mask_tiling": "12x12 lattice jitter + periodic speck noise",
        },
        files,
    )
    print(f"[clutter] manifest -> {manifest}")


if __name__ == "__main__":
    main()
