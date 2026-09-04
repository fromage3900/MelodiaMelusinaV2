"""Sea Above — island foliage manifest generator (2026-09-03).

Extends the heatmap-dress pattern to the ABOVE-SEA layer (Z > 13455): foliage
on the archipelago islands. CanonicalLandscape only, height-aware raycast snap
(BS_GodFile #2), phi-decay density from the gameplay loop (same golden rule as
the reef manifest).

Foliage authority tiers (AGENTS.md / material review):
  - SpeedTree master = tree authority (M_SpeedTreeMaster PRESENT)
  - Megascans 3D_Plants (74 presets) = photoreal bush/fern/palm tier
  - L-system flora (SM_Flora_*) = toon-form flora
Mesh refs are chosen from VERIFIED on-disk assets; the editor lane raycast-snaps
Z = surface + clearance. No new landscape, no new material masters.

Run: ./.venv/Scripts/python.exe Tools/PCG/build_sea_above_foliage.py [--verify]
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

SCHEMA = "melodia.sea_above_foliage.v1"
SEA_SURFACE_Z = 13455.0
PHI = (1 + 5 ** 0.5) / 2
PATH_BAND_IN = 20000.0

# Verified on-disk assets (2026-09-03 census)
SPEEDTREE_MASTER = "/Game/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.M_SpeedTreeMaster"
MEGASCAN_PLANTS = {
    "palm": "/Game/Megascans/3D_Plants/AlexandraPalm/SM_AlexandraPalm.SM_AlexandraPalm",
    "fern": "/Game/Megascans/3D_Plants/BeechFern/SM_BeechFern.SM_BeechFern",
    "boston": "/Game/Megascans/3D_Plants/BostonFern/SM_BostonFern.SM_BostonFern",
    "moss": "/Game/Megascans/3D_Plants/CustomMoss/SM_CustomMoss.SM_CustomMoss",
    "clover": "/Game/Megascans/3D_Plants/CloverVarieties/SM_CloverVarieties.SM_CloverVarieties",
}
REEF_FLORA = {
    "chime": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Flora_Chime.SM_Flora_Chime",
    "fern": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Flora_Fern.SM_Flora_Fern",
    "reed": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Flora_Reed.SM_Flora_Reed",
}
MEGASCAN_ISLAND_MI = "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_01.MI_ForestRockFormation_01"

# Loop polyline (PlayerStart -> Quill -> MusicKey -> Dock)
PATH_POLYLINE = [(0.0, 0.0), (-910.0, 500.0), (0.0, -950.0), (-5099.0, 5821.0)]

TARGET_COUNTS = {
    "IslandFoliage": 64,   # palms/ferns on island slopes near loop + islands
    "BalconyFlora": 12,    # toon-form flora at the Shorewake balcony area (~8k gold radius, ~NE)
    "MooringDress": 10,    # overlook mooring environs (-5099, 5821)
}

# Exploration anchors (from SEA_ABOVE_FOLIAGE_EXPLORATION_QUESTS plan)
MOORING = (-5099.0, 5821.0)
BALCONY = (4940.0, 6370.0)  # golden-radius 8k island, ~NE of the loop


def path_falloff(x: float, y: float) -> float:
    """Golden decay rho = (D/(d+D))^PHI — same rule as the reef manifest."""
    pts = PATH_POLYLINE
    best = 1e18
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        best = min(best, math.hypot(x - px, y - py))
    return (PATH_BAND_IN / (best + PATH_BAND_IN)) ** PHI


class Net:
    """Reads the sea_above_layers.npz (Z/SLOPE/bounds/grid)."""

    def __init__(self, layers: dict):
        self.Z = layers["Z"]
        self.SLOPE = layers.get("SLOPE", None)
        self.bounds = [float(v) for v in layers["bounds"]]
        self.grid = int(layers["grid"])

    def cell(self, x: float, y: float):
        n = self.grid
        bx = self.bounds
        i = min(n - 1, max(0, int(round((x - bx[0]) / (bx[2] - bx[0]) * (n - 1)))))
        j = min(n - 1, max(0, int(round((y - bx[1]) / (bx[3] - bx[1]) * (n - 1)))))
        z = float(self.Z[j, i])
        sl = float(self.SLOPE[j, i]) if self.SLOPE is not None else 0.0
        return z, sl


def generate(seed: int = 20260903, layers: dict | None = None) -> dict:
    rng = random.Random(seed)
    net = Net(layers)
    bx = net.bounds
    placements = []

    # --- IslandFoliage: above-sea cells (Z > SEA), slope-gated, phi density ---
    count = 0
    attempts = 0
    while count < TARGET_COUNTS["IslandFoliage"] and attempts < TARGET_COUNTS["IslandFoliage"] * 900:
        attempts += 1
        x = rng.uniform(bx[0], bx[2])
        y = rng.uniform(bx[1], bx[3])
        z, slope = net.cell(x, y)
        if z <= SEA_SURFACE_Z + 1500.0:   # only actual islands above the waterline
            continue
        if slope > 35.0:                   # no foliage on sheer cliff
            continue
        den = path_falloff(x, y)
        if rng.random() > den:             # phi decay (dense near loop, sparse far)
            continue
        kind = rng.choice(["palm", "fern", "boston", "clover"])
        s = rng.uniform(0.7, 1.6)
        placements.append({
            "id": f"FL_Island_{count:04d}",
            "zone": "IslandFoliage",
            "mesh": MEGASCAN_PLANTS[kind],
            "material": MEGASCAN_ISLAND_MI,
            "position": [round(x, 1), round(y, 1), round(z, 1)],
            "height_cm": round(z, 1),
            "clearance_cm": 5.0,
            "rotation": [0.0, 0.0, round(rng.uniform(0, 360), 2)],
            "scale": [round(s, 3), round(s, 3), round(s, 3)],
            "path_falloff": round(den, 4),
            "slope_deg": round(slope, 2),
        })
        count += 1

    # --- BalconyFlora: toon-form flora around the golden-radius balcony ---
    bx_, by_ = BALCONY
    for k in range(TARGET_COUNTS["BalconyFlora"]):
        ang = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(400.0, 1400.0)
        x = bx_ + math.cos(ang) * rad
        y = by_ + math.sin(ang) * rad
        z, slope = net.cell(x, y)
        if z <= SEA_SURFACE_Z:
            z = SEA_SURFACE_Z + 200.0   # author on the island shoulder; raycast snaps
        kind = rng.choice(list(REEF_FLORA.keys()))
        s = rng.uniform(0.8, 1.4)
        placements.append({
            "id": f"FL_Balcony_{k:03d}",
            "zone": "BalconyFlora",
            "mesh": REEF_FLORA[kind],
            "material": MEGASCAN_ISLAND_MI,
            "position": [round(x, 1), round(y, 1), round(z, 1)],
            "height_cm": round(z, 1),
            "clearance_cm": 5.0,
            "rotation": [0.0, 0.0, round(rng.uniform(0, 360), 2)],
            "scale": [round(s, 3), round(s, 3), round(s, 3)],
            "path_falloff": round(path_falloff(x, y), 4),
            "slope_deg": round(slope, 2),
        })

    # --- MooringDress: overlook mooring environs (-5099, 5821) ---
    mx_, my_ = MOORING
    for k in range(TARGET_COUNTS["MooringDress"]):
        ang = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(300.0, 1400.0)
        x = mx_ + math.cos(ang) * rad
        y = my_ + math.sin(ang) * rad
        z, slope = net.cell(x, y)
        if z <= SEA_SURFACE_Z:
            z = SEA_SURFACE_Z + 150.0
        kind = rng.choice(["fern", "boston", "chime", "clover"])
        s = rng.uniform(0.8, 1.5)
        placements.append({
            "id": f"FL_Mooring_{k:03d}",
            "zone": "MooringDress",
            "mesh": MEGASCAN_PLANTS.get(kind) or REEF_FLORA.get(kind),
            "material": MEGASCAN_ISLAND_MI,
            "position": [round(x, 1), round(y, 1), round(z, 1)],
            "height_cm": round(z, 1),
            "clearance_cm": 5.0,
            "rotation": [0.0, 0.0, round(rng.uniform(0, 360), 2)],
            "scale": [round(s, 3), round(s, 3), round(s, 3)],
            "path_falloff": round(path_falloff(x, y), 4),
            "slope_deg": round(slope, 2),
        })

    return {
        "schema": SCHEMA,
        "version": "1.0.0",
        "level": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
        "landscape": "CanonicalLandscape (used, never created)",
        "sea_surface_z_uu": SEA_SURFACE_Z,
        "seed": seed,
        "density_rule": "island cells Z>13455; phi falloff from loop; slope gate >35deg reject",
        "height_contract": "height_cm = landscape surface; editor raycasts and snaps Z = surface + clearance",
        "total_points": len(placements),
        "zone_summaries": {z: {"count": sum(1 for p in placements if p["zone"] == z)} for z in ("IslandFoliage", "BalconyFlora", "MooringDress")},
        "placements": placements,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="specs/water_veil/sea_above_foliage.v1.json")
    ap.add_argument("--layers", default="Saved/Audit/sea_above_layers.npz")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out).resolve()
    if args.verify:
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["schema"] == SCHEMA
        assert len(data["placements"]) == data["total_points"]
        assert all(p["height_cm"] is not None for p in data["placements"])
        print(f"verified {out.name}: total={data['total_points']} zones={data['zone_summaries']}")
        return 0
    import numpy as np
    npz = np.load(args.layers, allow_pickle=True)
    layers = {k: npz[k] for k in npz.files}
    m = generate(layers=layers)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"wrote {out} total={m['total_points']} zones={m['zone_summaries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())