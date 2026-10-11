"""Shared helpers for the Sea Above reef texture suite (BS_GodFile / Houdini lane).

Design rules (AGENTS.md evidence culture):
- Deterministic: every cook takes a seed; call order is part of the seed contract, so
  never parallelise cooks from one rng.
- Tileable: all noise is lattice-periodic (period divides size); all motif drawing is
  either confined to grid cells or drawn through WrappedDraw (9-offset wrap).
- Manifest-driven: cooks write PNGs + a sha256 manifest; nothing is "shipped" by prose.

Runtimes:
- Primary: plain Python (numpy + Pillow) - the proven path on this workstation
  (see Tools/Houdini/experiment_wool_lab.py).
- Fallback: headless Blender (blender --background --python <script>) for the
  numpy-only scripts. Blender path saves via bpy with Non-Color colorspace and a
  vertical flip (bpy pixel rows are bottom-up), giving byte-identical PNG content to
  the PIL path for authored values. Pillow-required scripts guard with require_pil().

All authored colour values are sRGB-space and are written verbatim; data maps
(height/normal/masks) must be imported in UE with sRGB=false.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"
IS_BLENDER = "bpy" in sys.modules


def ensure_out_dir():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR


def require_pil():
    try:
        import PIL  # noqa: F401
        import PIL.Image  # noqa: F401
        import PIL.ImageDraw  # noqa: F401
        import PIL.ImageFilter  # noqa: F401
    except ImportError:
        raise SystemExit(
            "Pillow is required for this script (motif drawing). "
            "Run with plain Python, not Blender: python Tools/Houdini/sea_above_reef/<script>.py"
        )


# ---------------------------------------------------------------------------
# Periodic (tileable) noise
# ---------------------------------------------------------------------------

def periodic_value_noise(size, period, rng):
    """Tileable value noise on a size x size float32 image.

    The lattice is period x period random values; period MUST divide size.
    Returns float32 in [0, 1].
    """
    size = int(size)
    period = int(period)
    if size % period != 0:
        raise ValueError(f"period {period} must divide size {size}")
    lat = rng.random((period, period)).astype(np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    fx = xs * (period / size)
    fy = ys * (period / size)
    x0 = np.floor(fx).astype(np.int32) % period
    y0 = np.floor(fy).astype(np.int32) % period
    x1 = (x0 + 1) % period
    y1 = (y0 + 1) % period
    tx = (fx - np.floor(fx)).astype(np.float32)
    ty = (fy - np.floor(fy)).astype(np.float32)
    sx = tx * tx * (3.0 - 2.0 * tx)
    sy = ty * ty * (3.0 - 2.0 * ty)
    v00 = lat[y0, x0]
    v01 = lat[y0, x1]
    v10 = lat[y1, x0]
    v11 = lat[y1, x1]
    top = v00 + (v01 - v00) * sx
    bot = v10 + (v11 - v10) * sx
    return top + (bot - top) * sy


def fbm(size, base_period, octaves, rng, gain=0.5):
    """Tileable fBm. base_period must divide size; octaves double the period."""
    acc = np.zeros((size, size), np.float32)
    amp = 1.0
    total = 0.0
    period = int(base_period)
    for _ in range(int(octaves)):
        acc += amp * periodic_value_noise(size, period, rng)
        total += amp
        amp *= gain
        period *= 2
        if period > size:
            break
    return acc / max(total, 1e-6)


def periodic_voronoi_f1(size, period, jitter, rng):
    """Tileable Voronoi F1 distance. Lattice points jittered; neighbour search is
    wrapped (mod period) so the field tiles exactly. Returns float32, normalized
    roughly to [0, 1] by dividing by the cell size.
    """
    size = int(size)
    period = int(period)
    if size % period != 0:
        raise ValueError(f"period {period} must divide size {size}")
    cell = size / period
    jr = rng.random((period, period, 2)).astype(np.float32) * jitter + (1.0 - jitter) * 0.5
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    fx = xs / cell
    fy = ys / cell
    cx = np.floor(fx).astype(np.int32)
    cy = np.floor(fy).astype(np.int32)
    best = np.full((size, size), np.float32(1e9))
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx = (cx + ox) % period
            gy = (cy + oy) % period
            px = (gx + jr[gy, gx, 0]) * cell
            py = (gy + jr[gy, gx, 1]) * cell
            dx = px - xs
            dy = py - ys
            # toroidal wrap: a point just across the tile edge must be measured
            # at its true wrapped distance, not ~size (this band-bug is what the
            # ingest seam metric caught on caustics/conch)
            dx = (dx + size * 0.5) % size - size * 0.5
            dy = (dy + size * 0.5) % size - size * 0.5
            d = np.sqrt(dx * dx + dy * dy)
            best = np.minimum(best, d)
    return best / cell


def tileable_sine(size, freq_x, freq_y, phase=0.0, warp=None, warp_amp=0.0):
    """Tileable sine field with integer frequencies; optional periodic warp."""
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    w = 0.0
    if warp is not None:
        w = warp.astype(np.float32) * warp_amp
    t = (xs * freq_x + ys * freq_y) / float(size) * 2.0 * np.pi + phase + w
    return (np.sin(t) * 0.5 + 0.5).astype(np.float32)


# ---------------------------------------------------------------------------
# Normal map from height (wrap-around Sobel, OpenGL Y+ convention)
# ---------------------------------------------------------------------------

def normal_from_height(height, strength=2.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -dx * strength
    ny = -dy * strength  # OpenGL Y+
    nz = np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    r = nx / ln * 0.5 + 0.5
    g = ny / ln * 0.5 + 0.5
    b = nz / ln * 0.5 + 0.5
    return np.stack([r, g, b], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------
# Saving (PIL primary, bpy fallback)
# ---------------------------------------------------------------------------

_KIND_TO_MODE = {"gray": "L", "rgb": "RGB", "rgba": "RGBA"}


def save_image(path, arr, kind):
    """Save a float array (0..1) as PNG. Values are written verbatim (sRGB-space
    authored values for colour; raw data for masks). Returns the written path.
    """
    arr = np.clip(np.asarray(arr, np.float32), 0.0, 1.0)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if IS_BLENDER:
        _save_bpy(path, arr, kind)
    else:
        _save_pil(path, arr, kind)
    return path


def _save_pil(path, arr, kind):
    from PIL import Image
    mode = _KIND_TO_MODE[kind]
    data = (arr * 255.0).round().astype(np.uint8)
    Image.fromarray(data, mode=mode).save(str(path), format="PNG", optimize=False)


def _save_bpy(path, arr, kind):
    import bpy
    h, w = arr.shape[:2]
    if kind == "gray":
        rgba = np.dstack([arr, arr, arr, np.ones_like(arr)])
    elif kind == "rgb":
        rgba = np.dstack([arr, np.ones_like(arr[..., :1])])
    else:
        rgba = arr
    rgba = rgba[::-1]  # bpy pixel rows are bottom-up
    name = path.stem
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    try:
        img.colorspace_settings.name = "Non-Color"  # pass-through: values written verbatim
    except Exception:
        pass
    flat = rgba.reshape(-1).astype(np.float32)
    try:
        img.pixels.foreach_set(flat)
    except Exception:
        img.pixels[:] = flat.tolist()
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


# ---------------------------------------------------------------------------
# Manifests
# ---------------------------------------------------------------------------

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(path, schema, seed, params, files):
    payload = {
        "schema": schema,
        "seed": seed,
        "params": params,
        "files": files,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


# ---------------------------------------------------------------------------
# Wrapped drawing (PIL only) - every primitive is drawn at 9 wrapped offsets
# ---------------------------------------------------------------------------

class WrappedDraw:
    """Draw primitives that may cross canvas edges, wrapping them seamlessly."""

    def __init__(self, size, background=0):
        require_pil()
        from PIL import Image, ImageDraw
        self.size = size
        self.img = Image.new("L", (size, size), background)
        self.draw = ImageDraw.Draw(self.img)

    def _shift(self, pts, dx, dy):
        return [(x + dx, y + dy) for (x, y) in pts]

    def _each_offset(self, fn, pts, **kw):
        s = self.size
        for dx in (-s, 0, s):
            for dy in (-s, 0, s):
                fn(self._shift(pts, dx, dy), **kw)

    def polygon(self, pts, fill=None, outline=None, width=1):
        self._each_offset(lambda p, **k: self.draw.polygon(p, **k), pts,
                          fill=fill, outline=outline, width=width)

    def ellipse(self, box_pts, fill=None, outline=None, width=1):
        # box_pts: [x0, y0, x1, y1] treated as 2 points
        self._each_offset(lambda p, **k: self.draw.ellipse([p[0][0], p[0][1], p[1][0], p[1][1]], **k),
                          box_pts, fill=fill, outline=outline, width=width)

    def line(self, pts, fill=None, width=1):
        self._each_offset(lambda p, **k: self.draw.line(p, **k), pts, fill=fill, width=width)

    def result(self):
        return self.img
