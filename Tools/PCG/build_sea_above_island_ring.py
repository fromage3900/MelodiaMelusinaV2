"""Sea Above — golden-radius silhouette island ring generator (2026-09-03).

Prep deliverable for LV_SeaAbove_Prototype horizon dressing (mission B of
SEA_ABOVE_FINAL_EXECUTION_PLAN_2026-09-03): flat fog-tinted silhouette
island cards placed at GOLDEN radii along the design spine, read from the
palace as distant-island silhouettes sitting on the waterline.

Golden radii (phi-scaled, 5k..55k uu): 5000, 8090, 13090, 21180, 34270,
55420. Each inner radius carries 4 deterministic angles; consecutive points
are offset by the golden angle 137.50776 deg (spiral pacing, seed-locked).
Two far spires at 55.42k close the composition. All points Z=13455 (horizon
is the waterline), all inside landscape bounds (+-250k uu).

Geometry/mesh decision (verified on disk 2026-09-03):
  - No flat silhouette-card mesh exists in Content (SM_Island_* measured
    z-ratio ~1.0; no SM_Cliff*, no SM_Spire*). Chosen proxy: the REAL
    sea-above island tier SM_Island_A/B/C (Content/EnvSandbox/Monoliths/
    SeaAbove/Prototype/Reef/Meshes/) scaled up s_xy 2-4.5x and flattened
    z-scale = 0.5*s_xy so they read as distant islands (flat_ratio ~0.5).
  - Material: REAL Megascans photo-scan MI_ForestRockFormation_01
    (Content/Megascans/3D_Assets/ForestRockFormation/), the AAA island tier.
    Fog tint is NOT baked here — the editor lane must apply distance-fog /
    PPV tint so cards read as fog-tinted silhouettes (fade_note per card).

Height-aware contract (BS_GodFile #2): placement height_cm is the surface
(sea sheet at 13455) datum; editor lane snaps Z = surface + clearance.
No new landscape, no editor mutation from this tool.

Run: ./.venv/Scripts/python.exe Tools/PCG/build_sea_above_island_ring.py
Verify: ... --verify
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Dict, List

SCHEMA = "melodia.sea_above_island_ring.v1"
SEA_SURFACE_Z = 13455.0
GOLDEN_ANGLE_DEG = 137.50776405003785   # 360 / phi^2 — golden-angle offset
PHI = 1.618033988749895

# Golden radii along the spiral (uu) — 5 inner rings + far spire ring
RADII = [5000.0, 8090.0, 13090.0, 21180.0, 34270.0]
FAR_SPIRE_RADIUS = 55420.0
# angles per inner radius (4 each -> 20 pts) + 2 far spires = 22 total
ANGLES_PER_RING = [4, 4, 4, 4, 4]
FAR_SPIRES = 2
BOUNDS = 250000.0  # landscape half-extent; |x|,|y| must stay inside +-250k

# Real mesh inventory (verified on disk 2026-09-03 — OBJ dims measured)
M = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"
ISLAND_MESH = {
    "A": f"{M}/SM_Island_A.SM_Island_A",   # 11.88 x 7.32 x 12.13 uu
    "B": f"{M}/SM_Island_B.SM_Island_B",   #  7.92 x 5.83 x  8.09 uu
    "C": f"{M}/SM_Island_C.SM_Island_C",   # 15.84 x 8.89 x 16.17 uu
}
# mesh per ring (homogeneous ring read) + far spires
RING_MESH = ["A", "B", "C", "A", "B"]
SPIRE_MESH = "C"
# xy scale per ring (larger silhouettes at larger radii)
RING_SCALE = [2.5, 3.0, 3.5, 4.0, 4.5]
SPIRE_SCALE = 6.0
FLAT_Z_SCALE = 0.5  # z-scale = s_xy * this -> flat_ratio ~0.5 distant island
SPIRE_Z_SCALE = 1.6  # far spires stay tall

# AAA island-tier material (verified on disk)
MAT_PATH = "/Game/Megascans/3D_Assets/ForestRockFormation/MI_ForestRockFormation_01"
MATERIAL = f"{MAT_PATH}.MI_ForestRockFormation_01"

LEVEL = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
LANDSCAPE = "CanonicalLandscape (one Landscape actor, never created)"


def generate(seed: int = 20260903) -> dict:
    """Deterministic golden-angle ring manifest (no editor, pure math)."""
    rng = random.Random(seed)
    # deterministic global spiral base angle from the seed
    base_angle = rng.uniform(0.0, 360.0)
    placements: List[dict] = []
    i = 0  # global point counter -> consecutive golden-angle offsets

    for ri, radius in enumerate(RADII):
        mesh = ISLAND_MESH[RING_MESH[ri]]
        s_xy = RING_SCALE[ri]
        for k in range(ANGLES_PER_RING[ri]):
            ang_deg = (base_angle + i * GOLDEN_ANGLE_DEG) % 360.0
            rad = radius * (1.0 + rng.uniform(-0.03, 0.03))  # tiny jitter
            x = math.cos(math.radians(ang_deg)) * rad
            y = math.sin(math.radians(ang_deg)) * rad
            assert abs(x) < BOUNDS and abs(y) < BOUNDS, (x, y)
            sx = s_xy * (1.0 + rng.uniform(-0.15, 0.15))
            sz = sx * FLAT_Z_SCALE
            yaw = (ang_deg + 90.0 + rng.uniform(-12.0, 12.0)) % 360.0  # broadside to center
            placements.append({
                "id": f"SA_IslandRing_R{int(radius) // 1000}k_{k:02d}",
                "zone": "IslandRing",
                "role": "silhouette",
                "mesh": mesh,
                "material": MATERIAL,
                "position": [round(x, 1), round(y, 1), SEA_SURFACE_Z],
                "rotation": [0.0, 0.0, round(yaw, 2)],
                "scale": [round(sx, 3), round(sx, 3), round(sz, 3)],
                "height_cm": 0.0,           # datum = sea sheet at 13455
                "clearance_cm": 0.0,        # card sits AT the waterline
                "radius_uu": round(rad, 1),
                "fade_note": "fog-tint by editor lane (distance fog/PPV); "
                             "card reads silhouette against horizon",
            })
            i += 1

    # far spire ring at 55.42k — 2 tall cards closing the golden spiral
    mesh_sp = ISLAND_MESH[SPIRE_MESH]
    for k in range(FAR_SPIRES):
        ang_deg = (base_angle + i * GOLDEN_ANGLE_DEG) % 360.0
        rad = FAR_SPIRE_RADIUS * (1.0 + rng.uniform(-0.02, 0.02))
        x = math.cos(math.radians(ang_deg)) * rad
        y = math.sin(math.radians(ang_deg)) * rad
        assert abs(x) < BOUNDS and abs(y) < BOUNDS, (x, y)
        sx = SPIRE_SCALE * (1.0 + rng.uniform(-0.10, 0.10))
        sz = sx * SPIRE_Z_SCALE
        yaw = (ang_deg + 90.0 + rng.uniform(-12.0, 12.0)) % 360.0
        placements.append({
            "id": f"SA_IslandRing_FarSpire_{k:02d}",
            "zone": "IslandRing",
            "role": "silhouette",
            "mesh": mesh_sp,
            "material": MATERIAL,
            "position": [round(x, 1), round(y, 1), SEA_SURFACE_Z],
            "rotation": [0.0, 0.0, round(yaw, 2)],
            "scale": [round(sx, 3), round(sx, 3), round(sz, 3)],
            "height_cm": 0.0,
            "clearance_cm": 0.0,
            "radius_uu": round(rad, 1),
            "fade_note": "far spire silhouette; editor lane may substitute a "
                         "cathedral-spire mesh (SM_Cathedral_Chapel) + fog tint",
        })
        i += 1

    # zone summaries: per-ring granularity
    summary: Dict[str, dict] = {}
    for p in placements:
        rid = p["id"].split("_")[2]  # R5k / FarSpire from SA_IslandRing_R5k_00
        key = "FarSpire" if rid.startswith("Far") else rid
        s = summary.setdefault(key, {"count": 0, "meshes": set(), "radii": []})
        s["count"] += 1
        s["meshes"].add(p["mesh"].split(".")[-1])
        s["radii"].append(p["radius_uu"])

    manifest = {
        "schema": SCHEMA,
        "version": "1.0.0",
        "level": LEVEL,
        "landscape": LANDSCAPE,
        "sea_surface_z": SEA_SURFACE_Z,
        "seed": seed,
        "principle": "golden radii 5k-55k, phi-scaled",
        "height_contract": "placement height_cm = sea-sheet datum (Z=13455); "
                           "editor rayscans and snaps Z = surface + clearance",
        "notes": "No flat silhouette-card mesh exists in Content (verified: "
                 "SM_Island_* measured z-ratio ~1.0). Proxy = real sea-above "
                 "island tier SM_Island_A/B/C scaled up, z flattened to "
                 "flat_ratio ~0.5. Material = Megascans AAA island tier "
                 "MI_ForestRockFormation_01. Fog tint applied by editor lane.",
        "total_points": len(placements),
        "zone_summaries": {k: {"count": v["count"],
                               "meshes": sorted(v["meshes"]),
                               "radii_min": round(min(v["radii"]), 1),
                               "radii_max": round(max(v["radii"]), 1)}
                           for k, v in summary.items()},
        "placements": placements,
    }
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="specs/water_veil/sea_above_island_ring.v1.json")
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out).resolve()
    if args.verify:
        data = json.loads(out.read_text(encoding="utf-8"))
        ok = data.get("schema") == SCHEMA
        n = data.get("total_points")
        ok &= n == len(data["placements"])
        ok &= 20 <= n <= 24
        for p in data["placements"]:
            assert p["mesh"], p["id"]
            assert abs(p["position"][0]) < BOUNDS and abs(p["position"][1]) < BOUNDS
            assert p["position"][2] == SEA_SURFACE_Z
            assert p["zone"] == "IslandRing" and p["role"] == "silhouette"
        print(f"verified {out.name}: schema={SCHEMA} ok={bool(ok)} "
              f"total={n} zones={list(data['zone_summaries'])}")
        return 0 if ok else 1

    m = generate(seed=args.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print(f"wrote {out} total={m['total_points']}")
    for z, s in m["zone_summaries"].items():
        print(f"  {z}: {s['count']} pts | {', '.join(s['meshes'])} "
              f"| r {s['radii_min']}..{s['radii_max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())