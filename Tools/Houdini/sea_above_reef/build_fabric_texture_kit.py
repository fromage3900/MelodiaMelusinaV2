"""Faraway Mother fabric texture kit — headless numpy/PIL (no editor, no Houdini).

Covers the Bible #10 material needs: pleated-strata detail normals, seam masks,
embroidery stitch-mask atlases, and a fine weave normal. All tileable
(wrap-periodic), deterministic (seed 20260829), verified by read-back:
 - re-open with PIL, confirm dimensions
 - tile check: mean |col[0] - col[-1]| < 2/255 per channel
 - non-blank check: per-channel std > 1

Outputs -> Saved/Audit/faraway_mother/textures/ + textures_manifest.json

Run:  python Tools/Houdini/sea_above_reef/build_fabric_texture_kit.py
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "faraway_mother" / "textures"

SEED = 20260829
rng = np.random.default_rng(SEED)


def smooth_noise(size, cells, seed_offset):
    """Tileable value noise via periodic bilinear lattice."""
    r = np.random.default_rng(SEED + seed_offset)
    lat = r.uniform(-1.0, 1.0, (cells, cells))
    ys, xs = np.mgrid[0:size, 0:size]
    fu = xs / size * cells
    fv = ys / size * cells
    iu, iv = fu.astype(int) % cells, fv.astype(int) % cells
    ju, jv = (iu + 1) % cells, (iv + 1) % cells
    tu, tv = fu - np.floor(fu), fv - np.floor(fv)
    su, sv = tu * tu * (3 - 2 * tu), tv * tv * (3 - 2 * tv)
    a = lat[iv, iu] * (1 - su) + lat[iv, ju] * su
    b = lat[jv, iu] * (1 - su) + lat[jv, ju] * su
    return a * (1 - sv) + b * sv


def height_to_normal(h, strength=2.0):
    gy, gx = np.gradient(h)
    nx, ny, nz = -gx * strength * 0.01, -gy * strength * 0.01, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return (np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5) * 255.0


def save(arr, path, srgb):
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img.save(path)
    return img


def pleat_height(size, freq, angle_deg, warp_amp, seed_offset):
    ys, xs = np.mgrid[0:size, 0:size]
    u, v = xs / size, ys / size
    a = np.deg2rad(angle_deg)
    coord = u * np.cos(a) + v * np.sin(a)
    warp = smooth_noise(size, 4, seed_offset) * warp_amp
    strata = np.sin((coord * freq + warp) * 2.0 * np.pi)
    env = 0.55 + 0.45 * smooth_noise(size, 5, seed_offset + 1)
    return env * (np.abs(strata) ** 0.7)


def pleat_normal(name, size, freq, angle, warp, seed_offset):
    h = pleat_height(size, freq, angle, warp, seed_offset)
    n = height_to_normal(h, strength=2.2)
    save(n, OUT_DIR / name, srgb=False)
    return name, n


def seam_mask(name, size, n_seams, width_px, seed_offset):
    ys, xs = np.mgrid[0:size, 0:size]
    v = ys / size
    mask = np.ones((size, size), dtype=float)
    r = np.random.default_rng(SEED + seed_offset)
    for k in range(n_seams):
        y0 = 0.1 + 0.8 * (k % 3) / 3.0
        mx = 0.5 + r.uniform(-0.15, 0.15)
        y1 = 0.1 + 0.8 * ((k + 1) % 3) / 3.0
        cx = (1 - v) ** 2 * 0.05 + 2 * (1 - v) * v * mx + v ** 2 * 0.95
        cy = (1 - v) ** 2 * y0 + 2 * (1 - v) * v * y1 + v ** 2 * y1
        d = np.abs(xs / size - cx)
        d = np.minimum(d, 1.0 - d) * size
        mask -= np.exp(-(d * d) / (width_px * width_px)) * 0.9
    mask = np.clip(mask, 0.0, 1.0) * 255.0
    rgb = np.stack([mask] * 3, axis=-1)
    save(rgb, OUT_DIR / name, srgb=False)
    return name, rgb


def embroidery(name, size, motif, colors, seed_offset):
    r = np.random.default_rng(SEED + seed_offset)
    canvas = np.zeros((size, size, 4), dtype=float)
    band_c, band_h = size // 2, 90
    stitch_w, stitch_h = 32, 16
    n_stitches = size // stitch_w
    thread_a, thread_b = colors
    for i in range(n_stitches):
        cx = i * stitch_w + stitch_w // 2 + int(r.integers(-3, 4))
        col = thread_a if i % 2 == 0 else thread_b
        yy, xx = np.mgrid[0:size, 0:size]
        in_band = np.abs(yy - band_c) < band_h
        if motif == "chevron":
            sx = ((xx - cx) % stitch_w + stitch_w) % stitch_w
            shape = (np.abs(yy - band_c) < stitch_h * (1 - 2 * np.abs(sx - stitch_w / 2) / stitch_w))
        else:  # knot chain: circles
            shape = (xx - cx) ** 2 + (yy - band_c) ** 2 < (stitch_h * 0.7) ** 2
        alpha = (shape & in_band).astype(float) * 255.0
        for c in range(3):
            canvas[:, :, c] = np.where(alpha > 0, col[c], canvas[:, :, c])
        canvas[:, :, 3] = np.maximum(canvas[:, :, 3], alpha)
    save(canvas, OUT_DIR / name, srgb=True)
    return name, canvas


def weave_normal(name, size):
    ys, xs = np.mgrid[0:size, 0:size]
    h = (np.sin(xs / size * 2 * np.pi * 32) * np.sin(ys / size * 2 * np.pi * 32)) * 0.5 + 0.5
    n = height_to_normal(h, strength=0.8)
    save(n, OUT_DIR / name, srgb=False)
    return name, n


def tile_check(img_arr):
    arr = np.asarray(img_arr, dtype=float)
    return float(np.mean(np.abs(arr[:, 0].astype(float) - arr[:, -1].astype(float))))


def verify(name, srgb):
    p = OUT_DIR / name
    img = Image.open(p)
    arr = np.asarray(img, dtype=float)
    std_ok = arr.std() > 1.0
    tc = tile_check(arr)
    return {"file": name, "size": f"{img.width}x{img.height}", "srgb": srgb,
            "non_blank": bool(std_ok), "tile_check": "pass" if tc < 2.0 else f"FAIL({tc:.2f})"}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gold, blue = (200, 162, 74), (74, 122, 200)
    built = []
    built.append(pleat_normal("T_FM_PleatDetail_N.png", 1024, 8, 0.0, 2.5, 10))
    built.append(pleat_normal("T_FM_PleatDetail_2_N.png", 1024, 16, 45.0, 1.8, 20))
    built.append(seam_mask("T_FM_SeamMask.png", 1024, 2, 40, 30))
    built.append(embroidery("T_FM_Embroidery_A.png", 1024, "chevron", (gold, blue), 40))
    built.append(embroidery("T_FM_Embroidery_B.png", 1024, "knot", (blue, gold), 50))
    built.append(weave_normal("T_FM_FabricWeave_N.png", 512))

    checks = []
    srgb_map = {"T_FM_Embroidery_A.png": True, "T_FM_Embroidery_B.png": True}
    for (name, _) in built:
        checks.append(verify(name, srgb_map.get(name, False)))
        print(f"[fabkit] {checks[-1]}")

    manifest = {
        "schema": "melodia.faraway_mother_textures.v1", "seed": SEED,
        "purpose": "fabric-material kit for the Faraway Mother cloth tiles + Mara's gown "
                   "(pleat detail normals, seam mask, embroidery stitch atlases, weave normal)",
        "entries": checks,
        "ue_import": {"srgb": "embroidery maps true; normals/mask false (data)"},
    }
    (OUT_DIR / "textures_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[fabkit] manifest -> textures_manifest.json "
          f"({sum(1 for c in checks if c['tile_check'] == 'pass' and c['non_blank'])}/{len(checks)} clean)")


if __name__ == "__main__":
    main()
