"""Faraway LOD Destruction — offline PCG destruction ecosystem (deterministic).

Extends faraway_mother_pcg_manifest pattern but computes per-point
destruction readiness (destruction_t 0..1, horizon_mask, tension) for
MF_LODDitheredDestruction. Height-aware Z resolved in-editor via raycast.
Deterministic SEED=20260829 matches all other Monolith hypotheses.

What varies from faraway_mother_pcg_ecosystem:
- each point knows which LOD tier it belongs to at rest
- destruction_t = tension*biome_factor + horizon_mask, clamped 0..1
- WeaveRidge dies first, FrillValley last, SeamWay (Chladni nodal) never fully

Run:
  .venv/Scripts/python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829

Outputs:
  specs/faraway_lod_destruction/faraway_lod_destruction_manifest.v1.json
  specs/faraway_lod_destruction/faraway_lod_destruction_placements.v1.json
  Saved/Audit/faraway_lod_destruction/preview.json
"""
from __future__ import annotations
import argparse, json, math, hashlib, random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "melodia.faraway_lod_destruction_pcg.v1"
SEED = 20260829
BOUNDS_UU = 400000.0

BIOME_DEFS = {
    "WeaveRidge":     {"builders":["MEL_mother_fabric_ridge","MEL_mother_shoulder_fold"], "t_lo":0.60, "t_hi":0.99, "mat":"/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Gown_CelestialSilkJacquard", "kill_thresh":0.35},
    "LaceCanopy":     {"builders":["MEL_mother_lace_tree","MEL_mother_pearl_bush"], "t_lo":0.40, "t_hi":0.85, "mat":"/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Veil_AquaticLullabyLace", "kill_thresh":0.50},
    "FrillValley":    {"builders":["MEL_mother_frill_rock","MEL_mother_frill_arch","MEL_mother_brocade_flower"], "t_lo":0.18, "t_hi":0.55, "mat":"/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Corset_GildedAcanthusBrocade", "kill_thresh":0.85},
    "ResonantSeamWay":{ "builders":["MEL_mother_walkway_straight","MEL_mother_heart_gate"], "t_lo":0.12, "t_hi":0.35, "mat":"/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Mantle_NightSkyVelvet", "kill_thresh":0.95},
}

def chladni(u,v,n=3,m=5):
    return math.cos(n*math.pi*u)*math.cos(m*math.pi*v) - math.cos(m*math.pi*u)*math.cos(n*math.pi*v)

def horizon_mask(x,y):
    r = math.hypot(x,y)
    return 1.0 if r>180000 else max(0.0, (r-60000)/120000)

def lod_for_dist(d):
    if d<1500: return "LOD0"
    if d<5000: return "LOD1"
    if d<20000: return "LOD2"
    return "LOD3"

