"""Sea Above texture suite v2 — R5 cook for the reef.

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_Droplet_Atlas.png       2048x2048, 4x4 grid of 512 cells, luminance
                                     mask encoded in RGB (no alpha), row-major
                                     frames 0..15, one upward droplet birth-to-
                                     death; Niagara flipbook target (P0 plan)
  T_SeaAbove_Membrane_Reveal.png     1024 centered radial reveal mask (non-wrapping)
  T_SeaAbove_Membrane_Ripple_N.png   1024 radial ripple normal, OpenGL Y+ (non-wrapping)
  T_SeaAbove_WetRock_Albedo.png      1024 tilable wet-basalt colour
  T_SeaAbove_WetRock_Normal.png      1024 tilable normal from the wet-rock height
  T_SeaAbove_WetRock_Wetline.png     1024 tilable crack+lowland darkening mask
  T_SeaAbove_BarnacleCrust_Mask.png  1024 tilable two-scale cluster-ring mask
  T_SeaAbove_PulseBand_LUT.png       1024x64 PC00..PC11 pastel ramp strip (sRGB)
  T_SeaAbove_Foam_Mask.png           1024 tilable foam streak noise (stretch)
  T_SeaAbove_Sediment_Ramp.png       64x1024 vertical sediment ramp strip (stretch)
  _TextureSuiteV2_ContactSheet.png
  texture_suite_v2_manifest.json     schema melodia.sea_above_reef_textures.v1

Non-square outputs are spec-pinned: the atlas and both strips ignore --size; the
square tilables honour it. Every 2-axis tiling target here is lattice-periodic
(toroidal), so ingest_reef_textures.py must report [OK ] on both axes for all of
them; the atlas, the centered radials and the strips are excluded there.

Run:  python Tools/Houdini/sea_above_reef/texture_suite_v2.py
"""

import argparse
import colorsys
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

rc.require_pil()
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

SEED = 20260828
SIZE = 1024
ATLAS_PX = 2048
CELL_PX = 512
GRID = 4
FRAMES = GRID * GRID
SUPER = 2                       # atlas supersample factor
STRIP_W, STRIP_H = 1024, 64     # pulse band LUT (horizontal strip, vertical constant)
RAMP_W, RAMP_H = 64, 1024       # sediment ramp (vertical strip)

# 12 chromatic steps PC00..PC11 — same hue table as blender_lit_sphere_render.py
PC_HUES = {
    0: ("C", 0.000), 1: ("Cs", 0.083), 2: ("D", 0.167), 3: ("Ds", 0.250),
    4: ("E", 0.333), 5: ("F", 0.417), 6: ("Fs", 0.500), 7: ("G", 0.583),
    8: ("Gs", 0.667), 9: ("A", 0.750), 10: ("As", 0.833), 11: ("B", 0.917),
}


def _ss01(v):
    v = min(1.0, max(0.0, v))
    return v * v * (3.0 - 2.0 * v)


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return (x * x * (3.0 - 2.0 * x)).astype(np.float32)


# ---------------------------------------------------------------------------
# T_SeaAbove_Droplet_Atlas — P0-serving droplet flipbook (cell-local, not a wrap)
# ---------------------------------------------------------------------------

def _teardrop_pts(cx, cy, R, H, ctrl, n=28):
    """Teardrop outline: round bottom bulb (semicircle), tapered top apex."""
    pts = []
    for k in range(n + 1):                     # right rim -> bottom -> left rim
        th = math.pi * k / n
        pts.append((cx + R * math.cos(th), cy + R * math.sin(th)))

    def quad(p0, pc, p1):
        out = []
        for k in range(1, n + 1):
            u = k / n
            out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * pc[0] + u ** 2 * p1[0],
                        (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * pc[1] + u ** 2 * p1[1]))
        return out

    apex = (cx, cy - H)
    pts += quad((cx - R, cy), (cx - ctrl, cy - H * 0.55), apex)
    pts += quad(apex, (cx + ctrl, cy - H * 0.55), (cx + R, cy))
    return pts


