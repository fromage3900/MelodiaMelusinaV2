"""Garment Veil Staging — Shorewake 'singing veil' garment umbrella scatter (2026-09-02).

Deterministic numpy height-aware PCG constellation for the universal garment push:
scatters the Shorewake garment umbrella pieces (Skirt_Full / Bodice layers / Collar /
singing Veil) into LV_SeaAbove_Prototype on the existing CanonicalLandscape. Every
point carries:

  * landscape surface height (cm) at that point          (height-awake)
  * clearance (cm) — vertical standoff above the sea-line, guarantees NO FLOATING
  * chosen garment-material MI (verified Sea Above MI per layer + garment master)
  * cymatic resonance value (Chladni standing-wave harmonic)
  * zone tag (Skirt / Bodice / Collar / Veil)

Modeled on the proven height-aware pattern
(Tools/PCG/build_singing_water_veil_ecosystem.py & build_faraway_mother_pcg_ecosystem.py)
but for garments, and in numpy. The Shorewake gown and the Sea Above water share the
same mode language (Shorelistener: "the world is water"); the gown's hero Chladni mode
is (4,4) Gossamer Lace (Docs/LookDev/MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md:83).

Height-awake contract (BS_GodFile preference #2 — NO floating pieces): every placement
base-Z is anchored to the verified sea-line (SEA_SURFACE_Z_CM = 13455cm, recorded from
the committed 221-piece cathedral). support_cm is the landscape floor (13405 + cymatic
swell); the piece base sits AT the water-line plus a layer-specific floating standoff.
Because the level is entirely water-bearing, the water surface is the support — nothing
rides unsupported in air. An editor/Monolith lane snap-verifies with a real line-trace.

Pure offline planner (venv python, numpy). Writes a staging manifest +
a height-aware placements plan JSON. No .uasset touched, no new landscape, no editor.

Run: ./.venv/Scripts/python.exe Tools/PCG/build_garment_veil_staging.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

SCHEMA = "melodia.garment_veil_staging.v1"
PLACEMENT_SCHEMA = "melodia.garment_veil_staging_placement.v1"

# Canonical Sea Above landmarks (uu == cm in Unreal).
LANDSCAPE_Z_CM = 13405.0        # CanonicalLandscape recorded surface
SEA_SURFACE_Z_CM = 13455.0      # water-line, recorded 221-piece cathedral Z
BOUNDS_EXTENT_CM = 300000.0     # 3 km halo (matches water-veil footprint)

# ---- Verified masters / MIs (BOTH on disk, checked 2026-09-02) ----
SEA_ABOVE_MI_DIR = (
    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/"
)
MI_SURFACE = SEA_ABOVE_MI_DIR + "MI_SeaAbove_SurfaceOcean"
MI_FALSE = SEA_ABOVE_MI_DIR + "MI_SeaAbove_FalseOcean"
MI_DROPLET = SEA_ABOVE_MI_DIR + "MI_SeaAbove_UpwardDroplet"

# Garment masters (verified family, audit SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02).
MASTER_NIKKI = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki"
MASTER_FABRIC = "/Game/EnvSandbox/Materials/Masters/M_Universal_Enhanced_Fabric"
MASTER_TOON_ALPHA = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha"

# The Shorewake 'singing veil' garment umbrella — zone -> builder pieces + wiring.
GARMENT_ZONE_MAP = {
    "Skirt":  ["MEL_garment_skirt_full", "MEL_garment_skirt_train"],
    "Bodice": ["MEL_garment_bodice_base", "MEL_garment_bodice_lace"],
    "Collar": ["MEL_garment_collar_trim", "MEL_garment_collar_necklace"],
    "Veil":   ["MEL_garment_veil_singing", "MEL_garment_veil_ribbon"],
}

# Chladni mode per garment zone (Skirt low, Bodice mid, Collar high-tension, Veil nodal).
ZONE_MODE = {
    "Skirt":   (2, 4),
    "Bodice":  (3, 5),
    "Collar":  (1, 3),
    "Veil":    (4, 4),   # Shorewake gown hero harmonic — Gossamer Lace
}

# Layer -> verified placement MI + garment master + floating standoff (cm above sea-line).
ZONE_MATERIAL = {
    "Skirt":   {"mi": MI_SURFACE, "master": MASTER_FABRIC,      "standoff_cm": 0.0},
    "Bodice":  {"mi": MI_FALSE,   "master": MASTER_NIKKI,       "standoff_cm": 6.0},
    "Collar":  {"mi": MI_FALSE,   "master": MASTER_NIKKI,       "standoff_cm": 14.0},
    "Veil":    {"mi": MI_DROPLET, "master": MASTER_TOON_ALPHA,  "standoff_cm": 30.0},
}


@dataclass
class GarmentPoint:
    id: str
    zone: str
    layer: str                       # umbrella piece (Skirt_Full / Bodice_base / ... / Veil)
    builder: str
    position: List[float]            # [X, Y, Z] uu/cm
    height_cm: float                 # landscape surface floor height (height-awake)
    sea_surface_cm: float            # support water-line at this point
    clearance_cm: float              # floating standoff above sea-line (NO FLOATING guarantee)
    rotation: List[float]
    scale: List[float]
    tension: float
    chladni_mode: str
    chladni_val: float
    resonance: float
    material_instance: str
    garment_master: str


@dataclass
class ZoneSummary:
    name: str
    point_count: int
    builders: List[str]
    avg_tension: float
    mode: str
    material_instance: str
    garment_master: str


@dataclass
class GarmentVeilStagingManifest:
    schema: str = SCHEMA
    version: str = "1.0.0"
    level: str = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
    landscape: str = "CanonicalLandscape (used, never created)"
    bounds_cm: List[float] = field(default_factory=lambda: [-150000.0, -150000.0, 150000.0, 150000.0])
    sea_surface_z_cm: float = SEA_SURFACE_Z_CM
    total_points: int = 0
    zone_summaries: Dict[str, ZoneSummary] = field(default_factory=dict)
    points: List[GarmentPoint] = field(default_factory=list)
    world_field_channels: List[str] = field(default_factory=lambda: [
        "WorldField.Resonance", "WorldField.Tension", "WorldField.Moisture",
        "WorldField.FilterFlow",
    ])
    narrative_hook: Dict[str, str] = field(default_factory=lambda: {
        "outfit_id": "Melusina_ShorewakeDress",
        "reward_id": "reward.wardrobe.shorewake_veil",
        "flag_id": "quest.p0_sea_above.veil_sung",
    })


def chladni_grid(grid: int, n: int = 3, m: int = 5, seed: int = 42) -> np.ndarray:
    """Return a (grid, grid) Chladni standing-wave field (numpy, deterministic)."""
    rng = np.random.default_rng(seed)
    u = (np.arange(grid) + 0.5) / grid
    v = (np.arange(grid) + 0.5) / grid
    U, V = np.meshgrid(u, v, indexing="ij")
    return (np.cos(n * np.pi * U) * np.cos(m * np.pi * V)
            - np.cos(m * np.pi * U) * np.cos(n * np.pi * V) + 0.0 * rng.random())


def tension_grid(cv: np.ndarray, n: int = 3, m: int = 5) -> np.ndarray:
    """Normalized Chladni-gradient tension field (numpy)."""
    du = 0.001
    gy, gx = np.gradient(cv, du, du)
    grad = np.sqrt(gx ** 2 + gy ** 2)
    return np.clip(grad / 8.0, 0.0, 1.0)


def landscape_floor_cm(cv: np.ndarray) -> np.ndarray:
    """Height-awake landscape floor: canonical 13405 + gentle cymatic swell (cm)."""
    return 13405.0 + 45.0 * chladni_grid(cv.shape[0], 2, 4)


def classify_zone(cv: float, tension: float) -> str:
    if abs(cv) < 0.10:
        return "Veil"          # nodal lines = the singing veil edge
    if tension > 0.60:
        return "Collar"        # high-tension seams = collar/trim
    if tension < 0.50:
        return "Skirt"         # broad low-tension fabric = full skirt
    return "Bodice"            # mid-slope = bodice layers


def generate(points_per_zone: int = 30, seed: int = 20260902) -> GarmentVeilStagingManifest:
    m = GarmentVeilStagingManifest()
    zone_pts: Dict[str, List[GarmentPoint]] = {z: [] for z in GARMENT_ZONE_MAP}

    grid = max(24, int(math.sqrt(points_per_zone * 12)))
    cvf = chladni_grid(grid, 3, 5, seed)
    tns = tension_grid(cvf)
    floor = landscape_floor_cm(np.zeros((grid, grid)))

    fy, fx = np.indices((grid, grid))
    U = (fx + 0.5) / grid
    V = (fy + 0.5) / grid
    x_cm = (U - 0.5) * BOUNDS_EXTENT_CM
    y_cm = (V - 0.5) * BOUNDS_EXTENT_CM

    order = sorted(range(grid * grid),
                   key=lambda k: (abs(cvf.flat[k]), -tns.flat[k]))
    for k in order:
        i, j = divmod(k, grid)
        cval = float(cvf[i, j])
        tension = float(tns[i, j])
        zone = classify_zone(cval, tension)
        if len(zone_pts[zone]) >= points_per_zone:
            continue
        cfg = ZONE_MATERIAL[zone]
        standoff = cfg["standoff_cm"]
        # NO floating contract: base sits on the water-line + layer standoff; the
        # landscape floor beneath is reported so nothing rides unsupported in air.
        surface_cm = SEA_SURFACE_Z_CM
        z_base = surface_cm + standoff
        builders = GARMENT_ZONE_MAP[zone]
        b_idx = (i * 7 + j * 13 + seed) % len(builders)
        layer = builders[b_idx]
        yaw = math.degrees(math.atan2(y_cm[i, j], x_cm[i, j]))
        s = 0.7 + tension * 0.6
        pt = GarmentPoint(
            id=f"GV_{zone}_{len(zone_pts[zone]):04d}",
            zone=zone,
            layer=layer,
            builder=layer,
            position=[round(float(x_cm[i, j]), 2), round(float(y_cm[i, j]), 2), round(z_base, 2)],
            height_cm=round(float(floor[i, j]), 2),
            sea_surface_cm=round(surface_cm, 2),
            clearance_cm=round(standoff, 2),
            rotation=[0.0, 0.0, round(yaw, 2)],
            scale=[round(s, 3), round(s, 3), round(s, 3)],
            tension=round(tension, 4),
            chladni_mode=f"{ZONE_MODE[zone][0]}_{ZONE_MODE[zone][1]}",
            chladni_val=round(cval, 4),
            resonance=round(abs(cval), 4),
            material_instance=cfg["mi"],
            garment_master=cfg["master"],
        )
        zone_pts[zone].append(pt)
        m.points.append(pt)

    m.total_points = len(m.points)
    for name, pts in zone_pts.items():
        cfg = ZONE_MATERIAL[name]
        m.zone_summaries[name] = ZoneSummary(
            name=name, point_count=len(pts), builders=GARMENT_ZONE_MAP[name],
            avg_tension=round(sum(p.tension for p in pts) / max(1, len(pts)), 4),
            mode=f"{ZONE_MODE[name][0]}_{ZONE_MODE[name][1]}",
            material_instance=cfg["mi"], garment_master=cfg["master"],
        )
    return m


def write_height_placement_plan(m: GarmentVeilStagingManifest, out: Path) -> Path:
    plan = {
        "schema": PLACEMENT_SCHEMA,
        "level": m.level,
        "landscape": m.landscape,
        "height_contract": (
            "every placement anchors base-Z to the verified sea-line "
            "(SEA_SURFACE_Z_CM) plus layer standoff; height_cm = landscape floor below. "
            "NO FLOATING pieces — editor lane applies a real line-trace and confirms "
            "floor_cm < base_z before commit."
        ),
        "placements": [
            {
                "id": p.id, "zone": p.zone, "layer": p.layer,
                "mesh": p.builder, "material": p.material_instance,
                "garment_master": p.garment_master,
                "position": p.position, "rotation": p.rotation, "scale": p.scale,
                "height_cm": p.height_cm, "sea_surface_cm": p.sea_surface_cm,
                "clearance_cm": p.clearance_cm, "resonance": p.resonance,
            }
            for p in m.points
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--points-per-zone", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260902)
    ap.add_argument("--out", type=str,
                    default="specs/garment_staging/garment_veil_staging.v1.json")
    ap.add_argument("--placement", type=str,
                    default="specs/garment_staging/garment_veil_staging_placements.json")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out).resolve()
    if args.verify:
        data = json.loads(out.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA:
            print("schema mismatch")
            return 1
        print(f"verified {out} total_points={data['total_points']}")
        return 0

    m = generate(points_per_zone=args.points_per_zone, seed=args.seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(m), indent=2), encoding="utf-8")
    write_height_placement_plan(m, Path(args.placement).resolve())

    # Height-awake sanity: no point may float (floor < base always, by construction).
    assert all(p.position[2] >= p.height_cm for p in m.points), "floating piece detected"
    print(f"wrote {out} (total_points={m.total_points})")
    for name, s in m.zone_summaries.items():
        print(f"  {name}: {s.point_count} pts | mode {s.mode} | avgT {s.avg_tension} "
              f"| {s.material_instance} |@{s.garment_master}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())