def build_points(n_per_biome=18, seed=SEED):
    rng=random.Random(seed)
    pts=[]
    pid=0
    for biome, cfg in BIOME_DEFS.items():
        for i in range(n_per_biome):
            # grid jitter in bounds
            u=rng.uniform(0,1)
            v=rng.uniform(0,1)
            # bias FrillValley low, WeaveRidge high, SeamWay nodal
            if biome=="FrillValley":
                u = rng.uniform(0.35,0.65); v=rng.uniform(0.35,0.65)
            if biome=="ResonantSeamWay":
                # keep near chladni nodal |cv|<0.12
                tries=0
                while tries<20:
                    tu, tv = rng.uniform(0,1), rng.uniform(0,1)
                    if abs(chladni(tu,tv))<0.22:
                        u,v=tu,tv; break
                    tries+=1
            x=(u*2-1)*BOUNDS_UU
            y=(v*2-1)*BOUNDS_UU
            cv=chladni(u,v)
            r=math.hypot(x,y)
            hm=horizon_mask(x,y)
            # tension in biome range + seam way pinned low
            if biome=="ResonantSeamWay":
                t = rng.uniform(0.15,0.35)
                if abs(cv)>0.12: t*=1.3
            else:
                t = rng.uniform(cfg["t_lo"], cfg["t_hi"])
                # bump with chladni gradient
                t = min(0.99, t + abs(cv)*0.12)
            # destruction readiness
            if biome=="ResonantSeamWay":
                destruction_t = min(0.88, t*0.3 + hm*0.25)
            else:
                destruction_t = min(1.0, t*0.62 + hm*0.45 + rng.uniform(-0.06,0.06))
                destruction_t = max(0, destruction_t)
            # LOD at rest distance
            dist = r
            lod=lod_for_dist(dist)
            builder=rng.choice(cfg["builders"])
            yaw=rng.uniform(0,360)
            scale=rng.uniform(0.85,1.45)
            z_base = 13405 + rng.uniform(-900, 1600)  # landscape-ish
            pts.append({
                "id": f"FL_{biome}_{pid:04d}",
                "biome": biome,
                "builder": builder,
                "position": [x,y,z_base],
                "height_cm": z_base,
                "final_z": z_base+35,
                "rotation": [0,0,yaw],
                "scale": [scale,scale,scale],
                "tension": round(t,4),
                "chladni_val": round(cv,4),
                "horizon_mask": round(hm,4),
                "destruction_t": round(destruction_t,4),
                "kill_threshold": cfg["kill_thresh"],
                "lod_at_rest": lod,
                "will_destroy": destruction_t > cfg["kill_thresh"],
                "material_instance": cfg["mat"],
            })
            pid+=1
    return pts

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n", type=int, default=18)
    ap.add_argument("--out", type=str, default="")
    args=ap.parse_args()
    pts=build_points(n_per_biome=args.n, seed=args.seed)
    summaries={}
    for biome in BIOME_DEFS:
        zs=[p for p in pts if p["biome"]==biome]
        summaries[biome]={
            "name":biome,"point_count":len(zs),"builders":BIOME_DEFS[biome]["builders"],
            "avg_tension":round(sum(p["tension"] for p in zs)/len(zs),4) if zs else 0,
            "avg_destruction":round(sum(p["destruction_t"] for p in zs)/len(zs),4) if zs else 0,
            "kill_thresh":BIOME_DEFS[biome]["kill_thresh"],"material_instance":BIOME_DEFS[biome]["mat"]
        }
    out_manifest = PROJECT_ROOT/"specs"/"faraway_lod_destruction"/"faraway_lod_destruction_manifest.v1.json"
    out_placements = Path(args.out) if args.out else PROJECT_ROOT/"specs"/"faraway_lod_destruction"/"faraway_lod_destruction_placements.v1.json"
    preview_dir = PROJECT_ROOT/"Saved"/"Audit"/"faraway_lod_destruction"
    preview_dir.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_placements.parent.mkdir(parents=True, exist_ok=True)
    h=hashlib.sha256(json.dumps(pts, sort_keys=True).encode()).hexdigest()[:16]
    manifest={"schema":SCHEMA,"version":"1.0.0","seed":args.seed,"bounds_uu":[-BOUNDS_UU,-BOUNDS_UU,BOUNDS_UU,BOUNDS_UU],"total_points":len(pts),"zone_summaries":summaries,"bus":"WorldField.Tension = HorizonEatAmount (UMelodiaAudioReactivePresentationSubsystem sole writer)","lod_contract":"LOD0 0-15m POM32 T0 R1 W1 | LOD1 15-50m POM16 T0.35 R1.15 W0.75 | LOD2 50-200m POM0 T0.75 R1.4 W0.3 | LOD3 200-5000m POM0 T1 R1.8 W0", "hash":h}
    placements={"schema":SCHEMA,"version":"1.0.0","seed":args.seed,"total_points":len(pts),"zone_summaries":summaries,"points":pts,"hash":h}
    out_manifest.write_text(json.dumps(manifest, indent=2))
    out_placements.write_text(json.dumps(placements, indent=2))
    (preview_dir/"preview.json").write_text(json.dumps({"hash":h,"counts":summaries}, indent=2))
    print(f"[FarawayLOD] seed={args.seed} pts={len(pts)} hash={h}")
    print(f" manifest -> {out_manifest}")
    print(f" placements -> {out_placements}")
    print(json.dumps(summaries, indent=2))

if __name__=="__main__":
    main()
