"""Horizon Eater — offline PCG filter-flow + horizon-cull ecosystem (deterministic).

Mirrors singing_water_veil + faraway_mother pattern: pure venv python, no editor.
Generates a point constellation representing:
 - distant ecology that will be drawn into filter-flow corridors,
 - HorizonMouth corridor itself,
 - DistanceEvidence scatter (impossible adjacencies),
 - LOD impostor crumble candidates at horizon.

Every point carries Tension + HorizonMask + destruction readiness. Height-aware
placements are resolved in-editor via raycast — this file only computes XY + synthetic Z.

Single bus: HorizonEatAmount alias Tension. Offline compute uses Tension only.

Run:
  .venv/Scripts/python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829
  .venv/Scripts/python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829 --n 80

Outputs:
  specs/horizon_eater/horizon_eater_manifest.v1.json
  specs/horizon_eater/horizon_eater_placements.v1.json
  Saved/Audit/horizon_eater/horizon_eater_preview.json
"""
from __future__ import annotations
import argparse, json, math, hashlib, random
from dataclasses import dataclass, asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "melodia.horizon_eater_pcg.v1"
SEED = 20260829
BOUNDS_UU = 400000.0  # 4km each side — matches faraway bounds, but horizon eater works beyond
SEA_Z = 13455.0

ZONE_MAP = {
    "FilterCorridor": ["MEL_horizon_filter_flow", "MEL_horizon_filter_plate"],
    "HorizonRim":     ["MEL_horizon_rim_proxy", "MEL_horizon_mouth_card"],
    "WayfoldPair":    ["MEL_horizon_wayfold_entry", "MEL_horizon_wayfold_exit"],
    "DistanceEvidence": ["MEL_horizon_distance_evidence", "MEL_horizon_pollen_drift"],
}
ZONE_MODE = {
    "FilterCorridor": (3, 7),
    "HorizonRim": (6, 9),
    "WayfoldPair": (4, 4),
    "DistanceEvidence": (5, 6),
}
ZONE_MATERIAL = {
    "FilterCorridor": "/Game/EnvSandbox/Textures/Copernicus/Shared/MI_Horizon_FilterFlow",
    "HorizonRim": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Materials/MI_Horizon_MouthCard",
    "WayfoldPair": "/Game/EnvSandbox/Monoliths/HorizonEater/Prototype/Materials/MI_Horizon_Wayfold",
    "DistanceEvidence": "/Game/EnvSandbox/Textures/Copernicus/Shared/MI_Horizon_Evidence",
}

def chladni(u,v,n,m):
    return math.cos(n*math.pi*u)*math.cos(m*math.pi*v) - math.cos(m*math.pi*u)*math.cos(n*math.pi*v)

def tension_at(chladni_val, r_norm):
    # tension rises with r (distance) and gradient of chladni
    return min(1.0, abs(chladni_val)*0.9 + r_norm*0.6)

def horizon_mask(x,y):
    # horizon = distance > 1500m or |xy| large — rim of bounds is horizon
    r = math.hypot(x,y)
    return 1.0 if r > 150000 else max(0.0, (r - 60000)/90000)

