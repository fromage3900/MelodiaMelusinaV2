import unreal, json, math
from unreal import EditorActorSubsystem

MANIFEST = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_house_dell.v1.json"
REPORT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_house_dell_apply.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
al = unreal.EditorAssetLibrary
GOLD = 137.50776

MESHES = {
    "pebble": "/Game/Megascans/3D_Assets/BeachSandWithPebbles/SM_BeachSandWithPebbles_01",
    "grass": "/Game/Custom/RS_Assets/MossyRock_29/SM_GrassGroundPatch_01",
    "flower": "/Game/EnvSandbox/Library/FoliageCards/GenericFlower1",
    "flower_tall": "/Game/EnvSandbox/Library/FoliageCards/GenericFlowerTall",
    "rock": "/Game/Custom/RS_Assets/ForestRock_01/Monika_Rock_1/SM_RockScan_01",
    "stump": "/Game/Megascans/3D_Assets/BirchTreeStump/SM_BirchTreeStump_01",
}
loaded = {}
for k, p in MESHES.items():
    m = al.load_asset(p)
    if m is not None:
        loaded[k] = m
manifest = {"seed": 2026, "missing_meshes": [k for k in MESHES if k not in loaded],
            "points": []}


def trace_z(x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 3000.0), unreal.Vector(x, y, -3000.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = hit.to_dict() if hit is not None else {}
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


def emit(kind, mesh, x, y, clearance, scale):
    if mesh not in loaded:
        return
    gz = trace_z(x, y)
    if gz is None:
        manifest["points"].append({"kind": kind, "status": "no_ground",
                                   "xy": [round(x, 1), round(y, 1)]})
        return
    manifest["points"].append({"kind": kind, "mesh": MESHES[mesh], "status": "placed",
                               "loc": [round(x, 1), round(y, 1), round(gz + clearance, 1)],
                               "scale": scale})


CX, CY = -950.0, 2300.0
# phyllotaxis bank rings (golden angle)
for i in range(14):
    a = math.radians(i * GOLD)
    emit("bank_pebble", "pebble", CX + math.cos(a) * 330.0, CY + math.sin(a) * 330.0, 15.0, 0.8)
for i in range(18):
    a = math.radians(i * GOLD + 40.0)
    emit("bank_flower", "flower", CX + math.cos(a) * 480.0, CY + math.sin(a) * 480.0, 25.0, 1.0)
for i in range(12):
    a = math.radians(i * GOLD + 80.0)
    emit("bank_grass", "grass", CX + math.cos(a) * 650.0, CY + math.sin(a) * 650.0, 20.0, 1.1)
# mandala rosette: 8 tall flowers at pond rim
for i in range(8):
    a = math.radians(i * 45.0 + 22.5)
    emit("rosette", "flower_tall", CX + math.cos(a) * 300.0, CY + math.sin(a) * 300.0, 25.0, 1.0)


def bez(p0, c, p2, f):
    u = 1.0 - f
    return (u * u * p0[0] + 2 * u * f * c[0] + f * f * p2[0],
            u * u * p0[1] + 2 * u * f * c[1] + f * f * p2[1])


def path(kind, mesh, p0, c, p2, step, clearance, scale):
    approx = math.dist(p0, c) + math.dist(c, p2)
    n = max(int(approx / step), 2)
    for i in range(n + 1):
        x, y = bez(p0, c, p2, i / n)
        emit(kind, mesh, x, y, clearance, scale)


# bed -> pond pebble path, pond -> window-light mixed path
path("path_bed_pond", "pebble", (1435.0, 2321.0), (300.0, 2560.0), (-620.0, 2330.0), 120.0, 15.0, 0.7)
path("path_pond_window", "grass", (-950.0, 2300.0), (-200.0, 1900.0), (900.0, 2150.0), 150.0, 20.0, 1.0)
# hero rocks + one stump
for j, (rx, ry, s) in enumerate([(-1350.0, 2500.0, 1.1), (-550.0, 2050.0, 0.7), (200.0, 2460.0, 0.9)]):
    emit("hero_rock_%d" % j, "rock", rx, ry, 10.0, s)
emit("stump", "stump", -1200.0, 2100.0, 10.0, 1.0)

open(MANIFEST, "w").write(json.dumps(manifest, indent=1))

# --- apply ---
placed = 0
for p in manifest["points"]:
    if p.get("status") != "placed":
        continue
    mesh = al.load_asset(p["mesh"])
    if mesh is None:
        p["status"] = "mesh_null_at_apply"
        continue
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh, unreal.Vector(*p["loc"]), unreal.Rotator(0, 0, 0))
    if a is None:
        p["status"] = "spawn_null"
        continue
    a.set_actor_label("MH_%s" % p["kind"])
    a.set_actor_scale3d(unreal.Vector(p["scale"], p["scale"], p["scale"]))
    placed += 1

# retire the failed tea test volume
for a in list(svc.get_all_level_actors()):
    try:
        if a.get_actor_label() == "Morning_TeaGarden_Test":
            svc.destroy_actor(a)
    except Exception:
        pass

rep = {"placed": placed,
       "manifest_points": len(manifest["points"]),
       "missing_meshes": manifest["missing_meshes"]}
open(REPORT, "w").write(json.dumps(rep, indent=1))
print("HOUSEDELL_WROTE placed=" + str(placed))
