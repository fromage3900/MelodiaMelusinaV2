#!/usr/bin/env python
"""
Copernicus film tilables - 2K tileable preset surfaces + ORM for film-304-toon-spine.

Why numpy and not COP nodes: this machine runs Houdini 22.0.368 Apprentice
(hou.licenseCategory() = Apprentice), and COP rop writes are capped at
1920x1080 under that license - the verified note in copernicus_surreal_cobble.py
says >=2048 needs Indie/Commercial. The 2048^2 maps therefore follow the lane's
other proven path: the pure numpy+PIL forge used by copernicus_cymatic_parallax.py
(9-map families incl. ORM). The COP graphs remain available for true-COP 2K
cooks once the license allows.

Tiling is guaranteed by construction, not by hope:
- value-noise lattices index with % freq; Worley cells search a 3x3
  neighbourhood with % cells; planks/tiles use mod arithmetic;
- the only sinusoids use integer periods over the image extent;
- normals derive from height via np.roll (wrap-around differencing),
  the exact height_to_normal of copernicus_cymatic_parallax.py;
- the seam metric in the manifest is a smoke check (wrap-edge delta vs the
  largest adjacent-row delta), not the proof - construction is the proof.

Maps per surface (4): BaseColor (sRGB), Normal (BC5), ORM (R=AO,
G=Roughness, B=Metallic - pack order proven in cymatic _assemble), Height.
Seed 20260828 locked (lane seed discipline).

Output: <out>/T_<Surface>_<Map>.png + copernicus_film_tilables_manifest.json
(sha256, seam metric, UE import hints). Verify re-opens every PNG from disk:
PNG magic, exact size, seam metric. Exit 1 on any failure.

Run:
  hython Tools/Houdini/copernicus/copernicus_film_tilables.py --surface all
  hython Tools/Houdini/copernicus/copernicus_film_tilables.py --surface Stone \
      --size 2048 --out G:/film-304-toon-spine/Saved/GeneratedTextures/Copernicus
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SEED = 20260828
DEFAULT_OUT = Path(__file__).resolve().parents[3] / "Saved" / "Audit" / "copernicus_film_tilables"
MAPS = ("BaseColor", "Normal", "ORM", "Height")
UE_IMPORT_HINTS = {
    "BaseColor": {"sRGB": True, "compression": "TC_Default (BC7)"},
    "Normal": {"sRGB": False, "compression": "TC_Normalmap (BC5), WorldNormalMap"},
    "ORM": {"sRGB": False, "compression": "TC_Default linear (BC7): R=AO G=Rough B=Metal"},
    "Height": {"sRGB": False, "compression": "TC_Default linear grayscale"},
}


# ---------- tileable primitives (all modulo-wrapped) ----------

def _fade(t: np.ndarray) -> np.ndarray:
    """Quintic fade - zero 1st/2nd derivative at lattice edges keeps seams smooth."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _value_noise(size: int, freq_x: int, freq_y: int, rng: np.random.Generator) -> np.ndarray:
    """Tileable bilinear value noise on a freq_y x freq_x random lattice."""
    grid = rng.random((freq_y, freq_x)).astype(np.float32)
    ys = np.arange(size, dtype=np.float32) * (freq_y / size)
    xs = np.arange(size, dtype=np.float32) * (freq_x / size)
    y0 = np.floor(ys).astype(np.int32) % freq_y
    x0 = np.floor(xs).astype(np.int32) % freq_x
    y1 = (y0 + 1) % freq_y
    x1 = (x0 + 1) % freq_x
    ty = _fade(ys - np.floor(ys))[:, None]
    tx = _fade(xs - np.floor(xs))[None, :]
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x1)]
    c = grid[np.ix_(y1, x0)]
    d = grid[np.ix_(y1, x1)]
    top = a * (1.0 - tx) + b * tx
    bot = c * (1.0 - tx) + d * tx
    return top * (1.0 - ty) + bot * ty


def _fbm(size: int, freq_x: int, freq_y: int, octaves: int,
         rng: np.random.Generator, persistence: float = 0.5) -> np.ndarray:
    out = np.zeros((size, size), np.float32)
    amp, norm, fx, fy = 1.0, 0.0, freq_x, freq_y
    for _ in range(octaves):
        out += amp * _value_noise(size, fx, fy, rng)
        norm += amp
        amp *= persistence
        fx *= 2
        fy *= 2
    return out / norm