def _droplet_frame(seed, i, draw_px):
    """One flipbook cell as an L-mode PIL image at supersampled draw_px."""
    rng = np.random.default_rng(seed + 101 + i)   # per-frame stream, fixed order
    t = i / (FRAMES - 1.0)
    S = draw_px
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)

    cx = S * 0.5 + rng.uniform(-0.012, 0.012) * S
    cy = S * (0.64 - 0.36 * (t ** 1.3))           # birth low -> death high, ease-in
    grow = _ss01(t / 0.45)
    R = S * (0.085 + 0.075 * grow)
    if t > 0.8:
        R *= 1.0 - 0.35 * (t - 0.8) / 0.2
    H = R * (1.15 + 0.85 * t)                     # taper lengthens as it rises
    ctrl = R * (0.95 - 0.45 * t)

    fade_in = _ss01(t / 0.18)
    fade_out = 1.0 - _ss01((t - 0.78) / 0.22)
    body = int(216 * (0.35 + 0.65 * fade_in) * fade_out)

    # motion smear on later frames: trailing ghosts + streak below the body
    smear = max(0.0, (t - 0.5) / 0.5)
    if smear > 0.0 and body > 0:
        for off, val in ((1.4, 0.32), (2.4, 0.16)):
            gp = _teardrop_pts(cx, cy + off * R, R * 1.04, H * 1.06, ctrl)
            d.polygon(gp, fill=int(body * val * smear))
        d.line([(cx, cy + R * 0.9), (cx, cy + R * 2.3)],
               fill=int(body * 0.22 * smear), width=max(2, int(R * 0.35)))

    pts = _teardrop_pts(cx, cy, R, H, ctrl)
    d.polygon(pts, fill=body)
    if body > 0:
        d.line(pts + [pts[0]], fill=int(body * 0.5), joint="curve",
               width=max(2, int(S * 0.006)))
        # soft internal highlight, offset up-left inside the bulb
        hr_x, hr_y = R * 0.20, R * 0.26
        hx, hy = cx - R * 0.28, cy - R * 0.10
        d.ellipse([hx - hr_x, hy - hr_y, hx + hr_x, hy + hr_y],
                  fill=min(255, body + 55))
    return img.filter(ImageFilter.GaussianBlur(radius=S * 0.008))


