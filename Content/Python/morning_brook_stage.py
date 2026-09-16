import unreal, json, math, re
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_brook_stage.json"
rep = {"arp": [], "bells": [], "water": {}}
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
al = unreal.EditorAssetLibrary


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


def num_suffix(lbl):
    m = re.search(r"(\d+)$", lbl)
    return int(m.group(1)) if m else 0


actors = list(svc.get_all_level_actors())
arps = sorted([a for a in actors if "ArpeggioBridge Music Node" in a.get_actor_label()],
              key=lambda a: num_suffix(a.get_actor_label()))
bells = [a for a in actors if "BellTreeGarden Music Node" in a.get_actor_label()]

# --- arpeggio: bed-side high -> sheep pond low, meandering brook line ---
sx, sy, sz = 1250.0, 2420.0, -460.0
ex, ey, ez = -700.0, 2290.0, -600.0
n = max(len(arps) - 1, 1)
for i, a in enumerate(arps):
    f = i / n
    x = sx + (ex - sx) * f
    y = (sy + (ey - sy) * f) + math.sin(f * math.pi * 2.0) * 130.0
    gz = trace_z(x, y)
    z = (gz + 45.0) if gz is not None else (sz + (ez - sz) * f)
    a.set_actor_location(unreal.Vector(x, y, z), False, True)
    rep["arp"].append({"label": a.get_actor_label(),
                       "loc": [round(x, 1), round(y, 1), round(z, 1)]})

# --- bells: two bank clusters flanking the pond ---
cx, cy = -950.0, 2300.0
for i, a in enumerate(bells):
    side = 1 if i % 2 == 0 else -1
    ang = (i / max(len(bells), 1)) * math.pi * 2.0
    x = cx + math.cos(ang) * 380.0
    y = cy + side * (300.0 + (i % 3) * 90.0)
    gz = trace_z(x, y)
    z = (gz + 60.0) if gz is not None else -540.0
    a.set_actor_location(unreal.Vector(x, y, z), False, True)
    rep["bells"].append({"label": a.get_actor_label(),
                         "loc": [round(x, 1), round(y, 1), round(z, 1)]})

# --- water: plane + lake MI at the dell ---
try:
    gz = trace_z(cx, cy)
    wz = (gz + 15.0) if gz is not None else -635.0
    plane = al.load_asset("/Engine/BasicShapes/Plane")
    w = unreal.EditorLevelLibrary.spawn_actor_from_object(
        plane, unreal.Vector(cx, cy, wz), unreal.Rotator(0, 0, 0))
    if w is None:
        rep["water"] = {"ok": False, "err": "plane spawn null"}
    else:
        w.set_actor_label("Morning_SheepDell_Water")
        w.set_actor_scale3d(unreal.Vector(5.2, 5.2, 1.0))
        mi = al.load_asset("/Oceanology_Plugin/Design/Lake/Materials/Water/SingleLayerWater/M_Lake_Inst")
        if mi is not None:
            comp = w.get_component_by_class(unreal.StaticMeshComponent)
            if comp is not None:
                comp.set_editor_property("override_materials", [mi])
                rep["water"]["mi"] = True
        rep["water"].update({"ok": True, "loc": [cx, cy, wz]})
except Exception as e:
    rep["water"] = {"ok": False, "err": str(e)[:200]}

# --- cleanup probe ---
for a in list(actors):
    try:
        if a.get_actor_label() == "Dbg_CubeProbe_DELETE":
            svc.destroy_actor(a)
            rep["cube_deleted"] = True
    except Exception:
        pass

open(OUT, "w").write(json.dumps(rep, indent=1))
print("BROOK_STAGE_WROTE " + OUT + " arp=" + str(len(rep["arp"])) +
      " bells=" + str(len(rep["bells"])))
