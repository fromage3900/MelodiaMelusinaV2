"""Faraway Mother PCG Ecosystem & Procedural Fabric Mountain Generator.

Synthesizes deterministic PCG point distributions, tension fields, and
cymatic harmonic standing-wave nodes across the 4 Faraway Mother biomes:
1. WeaveRidge (Macro fabric ridges, tensioned seam lines, silk vines)
2. LaceCanopy (Lace tree groves, pearl bushes, canopy volumes)
3. FrillValley (Volumetric fog basins, frill rocks, frill arches, brocade flowers)
4. ResonantSeamWay (Straight/curved fabric walkways, Heart Gate rhythm checkpoint)

Adheres to Melodia single-writer and World Field Bus contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA = "melodia.faraway_mother_pcg_manifest.v1"
BOUNDS_EXTENT_UU = 800000.0  # 8 km x 8 km (Unreal Units)

BIOME_BUILDER_MAP = {
    "WeaveRidge": [
        "MEL_mother_fabric_ridge",
        "MEL_mother_shoulder_fold",
        "MEL_mother_silk_vine",
    ],
    "LaceCanopy": [
        "MEL_mother_lace_tree",
        "MEL_mother_pearl_bush",
    ],
    "FrillValley": [
        "MEL_mother_valley_depression",
        "MEL_mother_frill_rock",
        "MEL_mother_frill_arch",
        "MEL_mother_brocade_flower",
        "MEL_mother_fog_volume",
    ],
    "ResonantSeamWay": [
        "MEL_mother_walkway_straight",
        "MEL_mother_walkway_curved",
        "MEL_mother_heart_gate",
        "MEL_mother_head_silhouette",
        "MEL_mother_hair_cascade",
    ],
}

BIOME_MATERIAL_MAP = {
    "WeaveRidge": "/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Gown_CelestialSilkJacquard",
    "LaceCanopy": "/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Veil_AquaticLullabyLace",
    "FrillValley": "/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Corset_GildedAcanthusBrocade",
    "ResonantSeamWay": "/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Mantle_NightSkyVelvet",
}


@dataclass
class PCGPoint:
    id: str
    biome: str
    builder: str
    position: List[float]  # [X, Y, Z] in uu
    rotation: List[float]  # [Roll, Pitch, Yaw] in degrees
    scale: List[float]     # [SX, SY, SZ]
    tension: float
    moisture: float
    resonance_mode: str
    chladni_val: float
    material_instance: str
    density: float = 1.0


@dataclass
class BiomeSummary:
    name: str
    point_count: int
    builders: List[str]
    avg_tension: float
    avg_altitude_uu: float
    material_instance: str


@dataclass
class FarawayMotherPCGManifest:
    schema: str = SCHEMA
    version: str = "1.0.0"
    landscape_bounds_uu: List[float] = field(default_factory=lambda: [-400000.0, -400000.0, 400000.0, 400000.0])
    total_points: int = 0
    biome_summaries: Dict[str, BiomeSummary] = field(default_factory=dict)
    points: List[PCGPoint] = field(default_factory=list)
    world_field_channels: List[str] = field(default_factory=lambda: [
        "WorldField.Tension",
        "WorldField.Resonance",
        "WorldField.Moisture",
        "WorldField.FilterFlow",
    ])
    narrative_challenge_hook: Dict[str, str] = field(default_factory=lambda: {
        "challenge_id": "challenge.mother_heart_gate",
        "reward_id": "reward.wardrobe.mother_velvet_mantle",
        "flag_id": "quest.p1_faraway_mother.heart_unlocked",
        "host_class": "APCGHeroMusicGraphHost",
    })


def evaluate_chladni(u: float, v: float, n: int = 3, m: int = 5, a: float = 1.0, b: float = 1.0) -> float:
    """Evaluate 2D Chladni standing wave interference."""
    pi = math.pi
    return a * math.cos(n * pi * u) * math.cos(m * pi * v) - b * math.cos(m * pi * u) * math.cos(n * pi * v)


def evaluate_tension(u: float, v: float) -> float:
    """Calculate normalized tension field gradient from wave curvature."""
    du = 0.001
    dv = 0.001
    z_center = evaluate_chladni(u, v, 3, 5)
    z_u = evaluate_chladni(u + du, v, 3, 5)
    z_v = evaluate_chladni(u, v + dv, 3, 5)
    grad_u = (z_u - z_center) / du
    grad_v = (z_v - z_center) / dv
    grad_mag = math.sqrt(grad_u * grad_u + grad_v * grad_v)
    return min(1.0, max(0.0, grad_mag / 8.0))


def classify_biome(u: float, v: float, altitude_uu: float, tension: float, chladni_val: float) -> str:
    """Classify world coordinate into one of 4 Faraway Mother biomes."""
    # Nodal line proximity triggers Resonant Seam Way
    if abs(chladni_val) < 0.12:
        return "ResonantSeamWay"
    # High altitude and high tension triggers Weave Ridge
    if altitude_uu > 1500.0 and tension > 0.6:
        return "WeaveRidge"
    # Low altitude and lower tension triggers Frill Valley
    if altitude_uu < -1000.0 or (tension < 0.4 and altitude_uu < 500.0):
        return "FrillValley"
    # Mid-slopes form Lace Canopy
    return "LaceCanopy"


def generate_faraway_pcg_ecosystem(points_per_biome: int = 50, seed: int = 42) -> FarawayMotherPCGManifest:
    """Generate complete PCG point constellation across all biomes."""
    manifest = FarawayMotherPCGManifest()
    points: List[PCGPoint] = []
    biome_points: Dict[str, List[PCGPoint]] = {b: [] for b in BIOME_BUILDER_MAP.keys()}

    # Deterministic grid sampling
    grid_res = max(30, int(math.sqrt(points_per_biome * 16)))

    for i in range(grid_res):
        for j in range(grid_res):
            u = (i + 0.5) / grid_res
            v = (j + 0.5) / grid_res

            # World position in UU (-400000 to +400000)
            x_uu = (u - 0.5) * BOUNDS_EXTENT_UU
            y_uu = (v - 0.5) * BOUNDS_EXTENT_UU

            chladni_val = evaluate_chladni(u, v, 3, 5)
            tension = evaluate_tension(u, v)

            # Altitude based on Chladni amplitude + macro swell
            altitude_uu = chladni_val * 4000.0 + math.sin(u * math.pi * 2.0) * 1500.0
            moisture = max(0.0, min(1.0, 0.5 - (altitude_uu / 8000.0) + (1.0 - tension) * 0.3))

            biome = classify_biome(u, v, altitude_uu, tension, chladni_val)
            if len(biome_points[biome]) >= points_per_biome:
                continue

            builders = BIOME_BUILDER_MAP[biome]
            builder_idx = (i * 7 + j * 13 + seed) % len(builders)
            builder = builders[builder_idx]

            yaw = math.atan2(y_uu, x_uu) * (180.0 / math.pi)
            pitch = (tension - 0.5) * 15.0
            roll = math.sin(u * 10.0) * 5.0

            scale_factor = 1.0 + (tension * 0.5)
            scale = [scale_factor, scale_factor, scale_factor]

            pt_id = f"PT_Mother_{biome}_{len(biome_points[biome]):04d}"
            mat_inst = BIOME_MATERIAL_MAP[biome]

            pt = PCGPoint(
                id=pt_id,
                biome=biome,
                builder=builder,
                position=[round(x_uu, 2), round(y_uu, 2), round(altitude_uu, 2)],
                rotation=[round(roll, 2), round(pitch, 2), round(yaw, 2)],
                scale=[round(scale[0], 3), round(scale[1], 3), round(scale[2], 3)],
                tension=round(tension, 4),
                moisture=round(moisture, 4),
                resonance_mode="3_5_Harmonic",
                chladni_val=round(chladni_val, 4),
                material_instance=mat_inst,
                density=round(1.0 - tension * 0.2, 3),
            )
            points.append(pt)
            biome_points[biome].append(pt)

    manifest.points = points
    manifest.total_points = len(points)

    # Compute summaries
    for b_name, b_pts in biome_points.items():
        if b_pts:
            avg_t = sum(p.tension for p in b_pts) / len(b_pts)
            avg_alt = sum(p.position[2] for p in b_pts) / len(b_pts)
        else:
            avg_t = 0.0
            avg_alt = 0.0
        manifest.biome_summaries[b_name] = BiomeSummary(
            name=b_name,
            point_count=len(b_pts),
            builders=BIOME_BUILDER_MAP[b_name],
            avg_tension=round(avg_t, 4),
            avg_altitude_uu=round(avg_alt, 2),
            material_instance=BIOME_MATERIAL_MAP[b_name],
        )

    return manifest


def validate_manifest_schema(data: dict) -> Tuple[bool, List[str]]:
    """Validate a loaded manifest against schema constraints."""
    errors = []
    if data.get("schema") != SCHEMA:
        errors.append(f"Invalid schema: {data.get('schema')!r} != {SCHEMA!r}")
    if not isinstance(data.get("points"), list) or len(data["points"]) == 0:
        errors.append("Manifest contains no points")
    if not isinstance(data.get("biome_summaries"), dict) or len(data["biome_summaries"]) != 4:
        errors.append("Manifest must contain exactly 4 biome summaries")
    for b_name in BIOME_BUILDER_MAP.keys():
        if b_name not in data.get("biome_summaries", {}):
            errors.append(f"Missing biome summary for {b_name}")
    return len(errors) == 0, errors


def export_manifest(manifest: FarawayMotherPCGManifest, out_path: Path) -> Path:
    """Save manifest to disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dict_repr = asdict(manifest)
    out_path.write_text(json.dumps(dict_repr, indent=2), encoding="utf-8")
    return out_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points-per-biome", type=int, default=30, help="Points to generate per biome")
    parser.add_argument("--out", type=str, default="specs/pcg/faraway_mother_pcg_manifest.v1.json")
    parser.add_argument("--verify", action="store_true", help="Verify existing manifest file")
    args = parser.parse_args(argv)

    out_file = Path(args.out).resolve()

    if args.verify:
        if not out_file.is_file():
            print(f"Error: manifest {out_file} not found")
            return 1
        data = json.loads(out_file.read_text(encoding="utf-8"))
        ok, errs = validate_manifest_schema(data)
        if not ok:
            print(f"Validation FAILED: {errs}")
            return 1
        print(f"Manifest {out_file} validated successfully ({data['total_points']} points).")
        return 0

    manifest = generate_faraway_pcg_ecosystem(points_per_biome=args.points_per_biome)
    export_manifest(manifest, out_file)
    print(f"Generated Faraway Mother PCG manifest: {out_file}")
    print(f"Total points: {manifest.total_points}")
    for b_name, summ in manifest.biome_summaries.items():
        print(f" - {b_name}: {summ.point_count} points | Avg Tension: {summ.avg_tension} | Alt: {summ.avg_altitude_uu} uu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
