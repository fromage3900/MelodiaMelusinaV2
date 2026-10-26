r"""build_faraway_fog_flipbooks.py -- W8: silk-fog bank + god-ray flipbooks (procedural, exactly periodic). spike: true

NOT a Pyro simulation (recorded in the canon doc): fields are sums of integer-wavenumber sinusoids, so they tile in x/y and loop in
time EXACTLY by construction (frame 64 == frame 0), deterministic, no hou. A Pyro/VDB version stays a later upgrade.
  fog_flipbook.png   8x8 cells of 128^2 (1024^2), R = density (soft fog banks, drift), G = lacy filament mask, B = height-fade bias
  godray_flipbook.png 4x4 cells of 256^2, R = shaft intensity (radial-from-top streaks, slow sway), G/B = 0 (single-channel mask)
Gate: range, x/y wrap seam vs interior step, temporal loop exact, motion, determinism (hash), shaft angular contrast.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayFog_20261026"


def h32(*a):
    x = 2166136261
    for v in a:
        x = ((x ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 4294967295.0


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def waves(n_waves, kmax, seed, tmax):
    W = []
    for i in range(n_waves):
        kx = int(h32(seed, i, 1) * (2 * kmax + 1)) - kmax
        ky = int(h32(seed, i, 2) * (2 * kmax + 1)) - kmax
        if kx == 0 and ky == 0:
            kx = 1
        w = int(h32(seed, i, 3) * (2 * tmax + 1)) - tmax
        amp = 1.0 / (1.0 + 0.55 * math.hypot(kx, ky))
        W.append((kx, ky, w, h32(seed, i, 4) * 2 * math.pi, amp))
    return W


def field(W, res, t01):
    x = np.arange(res) / res
    X, Y = np.meshgrid(x, x)
    f = np.zeros((res, res))
    for kx, ky, w, ph, amp in W:
        f += amp * np.sin(2 * math.pi * (kx * X + ky * Y + w * t01) + ph)
    return f


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    N, CF = 64, 128
    Wf, Wl = waves(26, 6, 3900, 1), waves(30, 14, 3901, 2)
    fog = np.zeros((N + 1, CF, CF, 3))
    for k in range(N + 1):
        t = k / N
        a = field(Wf, CF, t); b = field(Wl, CF, t)
        d = np.clip(0.5 + 0.9 * a / max(np.abs(a).max(), 1e-9) * 0.5, 0, 1) ** 1.6
        lace = np.clip(1.0 - np.abs(b) / (np.abs(b).max() * 0.22), 0, 1) ** 2
        yy = np.arange(CF)[:, None] / CF
        fog[k] = np.stack([d, lace * d, np.broadcast_to(0.5 + 0.5 * np.cos(2 * math.pi * yy), (CF, CF))], -1)
    atlas = np.zeros((8 * CF, 8 * CF, 3), np.uint8)
    for k in range(64):
        r, c = k // 8, k % 8
        atlas[r * CF:(r + 1) * CF, c * CF:(c + 1) * CF] = (np.clip(fog[k], 0, 1) * 255 + 0.5).astype(np.uint8)
    png(OUT / "fog_flipbook.png", atlas)

    # god rays: shafts radiate from the top-centre; angular noise (integer harmonics) swaying slowly, radial falloff
    CG, GN = 256, 16
    gx = (np.arange(CG) / CG - 0.5)
    X, Y = np.meshgrid(gx, np.arange(CG) / CG)
    ang = np.arctan2(X, Y + 0.12)                       # 0 = straight down from the source above the cell
    rad = np.hypot(X, Y + 0.12)
    Wg = [(int(2 + h32(3902, i, 1) * 9), int(h32(3902, i, 2) * 3) - 1, h32(3902, i, 3) * 2 * math.pi, 1.0 / (1 + 0.15 * i)) for i in range(12)]
    def gframe(t):
        s_ = np.zeros((CG, CG))
        for m, w, ph, amp in Wg:
            s_ += amp * np.sin(m * ang * 3.0 + 2 * math.pi * w * t + ph)
        s_ = np.clip(0.5 + 0.5 * s_ / 3.0, 0, 1) ** 2.2        # fixed normaliser (not per-frame max) so frames stay comparable and loop exactly
        return s_ * np.clip(1.05 - rad * 1.1, 0, 1) * np.clip(1.0 - np.abs(X) * 2.0 * 0.9, 0, 1)
    gr = np.array([gframe(k / GN) for k in range(GN)])
    gloop = float(np.abs(gframe(1.0) - gframe(0.0)).max())
    g_atlas = np.zeros((4 * CG, 4 * CG, 3), np.uint8)
    for k in range(GN):
        r, c = k // 4, k % 4
        g_atlas[r * CG:(r + 1) * CG, c * CG:(c + 1) * CG, 0] = (np.clip(gr[k], 0, 1) * 255 + 0.5).astype(np.uint8)
    png(OUT / "godray_flipbook.png", g_atlas)

    d0 = fog[0, :, :, 0]
    wrap = lambda a_: (float(np.abs(a_[:, 0] - a_[:, -1]).mean()) / max(float(np.abs(np.diff(a_, axis=1)).mean()), 1e-9),
                       float(np.abs(a_[0, :] - a_[-1, :]).mean()) / max(float(np.abs(np.diff(a_, axis=0)).mean()), 1e-9))
    wx, wy = wrap(d0)
    gate = {"fog_range": [round(float(fog[..., 0].min()), 3), round(float(fog[..., 0].max()), 3)],
            "fog_loop_err": float(np.abs(fog[0] - fog[N]).max()),
            "fog_wrap_seam_ratio": [round(wx, 2), round(wy, 2)],
            "fog_motion_rel": round(float(np.abs(fog[16, :, :, 0] - fog[0, :, :, 0]).mean() / max(fog[0, :, :, 0].mean(), 1e-9)), 3),
            "godray_motion_rel": round(float(np.abs(gr[4] - gr[0]).mean() / max(gr[0].mean(), 1e-9)), 3),
            "godray_loop_err": gloop,
            "godray_angular_contrast": round(float(gr[0][CG // 2].max() - gr[0][CG // 2].min()), 3)}
    gate["pass"] = bool(gate["fog_loop_err"] < 1e-9 and max(gate["fog_wrap_seam_ratio"]) < 3.0 and gate["fog_motion_rel"] > 0.2
                        and gate["godray_loop_err"] < 1e-9 and gate["godray_motion_rel"] > 0.05 and gate["godray_angular_contrast"] > 0.15 and 0.0 <= gate["fog_range"][0] and gate["fog_range"][1] <= 1.0)
    (OUT / "fog_params.json").write_text(json.dumps({"fog": {"grid": "8x8 of 128^2, frame 0 top-left row-major", "loop_s_suggested": 24, "R": "density", "G": "lace filaments x density", "B": "vertical fade bias"},
        "godray": {"grid": "4x4 of 256^2 (16 frames)", "R": "shaft intensity", "source": "top-centre of each cell", "loop_s_suggested": 12},
        "honesty": "procedural periodic sinusoid fields, not a Pyro sim"}, indent=1))
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_fog.spike.v1", "spike": True, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
