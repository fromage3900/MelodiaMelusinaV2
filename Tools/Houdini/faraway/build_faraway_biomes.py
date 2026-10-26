r"""build_faraway_biomes.py -- Faraway Mother Chladni biome classifier + per-HDA placement sets. spike: true

Pure Python (no hou, no editor) on the shared global field F of chladni_field.py. 8 km world, X/Y in [-4000, 4000] m,
u=(X+4000)/8000. Nothing tile-local. Deterministic (seed 3900, no time/random state).

Biomes (by signed F, |F|, |grad F| and distance to the F=0 seam):
  0 SeamWay      walkable valley along the nodal lines          (Heart Gate, Frill Arch, Lace Bridge)
  1 SilkCrest    F >  crest_f   high positive antinodes         (Silk Peak, Silk Ribbon sky anchors)
  2 VelvetBasin  F < -crest_f   deep negative antinodes         (Motherfold Basin)
  3 Terrace      mid |F|, low gradient, off-seam                (Terraced Island, Orchard Tree)
  4 Cascade      high gradient                                   (waterfall / ribbon sources, no building)
Outputs (never Content/, never Saved/Audit/houdini_faraway_mother/): <out>/biome_mask.png (RGBA 8-bit: R biome id,
G signed F, B tension01, A seam distance), biomes.json (counts, params), placements.json, manifest.json.

Usage: python Tools/Houdini/faraway/build_faraway_biomes.py [--out DIR] [--grid 512] [--tension-div 8pi|8]
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import chladni_field as cf  # noqa: E402

HALF = 4000.0
SEED = 3900
JUNCTION_R = 80.0   # m, handoff rule: nothing within 80 m of a seam junction
EDGE_R = 60.0       # m from the world edge

# role -> (biome, min spacing m, target count, extra filter)
ROLES = {
    "HeartGate":        (0, 700.0, 3),
    "FrillArch":        (0, 350.0, 8),
    "LaceBridge":       (0, 300.0, 10),
    "SilkPeak":         (1, 450.0, 14),
    "SilkRibbon":       (1, 220.0, 24),
    "MotherfoldBasin":  (2, 700.0, 4),
    "TerracedIsland":   (3, 600.0, 12),
    "ListeningOrchardTree": (3, 120.0, 120),
}


def png_rgba(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    Path(path).write_bytes(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayBiomes_20261026"))
    ap.add_argument("--grid", type=int, default=512)
    ap.add_argument("--tension-div", default="8pi", choices=["8pi", "8"])
    ap.add_argument("--crest-f", type=float, default=0.9)
    ap.add_argument("--seam-m", type=float, default=45.0)
    ap.add_argument("--cascade-grad", type=float, default=0.75, help="tension01 above this = Cascade")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    N = a.grid
    cell = 2 * HALF / N

    # tension01 as defined in chladni_field (|grad_uv F| / (8*pi)); the /8 variant is a pure rescale
    scale = math.pi if a.tension_div == "8pi" else 1.0

    def tension(x, y):
        g = cf.grad(x, y)
        gm = math.hypot(g[0], g[1])
        return min(1.0, gm * 8000.0 / (8.0 * scale)), gm

    biome = [[0] * N for _ in range(N)]
    rows = []
    counts = [0] * 5
    for j in range(N):                      # row 0 = min Y (south-up, matches the handoff masks)
        y = -HALF + (j + 0.5) * cell
        row = bytearray()
        for i in range(N):
            x = -HALF + (i + 0.5) * cell
            f = cf.F(x, y)
            t, gm = tension(x, y)
            sd = abs(f) / max(gm, 1e-9)     # first-order seam distance (m), valid near the seam
            if sd < a.seam_m:
                b = 0
            elif t > a.cascade_grad:
                b = 4
            elif f > a.crest_f:
                b = 1
            elif f < -a.crest_f:
                b = 2
            else:
                b = 3
            biome[j][i] = b
            counts[b] += 1
            row += bytes((b * 50, int((f / 2.0 * 0.5 + 0.5) * 255), int(t * 255), int(min(sd, 255.0))))
        rows.append(row)
    png_rgba(out / "biome_mask.png", N, N, rows)

    def b_at(x, y):
        i = int((x + HALF) / cell); j = int((y + HALF) / cell)
        if not (0 <= i < N and 0 <= j < N):
            return -1
        return biome[j][i]

    # junctions: |F| ~ 0 and |grad| ~ 0 (8-way crossings), found on the lattice of grid centres
    junctions = []
    for j in range(1, N - 1):
        y = -HALF + (j + 0.5) * cell
        for i in range(1, N - 1):
            x = -HALF + (i + 0.5) * cell
            if abs(cf.F(x, y)) < 0.06 and tension(x, y)[0] < 0.03:   # |F|~0 and |grad F|~0 (normalised)
                junctions.append((x, y))
    # collapse neighbours
    uj = []
    for p in junctions:
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 3 * cell for q in uj):
            uj.append(p)

    def clear(x, y):
        if abs(x) > HALF - EDGE_R or abs(y) > HALF - EDGE_R:
            return False
        return all(math.hypot(x - q[0], y - q[1]) > JUNCTION_R for q in uj)

    # deterministic placement: candidates on a golden-ratio sequence, accepted by biome + spacing
    placements = {}
    phi = (math.sqrt(5) - 1) / 2
    for role, (want, spacing, target) in ROLES.items():
        pts = []
        k = SEED % 997
        tries = 0
        while len(pts) < target and tries < 60000:
            tries += 1
            k += 1
            x = (((k * 0.7548776662466927) + 0.31) % 1.0) * 2 * HALF - HALF
            y = (((k * 0.5698402909980532) + 0.77) % 1.0) * 2 * HALF - HALF
            if b_at(x, y) != want or not clear(x, y):
                continue
            if any(math.hypot(x - p["x"], y - p["y"]) < spacing for p in pts):
                continue
            f = cf.F(x, y)
            t, _ = tension(x, y)
            g = cf.grad(x, y)
            pts.append({"x": round(x, 2), "y": round(y, 2), "F": round(f, 5), "tension": round(t, 4),
                        "side": 1 if f >= 0 else -1,
                        # aim along the seam tangent (perpendicular to grad F): the walkable direction
                        "yaw_deg": round(math.degrees(math.atan2(g[0], -g[1])) % 180.0, 2)})
        placements[role] = pts

    gate = {
        "biome_cells": counts,
        "biome_fraction": [round(c / (N * N), 4) for c in counts],
        "junction_count": len(uj),
        "junctions_nearest_origin": sorted([[round(p[0], 1), round(p[1], 1)] for p in uj], key=lambda q: q[0]**2 + q[1]**2)[:8],
        "roles_met": {r: [len(placements[r]), ROLES[r][2]] for r in ROLES},
    }
    gate["all_biomes_present"] = all(c > 0 for c in counts)
    gate["all_roles_placed"] = all(len(placements[r]) >= max(1, ROLES[r][2] // 2) for r in ROLES)
    gate["no_point_near_junction_or_edge"] = all(clear(p["x"], p["y"]) for r in placements for p in placements[r])
    gate["pass"] = bool(gate["all_biomes_present"] and gate["all_roles_placed"] and gate["no_point_near_junction_or_edge"])

    (out / "placements.json").write_text(json.dumps({"seed": SEED, "tension_div": a.tension_div, "units": "m, X/Y global",
                                                      "placements": placements}, indent=1))
    (out / "biomes.json").write_text(json.dumps({"params": vars(a), "gate": gate}, indent=1))
    man = {"schema": "melodia.faraway_biomes.spike.v1", "spike": True, "grid": N, "cell_m": round(cell, 3),
           "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(out.glob("*")) if p.is_file() and p.name != "manifest.json"}}
    (out / "manifest.json").write_text(json.dumps(man, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
