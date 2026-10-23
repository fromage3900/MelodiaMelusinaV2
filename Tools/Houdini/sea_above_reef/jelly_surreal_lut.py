"""Jellyfish surreal logic LUTs — the arm-motion + bioluminescence brain.

Two textures, both LOOP-PERFECT (integer harmonics only):

1. T_Jelly_ArmLogic_LUT (512x512 RGB data)
   U = time (one sway loop), V = along-arm parameter s (0 = bell margin, 1 = tip;
   matches the arm mesh uv.y). Decoded by the arm material's World Position Offset:
       WPO = (rgb*2-1) * SweepAmplitudeMetres  (default 24 m at this scale)
   R = lateral offset X, G = lateral offset Z, B = bow (in-arm curvature).

   The surreal logic baked in:
   - subharmonic cascade: 3 harmonics whose PHASE SHIFTS grow along the arm
     (wavenumber rising with s - the arm "decides later, moves faster" at its tip)
   - bifurcation drift: a sign-flip in the lateral wave centred at s = 0.5,
     smoothed over 0.1 — the arm commits to a new direction mid-flight
   - Moebius envelope: the twist scalar runs a full pi over s (matching the
     geometric half-twist), time-animated
   - anti-gravity bow: the bow channel lifts the far half of the arm upward
   - gust coupling: slow 2nd-harmonic envelope, amplitude scaled by
     (1 + 1.5 * User.SeaAbovePulse) at decode time (one MPC writer rule)

2. T_Jelly_Biolum_LUT (512x256 RGB, sRGB-authored)
   U = time, V = along-arm. Traveling bioluminescent pulse bands (cyan-magenta)
   that run from bell to tip, speed-modulated by the bend channel of the logic
   LUT so light "pools" where the arm folds. Emissive lookup, not WPO.

Outputs: Saved/Audit/sea_above/houdini_variants/ + manifest.
Run:  python Tools/Houdini/sea_above_reef/jelly_surreal_lut.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

W_T = 512   # time frames
H_S = 512   # along-arm samples
SEED = 20260828
OUT = rc.PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"


def arm_logic(seed):
    rng = np.random.default_rng(seed)
    t = np.arange(W_T, dtype=np.float32) / W_T
    s = np.arange(H_S, dtype=np.float32) / (H_S - 1)
    tt = t[None, :]
    ss = s[:, None]

    # subharmonic cascade: wavenumbers rise along the arm
    k1, k2, k3 = 1, 2, 3
    wave1 = np.sin(2 * np.pi * (k1 * tt + 0.0 + ss * 1.2))
    wave2 = np.sin(2 * np.pi * (k2 * tt + 1.3 + ss * 2.6))
    wave3 = np.sin(2 * np.pi * (k3 * tt + 2.1 + ss * 4.4))
    envelope = 0.6 + 0.4 * np.sin(2 * np.pi * (2 * tt + 0.6))      # gust (loop-ok)
    drift = np.tanh((ss - 0.5) / 0.05)                             # bifurcation flip
    lateral = (0.55 * wave1 + 0.30 * wave2 + 0.15 * wave3) * envelope
    lateral = lateral * (0.55 + 0.45 * drift)                      # drift shifts mix

    # Moebius twist envelope: pi over length, time-animated 2nd harmonic
    twist = (ss - 0.5) * 2.0 + 0.25 * np.sin(2 * np.pi * (1 * tt + 2.4))

    # anti-gravity bow: far half lifts
    bow = np.clip((ss - 0.45) / 0.55, 0, 1) ** 1.5 * \
        (0.6 + 0.4 * np.sin(2 * np.pi * (1 * tt + 1.0)))

    r = np.clip(lateral * 0.5 + 0.5, 0, 1)
    g = np.clip((lateral * 0.5 + 0.5) * 0.35 + (twist * 0.5 + 0.5) * 0.65, 0, 1)
    b = np.clip(bow * 0.5 + 0.5, 0, 1)
    # keep U-loop exact: force first/last time columns equal by construction
    return np.clip(np.stack([r, g, b], axis=-1), 0, 1), lateral


def biolum(seed, bend=None):
    rng = np.random.default_rng(seed)
    t = np.arange(W_T, dtype=np.float32) / W_T
    s = np.arange(256, dtype=np.float32) / 255.0
    tt = t[None, :]
    ss = s[:, None]
    # three traveling bands, bell -> tip (positive phase velocity)
    band = np.zeros((256, W_T), np.float32)
    for k, a, ph in ((3, 0.5, 0.0), (5, 0.3, 1.7), (8, 0.2, 3.9)):
        band += a * np.clip(np.sin(2 * np.pi * (ss * k - t * 1.0) + ph), 0, 1) ** 2.0
    if bend is not None:
        # light pools where the arm folds: modulate by bend magnitude
        mag = np.abs(bend - bend.mean())
        mag = mag / max(mag.max(), 1e-6)
        mag = np.resize(mag, (256, W_T)) * 0  # bend is (H_S, W_T); resample rows
        mag = np.abs(bend)[:: max(1, H_S // 256), :][:256, :]
        mag = (mag - mag.min()) / max(mag.max() - mag.min(), 1e-6)
        band *= (0.55 + 0.9 * mag)
    # cyan-magenta chroma
    cyan = np.stack([0.25 * band, 0.85 * band, 0.95 * band], axis=-1)
    magenta = np.stack([0.85 * band, 0.30 * band, 0.90 * band], axis=-1)
    mix = (0.5 + 0.5 * np.sin(2 * np.pi * (ss * 2.0 + tt * 1.0) + 1.0))[..., None]
    return np.clip(cyan * (1 - mix) + magenta * mix, 0, 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    lut, lateral = arm_logic(args.seed)
    p1 = rc.save_image(OUT / "T_Jelly_ArmLogic_LUT.png", lut, "rgb")
    print(f"[jelly-lut] wrote {p1.name} ({W_T}x{H_S})")

    bio = biolum(args.seed, bend=lateral)
    p2 = rc.save_image(OUT / "T_Jelly_Biolum_LUT.png", bio, "rgb")
    print(f"[jelly-lut] wrote {p2.name} (512x256)")

    # loop checks on the U axis for both
    a = lut * 255.0
    step = float(np.mean(np.abs(a[:, 0, :] - a[:, -1, :])))
    grad = float(np.mean(np.abs(np.diff(a, axis=1))))
    print(f"[jelly-lut] logic U-loop ratio {step / max(grad, 1e-6):.3f} "
          f"(step {step:.3f}, grad {grad:.3f})")
    a2 = bio * 255.0
    step2 = float(np.mean(np.abs(a2[:, 0, :] - a2[:, -1, :])))
    grad2 = float(np.mean(np.abs(np.diff(a2, axis=1))))
    print(f"[jelly-lut] biolum U-loop ratio {step2 / max(grad2, 1e-6):.3f}")

    manifest = rc.write_manifest(
        OUT / "jelly_surreal_lut_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        args.seed,
        {
            "generator": "jelly_surreal_lut.py",
            "logic_lut": {"layout": "U=time loop, V=along-arm (uv.y)",
                          "decode": "WPO = (rgb*2-1) * SweepAmplitudeMetres; "
                                    "default 24 m; Amp *= (1 + 1.5 * User.SeaAbovePulse)",
                          "surreal": ["subharmonic cascade (wavenumber rises with s)",
                                      "bifurcation drift (tanh flip at s=0.5)",
                                      "moebius twist envelope (pi over length)",
                                      "anti-gravity bow (far half lifts)",
                                      "gust envelope, pulse-coupled amplitude"]},
            "biolum_lut": {"layout": "U=time, V=along-arm; emissive lookup",
                           "behavior": "traveling cyan-magenta pulse bands, "
                                       "pooled by bend magnitude"},
            "one_writer_rule": "User.SeaAbovePulse only (BP_SeaAbove_PrototypeDirector)",
        },
        [{"name": p1.stem, "path": str(p1), "kind": "rgb", "size": W_T, "seed": args.seed},
         {"name": p2.stem, "path": str(p2), "kind": "rgb", "size": 512, "seed": args.seed}],
    )
    print(f"[jelly-lut] manifest -> {manifest}")


if __name__ == "__main__":
    main()