def _worley(size: int, cells: int, rng: np.random.Generator, jitter: float = 0.9):
    """Tileable Worley: (f1, f2) distances in cell units, 3x3 wrapped neighbourhood."""
    pts = (rng.random((cells, cells, 2)).astype(np.float32) - 0.5) * jitter + 0.5
    coords = (np.arange(size, dtype=np.float32) + 0.5) * (cells / size)
    cell = np.floor(coords).astype(np.int32)
    f1 = np.full((size, size), 1e9, np.float32)
    f2 = np.full((size, size), 1e9, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny = (cell + dy) % cells
            nx = (cell + dx) % cells
            oy = pts[ny[:, None], nx[None, :], 1]  # (size,size) outer index
            ox = pts[ny[:, None], nx[None, :], 0]
            py = (cell + dy)[:, None].astype(np.float32) + oy
            px = (cell + dx)[None, :].astype(np.float32) + ox
            d = np.sqrt((py - coords[:, None]) ** 2 + (px - coords[None, :]) ** 2)
            new_f1 = np.minimum(f1, d)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = new_f1
    return f1, f2


def _height_to_normal(height: np.ndarray, strength: float = 2.0) -> np.ndarray:
    """Wrap-around differencing (identical to cymatic lane) - tiles exactly."""
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
    normal = np.dstack((-dx, -dy, np.ones(height.shape, np.float32)))
    length = np.sqrt(np.sum(normal * normal, axis=2) + 1e-9)
    normal = normal / length[:, :, None]
    return np.clip((normal * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)


def _to_u8(x: np.ndarray) -> np.ndarray:
    return np.clip(x * 255.0, 0, 255).astype(np.uint8)


# ---------- surface builders: each returns color/height/rough/metal[/ao] f32 ----------

def build_stone(size: int, rng: np.random.Generator) -> dict:
    """Storybook cobble for MI_Toon_Stone / MI_Toon_CrackedStone / landscape rock."""
    f1, f2 = _worley(size, cells=8, rng=rng)
    mortar = np.clip(1.0 - (f2 - f1) * 3.2, 0.0, 1.0)
    dome = np.clip(1.0 - f1 * 1.35, 0.0, 1.0) ** 1.4
    breakup = _fbm(size, 12, 12, 4, rng)
    stone_mask = 1.0 - mortar
    height = stone_mask * (0.30 + 0.55 * dome + 0.12 * breakup) + mortar * 0.08
    height = np.clip(height, 0.0, 1.0)
    stone_col = np.dstack([
        0.42 + 0.20 * breakup + 0.10 * dome,
        0.41 + 0.19 * breakup + 0.10 * dome,
        0.47 + 0.18 * breakup + 0.09 * dome,
    ]).astype(np.float32)
    mortar_col = np.array([0.20, 0.19, 0.22], np.float32)[None, None, :] * np.ones_like(stone_col)
    color = mortar_col + (stone_col - mortar_col) * stone_mask[..., None]
    rough = 0.86 - 0.24 * stone_mask + 0.06 * (breakup - 0.5)
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_office_carpet(size: int, rng: np.random.Generator) -> dict:
    """Loop-pile carpet squares for MI_Toon_Office_Carpet (4x4 tile grid)."""
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    rib_period = size // 128  # integer -> exact wrap
    rib = 0.5 + 0.5 * np.sin(2.0 * np.pi * y / rib_period)
    fibre = _fbm(size, 64, 64, 3, rng)
    grain = _fbm(size, 16, 16, 4, rng)
    tile = size // 4
    seam_y = (y % tile) < 4.0
    seam_x = (x % tile) < 4.0
    seam = np.broadcast_to(seam_y | seam_x, (size, size)).astype(np.float32)
    height = 0.46 + 0.10 * rib + 0.22 * fibre + 0.10 * grain - 0.28 * seam
    height = np.clip(height, 0.0, 1.0)
    base = np.array([0.30, 0.33, 0.40], np.float32)  # cool office blue-grey
    tint = (0.85 + 0.30 * grain)[..., None]
    color = base[None, None, :] * tint + 0.05 * (fibre - 0.5)[..., None]
    color *= (1.0 - 0.35 * seam)[..., None]
    rough = np.full((size, size), 0.94, np.float32) - 0.05 * rib - 0.04 * grain
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_office_laminate(size: int, rng: np.random.Generator) -> dict:
    """Oak plank floor for MI_Toon_Office_Laminate: 6 rows, offset butt joints."""
    n_planks = 6
    ph = size // n_planks
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    plank = np.minimum((y // ph).astype(np.int32), n_planks - 1)
    jitter = rng.random(n_planks).astype(np.float32)
    jitter_map = jitter[plank]  # per-row plank id -> jitter
    grain = _fbm(size, 4, 64, 4, rng)  # stretched along x
    fine = _fbm(size, 8, 160, 2, rng)
    offs = (rng.random(n_planks) * (size // 2)).astype(np.int32)
    butt = (x.astype(np.int32) + offs[plank]) % (size // 2) < 3
    groove = ((y % ph) < 3.0)
    groove = np.broadcast_to(groove, (size, size)) | butt
    height = 0.55 + 0.16 * grain + 0.06 * fine - 0.40 * groove
    height = np.clip(height, 0.0, 1.0)
    light = np.array([0.74, 0.56, 0.36], np.float32)
    dark = np.array([0.42, 0.29, 0.17], np.float32)
    g = np.clip(0.35 + 0.55 * grain + 0.18 * (jitter_map - 0.5) + 0.10 * fine, 0, 1)
    color = dark[None, None, :] + (light - dark)[None, None, :] * g[..., None]
    color *= (1.0 - 0.45 * groove)[..., None]
    rough = 0.34 + 0.10 * grain - 0.12 * g + 0.30 * groove
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_office_ceiling(size: int, rng: np.random.Generator) -> dict:
    """Mineral tile + metal T-bar for MI_Toon_Office_DropCeiling (ORM demo: metal=1 on bar)."""
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    tile = size // 4
    bar_y = (y % tile) < 8.0
    bar_x = (x % tile) < 8.0
    bar = np.broadcast_to(bar_y | bar_x, (size, size)).astype(np.float32)
    speckle = _fbm(size, 96, 96, 3, rng)
    pin = _fbm(size, 48, 48, 2, rng)
    fibre = _fbm(size, 16, 16, 3, rng)
    height = 0.44 + 0.16 * speckle + 0.08 * fibre + 0.34 * bar
    height = np.clip(height, 0.0, 1.0)
    tile_col = np.array([0.90, 0.89, 0.85], np.float32)
    bar_col = np.array([0.66, 0.67, 0.70], np.float32)
    interior = tile_col[None, None, :] * (0.90 + 0.14 * speckle + 0.06 * fibre)[..., None]
    interior -= 0.12 * (np.clip(0.55 - pin, 0, 1))[..., None]  # pinholes
    color = interior * (1.0 - bar[..., None]) + bar_col[None, None, :] * bar[..., None]
    rough = np.full((size, size), 0.90, np.float32) - 0.10 * speckle
    rough = rough * (1.0 - bar) + 0.40 * bar
    metal = bar.copy()
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=metal)


def build_ground_dirt(size: int, rng: np.random.Generator) -> dict:
    """Soil + sparse pebbles for MI_Toon_Landscape ground."""
    base = _fbm(size, 12, 12, 5, rng)
    detail = _fbm(size, 48, 48, 3, rng)
    f1, _f2 = _worley(size, cells=20, rng=rng)
    pebble_dome = np.clip(1.0 - f1 * 2.1, 0.0, 1.0) ** 1.5
    sparse = np.clip((_fbm(size, 10, 10, 3, rng) - 0.52) * 6.0, 0.0, 1.0)
    pebble = pebble_dome * sparse
    height = 0.30 + 0.28 * base + 0.14 * detail + 0.40 * pebble
    height = np.clip(height, 0.0, 1.0)
    soil_lo = np.array([0.24, 0.18, 0.13], np.float32)
    soil_hi = np.array([0.46, 0.36, 0.25], np.float32)
    soil = soil_lo[None, None, :] + (soil_hi - soil_lo)[None, None, :] * (0.35 + 0.65 * base)[..., None]
    peb_col = np.array([0.55, 0.53, 0.50], np.float32)[None, None, :] * (0.85 + 0.30 * detail)[..., None]
    m = np.clip(pebble * 1.4, 0, 1)[..., None]
    color = soil * (1.0 - m) + peb_col * m
    rough = 0.96 - 0.10 * base - 0.30 * np.clip(pebble, 0, 1)
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


SURFACES = {
    "Stone": build_stone,
    "OfficeCarpet": build_office_carpet,
    "OfficeLaminate": build_office_laminate,
    "OfficeCeiling": build_office_ceiling,
    "GroundDirt": build_ground_dirt,
}


# ---------- assemble + verify ----------

def assemble(m: dict) -> dict:
    """uint8 maps from a builder dict - ORM pack order: R=AO, G=Rough, B=Metal."""
    height = np.clip(m["height"], 0.0, 1.0)
    rough = np.clip(m["rough"], 0.0, 1.0)
    metal = np.clip(m.get("metal", np.zeros_like(height)), 0.0, 1.0)
    ao = 1.0 - height * 0.6
    if "ao" in m:
        ao = np.clip(m["ao"], 0.0, 1.0)
    color_u8 = _to_u8(np.clip(m["color"], 0.0, 1.0))
    return {
        "BaseColor": color_u8,
        "Normal": _height_to_normal(height),
        "ORM": np.dstack([_to_u8(ao), _to_u8(rough), _to_u8(metal)]),
        "Height": np.dstack([_to_u8(height)] * 3),
    }


def seam_metric(img: np.ndarray) -> dict:
    """Wrap-edge row delta vs the largest adjacent-row delta (smoke check)."""
    f = img.astype(np.float32)
    wrap = float(np.mean(np.abs(f[0] - f[-1])))
    adjacent = np.mean(np.abs(np.diff(f, axis=0)), axis=(1, 2))
    amax = float(np.max(adjacent))
    return {"wrap_delta": round(wrap, 3), "max_adjacent_delta": round(amax, 3),
            "ratio": round(wrap / (amax + 1e-6), 3), "ok": bool(wrap <= amax * 1.5 + 2.0)}


def verify_png(path: Path, size: int) -> dict:
    """Re-open from disk: magic, IHDR size, seam metric."""
    raw = path.read_bytes()
    magic_ok = raw[:8] == b"\x89PNG\r\n\x1a\n"
    with Image.open(path) as im:
        w, h = im.size
        arr = np.asarray(im)
    seam = seam_metric(arr)
    ok = magic_ok and w == size and h == size and seam["ok"]
    return {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
            "w": w, "h": h, "magic_ok": magic_ok, "seam": seam, "ok": ok}


def main() -> int:
    ap = argparse.ArgumentParser(description="2K tileable film preset surfaces + ORM (Copernicus lane)")
    ap.add_argument("--surface", default="all", choices=list(SURFACES) + ["all"])
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    size = args.size
    if size < 256 or size & (size - 1):
        print(f"[FILMTIL] size must be a power of two >= 256, got {size}")
        return 1
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(SURFACES) if args.surface == "all" else [args.surface]

    results, ok_all = [], True
    for i, name in enumerate(names):
        rng = np.random.default_rng(args.seed + i * 1009)
        maps = assemble(SURFACES[name](size, rng))
        for map_name in MAPS:
            path = out_dir / f"T_{name}_{map_name}.png"
            Image.fromarray(maps[map_name]).save(str(path))
            v = verify_png(path, size)
            v["surface"] = name
            v["map"] = map_name
            results.append(v)
            ok_all = ok_all and v["ok"]
            print(f"[FILMTIL] {path.name} {v['w']}x{v['h']} "
                  f"seam_ratio={v['seam']['ratio']} ok={v['ok']}")

    manifest = {
        "generator": "Tools/Houdini/copernicus/copernicus_film_tilables.py",
        "seed": args.seed, "size": size, "surfaces": names,
        "license": "Houdini 22.0.368 Apprentice - COP rop writes capped at 1920x1080; "
                   "2K maps use the lane's numpy+PIL path (cymatic precedent)",
        "orm_pack": "R=AO G=Roughness B=Metallic",
        "ue_import_hints": UE_IMPORT_HINTS,
        "out_dir": str(out_dir),
        "files": results, "ok": ok_all,
    }
    mpath = out_dir / "copernicus_film_tilables_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[FILMTIL] wrote {mpath} files={len(results)} ok={ok_all}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
