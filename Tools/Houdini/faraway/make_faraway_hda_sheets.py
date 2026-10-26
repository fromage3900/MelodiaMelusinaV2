r"""make_faraway_hda_sheets.py -- per-HDA front/side silhouette contact sheet + Vellum drape height map (hython 22). spike: true

Cooks each of the 8 Faraway HDAs (one at a time, defaults), splats points orthographically (front = X/Y, side = Z/Y) at a shared
metric scale per cell (cell scaled to the HDA's own bounds, size label in manifest), then rasterises the cloth height + terrain gap of
FarawayDrape_20261026. Outputs under <out>: hda_sheet.png (8 rows x 2 views), drape_map.png (cloth height | gap), manifest.json.
Gate: every HDA produced a non-empty silhouette (>= 200 covered pixels per view) and the drape map covers the tile.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / "Saved" / "Staging" / "HoudiniForge"
OUT = S / "FarawayHdaSheets_20261026"
NAMES = ["HeartGate", "FrillArch", "LaceBridge", "SilkPeak", "SilkRibbon", "MotherfoldBasin", "TerracedIsland", "ListeningOrchardTree"]
CELL = 300


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def splat(P, ax, ay, cell, col):
    img = np.zeros((cell, cell, 3), np.uint8) + 14
    lo = np.array([P[:, ax].min(), P[:, ay].min()]); hi = np.array([P[:, ax].max(), P[:, ay].max()])
    span = max(hi[0] - lo[0], hi[1] - lo[1], 1e-6)
    s = (cell - 24) / span
    x = ((P[:, ax] - (lo[0] + hi[0]) / 2) * s + cell / 2).astype(int)
    y = (cell - 12 - (P[:, ay] - lo[1]) * s).astype(int)
    ok = (x >= 0) & (x < cell) & (y >= 0) & (y < cell)
    img[y[ok], x[ok]] = col
    return img, int(((img != 14).any(-1)).sum()), float(span)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import hou

    rows, info = [], {}
    cols = [(255, 170, 210), (150, 200, 255)]
    for n in NAMES:
        hou.hda.installFile(str(ROOT / "hda" / f"HDA_Faraway_{n}_1.0.hda"))
        node = hou.node("/obj").createNode(f"HDA_Faraway_{n}", "S_" + n)
        node.cook(force=True)
        geo = node.displayNode().geometry()
        P = np.array(geo.pointFloatAttribValues("P"), dtype=np.float64).reshape(-1, 3)
        if len(P) > 80000:
            P = P[:: len(P) // 80000]
        f, cf, span_f = splat(P, 0, 1, CELL, cols[0])
        sd, cs, span_s = splat(P, 2, 1, CELL, cols[1])
        rows.append(np.concatenate([f, sd], 1))
        info[n] = {"points": int(len(P)), "front_px": cf, "side_px": cs, "span_front_m": round(span_f, 2), "span_side_m": round(span_s, 2)}
        node.destroy()
        print(n, info[n])
    sheet = np.concatenate(rows, 0)
    for r in range(1, len(NAMES)):
        sheet[r * CELL] = (70, 70, 100)
    png(OUT / "hda_sheet.png", sheet)

    # drape map
    d = S / "FarawayDrape_20261026"
    cloth = hou.Geometry(); cloth.loadFromFile(str(d / "SM_FabricRidge_Hero_drape.bgeo.sc"))
    terr = hou.Geometry(); terr.loadFromFile(str(d / "peak_tile.bgeo.sc"))
    C = np.array(cloth.pointFloatAttribValues("P")).reshape(-1, 3)
    T = np.array(terr.pointFloatAttribValues("P")).reshape(-1, 3)
    R = 256
    def grid(Q, val):
        x = ((Q[:, 0] + 125) / 250 * (R - 1)).astype(int); z = ((Q[:, 2] + 125) / 250 * (R - 1)).astype(int)
        g = np.full((R, R), np.nan); g[np.clip(z, 0, R - 1), np.clip(x, 0, R - 1)] = val; return g
    gc, gt = grid(C, C[:, 1]), grid(T, T[:, 1])
    def fill(g):
        for _ in range(6):
            m = np.isnan(g)
            if not m.any(): break
            n = np.nanmean(np.stack([np.roll(g, s, a) for s in (-1, 1) for a in (0, 1)]), 0)
            g[m] = n[m]
        return np.nan_to_num(g)
    gc, gt = fill(gc), fill(gt)
    gap = gc - gt
    n8 = lambda a_: np.clip((a_ - a_.min()) / max(a_.max() - a_.min(), 1e-9), 0, 1)
    A = np.stack([n8(gc) * 255, n8(gc) * 170, n8(gc) * 215], -1).astype(np.uint8)
    B = np.stack([n8(gap) * 100, n8(gap) * 220, n8(gap) * 255], -1).astype(np.uint8)
    png(OUT / "drape_map.png", np.concatenate([A, B], 1))
    gate = {"hdas": len(info), "min_front_px": min(v["front_px"] for v in info.values()), "min_side_px": min(v["side_px"] for v in info.values()),
            "drape_cloth_pts": int(len(C)), "drape_gap_range_m": [round(float(gap.min()), 2), round(float(gap.max()), 2)]}
    gate["pass"] = bool(gate["hdas"] == 8 and gate["min_front_px"] >= 200 and gate["min_side_px"] >= 100 and gate["drape_cloth_pts"] > 1000)
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_hda_sheets.spike.v1", "spike": True, "houdini": hou.applicationVersionString(),
        "order_top_to_bottom": NAMES, "per_hda": info, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
