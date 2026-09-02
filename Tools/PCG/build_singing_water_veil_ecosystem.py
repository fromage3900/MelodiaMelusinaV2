"""Singing Water Veil — Sea Above cymatic water ecosystem (2026-09-02).

Synthesizes a deterministic PCG point constellation + landscape-awake heatmap
placement plan for the "singing water veil" — FLIP-surfaced veil meshes placed
into LV_SeaAbove_Prototype on the existing CanonicalLandscape, each carrying a
cymatic Chladni standing-wave mode (paired with shorewake_cymatic_garment.py:
the garment and the water share the same mode language, Shorelistener: "the
world is water").

Mirrors the proven faraway-mother pattern (Tools/PCG/build_faraway_mother_pcg_ecosystem.py)
but for water. Height-aware contract (BS_GodFile preference #2): every placement
is raycast to the landscape surface — no floating pieces. PBR/MI references target
the verified Sea Above + Melodia masters, no new landscape.

Pure offline generator (venv python). Produces a manifest + a height-aware
placement plan JSON that an editor lane (Monolith, height-aware raycast) applies.
Adheres to single-writer + World Field Bus (Resonance) contracts.

Run: ./.venv/Scripts/python.exe Tools/PCG/build_singing_water_veil_ecosystem.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

SCHEMA = "melodia.singing_water_veil_pcg.v1"
# Sea Above prototype bounds (uncertain; swept by a larger halo in uu). Use a
# compact canonical footprint so placement stays inside the level's water.
BOUNDS_EXTENT_UU = 300000.0  # 3 km halo
SEA_SURFACE_Z_UU = 13455.0   # canonical landscape Z=13405 + water sheet ~50uu (recorded 221-piece cathedral Z=13455)

# Water veil "biomes" — their own mode language, each a cymatic harmonic.
VEIL_ZONE_MAP = {
    "SheetVeil":   [  # broad low water sheet
        "MEL_water_veil_sheet", "MEL_water_veil_ripple",
    ],
    "SingingFall": [  # cascading curtain where tension is highest
        "MEL_water_veil_fall", "MEL_water_veil_plume",
    ],
    "HearthPool":  [  # calm mirrored pools, resonance nodes
        "MEL_water_veil_pool", "MEL_water_veil_mirror",
    ],
    "TideSeam":    [  # nodal lines of the standing wave — the "heard" edge
        "MEL_water_veil_seam", "MEL_water_veil_foam",
    ],
}

# Chladni mode per zone — distinct harmonics, none repeated (garment parity).
ZONE_MODE = {
    "SheetVeil":   (2, 4),
    "SingingFall": (5, 7),
    "HearthPool":  (1, 3),
    "TideSeam":    (6, 6),
}

# PBR/MI references — verified Sea Above + Melodia masters (no new master).
ZONE_MATERIAL = {
    "SheetVeil":   "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_SeaAbove_SurfaceOcean",
    "SingingFall": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_SeaAbove_FalseOcean",
    "HearthPool":  "/Game/EnvSandbox/Textures/PearlWoven_Lace",  # placeholder res note (lace pools)
    "TideSeam":    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_SeaAbove_UpwardDroplet",
}


@dataclass
class WaterPoint:
    id: str
    zone: str
    builder: str
    position: List[float]      # [X, Y, Z] uu (Z = sea surface, height-awake)
    height_cm: float           # landscape surface height at this point (height-awake)
    clearance_cm: float        # vertical water above surface
    rotation: List[float]
    scale: List[float]
    tension: float
    chladni_mode: str
    chladni_val: float
    resonance: float
    material_instance: str


@dataclass
class ZoneSummary:
    name: str
    point_count: int
    builders: List[str]
    avg_tension: float
    mode: str
    material_instance: str


@dataclass
class SingingWaterVeilManifest:
    schema: str = SCHEMA
    version: str = "1.0.0"
    landscape: str = "CanonicalLandscape"          # used, never created
    sea_surface_z_uu: float = SEA_SURFACE_Z_UU
    bounds_uu: List[float] = field(default_factory=lambda: [-150000.0, -150000.0, 150000.0, 150000.0])
    total_points: int = 0
    zone_summaries: Dict[str, ZoneSummary] = field(default_factory=dict)
    points: List[WaterPoint] = field(default_factory=list)
    world_field_channels: List[str] = field(default_factory=lambda: [
        "WorldField.Resonance", "WorldField.Tension", "WorldField.Moisture",
        "WorldField.FilterFlow",
    ])
    narrative_hook: Dict[str, str] = field(default_factory=lambda: {
        "encounter_id": "encounter.shorelistener.reveal",
        "reward_id": "reward.wardrobe.shorewake_veil",
        "flag_id": "quest.p0_sea_above.veil_sung",
    })


def evaluate_chladni(u, v, n=3, m=5, a=1.0, b=1.0):
    pi = math.pi
    return a * math.cos(n * pi * u) * math.cos(m * pi * v) \
        - b * math.cos(m * pi * u) * math.cos(n * pi * v)


def evaluate_tension(u, v):
    du = dv = 0.001
    zc = evaluate_chladni(u, v, 3, 5)
    zu = evaluate_chladni(u + du, v, 3, 5)
    zv = evaluate_chladni(u, v + dv, 3, 5)
    grad = math.sqrt(((zu - zc) / du) ** 2 + ((zv - zc) / dv) ** 2)
    return max(0.0, min(1.0, grad / 8.0))


def landscape_height_cm(u, v):
    """Height-awake: approximate the canonical landscape surface height (cm).

    Stand-in for a real raycast (editor/Monolith lane flips this with an actual
    line-trace). Encodes the recorded canonical Z=13405cm landmark + a gentle
    cymatic swell so no flush sits in air/rock.
    """
    return 13405.0 + 45.0 * evaluate_chladni(u, v, 2, 4)


def classify_zone(u, v, tension, chladni_val):
    if abs(chladni_val) < 0.12:
        return "TideSeam"        # on the standing-wave nodal line = the heard edge
    if tension > 0.62:
        return "SingingFall"
    if tension < 0.55:
        return "HearthPool"      # calm mirrored pools (bottom ~decile)
    return "SheetVeil"


def generate(points_per_zone: int = 30, seed: int = 42) -> SingingWaterVeilManifest:
    m = SingingWaterVeilManifest()
    zone_pts: Dict[str, List[WaterPoint]] = {z: [] for z in VEIL_ZONE_MAP}
    grid = max(24, int(math.sqrt(points_per_zone * 12)))
    for i in range(grid):
        for j in range(grid):
            u = (i + 0.5) / grid
            v = (j + 0.5) / grid
            cv = evaluate_chladni(u, v, 3, 5)
            tension = evaluate_tension(u, v)
            zone = classify_zone(u, v, tension, cv)
            if len(zone_pts[zone]) >= points_per_zone:
                continue
            x_uu = (u - 0.5) * BOUNDS_EXTENT_UU
            y_uu = (v - 0.5) * BOUNDS_EXTENT_UU
            h_cm = landscape_height_cm(u, v)
            z_uu = SEA_SURFACE_Z_UU
            clearance = max(20.0, 25.0 + cv * 60.0)   # taller swell at nodes
            builders = VEIL_ZONE_MAP[zone]
            b_idx = (i * 7 + j * 13 + seed) % len(builders)
            yaw = math.degrees(math.atan2(y_uu, x_uu))
            s = 0.7 + tension * 0.6
            pt = WaterPoint(
                id=f"WV_{zone}_{len(zone_pts[zone]):04d}",
                zone=zone,
                builder=builders[b_idx],
                position=[round(x_uu, 2), round(y_uu, 2), round(z_uu, 2)],
                height_cm=round(h_cm, 2),
                clearance_cm=round(clearance, 2),
                rotation=[0.0, 0.0, round(yaw, 2)],
                scale=[round(s, 3), round(s, 3), round(s, 3)],
                tension=round(tension, 4),
                chladni_mode=f"{ZONE_MODE[zone][0]}_{ZONE_MODE[zone][1]}",
                chladni_val=round(cv, 4),
                resonance=round(abs(cv), 4),
                material_instance=ZONE_MATERIAL[zone],
            )
            zone_pts[zone].append(pt)
            m.points.append(pt)
    m.total_points = len(m.points)
    for name, pts in zone_pts.items():
        m.zone_summaries[name] = ZoneSummary(
            name=name, point_count=len(pts), builders=VEIL_ZONE_MAP[name],
            avg_tension=round(sum(p.tension for p in pts) / max(1, len(pts)), 4),
            mode=f"{ZONE_MODE[name][0]}_{ZONE_MODE[name][1]}",
            material_instance=ZONE_MATERIAL[name],
        )
    return m


def write_height_placement_plan(m: SingingWaterVeilManifest, out: Path):
    """Emit a height-awake placement plan JSON an editor lane applies (raycast)."""
    plan = {
        "schema": "melodia.singing_water_veil_placement.v1",
        "level": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
        "landscape": "CanonicalLandscape (used, never created)",
        "height_contract": "placements marked height_cm are the landscape surface; "
                           "editor applies a real line-trace and snaps Z=clearance above it",
        "placements": [
            {
                "id": p.id, "mesh": p.builder, "material": p.material_instance,
                "position": p.position, "rotation": p.rotation, "scale": p.scale,
                "height_cm": p.height_cm, "clearance_cm": p.clearance_cm,
                "resonance": p.resonance,
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
    ap.add_argument("--out", type=str,
                    default="specs/water_veil/singing_water_veil_pcg.v1.json")
    ap.add_argument("--placement", type=str,
                    default="specs/water_veil/singing_water_veil_placements.json")
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
    m = generate(points_per_zone=args.points_per_zone)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(m), indent=2), encoding="utf-8")
    write_height_placement_plan(m, Path(args.placement).resolve())
    print(f"wrote {out} (total_points={m.total_points})")
    for name, s in m.zone_summaries.items():
        print(f"  {name}: {s.point_count} pts | mode {s.mode} | avgT {s.avg_tension} | {s.material_instance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())