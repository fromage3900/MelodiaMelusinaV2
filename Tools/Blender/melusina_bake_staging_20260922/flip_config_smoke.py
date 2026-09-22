# FLIP bake-gen config + smoke bake (headless, factory-startup).
# Opens the staging copy, enables flip_fluids_addon (default_set=True per house rule),
# records the existing FLIP roles, fixes the two known silent-failure blockers
# (viewport-hidden participants, sub-voxel emitters), runs a res-24 frames-1-10
# smoke to a dedicated cache, and verifies bobj headers (8-byte = empty = FAIL).
# Saves the bake-gen blend ONLY after the smoke passes, configured for the full run.
import bpy, addon_utils, json, os, struct

SRC = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922\harp_wip_stage_src.blend"
GEN = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922\harp_FLIP_bake_gen1.blend"
CACHE_SMOKE = r"C:\EnvironmentPortfolio\FlipCache\hair_hero_20260922_smoke2"
CACHE_FULL = r"C:\EnvironmentPortfolio\FlipCache\hair_hero_20260922"
LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_bake_staging_20260922"
EV = os.path.join(LANE, "flip_config_smoke_evidence.json")

ev = {"schema": "melodia.flip_bake_gen.v1", "source": SRC, "bake_gen": GEN,
      "cache_smoke": CACHE_SMOKE, "cache_full": CACHE_FULL}

# addon enable — default_set=True is load-bearing headless
addon_utils.enable("flip_fluids_addon", default_set=True, persistent=False)
ev["addon_enabled"] = ("flip_fluids_addon" in bpy.context.preferences.addons)

scene = bpy.context.scene
ff = scene.flip_fluid
ev["num_domains"] = ff.get_num_domain_objects() if hasattr(ff, "get_num_domain_objects") else None

domain = None
roles = {}
for ob in bpy.data.objects:
    ffp = getattr(ob, "flip_fluid", None)
    if ffp is None or not hasattr(ffp, "object_type"):
        continue
    try:
        if ffp.is_domain():
            domain = ob
    except Exception:
        pass
    if ob.name.startswith(("FF_", "LF_TipDrip")):
        roles[ob.name] = ffp.object_type
ev["roles"] = roles
ev["domain_object"] = domain.name if domain else None
assert domain is not None, "no FLIP domain found"

# Blocker 1: exporter skips viewport-hidden objects — unhide every participant
unhidden = []
for ob in bpy.data.objects:
    ffp = getattr(ob, "flip_fluid", None)
    if ffp is not None and hasattr(ffp, "object_type") and ob.hide_viewport:
        ob.hide_viewport = False
        unhidden.append(ob.name)
ev["unhidden"] = unhidden

# Blocker 2b: non-mesh participants (CURVES) cannot be extracted by the exporter
deactivated = []
for ob in bpy.data.objects:
    ffp = getattr(ob, "flip_fluid", None)
    if ffp is None or not hasattr(ffp, "object_type"):
        continue
    try:
        if not ffp.is_active or ffp.is_domain():
            continue
    except Exception:
        continue
    if ob.type != "MESH":
        ffp.is_active = False
        deactivated.append(ob.name + ":" + ob.type)
ev["deactivated_nonmesh"] = deactivated

# Blocker 2: sub-voxel emitters — bulk x2.5 about center (proven diagnostic)
BULK = ("FF_MelusinaHair_Drip", "FF_MelusinaHair_Sheet",
        "LF_TipDrip_Hair_Strand.002", "LF_TipDrip_Hair_Strand.004",
        "LF_TipDrip_Hair_Strand.007")
bulk = {}
for nm in BULK:
    ob = bpy.data.objects.get(nm)
    if ob:
        ob.scale = tuple(s * 2.5 for s in ob.scale)
        bulk[nm] = [round(s, 2) for s in ob.scale]
ev["bulk_x2.5"] = bulk

dom = domain.flip_fluid.domain
sim = dom.simulation
cache = dom.cache

# --- SMOKE: res 48, frames 1-10, dedicated cache (res 24 cell 0.09 m leaves the
# x2.5-bulked 10.5 cm drip at 1.17 voxels -> zero fluid; res 48 cell 0.045 m = 2.3 voxels)
sim.resolution = 48
sim.frame_range_mode = "FRAME_RANGE_TIMELINE"
scene.frame_start = 1
scene.frame_end = 10
cache.cache_directory = CACHE_SMOKE
cache.mark_cache_directory_set()
import shutil
if os.path.isdir(CACHE_SMOKE):
    shutil.rmtree(CACHE_SMOKE)      # stale-cache trap: prove a FRESH cook
bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()

def bobj_report(cache_dir):
    out = {"dirs": [], "frames": {}}
    for root, _dirs, files in os.walk(cache_dir):
        for fn in files:
            p = os.path.join(root, fn)
            if fn.endswith(".bobj"):
                with open(p, "rb") as f:
                    head = f.read(4)
                nv = struct.unpack("<i", head)[0] if len(head) == 4 else -1
                out["frames"][os.path.basename(p)] = {
                    "bytes": os.path.getsize(p), "num_verts": nv,
                    "empty": os.path.getsize(p) <= 8}
            elif fn in ("flipdata.sim",):
                out["dirs"].append(p)
    return out

rep = bobj_report(CACHE_SMOKE)
ev["smoke"] = rep
bobjs = [v for k, v in rep["frames"].items()]
nonempty = [v for v in bobjs if not v["empty"]]
ev["smoke_verdict"] = ("PASS" if len(nonempty) >= 5 else
                       "FAIL_ZERO_FLUID" if bobjs else "FAIL_NO_BOBJ")

if ev["smoke_verdict"] == "PASS":
    # --- configure FULL bake: res 72, frames 1-240, full cache ---
    sim.resolution = 72
    scene.frame_end = 240
    cache.cache_directory = CACHE_FULL
    cache.mark_cache_directory_set()
    bpy.ops.wm.save_as_mainfile(filepath=GEN)
    ev["bake_gen_saved"] = os.path.isfile(GEN)

with open(EV, "w", encoding="utf-8") as f:
    json.dump(ev, f, indent=1)
print("FLIP_SMOKE_VERDICT:", ev["smoke_verdict"])
print("domains:", ev["num_domains"], "| roles:", json.dumps(roles))
print("unhidden:", unhidden, "| bulked:", list(bulk.keys()))
ne = [v for v in bobjs if not v["empty"]]
print("smoke bobjs: %d total, %d non-empty, verts sample=%s" % (
    len(bobjs), len(ne), [v["num_verts"] for v in bobjs[:5]]))
