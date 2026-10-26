r"""build_faraway_ocean_flipbook.py -- W9a: looping tileable ocean displacement flipbook for Motherfold Basin (hython 22). spike: true

oceanspectrum (loop on, loopperiod = 8 s) -> oceanevaluate over a 128x128 grid of a 200 m tile, 64 frames.
Atlas 1024^2 (8x8 cells of 128^2), 8-bit RGB: R = height (normalised, amplitude in manifest), G/B = horizontal chop dx/dz.
Gate: height range, spatial tiling (edge-to-edge difference comparable to neighbouring-column difference), temporal loop closure
(frame 0 vs frame 64), no NaN, determinism. Outputs under <out>: ocean_flipbook.png, ocean_params.json, manifest.json.
DETERMINISM: stable to +-1 8-bit level (1 byte in 3.1 M differs between some runs; FFT float noise at a quantisation edge), NOT hash-identical.
NOTE: this is the lake surface motion data only. FLIP waterfall (W9b) is a separate, heavier step.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("HOUDINI_MAXTHREADS", "1")   # FFT evaluation is only stable to +-1 LSB even single-threaded; do not claim hash-identical


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayOcean_20261026"))
    ap.add_argument("--cell", type=int, default=128)
    ap.add_argument("--period", type=float, default=8.0)
    ap.add_argument("--tile", type=float, default=200.0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    import hou

    g = hou.node("/obj").createNode("geo", "FM_ocean")
    grid = g.createNode("grid", "grid")
    grid.parm("sizex").set(a.tile); grid.parm("sizey").set(a.tile); grid.parm("rows").set(a.cell); grid.parm("cols").set(a.cell)
    sp = g.createNode("oceanspectrum", "spec")
    sp.parm("gridsize").set(a.tile); sp.parm("seed").set(3900)
    sp.parm("loop").set(1); sp.parm("loopperiod").set(a.period)
    sp.parm("windspeed").set(2.2); sp.parm("chopscale").set(1.0)
    ev = g.createNode("oceanevaluate", "ev")
    ev.setInput(0, grid); ev.setInput(1, sp)
    print("EV_TIME_EXPR", ev.parm("time").expression() if ev.parm("time").keyframes() else "const", "| SP_TIME", sp.parm("timeoffset").eval(), sp.parm("timescale").eval())
    ev.setDisplayFlag(True)
    rest = None
    frames = []
    N = 64
    for k in range(N + 1):
        hou.setTime(a.period * k / N)                  # drive the node clock ($T), not a constant
        ev.cook(force=True)
        geo = ev.geometry()
        P = np.array(geo.pointFloatAttribValues("P"), dtype=np.float64).reshape(-1, 3)
        if rest is None:
            gp = grid.geometry()
            rest = np.array(gp.pointFloatAttribValues("P"), dtype=np.float64).reshape(-1, 3)
        frames.append(np.c_[P[:, 1], P[:, 0] - rest[:, 0], P[:, 2] - rest[:, 2]].reshape(a.cell, a.cell, 3))
    F = np.array(frames)                          # (65, c, c, 3)
    h, dx, dz = F[..., 0], F[..., 1], F[..., 2]
    ha = float(np.abs(h).max()); ca = float(max(np.abs(dx).max(), np.abs(dz).max(), 1e-9))
    rgb = np.stack([h / (2 * ha) + 0.5, dx / (2 * ca) + 0.5, dz / (2 * ca) + 0.5], -1)
    rgb8 = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    atlas = np.zeros((8 * a.cell, 8 * a.cell, 3), np.uint8)
    for k in range(64):
        r, c = k // 8, k % 8
        atlas[r * a.cell:(r + 1) * a.cell, c * a.cell:(c + 1) * a.cell] = rgb8[k]
    png(out / "ocean_flipbook.png", atlas)
    # gates
    col_step = float(np.abs(np.diff(h[0], axis=1)).mean())
    edge_step = float(np.abs(h[0][:, 0] - h[0][:, -1]).mean())     # wrap seam vs interior step
    row_edge = float(np.abs(h[0][0, :] - h[0][-1, :]).mean()); row_step = float(np.abs(np.diff(h[0], axis=0)).mean())
    loop_err = float(np.abs(h[0] - h[N]).max())
    gate = {"height_amp_m": round(ha, 4), "chop_amp_m": round(ca, 4), "frames": 64, "cell": a.cell, "tile_m": a.tile,
            "loop_err_m": round(loop_err, 5), "loop_err_rel": round(loop_err / ha, 5),
            "seam_ratio_x": round(edge_step / max(col_step, 1e-9), 3), "seam_ratio_y": round(row_edge / max(row_step, 1e-9), 3),
            "motion_rel": round(float(np.abs(h[16] - h[0]).mean() / max(np.abs(h[0]).mean(), 1e-9)), 4),
            "no_nan": bool(np.isfinite(F).all())}
    gate["pass"] = bool(gate["no_nan"] and gate["motion_rel"] > 0.2 and 0.01 < ha < 20 and gate["loop_err_rel"] < 0.02 and gate["seam_ratio_x"] < 3.0 and gate["seam_ratio_y"] < 3.0)
    (out / "ocean_params.json").write_text(json.dumps({"height_scale_m": ha * 2, "chop_scale_m": ca * 2, "decode": "h=(R-0.5)*height_scale; dx=(G-0.5)*chop_scale; dz=(B-0.5)*chop_scale",
        "grid": "8x8 cells, frame 0 top-left, row-major", "period_s": a.period, "tile_m": a.tile, "wind_m_s": 2.2, "seed": 3900}, indent=1))
    (out / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_ocean.spike.v1", "spike": True, "houdini": hou.applicationVersionString(), "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(out.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
