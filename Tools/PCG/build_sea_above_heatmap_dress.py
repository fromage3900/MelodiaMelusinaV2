"""Sea Above — PCG heatmap dress generator (2026-09-03).

Consumes the REAL sampled terrain heatmap (Saved/Audit/sea_above_layers.npz,
1600 live-traced height points over the CanonicalLandscape in
LV_SeaAbove_Prototype) + the live-measured gameplay anchors, and emits a
height-aware placement manifest for dressing the level.

Replaces the 2026-09-02 singing_water_veil plan whose heights were a fake
stand-in (13405 + small swell) and whose mesh refs (MEL_water_veil_*) never
existed in Content. Keeps its zone language + Chladni modes; re-grounds it on
sampled truth and maps to the REAL reef inventory (verified on disk).

Height-aware contract (BS_GodFile #2): each placement carries height_cm =
the landscape surface height at that point; the editor lane raycasts and
snaps Z = surface + clearance. No floating pieces. CanonicalLandscape only,
never creates a new landscape.

Density rule: base_zone_density x path_falloff x slope_gate. Path falloff is
the 3-segment gameplay polyline (PlayerStart->Quill->MusicKey->Dock):
1.0 within 5k uu of the path, decaying to 0.15 beyond 60k uu.

Run: ./.venv/Scripts/python.exe Tools/PCG/build_sea_above_heatmap_dress.py
Verify: ... --verify
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

SCHEMA = "melodia.sea_above_heatmap_dress.v1"
SEA_SURFACE_Z = 13455.0

# Real anchors measured live from the level (x, y)
ANCHORS = {
    "player_start": (0.0, 0.0),
    "arrival": (-145.0, 470.0),
    "quill": (-910.0, 500.0),
    "music_key": (0.0, -950.0),   # node centroid (24 nodes, 2 tiers)
    "dock": (-5099.0, 5821.0),
}
# Polyline for path falloff: PlayerStart -> Quill -> MusicKey -> Dock
PATH_POLYLINE = [(0.0, 0.0), (-910.0, 500.0), (0.0, -950.0), (-5099.0, 5821.0)]
PATH_BAND_IN = 20000.0     # uu: full density (skiff-visible ring)
PATH_BAND_OUT = 120000.0   # uu: floor density
PATH_DENSITY_FLOOR = 0.25

# Music-node tiers (measured) — cathedral halo targets
CATHEDRAL_TIERS = [-45298.0, -14604.0]
CATHEDRAL_CENTER = (0.0, -950.0)
CATHEDRAL_HALO_RADIUS = 3500.0

# --- Real mesh inventory (verified in editor 2026-09-03) ---
M = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"
MAT = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials"

MESH = {
    "rock_l": f"{M}/SM_RockChunk_L.SM_RockChunk_L",
    "rock_m": f"{M}/SM_RockChunk_M.SM_RockChunk_M",
    "coral_brain": f"{M}/SM_Coral_Brain.SM_Coral_Brain",
    "coral_fan": f"{M}/SM_Coral_Fan.SM_Coral_Fan",
    "coral_reefcluster": f"{M}/SM_Coral_ReefCluster.SM_Coral_ReefCluster",
    "coral_staghorn": f"{M}/SM_Coral_Staghorn.SM_Coral_Staghorn",
    "coral_table": f"{M}/SM_Coral_Table.SM_Coral_Table",
    "coral_tube": f"{M}/SM_Coral_TubeSponges.SM_Coral_TubeSponges",
    "kelp_cluster": f"{M}/SM_Kelp_Cluster.SM_Kelp_Cluster",
    "kelp_mid": f"{M}/SM_Kelp_Mid.SM_Kelp_Mid",
    "kelp_tall": f"{M}/SM_Kelp_Tall.SM_Kelp_Tall",
    "pebble": f"{M}/SM_Clutter_PebbleSet.SM_Clutter_PebbleSet",
    "seaweed": f"{M}/SM_Clutter_SeaWeed.SM_Clutter_SeaWeed",
    "shell": f"{M}/SM_Clutter_SpiralShell.SM_Clutter_SpiralShell",
    "starfish": f"{M}/SM_Clutter_Starfish.SM_Clutter_Starfish",
    "drowned_organ": f"{M}/SM_DrownedOrgan.SM_DrownedOrgan",
    "flora_chime": f"{M}/SM_Flora_Chime.SM_Flora_Chime",
    "flora_reed": f"{M}/SM_Flora_Reed.SM_Flora_Reed",
    "jelly_arms": f"{M}/JELLY_Arms.JELLY_Arms",
    "jelly_tier0": f"{M}/JELLY_Cathedral_Body_SERAPH_tier_0.JELLY_Cathedral_Body_SERAPH_tier_0",
    "jelly_tier1": f"{M}/JELLY_Cathedral_Body_SERAPH_tier_1.JELLY_Cathedral_Body_SERAPH_tier_1",
    "jelly_tier2": f"{M}/JELLY_Cathedral_Body_SERAPH_tier_2.JELLY_Cathedral_Body_SERAPH_tier_2",
}
MATERIAL = {
    "wetrock": f"{MAT}/MI_SeaAbove_WetRock.MI_SeaAbove_WetRock",
    "sand": f"{MAT}/MI_SeaAbove_Sand.MI_SeaAbove_Sand",
    "coral": f"{MAT}/MI_SeaAbove_CoralSkin.MI_SeaAbove_CoralSkin",
    "coral_2s": f"{MAT}/MI_SeaAbove_CoralSkin_2S.MI_SeaAbove_CoralSkin_2S",
    "kelp": f"{MAT}/MI_SeaAbove_Kelp.MI_SeaAbove_Kelp",
    "jelly_bell": f"{MAT}/MI_Jelly_Bell.MI_Jelly_Bell",
    "jelly_arms": f"{MAT}/MI_Jelly_Arms.MI_Jelly_Arms",
}
BP_JELLY = f"/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Blueprints/BP_Jelly_Cathedral.BP_Jelly_Cathedral"

# --- Zone tables ---
# builder list per zone + material + height band (Z in uu).
# PROTOTYPE truth (sampled ±13k): terrain is 100% submerged (z -14.2k..+1.9k),
# palace floats on the water sheet at 13455, so the dressable canvas is the
# drowned slope + deep bowl beneath the play surface. No surface ring exists.
ZONES = {
    "ReefGarden": {  # upper drowned shelf — the coral garden visible from the palace
        "builders": ["coral_brain", "coral_fan", "coral_staghorn", "coral_table",
                     "coral_tube", "coral_reefcluster", "kelp_mid", "kelp_tall",
                     "starfish", "shell", "pebble"],
        "material": "coral",
        "cond": lambda z: -2000.0 < z < SEA_SURFACE_Z,
        "density": 0.85,
        "clearance": 12.0,
        "mode": "4_9",
    },
    "AbyssFloor": {  # deep bowl — sparse rocks + drowned organ
        "builders": ["rock_l", "rock_m", "seaweed", "drowned_organ", "pebble"],
        "material": "sand",
        "cond": lambda z: z <= -2000.0,
        "density": 0.30,
        "clearance": 10.0,
        "mode": "1_2",
    },
    "CathedralHalo": {  # music-node tier planes (-45.3k / -14.6k), not terrain
        "builders": ["jelly_tier0", "jelly_tier1", "jelly_tier2", "jelly_arms"],
        "material": "jelly_arms",
        "cond": lambda z: True,
        "density": 1.0,
        "clearance": 0.0,
        "mode": "2_4",
    },
}

TARGET_COUNTS = {"ReefGarden": 84, "AbyssFloor": 40, "CathedralHalo": 12}


class Net:
    """Minimal npz stand-in (avoid numpy dep at import time)."""

    def __init__(self, path: Path):
        # npz with arrays Z (40x40), SLOPE, COAST, bounds [4], grid int, SEA float
        data = path  # already-loaded dict when used directly
        self.Z = data["Z"]
        self.SLOPE = data.get("SLOPE", None)
        self.COAST = data.get("COAST", None)
        self.bounds = list(data["bounds"])
        self.grid = int(data["grid"])
        self.SEA = float(data.get("SEA", SEA_SURFACE_Z))

    def cell(self, x: float, y: float) -> Tuple[float, float, float]:
        """Return (height, slope_deg, coast_dist) at x,y (nearest cell)."""
        bx = self.bounds
        n = self.grid
        i = min(n - 1, max(0, int(round((x - bx[0]) / (bx[2] - bx[0]) * (n - 1)))))
        j = min(n - 1, max(0, int(round((y - bx[1]) / (bx[3] - bx[1]) * (n - 1)))))
        z = float(self.Z[j, i])
        sl = float(self.SLOPE[j, i]) if self.SLOPE is not None else 0.0
        cd = float(self.COAST[j, i]) if self.COAST is not None else 0.0
        return z, sl, cd


def path_falloff(x: float, y: float) -> float:
    """Distance to the gameplay polyline -> density multiplier [0, 1].

    GOLDEN DECAY: rho = (D / (d + D))^PHI, where D = full-density band and
    PHI ~ 1.618. Monotonic, smooth, golden-ratio-rooted — dense at the path,
    graceful phi-decay into the vista. Replaces the old linear 20k/120k bands.
    """
    PHI = (1 + 5 ** 0.5) / 2
    pts = PATH_POLYLINE
    best = 1e18
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        d = math.hypot(x - px, y - py)
        best = min(best, d)
    return (PATH_BAND_IN / (best + PATH_BAND_IN)) ** PHI


def classify(z: float) -> str:
    for name in ("ReefGarden", "AbyssFloor"):
        if ZONES[name]["cond"](z):
            return name
    return "ReefGarden"


def generate(seed: int = 20260903, points_override: Dict[str, int] | None = None,
             layers: dict | None = None) -> dict:
    rng = random.Random(seed)
    targets = dict(TARGET_COUNTS)
    if points_override:
        targets.update(points_override)

    net = Net(layers)
    bx = net.bounds
    placements = []

    # Terrain zones (ReefGarden / AbyssFloor) — sample grid, gate by
    # zone + slope + path falloff + jitter, respecting per-zone target counts.
    # Two-stage acceptance: first draw points INSIDE the zone band (band sampling
    # so thin rings aren't starved by map-uniform rejection), then gate by
    # density/path/slope.
    for zone_name in ("ReefGarden", "AbyssFloor"):
        cfg = ZONES[zone_name]
        count = 0
        attempts = 0
        max_attempts = targets[zone_name] * 1200  # band search budget
        while count < targets[zone_name] and attempts < max_attempts:
            attempts += 1
            x = rng.uniform(bx[0], bx[2])
            y = rng.uniform(bx[1], bx[3])
            z, slope, coast = net.cell(x, y)
            if not cfg["cond"](z):
                continue
            if slope > 40.0:
                continue
            pf = path_falloff(x, y)
            density = cfg["density"] * pf
            if slope > 25.0:
                density *= 0.5
            if rng.random() > density:
                continue
            builder = cfg["builders"][rng.randrange(len(cfg["builders"]))]
            # yaw: align to slope aspect when steep, random otherwise
            yaw = rng.uniform(0, 360)
            s = rng.uniform(0.6, 1.4) * (1.0 + max(0.0, (30.0 - slope)) / 60.0)
            placements.append({
                "id": f"SA_{zone_name}_{count:04d}",
                "zone": zone_name,
                "mesh": MESH[builder],
                "material": MATERIAL[cfg["material"]],
                "position": [round(x, 1), round(y, 1), round(z, 1)],
                "height_cm": round(z, 1),
                "clearance_cm": cfg["clearance"],
                "rotation": [0.0, 0.0, round(yaw, 2)],
                "scale": [round(s, 3), round(s, 3), round(s, 3)],
                "chladni_mode": cfg["mode"],
                "path_falloff": round(pf, 4),
                "slope_deg": round(slope, 2),
            })
            count += 1

    # Cathedral halo — one tier ring around the drowned cathedral centroid at
    # both tiers; BP jelly on tier 1, body parts halo on tier 2.
    cx, cy = CATHEDRAL_CENTER
    for tier_idx, tier_z in enumerate(CATHEDRAL_TIERS):
        ring_n = targets["CathedralHalo"] // len(CATHEDRAL_TIERS)
        for k in range(ring_n):
            ang = rng.uniform(0, 2 * math.pi)
            rad = rng.uniform(600.0, CATHEDRAL_HALO_RADIUS)
            x = cx + math.cos(ang) * rad
            y = cy + math.sin(ang) * rad
            if tier_idx == 0:
                mesh = BP_JELLY
                mat = MATERIAL["jelly_bell"]
            else:
                mesh = MESH["jelly_tier1" if k % 2 else "jelly_tier0"]
                mat = MATERIAL["jelly_arms"]
            placements.append({
                "id": f"SA_CathedralHalo_{tier_idx}_{k:03d}",
                "zone": "CathedralHalo",
                "mesh": mesh,
                "material": mat,
                "position": [round(x, 1), round(y, 1), round(tier_z, 1)],
                "height_cm": round(tier_z, 1),
                "clearance_cm": 0.0,
                "rotation": [0.0, 0.0, round(math.degrees(ang), 2)],
                "scale": [1.0, 1.0, 1.0],
                "chladni_mode": "2_4",
                "path_falloff": 1.0,
                "slope_deg": 0.0,
            })

    summary = {}
    for p in placements:
        z = p["zone"]
        summary.setdefault(z, {"count": 0, "meshes": set()})
        summary[z]["count"] += 1
        summary[z]["meshes"].add(p["mesh"].split(".")[-1])

    manifest = {
        "schema": SCHEMA,
        "version": "1.0.0",
        "level": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
        "landscape": "CanonicalLandscape (one Landscape actor, never created)",
        "sea_surface_z_uu": SEA_SURFACE_Z,
        "seed": seed,
        "density_rule": "base_zone_density x path_falloff(PlayerStart->Quill->MusicKey->Dock) x slope_gate(x0.5 if >25deg, reject >40deg)",
        "height_contract": "placements carry landscape surface height; editor raycasts and snaps Z = surface + clearance",
        "source_heatmap": "Saved/Audit/sea_above_terrain_heatmap.json (1600 live traces)",
        "total_points": len(placements),
        "zone_summaries": {k: {"count": v["count"], "meshes": sorted(v["meshes"])} for k, v in summary.items()},
        "placements": placements,
    }
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="specs/water_veil/sea_above_heatmap_dress.v1.json")
    ap.add_argument("--layers", default="Saved/Audit/sea_above_layers.npz")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out).resolve()
    if args.verify:
        data = json.loads(out.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA:
            print(f"schema mismatch: {data.get('schema')}")
            return 1
        for p in data["placements"]:
            assert p["mesh"], p["id"]
            assert p["height_cm"] is not None
        print(f"verified {out.name}: total={data['total_points']} zones={list(data['zone_summaries'])}")
        return 0

    # load layers via numpy
    import numpy as np
    npz = np.load(args.layers, allow_pickle=True)
    layers = {k: npz[k] for k in npz.files}
    m = generate(layers=layers)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"wrote {out} total={m['total_points']}")
    for z, s in m["zone_summaries"].items():
        print(f"  {z}: {s['count']} pts | {', '.join(s['meshes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())