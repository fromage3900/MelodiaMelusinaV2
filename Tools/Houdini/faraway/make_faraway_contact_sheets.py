r"""make_faraway_contact_sheets.py -- top-down contact sheets of every Faraway Mother data layer. spike: true

numpy + zlib PNG writer only. South-up like the masks (row 0 = min Y), 1024^2 for 8 km (7.8 m/px).
Sheets: 01_biomes_placements, 02_seams_stitches, 03_wonder_layer, 04_all_layers (+ legend in contact_index.json)
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / "Saved" / "Staging" / "HoudiniForge"
OUT = S / "FarawayContact_20261026"
HALF, N = 4000.0, 1024
COL = {0: (90, 160, 190), 1: (235, 160, 200), 2: (70, 70, 140), 3: (205, 180, 130), 4: (150, 90, 110)}   # biomes
ROLE = {"HeartGate": (255, 255, 255), "FrillArch": (255, 230, 120), "LaceBridge": (120, 255, 255), "SilkPeak": (255, 80, 160),
        "SilkRibbon": (255, 140, 220), "MotherfoldBasin": (80, 120, 255), "TerracedIsland": (255, 170, 60), "ListeningOrchardTree": (140, 255, 140)}


def png(path, a):
    h, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def px(x, y):
    return int((x + HALF) / (2 * HALF) * (N - 1)), int((y + HALF) / (2 * HALF) * (N - 1))


def dot(img, x, y, r, c):
    i, j = px(x, y)
    img[max(0, j - r):j + r + 1, max(0, i - r):i + r + 1] = c


def base():
    m = np.array(__import__("PIL.Image", fromlist=["x"]).open(S / "FarawayBiomes_20261026" / "biome_mask.png").convert("RGBA")) if False else None
    # biome id lives in the PNG R channel (id*50); decode with our own reader to avoid PIL
    d = (S / "FarawayBiomes_20261026" / "biome_mask.png").read_bytes()
    i, idat = 8, b""
    while i < len(d):
        n, = struct.unpack(">I", d[i:i + 4]); t = d[i + 4:i + 8]; c = d[i + 8:i + 8 + n]; i += 12 + n
        if t == b"IHDR": w, h, *_ = struct.unpack(">IIBB", c[:10])
        elif t == b"IDAT": idat += c
    raw = zlib.decompress(idat); st = w * 4; rows = []; prev = np.zeros(st, np.uint8); k = 0
    for y in range(h):
        f = raw[k]; line = np.frombuffer(raw[k + 1:k + 1 + st], np.uint8).astype(np.int32); k += 1 + st
        for x in range(st):
            a = line[x - 4] if x >= 4 else 0; b = int(prev[x]); c2 = int(prev[x - 4]) if x >= 4 else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c2), abs(a - c2), abs(a + b - 2 * c2)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c2); line[x] = (line[x] + pr) & 255
        prev = line.astype(np.uint8); rows.append(prev)
    A = np.array(rows).reshape(h, w, 4)
    ids = np.rint(A[:, :, 0] / 50.0).astype(int)
    img = np.zeros((h, w, 3), np.uint8)
    for b, c in COL.items(): img[ids == b] = c
    big = np.repeat(np.repeat(img, N // w, 0), N // w, 1) if N % w == 0 and N >= w else img
    return (big.astype(np.float32) * 0.55).astype(np.uint8), ids


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img0, ids = base()
    pl = json.load(open(S / "FarawayBiomes_20261026" / "placements.json"))["placements"]
    seams = json.load(open(S / "FarawaySeamDressing_20261026" / "seam_polylines.json"))["seams"]
    J = json.load(open(S / "FarawaySeamDressing_20261026" / "junctions.json"))["junctions"]
    st = json.load(open(S / "FarawaySeamDressing_20261026" / "stitches.json"))["instances"]
    lw = json.load(open(S / "FarawayWonder_20261026" / "lace_wings.json"))
    wd = json.load(open(S / "FarawayWonder_20261026" / "wonders.json"))
    lm = json.load(open(S / "FarawayWonder_20261026" / "landmarks.json"))

    def seamlines(img, c=(255, 255, 255)):
        for s in seams:
            for x, y in s["points"]:
                dot(img, x, y, 0, c)

    # 01 biomes + placements
    a = img0.copy(); seamlines(a, (240, 240, 240))
    for role, pts in pl.items():
        for p in pts: dot(a, p["x"], p["y"], 3 if role != "ListeningOrchardTree" else 1, ROLE[role])
    for j in J: dot(a, j[0], j[1], 5, (255, 40, 40))
    png(OUT / "01_biomes_placements.png", a)
    # 02 seams + stitches (dark ground)
    a = np.zeros((N, N, 3), np.uint8) + 18
    for s in st: dot(a, s["x"], s["y"], 0, (255, 200, 90) if s["kind"] != "button" else (255, 60, 60))
    seamlines(a, (120, 200, 255))
    for j in J: dot(a, j[0], j[1], 5, (255, 60, 60))
    png(OUT / "02_seams_stitches.png", a)
    # 03 wonder layer
    a = (img0.astype(np.float32) * 0.5).astype(np.uint8)
    for p in lw["settle_points"]: dot(a, p["x"], p["y"], 2, (255, 255, 160))
    for b in wd["sing_to_bloom"]: dot(a, b["x"], b["y"], 0, (255, 120, 200) if b["side_F"] > 0 else (120, 160, 255))
    for l in wd["wish_lanterns"]: dot(a, l["x"], l["y"], 3, (255, 210, 80))
    for b in wd["stitch_hop_path"]["buttons"]: dot(a, b["x"], b["y"], 1, (255, 255, 255))
    dot(a, lm["la_berceuse"]["site"]["x"], lm["la_berceuse"]["site"]["y"], 9, (255, 70, 70))
    for g in lm["guide"]["beats"]: dot(a, g["x"], g["y"], 2, (60, 255, 120))
    png(OUT / "03_wonder_layer.png", a)
    # 04 all
    a = img0.copy(); seamlines(a, (235, 235, 235))
    for s in st[::3]: dot(a, s["x"], s["y"], 0, (255, 200, 90))
    for role, pts in pl.items():
        for p in pts: dot(a, p["x"], p["y"], 2, ROLE[role])
    for p in lw["settle_points"]: dot(a, p["x"], p["y"], 1, (255, 255, 160))
    for l in wd["wish_lanterns"]: dot(a, l["x"], l["y"], 2, (255, 210, 80))
    dot(a, lm["la_berceuse"]["site"]["x"], lm["la_berceuse"]["site"]["y"], 9, (255, 70, 70))
    png(OUT / "04_all_layers.png", a)
    (OUT / "contact_index.json").write_text(json.dumps({
        "orientation": "south-up (row 0 = min Y), 8 km, 7.8 m/px",
        "biome_colours": {"0 SeamWay": COL[0], "1 SilkCrest": COL[1], "2 VelvetBasin": COL[2], "3 Terrace": COL[3], "4 Cascade": COL[4]},
        "role_colours": ROLE, "red": "junctions / La Berceuse", "sheets": sorted(p.name for p in OUT.glob("*.png"))}, indent=1))
    print("SHEETS", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
