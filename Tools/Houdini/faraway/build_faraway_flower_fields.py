r"""build_faraway_flower_fields.py -- W18: procedural flower/foliage fields from the Chladni field + bloom systems. spike: true

numpy only, deterministic (hash-based, seed 3900). Consumes: FarawayBiomes (orchard placements), FarawaySeamDressing
(seam polylines, junctions), FarawayLullaby (note->species). Three field types:
  orchard_ring   golden-angle phyllotaxis rings around every ListeningOrchardTree (r = 1.6*sqrt(i), up to 26 m)
  seam_lace      two bands (3-14 m each side) along every F=0 seam, thinning toward junctions
  crest_drift    jittered 18 m grid inside SilkCrest (F > 0.9), species by sign/size of F
Per point: species (0-6 = lullaby scale degree D E F# G# A B C#), scale, yaw, bloom_phase (0-1 offset against the beat),
height class, palette (0 pink for F>=0, 1 blue for F<0), field type. Streaming tiles of 500 m with per-tile counts.
Outputs (<out>): flowers.csv, tiles.json, species.json, density_sheet.png, manifest.json. No materials, no UE.
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
S = ROOT / "Saved" / "Staging" / "HoudiniForge"
OUT = S / "FarawayFlowers_20261026"
HALF, PI = 4000.0, math.pi
SPECIES = ["Moonpetal", "Bellflower", "LaceFoxglove", "DwarfSakura", "LanternLily", "PearlClover", "SilkPoppy"]
TILE = 500.0
TILE_BUDGET = 9000


def F(x, y):
    u, v = (x + HALF) / 8000.0, (y + HALF) / 8000.0
    return math.cos(3 * PI * u) * math.cos(5 * PI * v) - math.cos(5 * PI * u) * math.cos(3 * PI * v)


def h(*a):
    x = 2166136261
    for v in a:
        x = ((x ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 4294967295.0


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pl = json.load(open(S / "FarawayBiomes_20261026" / "placements.json"))["placements"]
    seams = json.load(open(S / "FarawaySeamDressing_20261026" / "seam_polylines.json"))["seams"]
    J = np.array(json.load(open(S / "FarawaySeamDressing_20261026" / "junctions.json"))["junctions"])
    pts = []

    def jd(x, y):
        return float(np.min(np.hypot(J[:, 0] - x, J[:, 1] - y)))

    def add(kind, x, y, sp, seed):
        if abs(x) > HALF - 40 or abs(y) > HALF - 40 or jd(x, y) < 40:
            return
        f = F(x, y)
        pts.append((kind, round(x, 2), round(y, 2), sp % 7, round(0.7 + 0.8 * h(seed, 1), 3), round(h(seed, 2) * 360, 1),
                    round(h(seed, 3), 3), int(h(seed, 4) * 3), 0 if f >= 0 else 1))

    golden = PI * (3 - math.sqrt(5))
    for ti, t in enumerate(pl["ListeningOrchardTree"]):
        for i in range(1, 221):
            r = 1.6 * math.sqrt(i) * 1.0
            if r > 26: break
            a = i * golden + h(ti, 7) * 6.28
            add("orchard_ring", t["x"] + r * math.cos(a), t["y"] + r * math.sin(a), i // 3 + ti, ti * 1000 + i)
    for s in seams:
        P = s["points"]
        for k, (x, y) in enumerate(P):
            if jd(x, y) < 80: continue
            tx, ty = (P[min(k + 1, len(P) - 1)][0] - P[max(k - 1, 0)][0]), (P[min(k + 1, len(P) - 1)][1] - P[max(k - 1, 0)][1])
            n = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / n, tx / n
            thin = min(1.0, (jd(x, y) - 80) / 160)
            for side in (-1, 1):
                for q in range(int(2 + 4 * thin)):
                    off = 3 + 11 * h(s["id"], k, side, q)
                    al = (h(s["id"], k, side, q, 9) - 0.5) * 10
                    add("seam_lace", x + nx * side * off + tx / n * al, y + ny * side * off + ty / n * al, k // 4 + q + (1 if side > 0 else 4), s["id"] * 100000 + k * 10 + q + (5 if side > 0 else 0))
    step = 18.0
    for gx in np.arange(-HALF + 40, HALF - 40, step):
        for gy in np.arange(-HALF + 40, HALF - 40, step):
            x = gx + (h(int(gx), int(gy), 1) - 0.5) * step * 0.8
            y = gy + (h(int(gx), int(gy), 2) - 0.5) * step * 0.8
            f = F(x, y)
            if f > 0.9 and h(int(gx), int(gy), 3) < 0.6:
                add("crest_drift", x, y, int((f - 0.9) * 40) + int(h(int(gx), int(gy), 5) * 3), int(gx) * 7919 + int(gy))

    tiles = {}
    for p in pts:
        key = f"{int((p[1] + HALF) // TILE)}_{int((p[2] + HALF) // TILE)}"
        tiles[key] = tiles.get(key, 0) + 1
    (OUT / "flowers.csv").write_text("field,x_m,y_m,species,scale,yaw_deg,bloom_phase,height_class,palette\n" + "\n".join(",".join(str(v) for v in p) for p in pts))
    (OUT / "tiles.json").write_text(json.dumps({"tile_m": TILE, "budget": TILE_BUDGET, "tiles": tiles}, indent=0))
    (OUT / "species.json").write_text(json.dumps({"species": [{"id": i, "name": n, "lullaby_degree": ["D", "E", "F#", "G#", "A", "B", "C#"][i],
        "bloom_on": "beat of its note (lullaby_curves.bloom_note_index)", "palette": ["pink (F>=0)", "blue (F<0)"]} for i, n in enumerate(SPECIES)],
        "ue_intake": "existing foliage/bloom assets only (PCG_MeadowBloom, PCG_Nikki_PhyllotaxisGarden, MI_ProcFoliage_Sakura); one HISM per species"}, indent=1))
    N = 1024
    img = np.zeros((N, N, 3), np.uint8) + 14
    cols = [(255, 160, 200), (150, 180, 255), (255, 230, 140), (255, 110, 150), (255, 190, 90), (190, 255, 210), (255, 130, 130)]
    for p in pts:
        i = int((p[1] + HALF) / 8000 * (N - 1)); j = int((p[2] + HALF) / 8000 * (N - 1))
        c = cols[p[3]]
        img[j, i] = np.maximum(img[j, i], c)
    png(OUT / "density_sheet.png", img)

    by = {k: sum(1 for p in pts if p[0] == k) for k in ("orchard_ring", "seam_lace", "crest_drift")}
    gate = {"total": len(pts), "by_field": by, "max_tile": max(tiles.values()), "tile_budget": TILE_BUDGET,
            "tiles_over_budget": sum(1 for v in tiles.values() if v > TILE_BUDGET),
            "all_in_bounds": all(abs(p[1]) < HALF and abs(p[2]) < HALF for p in pts),
            "crest_all_f_gt_0p9": all(F(p[1], p[2]) > 0.9 - 1e-9 for p in pts if p[0] == "crest_drift"),
            "min_junction_clearance_m": round(min(jd(p[1], p[2]) for p in pts[::25]), 1)}
    gate["pass"] = bool(gate["total"] > 50000 and all(v > 0 for v in by.values()) and gate["tiles_over_budget"] == 0 and gate["all_in_bounds"]
                        and gate["crest_all_f_gt_0p9"] and gate["min_junction_clearance_m"] >= 39.9)
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_flowers.spike.v1", "spike": True, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
