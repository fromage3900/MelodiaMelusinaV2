"""Kelp sway LUT — the R3 'VAT' texture for the Sea Above reef.

A classic UE FLIPBOOK-style VAT needs per-vertex ID indexing, which OBJ cannot
carry (single UV set). So this ships the honest equivalent: a **sway LUT** the
material samples in World Position Offset —

    U = time  (0..1, LOOP-PERFECT: integer harmonics only)
    V = height along the stalk (matches mesh uv.y: 0 = base, 1 = tip)
    R = lateral offset X, G = lateral offset Z (bend)
    B = bow (secondary forward-bow scalar)

    WPO = (rgb * 2 - 1) * SwayAmplitudeMetres, and
    SwayAmplitude *= (1.0 + 1.5 * User.SeaAbovePulse)  -- pulse-reactive, one writer

Amplitude shaping (h^1.8) is baked in, so the base stays pinned. True per-vertex
VAT (FLIPBOOK, UV1 vertex-ID) is the Engine-license upgrade path — recorded in
the reference doc.

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_KelpSway_LUT.png  512x512 RGB data texture
  _KelpSway_ContactSheet.png   QA sheet (offset curves + a few ghost frames)

Run:  python Tools/Houdini/sea_above_reef/kelp_vat_textures.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

W, H = 512, 512          # U = time frames, V = height rows
SEED = 20260828
AMP_X = 0.30             # peak lateral bend at the tip (fraction of stalk height)
AMP_Z = 0.16
GUST = 0.30              # gust modulation depth


def sway_field(n_t=W, n_h=H, seed=SEED):
    """Return (offset_x, offset_z, bow) each as (n_h, n_t) float arrays in [-1, 1]."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_t, dtype=np.float32) / n_t              # 0..1 time
    h = np.arange(n_h, dtype=np.float32) / (n_h - 1)        # 0..1 height
    shape = h[:, None] ** 1.8                               # base pinned, tip free

    # wind gust envelope: loop-perfect (integer harmonic)
    gust = 1.0 - GUST + GUST * np.sin(2.0 * np.pi * 2.0 * t + 0.6)

    def curve(amps, phases):
        v = np.zeros(n_t, np.float32)
        for a, ph, k in zip(amps, phases, (1, 2, 3)):
            v += a * np.sin(2.0 * np.pi * k * t + ph)
        return v

    # organic-ish bend curves: 3 harmonics each, deterministic phases
    cx = curve((0.62, 0.28, 0.10), (0.0, 1.3, 2.1)) * gust
    cz = curve((0.55, 0.32, 0.13), (1.9, 0.4, 2.8)) * gust
    bow = curve((0.5, 0.5), (0.8, 2.6))

    off_x = AMP_X * shape * cx[None, :]
    off_z = AMP_Z * shape * cz[None, :]
    bow_v = 0.5 * shape * bow[None, :]
    return off_x, off_z, bow_v


def build(seed):
    off_x, off_z, bow = sway_field(seed=seed)
    # pack to [0,1] RGB; leave 1px wrap margin handled by sampler Repeat + exact loop
    r = off_x / (2.0 * AMP_X) + 0.5
    g = off_z / (2.0 * AMP_Z) + 0.5
    b = bow / (1.0) * 0.5 + 0.5
    lut = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    return lut, off_x, off_z


def main():
    out = rc.ensure_out_dir()
    seed = SEED
    if not rc.IS_BLENDER:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        args = ap.parse_args()
        seed = args.seed

    lut, off_x, off_z = build(seed)
    p = rc.save_image(out / "T_SeaAbove_KelpSway_LUT.png", lut, "rgb")
    print(f"[kelp-vat] wrote {p.name} ({W}x{H}, U=time loop, V=height)")

    # QA sheet: LUT + tip trajectory for one loop
    from PIL import Image, ImageDraw
    sheet = Image.new("RGB", (W * 2 + 40, H + 40), (24, 28, 32))
    sheet.paste(Image.fromarray((lut * 255).round().astype(np.uint8), "RGB"), (20, 20))
    d = ImageDraw.Draw(sheet)
    ox, oz = off_x[-1], off_z[-1]   # tip row
    for i in range(W - 1):
        x0 = W + 40 + (ox[i] / (2 * AMP_X) + 0.5) * W
        y0 = 20 + (oz[i] / (2 * AMP_Z) + 0.5) * H
        x1 = W + 40 + (ox[i + 1] / (2 * AMP_X) + 0.5) * W
        y1 = 20 + (oz[i + 1] / (2 * AMP_Z) + 0.5) * H
        d.line([(x0, y0), (x1, y1)], fill=(120, 220, 190))
    d.text((W + 40, 4), "tip trajectory, one loop", fill=(200, 210, 200))
    sheet_path = out / "_KelpSway_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    print(f"[kelp-vat] wrote {sheet_path.name}")

    # loop-continuity check on the U axis ONLY (V=height does not wrap by design:
    # row 0 is the pinned base, row N-1 is the free tip). Wrap step vs local gradient.
    a = lut * 255.0
    wrap_step = float(np.mean(np.abs(a[:, 0, :] - a[:, -1, :])))
    grad = float(np.mean(np.abs(np.diff(a, axis=1))))
    ratio = wrap_step / max(grad, 1e-6)
    print(f"[kelp-vat] U-loop check: wrap step {wrap_step:.3f} levels, "
          f"local gradient {grad:.3f}, ratio {ratio:.3f} "
          f"({'LOOP OK' if ratio < 1.6 else 'LOOP SEAM - investigate'})")

    manifest = rc.write_manifest(
        out / "kelp_vat_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "kelp_vat_textures.py",
            "runtime": "python+numpy+PIL",
            "lut_layout": "U=time (0..1 loop, integer harmonics), V=height (0=base,1=tip)",
            "channels": {"R": "offset_x", "G": "offset_z", "B": "bow scalar"},
            "decode": "WPO = (rgb*2-1) * SwayAmplitudeMetres; "
                      "SwayAmplitude *= (1 + 1.5 * User.SeaAbovePulse)",
            "amplitude_fractions": {"x": AMP_X, "z": AMP_Z, "gust_depth": GUST},
            "upgrade_path": "true per-vertex VAT needs UV1/vertex-ID (Engine-license import)",
        },
        [{"name": "T_SeaAbove_KelpSway_LUT", "path": str(p), "kind": "rgb",
          "size": W, "seed": seed}],
    )
    print(f"[kelp-vat] manifest -> {manifest}")


if __name__ == "__main__":
    main()