def build_points(n_per_zone=20, seed=SEED):
    rng = random.Random(seed)
    points=[]
    pid=0
    zones = list(ZONE_MAP.keys())
    for zone in zones:
        builders = ZONE_MAP[zone]
        n,m = ZONE_MODE[zone]
        mat = ZONE_MATERIAL[zone]
        for i in range(n_per_zone):
            # stratified grid jitter
            gx = (i % 5)/5.0
            gy = (i // 5)/5.0
            u = max(0,min(1,gx + rng.uniform(-0.12,0.12)))
            v = max(0,min(1,gy + rng.uniform(-0.12,0.12)))
            # map u,v to world XY in bounds, but push HorizonRim outward
            if zone=="HorizonRim":
                ang = rng.uniform(0, 2*math.pi)
                r = rng.uniform(180000, 380000)
                x = math.cos(ang)*r
                y = math.sin(ang)*r
                u = (x/BOUNDS_UU+1)/2
                v = (y/BOUNDS_UU+1)/2
            elif zone=="WayfoldPair":
                # pairs near centre, aligned along Chladni nodal
                ang = rng.uniform(-0.5,0.5)
                r = rng.uniform(40000, 90000)
                x = math.cos(ang)*r + rng.uniform(-20000,20000)
                y = math.sin(ang)*r + rng.uniform(-20000,20000)
            else:
                x = (u*2-1)*BOUNDS_UU
                y = (v*2-1)*BOUNDS_UU
            cv = chladni(u,v,n,m)
            r_norm = math.hypot(x,y)/BOUNDS_UU
            t = tension_at(cv, r_norm)
            hm = horizon_mask(x,y)
            # Wayfold stays low tension corridor
            if zone=="WayfoldPair":
                t = min(t, 0.35)
            builder = rng.choice(builders)
            yaw = rng.uniform(0,360)
            scale = rng.uniform(0.8,1.6) if zone!="HorizonRim" else rng.uniform(1.4,2.8)
            # synthetic Z: sea-ish for filter, + height for rim (mouth card hovers)
            if zone=="HorizonRim":
                z = SEA_Z + rng.uniform(8000, 22000)
                clearance = z - SEA_Z
            else:
                z = SEA_Z + rng.uniform(-200, 800)
                clearance = z - SEA_Z
            points.append({
                "id": f"HE_{zone}_{pid:04d}",
                "zone": zone,
                "builder": builder,
                "position": [x,y,z],
                "height_cm": SEA_Z,
                "clearance_cm": clearance,
                "rotation": [0,0,yaw],
                "scale": [scale,scale,scale],
                "tension": round(t,4),
                "horizon_mask": round(hm,4),
                "destruction_t": round(min(1.0, t*0.6 + hm*0.5),4),
                "chladni_val": round(cv,4),
                "mode": f"{n}_{m}",
                "material_instance": mat,
                "density": round(1.0 - hm*0.3,3),
            })
            pid+=1
    return points

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n", type=int, default=20, help="points per zone")
    ap.add_argument("--out", type=str, default="", help="placements json override")
    args=ap.parse_args()
    pts = build_points(n_per_zone=args.n, seed=args.seed)
    # summaries
    summaries={}
    for zone in ZONE_MAP:
        zs=[p for p in pts if p["zone"]==zone]
        if zs:
            summaries[zone]={"name":zone,"point_count":len(zs),"builders":ZONE_MAP[zone],"avg_tension":round(sum(p["tension"] for p in zs)/len(zs),4),"avg_horizon_mask":round(sum(p["horizon_mask"] for p in zs)/len(zs),4),"material_instance":ZONE_MATERIAL[zone],"mode":"_".join(map(str,ZONE_MODE[zone]))}
    manifest={
        "schema": SCHEMA,
        "version":"1.0.0",
        "seed": args.seed,
        "bounds_uu": [-BOUNDS_UU,-BOUNDS_UU,BOUNDS_UU,BOUNDS_UU],
        "sea_surface_z_uu": SEA_Z,
        "total_points": len(pts),
        "zone_summaries": summaries,
        "horizon_scalar": "MPC_Melodia_Palette.HorizonEatAmount 0..1 (alias WorldField.Tension/HorizonEat)",
        "bus": "UMelodiaAudioReactivePresentationSubsystem sole writer"
    }
    placements={
        "schema": SCHEMA,
        "version":"1.0.0",
        "seed": args.seed,
        "total_points": len(pts),
        "zone_summaries": summaries,
        "points": pts
    }
    out_manifest = PROJECT_ROOT / "specs" / "horizon_eater" / "horizon_eater_manifest.v1.json"
    out_placements = Path(args.out) if args.out else PROJECT_ROOT / "specs" / "horizon_eater" / "horizon_eater_placements.v1.json"
    preview_dir = PROJECT_ROOT / "Saved" / "Audit" / "horizon_eater"
    preview_dir.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_placements.parent.mkdir(parents=True, exist_ok=True)
    # stable hash
    h = hashlib.sha256(json.dumps(pts, sort_keys=True).encode()).hexdigest()[:16]
    manifest["hash"] = h
    placements["hash"] = h
    out_manifest.write_text(json.dumps(manifest, indent=2))
    out_placements.write_text(json.dumps(placements, indent=2))
    (preview_dir / "horizon_eater_preview.json").write_text(json.dumps({"hash":h, "counts": summaries}, indent=2))
    print(f"[HorizonEater] seed={args.seed} points={len(pts)} hash={h}")
    print(f" manifest -> {out_manifest}")
    print(f" placements -> {out_placements}")
    print(json.dumps(summaries, indent=2))

if __name__=="__main__":
    main()
