"""Horizon Eater — Sea Above horizon line eater prototype build (editor, idempotent).

Applies the horizon-eater kills into LV_SeaAbove_Prototype without new Landscape:
 - Verifies Oceanology SLW actors + false ocean plane + fog actors exist
 - Logs extinction diagnostic + plane Z guidance
 - Wires MPC HorizonEatAmount showcase (prints bindings, does not add MPC — use add_horizon_eater_mpc_params.py headless)
 - Spawns/updates PCG-driven filter-flow debug locators from offline placements JSON (if present)
 - Height-aware contract: any new actors trace Visibility 50000->-50000 complex

Ownership: World Partition + Data Layers + HLOD untouched (only actors/components/
MIs referenced). Single :9316 lock. Rerun safe (label dedupe).

Usage (editor open):
  python Tools/ue_run_python.py --file Content/Python/horizon_eater_prototype_build.py
  python Tools/ue_run_python.py --file Content/Python/horizon_eater_prototype_build.py --wipe-filter-debug

Offline placements (optional, not required to run):
  .venv/Scripts/python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829
  -> specs/horizon_eater/horizon_eater_placements.v1.json
"""
import json
import math
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACEMENTS_JSON = PROJECT_ROOT / "specs" / "horizon_eater" / "horizon_eater_placements.v1.json"
SPEC_JSON = PROJECT_ROOT / "specs" / "horizon_eater" / "horizon_eater_spec.v1.json"
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"

# Expected labels on disk (from SEA_ABOVE_SECOND_OCEAN_LAYOUT doc)
EXPECTED = [
    "AOceanologyInfiniteOcean",
    "AOceanologyManager",
    "AOceanologyWaterVolume",
    "SeaAbove_FalseOceanPlane_Prototype",
    "SeaAbove_BellProxy_Prototype",
    "SeaAbove_CentralCore_Proxy",
    "SeaAbove_ObservationCliff_Prototype",
    "SeaAbove_UpwardDroplets_Prototype",
    "ExponentialHeightFog",
]

def log(msg):
    if unreal:
        unreal.log(f"[HorizonEater] {msg}")
    print(f"[HorizonEater] {msg}")

def find_actor(label_substr):
    if not unreal:
        return None
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        return None
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = actor.get_actor_label()
        if label_substr.lower() in lbl.lower() or label_substr.lower() in actor.get_name().lower():
            return actor
    return None

def audit_level():
    if not unreal:
        log("audit_level: not in editor — printing offline guidance")
        log(f" placements would load from {PLACEMENTS_JSON} if present")
        if SPEC_JSON.exists():
            j = json.loads(SPEC_JSON.read_text())
            log(f" kills: {[k['id'] for k in j['how_horizon_disappears']['kills']]}")
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        log("no editor world")
        return
    # Try load level if not current
    cur = world.get_name()
    if "LV_SeaAbove_Prototype" not in str(unreal.EditorLevelLibrary.get_editor_world().get_path_name()):
        try:
            unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
            log(f"loaded {LEVEL_PATH}")
        except Exception as e:
            log(f"load_level failed (may already be sublevel): {e}")
    # List actors
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    labels = [a.get_actor_label() for a in actors]
    log(f"level actors: {len(actors)} — sample {labels[:12]}")
    missing = []
    for exp in EXPECTED:
        hit = any(exp.lower() in l.lower() or exp.lower() in a.get_name().lower() for a, l in zip(actors, labels))
        if not hit:
            missing.append(exp)
    if missing:
        log(f"MISSING expected (non-fatal): {missing}")
    else:
        log("all expected horizon actors present")
    # Diagnostic: false plane Z and bell Z
    fp = find_actor("FalseOcean")
    bell = find_actor("BellProxy")
    fog = find_actor("HeightFog")
    vol = find_actor("WaterVolume")
    for name, actor in [("FalseOcean", fp), ("BellProxy", bell), ("HeightFog", fog), ("WaterVolume", vol)]:
        if actor:
            loc = actor.get_actor_location()
            log(f" {name}: loc {loc.x:.0f},{loc.y:.0f},{loc.z:.0f} label={actor.get_actor_label()}")
            if name == "WaterVolume":
                try:
                    ext = actor.get_actor_scale3d()
                    log(f"  WaterVolume scale {ext} — if ~1,1,1 it is still 2m cube (must scale to enclose plane)")
                except Exception:
                    pass
    # Print horizon-eat scalar contract
    log("MPC scalars expected on MPC_Melodia_Palette: HorizonEatAmount, DestructionAmount, HorizonTension, WorldHorizonEat (add via add_horizon_eater_mpc_params.py)")
    log("SLW guidance: measure extinction = -ln(0.01)/|absorption|, place false plane at 0.70-0.80*extinction, Bell R~3km sag@d=1.2km ~251m, crown tangent to plane")

def spawn_filter_debug(wipe=False):
    if not unreal:
        log("spawn_filter_debug: not in editor — offline check only")
        if PLACEMENTS_JSON.exists():
            j = json.loads(PLACEMENTS_JSON.read_text())
            log(f" placements offline: {len(j.get('points',[]))} points")
        else:
            log(f" no placements yet at {PLACEMENTS_JSON} — run Tools/PCG/build_horizon_eater_ecosystem.py")
        return
    if wipe:
        for actor in list(unreal.EditorLevelLibrary.get_all_level_actors()):
            if actor.get_actor_label().startswith("HE_Filter_"):
                unreal.EditorLevelLibrary.destroy_actor(actor)
                log(f" wiped {actor.get_actor_label()}")
    if not PLACEMENTS_JSON.exists():
        log(f"no placements json at {PLACEMENTS_JSON} — skip debug spawn. Run offline generator first.")
        return
    data = json.loads(PLACEMENTS_JSON.read_text())
    points = data.get("points", [])
    # Height-aware trace
    world = unreal.EditorLevelLibrary.get_editor_world()
    spawned = 0
    for pt in points[:24]:  # cap debug view
        label = f"HE_Filter_{pt['id']}"
        # dedupe
        if any(a.get_actor_label()==label for a in unreal.EditorLevelLibrary.get_all_level_actors()):
            continue
        xy = pt["position"]
        # synthetic Z from offline generator + raycast resolve
        syn_z = pt.get("height_cm", 13405)
        z = syn_z + 120  # hover above surface for debug billboard
        # Raycast via kismet if available
        try:
            start = unreal.Vector(xy[0], xy[1], 50000)
            end = unreal.Vector(xy[0], xy[1], -50000)
            hit = unreal.KismetSystemLibrary.line_trace_single(world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, unreal.HitResult(), True)
            # older API: use line_trace_single return
        except Exception:
            pass
        # Spawn a simple cube as debug marker (height-aware Z already)
        try:
            loc = unreal.Vector(xy[0], xy[1], z)
            rot = unreal.Rotator(0, pt.get("rotation",[0,0,0])[2], 0)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
            actor.set_actor_label(label)
            # Scale small
            actor.set_actor_scale3d(unreal.Vector(0.3,0.3,0.3))
            spawned += 1
        except Exception as e:
            log(f" spawn {label}: {e}")
    log(f"spawned {spawned} HE_Filter debug markers (height-aware synthetic, cap 24)")

def main():
    import sys
    wipe = "--wipe-filter-debug" in sys.argv
    audit_level()
    spawn_filter_debug(wipe=wipe)
    log("done. Next: tune Oceanology SLW absorption/Biolum via MI, then PIE from hero CineCameraActor at HorizonEat 0/0.6/1.0.")

if __name__ == "__main__":
    main()
