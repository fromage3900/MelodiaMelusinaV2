"""Faraway LOD Destruction — apply Tension/dither destruction into LV_FarawayMother_Prototype.

Wires MF_LODDitheredDestruction + WPO fade + Toksvig/rim per LOD into existing
Faraway Mother fabric ridge terrain without new masters.

What this does (editor, idempotent):
 - Audits existing Nanite terrain (SM_FarawayMother_FabricRidge), fog/PPV/volume actors
 - Logs current MI DestructionAmount bindings (no asset mutation — MIs are tuned via param)
 - Optionally spawns height-aware debug markers from offline placements JSON
 - Prints MPC<->material wiring contract so owner can tune without code

Offline placements (required for debug markers, optional for audit):
  .venv/Scripts/python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829
  -> specs/faraway_lod_destruction/faraway_lod_destruction_placements.v1.json

Use after add_horizon_eater_mpc_params.py has added MPC scalars headless.

Single :9316 lock. Safe to rerun (label dedupe).

Run (editor open):
  python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py
  python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py --wipe-lod-debug
"""
from pathlib import Path
import json

try:
    import unreal
except ImportError:
    unreal = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACEMENTS_JSON = PROJECT_ROOT / "specs" / "faraway_lod_destruction" / "faraway_lod_destruction_placements.v1.json"
SPEC_JSON = PROJECT_ROOT / "specs" / "faraway_lod_destruction" / "faraway_lod_destruction_spec.v1.json"
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"

EXPECTED_LABELS = [
    "FM_Ridge_Rosette_Crest",
    "FM_Valley_Arch_Entrance",
    "FM_Shoulder_Capital",
    "FM_Heart_Finial_Gate",
    "FM_Torso_RoseWindow",
    "FM_MoonHaze_Fog",
    "FM_MoonHaze_PPV",
    "FM_MoonHaze_VolumeBox",
]

def log(msg):
    if unreal:
        unreal.log(f"[FarawayLOD] {msg}")
    print(f"[FarawayLOD] {msg}")

def audit():
    if not unreal:
        log("not in editor — offline audit")
        if SPEC_JSON.exists():
            j = json.loads(SPEC_JSON.read_text())
            log(f" LOD tiers: {list(j['lod_tiers'].keys())}")
            log(f" destruction ops: {[o['id'] for o in j['destruction_operators']]}")
        if PLACEMENTS_JSON.exists():
            p = json.loads(PLACEMENTS_JSON.read_text())
            log(f" placements offline: {p.get('total_points')} pts, zones {list(p.get('zone_summaries',{}).keys())}")
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = [a.get_actor_label() for a in actors]
    log(f"actors in level: {len(actors)} — expected fabric labels check")
    missing = [e for e in EXPECTED_LABELS if not any(e.lower() in l.lower() for l in labels)]
    if missing:
        log(f" MISSING fabric labels (non-fatal, run faraway_mother_prototype_build.py first): {missing}")
    else:
        log(" all expected FM_* labels present")
    # Try to find terrain mesh actor
    terrain_hits = [a for a in actors if "FabricRidge" in a.get_actor_label() or "FabricRidge" in a.get_name()]
    if terrain_hits:
        for a in terrain_hits[:3]:
            loc = a.get_actor_location()
            log(f" terrain: {a.get_actor_label()} @ {loc.x:.0f},{loc.y:.0f},{loc.z:.0f}")
    else:
        log(" no FabricRidge terrain actor found (build_faraway_mother_prototype_build.py will create)")
    # MPC preview
    for mpc_path in ["/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette","/Game/EnvSandbox/Materials/MPC_Melodia_Palette"]:
        asset = unreal.EditorAssetLibrary.load_asset(mpc_path)
        if asset:
            try:
                scalars = {s.get_editor_property("parameter_name"): s.get_editor_property("default_value") for s in asset.get_editor_property("scalar_parameters")}
                interesting = {k: scalars[k] for k in ["HorizonEatAmount","DestructionAmount","HorizonTension","DreadPresence","BeatPulse","BassIntensity"] if k in scalars}
                log(f" MPC {mpc_path}: {interesting}")
            except Exception as e:
                log(f" MPC {mpc_path} read: {e}")
            break
    log("Material contract: DestructionAmount -> MF_LODDitheredDestruction opacity dither, WPO_Resonance_Scale fade 1.0|0.75|0.3|0.0, POM 32|16|0|0, Toksvig 0|0.35|0.75|1.0, rim 1.0|1.15|1.4|1.8")
    log("Per-biome: WeaveRidge dies first (0.35), FrillValley last (0.85), SeamWay never (Wayfold)")

def spawn_debug(wipe=False):
    if not unreal:
        log("spawn_debug: not in editor")
        return
    if wipe:
        for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
            if a.get_actor_label().startswith("FL_LodDestruct_"):
                unreal.EditorLevelLibrary.destroy_actor(a)
                log(f" wiped {a.get_actor_label()}")
    if not PLACEMENTS_JSON.exists():
        log(f"no placements at {PLACEMENTS_JSON} — run offline generator first")
        return
    data = json.loads(PLACEMENTS_JSON.read_text())
    points = data.get("points",[])
    spawned=0
    for pt in points:
        # Only spawn destroyed-tier preview (LOD2+ / destruction_t > 0.5) to show dissolve, capped
        if pt.get("destruction_t",0) < 0.45:
            continue
        if spawned>=20:
            break
        label = f"FL_LodDestruct_{pt['id']}"
        if any(a.get_actor_label()==label for a in unreal.EditorLevelLibrary.get_all_level_actors()):
            continue
        xy = pt["position"]
        z = pt.get("final_z", pt.get("height_cm",12200)+35)
        try:
            loc = unreal.Vector(xy[0], xy[1], z+40)
            rot = unreal.Rotator(0, pt.get("rotation",[0,0,0])[2], 0)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
            actor.set_actor_label(label)
            scale = pt.get("scale", [1])[0] if isinstance(pt.get("scale"), list) else pt.get("scale",1)
            actor.set_actor_scale3d(unreal.Vector(scale*0.4, scale*0.4, scale*0.4))
            spawned+=1
        except Exception as e:
            log(f" spawn {label}: {e}")
    log(f"spawned {spawned} FL_LodDestruct debug markers (destruction_t>=0.45, cap 20, height-aware)")

def main():
    import sys
    wipe="--wipe-lod-debug" in sys.argv
    audit()
    spawn_debug(wipe=wipe)
    log("done. Tune MIs DestructionAmount 0..1 in editor MI instances to preview. HorizonEat drives horizon-tier destruction.")

if __name__=="__main__":
    main()
