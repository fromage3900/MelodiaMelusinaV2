r"""build_faraway_peak_erosion.py -- W10: heightfield erosion + strata masks for a silk-peak window (hython 22). spike: true

A 2 km x 2 km window (global X/Y in [-1000, 1000] m) of the Faraway silk landform is built in numpy (macro Gaussian peaks +
Chladni-phase pleats, same family as the SilkPeak HDA), pushed into a Houdini heightfield, run through
`heightfield_erode`, and read back. Outputs: height_before / height_after (16-bit PNG, metres in manifest), erosion_delta,
flow, strata (banded mask from eroded height) and a 4-up contact sheet. Pure staging data; no UE, no materials.

Usage: hython Tools/Houdini/faraway/build_faraway_peak_erosion.py [--out DIR] [--res 256] [--iters 40]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HALF, PI = 4000.0, math.pi


def F(x, y):
    u, v = (x + HALF) / 8000.0, (y + HALF) / 8000.0
    return np.cos(3 * PI * u) * np.cos(5 * PI * v) - np.cos(5 * PI * u) * np.cos(3 * PI * v)


def terrain(res, size=2000.0, hs=420.0):
    xs = np.linspace(-size / 2, size / 2, res)
    X, Y = np.meshgrid(xs, xs)
    h = np.zeros_like(X)
    for ax, ay, r, k in [(-250, 150, 380, 1.0), (330, -180, 300, 0.7), (60, 400, 260, 0.55)]:
        h += k * np.exp(-((X - ax) ** 2 + (Y - ay) ** 2) / (2 * r * r))
    h *= hs
    phase = X * math.cos(math.radians(35)) + Y * math.sin(math.radians(35)) + 80.0 * F(X, Y)
    ridge = np.clip(h / hs, 0, 1)
    h += (np.abs(np.sin(2 * PI * phase / 36.0)) ** 1.0) * 5.0 * (0.15 + 0.85 * ridge)
    return h.astype(np.float32)


def png16(path, a):
    a16 = (np.clip(a, 0, 1) * 65535).astype(">u2")
    raw = b"".join(b"\x00" + a16[y].tobytes() for y in range(a16.shape[0]))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", a.shape[1], a.shape[0], 16, 0, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def png8rgb(path, a):
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(a.shape[0]))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", a.shape[1], a.shape[0], 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def norm(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / max(hi - lo, 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayErosion_20261026"))
    ap.add_argument("--res", type=int, default=256)
    ap.add_argument("--iters", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    import hou

    H0 = terrain(a.res)
    g = hou.node("/obj").createNode("geo", "FM_erosion")
    hf = g.createNode("heightfield", "hf")
    hf.parm("sizex").set(2000.0); hf.parm("sizey").set(2000.0)
    hf.parm("divisionmode").set(1) if hf.parm("divisionmode").menuItems()[1:2] else None
    try:
        hf.parm("gridsamples").set(a.res)
    except Exception:
        pass
    hf.cook(force=True)
    vols = {v.attribValue("name"): v for v in hf.geometry().prims() if hasattr(v, "resolution")} if hf.geometry().findPrimAttrib("name") else {}
    res = vols["height"].resolution()
    print("HF_RES", res, "layers", list(vols))
    # write numpy heights into the heightfield via a python SOP
    py = g.createNode("python", "write_height"); py.setInput(0, hf)
    flat = H0.ravel(order="C") if res[0] == a.res else None
    if flat is None:
        # resample to the heightfield resolution
        xs = np.linspace(0, a.res - 1, res[0]); ys = np.linspace(0, a.res - 1, res[1])
        flat = np.array([[H0[int(round(j)), int(round(i))] for i in xs] for j in ys], dtype=np.float32).ravel(order="C")
        H0 = flat.reshape(res[1], res[0])
    np.save(out / "_h0.npy", flat)
    py.parm("python").set(
        "import hou, numpy as np\ngeo=hou.pwd().geometry()\n"
        "vol=[p for p in geo.prims() if p.attribValue('name')=='height'][0]\n"
        f"vol.setAllVoxels(list(map(float,np.load(r'{(out / '_h0.npy').as_posix()}'))))\n")
    er = g.createNode("heightfield_erode", "erode"); er.setInput(0, py)
    er.parm("iterations").set(a.iters)
    er.parm("resimulate").pressButton() if er.parm("resimulate") else None
    hou.setFrame(er.parm("startframe").eval() + a.iters)
    er.cook(force=True)
    err = er.errors()
    if err: print("ERODE_ERR", err)
    geo = er.geometry()
    names = {p.attribValue("name"): p for p in geo.prims() if geo.findPrimAttrib("name")}
    print("ERODE_LAYERS", list(names))
    H1 = np.array(names["height"].allVoxels(), dtype=np.float32).reshape(H0.shape)
    flow = np.array(names["flow"].allVoxels(), dtype=np.float32).reshape(H0.shape) if "flow" in names else np.zeros_like(H0)
    delta = H1 - H0
    print('STATS H0',float(H0.min()),float(H0.max()),float(H0.mean()),'H1',float(H1.min()),float(H1.max()),float(H1.mean()))
    band = 28.0
    strata = (0.5 + 0.5 * np.sin(2 * PI * H1 / band)) ** 3
    slope = np.hypot(*np.gradient(H1, 2000.0 / H1.shape[0]))
    strata *= np.clip(slope * 2.0, 0, 1)          # strata read on steep faces only

    png16(out / "height_before.png", norm(H0)); png16(out / "height_after.png", norm(H1))
    png16(out / "erosion_delta.png", norm(np.abs(delta))); png16(out / "flow.png", norm(flow)); png16(out / "strata.png", norm(strata))
    tile = lambda m, tint: (np.stack([norm(m) * tint[0], norm(m) * tint[1], norm(m) * tint[2]], -1) * 255).astype(np.uint8)
    sheet = np.concatenate([np.concatenate([tile(H0, (1, .8, .9)), tile(H1, (1, .8, .9))], 1),
                            np.concatenate([tile(np.abs(delta), (.4, .8, 1)), tile(strata, (1, .85, .4))], 1)], 0)
    png8rgb(out / "contact_erosion.png", sheet)
    (out / "_h0.npy").unlink()
    gate = {"res": [int(H0.shape[1]), int(H0.shape[0])], "iters": a.iters, "height_min_max_after": [round(float(H1.min()), 2), round(float(H1.max()), 2)],
            "mean_abs_delta_m": round(float(np.abs(delta).mean()), 4), "max_abs_delta_m": round(float(np.abs(delta).max()), 3),
            "peak_preserved": float(H1.max()) > 0.8 * float(H0.max()), "no_nan": bool(np.isfinite(H1).all()),
            "layers": sorted(names)}
    gate["pass"] = bool(gate["mean_abs_delta_m"] > 0.01 and gate["peak_preserved"] and gate["no_nan"] and gate["max_abs_delta_m"] < 120)
    (out / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_erosion.spike.v1", "spike": True, "houdini": hou.applicationVersionString(),
        "window_m": 2000.0, "gate": gate, "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(out.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