def _droplet_atlas(seed):
    """4x4 atlas of 512 cells, frame i at row=i//4 col=i%4; mask in RGB, no alpha."""
    cell = CELL_PX * SUPER
    atlas = Image.new("L", (CELL_PX * GRID, CELL_PX * GRID), 0)
    for i in range(FRAMES):
        fr = _droplet_frame(seed, i, cell).resize((CELL_PX, CELL_PX), Image.LANCZOS)
        atlas.paste(fr, ((i % GRID) * CELL_PX, (i // GRID) * CELL_PX))
    a = np.asarray(atlas, np.float32) / 255.0
    return np.dstack([a, a, a]).astype(np.float32)


# ---------------------------------------------------------------------------
# T_SeaAbove_Membrane_Reveal / _Ripple_N — centered radial (non-wrapping by design)
# ---------------------------------------------------------------------------

def _membrane_reveal(seed, size):
    rng = np.random.default_rng(seed + 201)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    dx, dy = xs - size * 0.5, ys - size * 0.5
    r = np.sqrt(dx * dx + dy * dy)
    r_n = np.clip(r / (size * 0.5), 0.0, 1.3)
    theta = np.arctan2(dy, dx)
    breakup = rc.fbm(size, 16, 4, rng, gain=0.55)
    rings = (0.5 + 0.5 * np.sin(r_n * math.pi * 7.0)) ** 1.4      # concentric soft rings
    wedges = (0.5 + 0.5 * np.cos(theta * 12.0 + 0.7)) ** 1.6      # radial wedges
    reveal = r_n * (0.42 + 0.58 * rings) * (0.70 + 0.48 * wedges)
    reveal += (breakup - 0.5) * 0.34
    reveal *= np.clip(r_n / 0.10, 0.0, 1.0)                        # hard zero at centre
    return np.clip(reveal, 0.0, 1.0).astype(np.float32)


def _membrane_ripple_height(seed, size):
    rng = np.random.default_rng(seed + 202)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    dx, dy = xs - size * 0.5, ys - size * 0.5
    r = np.sqrt(dx * dx + dy * dy)
    warp = rc.fbm(size, 16, 3, rng, gain=0.55)
    h = 0.5 + 0.5 * np.sin(r / (size * 0.5) * math.pi * 2.0 * 8.0 + (warp - 0.5) * 1.7)
    return h.astype(np.float32)


# ---------------------------------------------------------------------------
# T_SeaAbove_WetRock_* — tilable wet-basalt suite
# ---------------------------------------------------------------------------

def _wetrock(seed, size):
    rng = np.random.default_rng(seed + 301)
    forms = rc.fbm(size, 8, 5, rng, gain=0.55)          # large basalt forms
    detail = rc.fbm(size, 64, 3, rng, gain=0.6)         # medium grain
    crack_a = 1.0 - np.abs(rc.fbm(size, 16, 4, rng, gain=0.5) - 0.5) * 2.0
    crack_b = 1.0 - np.abs(rc.fbm(size, 64, 3, rng, gain=0.5) - 0.5) * 2.0
    cracks = np.clip(crack_a ** 6.0 + (crack_b ** 9.0) * 0.7, 0.0, 1.0)
    f1 = rc.periodic_voronoi_f1(size, 128, 0.85, rng)
    speck = np.clip(1.0 - f1 * 6.5, 0.0, 1.0) ** 1.8    # lighter mineral speckles

    h = forms * 0.62 + detail * 0.23 - cracks * 0.45    # cracks carve down
    h = (h - h.min()) / (h.max() - h.min())
    lowland = np.clip((0.45 - forms) / 0.40, 0.0, 1.0)

    g = 0.16 + 0.115 * forms                            # grays 40..70
    g = g * (1.0 - 0.30 * lowland)                      # lowland darkening
    g = g + speck * 0.20                                # mineral speckles lighten
    g = np.clip(g * (1.0 - cracks * 0.80), 0.0, 1.0)    # cracks darkest
    albedo = np.dstack([g * 0.965, g, g * 1.07]).astype(np.float32)  # cool tint

    wetline = np.clip(cracks * 0.95 + lowland * 0.55, 0.0, 1.0) ** 1.15
    return albedo, rc.normal_from_height(h, strength=3.0), wetline.astype(np.float32)


# ---------------------------------------------------------------------------
# T_SeaAbove_BarnacleCrust_Mask — tilable two-scale cluster rings
# ---------------------------------------------------------------------------

def _barnacle_crust(seed, size):
    rng = np.random.default_rng(seed + 401)
    f1a = rc.periodic_voronoi_f1(size, 8, 0.9, rng)     # coarse clusters
    f1b = rc.periodic_voronoi_f1(size, 32, 0.85, rng)   # fine barnacle dots

    def band(f, c, w):
        return _smoothstep(1.0 - np.abs(f - c) / w)

    rings = band(f1a, 0.30, 0.10) * 0.85 + band(f1a, 0.52, 0.12) * 0.55
    dots = np.clip(1.0 - f1b * 4.2, 0.0, 1.0) ** 2.2
    return np.clip(rings + dots * 0.75, 0.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# T_SeaAbove_PulseBand_LUT — 12 pastel pitch-class bands, sRGB ramp strip
# ---------------------------------------------------------------------------

def _pulse_band_lut():
    band_w = STRIP_W / 12.0
    blend = 16.0 / band_w                       # ~16px soft edge, in band units
    xs = (np.arange(STRIP_W, dtype=np.float32) + 0.5) / band_w
    k = np.clip(np.floor(xs).astype(np.int32), 0, 11)
    f = xs - np.floor(xs)
    s = np.clip((f - 0.5) / blend + 0.5, 0.0, 1.0)
    s = (s * s * (3.0 - 2.0 * s)).astype(np.float32)
    # dusty Nikki-adjacent pastel: sat 0.40 (0.35..0.45 band), val 0.92
    cols = np.asarray(
        [colorsys.hsv_to_rgb(PC_HUES[p][1], 0.40, 0.92) for p in range(12)], np.float32)
    row = cols[k] * (1.0 - s)[:, None] + cols[np.minimum(k + 1, 11)] * s[:, None]
    return np.tile(row[None, :, :], (STRIP_H, 1, 1)).astype(np.float32)


# ---------------------------------------------------------------------------
# Stretch: T_SeaAbove_Foam_Mask (tilable) + T_SeaAbove_Sediment_Ramp (strip)
# ---------------------------------------------------------------------------

def _foam_mask(seed, size):
    rng = np.random.default_rng(seed + 501)
    base = rc.fbm(size, 32, 4, rng, gain=0.55)
    streak_src = rc.fbm(size, 64, 3, rng, gain=0.6)
    ys = np.arange(size)
    # compress the torus in y (periodic): horizontal foam streaks, still seamless
    sheared = streak_src[(ys * 4) % size, :]
    fine = rc.fbm(size, 128, 2, rng, gain=0.55)
    foam = 0.50 * base + 0.62 * sheared + 0.18 * fine
    foam = np.clip((foam - 0.70) * 3.0, 0.0, 1.0) ** 1.25
    return foam.astype(np.float32)


def _rect_value_noise(h, w, py, px, rng):
    """Tileable value noise on an h x w strip (rect lattice; local helper)."""
    lat = rng.random((py, px)).astype(np.float32)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    fy, fx = ys * (py / h), xs * (px / w)
    y0 = np.floor(fy).astype(np.int32) % py
    x0 = np.floor(fx).astype(np.int32) % px
    y1, x1 = (y0 + 1) % py, (x0 + 1) % px
    ty, tx = fy - np.floor(fy), fx - np.floor(fx)
    sy, sx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    top = lat[y0, x0] + (lat[y0, x1] - lat[y0, x0]) * sx
    bot = lat[y1, x0] + (lat[y1, x1] - lat[y1, x0]) * sx
    return (top + (bot - top) * sy).astype(np.float32)


def _sediment_ramp(seed):
    rng = np.random.default_rng(seed + 601)
    ys = (np.arange(RAMP_H, dtype=np.float32) / (RAMP_H - 1))[:, None, None]
    dark = np.array([0.16, 0.15, 0.13], np.float32)
    light = np.array([0.82, 0.77, 0.66], np.float32)
    col = dark * (1.0 - ys) + light * ys                       # dark silt -> pale sand
    mottle = (_rect_value_noise(RAMP_H, RAMP_W, 128, 8, rng) * 0.65
              + _rect_value_noise(RAMP_H, RAMP_W, 256, 16, rng) * 0.35)
    col = col * (1.0 + (mottle[:, :, None] - 0.5) * 0.22)
    bands = 0.5 + 0.5 * np.sin(ys * math.pi * 2.0 * 9.0)       # faint settlement bands
    col = col * (1.0 + (bands - 0.5) * 0.06)
    return np.clip(col, 0.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# build() — house contract: name -> (array, kind)
# ---------------------------------------------------------------------------

def build(seed, size):
    albedo, normal, wetline = _wetrock(seed, size)
    return {
        "T_SeaAbove_Droplet_Atlas": (_droplet_atlas(seed), "rgb"),
        "T_SeaAbove_Membrane_Reveal": (_membrane_reveal(seed, size), "gray"),
        "T_SeaAbove_Membrane_Ripple_N": (
            rc.normal_from_height(_membrane_ripple_height(seed, size), strength=4.0), "rgb"),
        "T_SeaAbove_WetRock_Albedo": (albedo, "rgb"),
        "T_SeaAbove_WetRock_Normal": (normal, "rgb"),
        "T_SeaAbove_WetRock_Wetline": (wetline, "gray"),
        "T_SeaAbove_BarnacleCrust_Mask": (_barnacle_crust(seed, size), "gray"),
        "T_SeaAbove_PulseBand_LUT": (_pulse_band_lut(), "rgb"),
        "T_SeaAbove_Foam_Mask": (_foam_mask(seed, size), "gray"),
        "T_SeaAbove_Sediment_Ramp": (_sediment_ramp(seed), "rgb"),
    }


EXTRA_META = {
    "T_SeaAbove_Droplet_Atlas": {"grid": [GRID, GRID], "cell_px": CELL_PX,
                                 "frames": FRAMES, "frame_order": "row-major",
                                 "tiling": "atlas (cell-local, non-wrapping)"},
    "T_SeaAbove_Membrane_Reveal": {"tiling": "centered radial, non-wrapping by design"},
    "T_SeaAbove_Membrane_Ripple_N": {"tiling": "centered radial, non-wrapping by design"},
    "T_SeaAbove_PulseBand_LUT": {"bands": 12, "tiling": "1D ramp strip, CLAMP U"},
    "T_SeaAbove_Sediment_Ramp": {"tiling": "1D ramp strip, CLAMP V"},
}


def main():
    out = rc.ensure_out_dir()
    seed, size = SEED, SIZE
    if not rc.IS_BLENDER:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        ap.add_argument("--size", type=int, default=SIZE,
                        help="square tilables; atlas/strips are spec-pinned")
        args = ap.parse_args()
        seed, size = args.seed, args.size

    images = build(seed, size)
    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(out / f"{name}.png", arr, kind)
        entry = {"name": name, "path": str(p), "kind": kind,
                 "size": int(arr.shape[1]), "seed": seed}
        if arr.shape[0] != arr.shape[1]:
            entry["height"] = int(arr.shape[0])
        if name in EXTRA_META:
            entry.update(EXTRA_META[name])
        files.append(entry)
        print(f"[suite-v2] wrote {p.name} ({arr.shape[1]}x{arr.shape[0]})")

    # contact sheet (QA only; never a tiling target)
    thumb, cols = 256, 5
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb, rows * thumb), (30, 34, 38))
    for i, (name, (arr, kind)) in enumerate(images.items()):
        a = np.clip(arr, 0, 1)
        rgb = np.dstack([a, a, a]) if kind == "gray" else a[..., :3]
        im = Image.fromarray((rgb * 255).round().astype(np.uint8), "RGB")
        sheet.paste(im.resize((thumb, thumb), Image.LANCZOS),
                    ((i % cols) * thumb, (i // cols) * thumb))
    sheet_path = out / "_TextureSuiteV2_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    files.append({"name": sheet_path.stem, "path": str(sheet_path),
                  "kind": "contact_sheet", "size": cols * thumb, "seed": seed})
    print(f"[suite-v2] wrote {sheet_path.name}")

    manifest = rc.write_manifest(
        out / "texture_suite_v2_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "texture_suite_v2.py",
            "runtime": "python+PIL",
            "tiling": "lattice-periodic toroidal for 2-axis targets; atlas / centered "
                      "radials / strips non-wrapping by design",
            "droplet_atlas": "4x4 grid of 512px cells, row-major frames 0..15, "
                             "grayscale mask encoded in RGB (no alpha); Niagara "
                             "flipbook target (P0 droplet plan)",
            "pulse_band_lut": "12 pastel pitch-class bands PC00..PC11 (~16px soft "
                              "edges), import sRGB, CLAMP U in UE",
        },
        files,
    )
    print(f"[suite-v2] manifest -> {manifest}")


if __name__ == "__main__":
    main()
