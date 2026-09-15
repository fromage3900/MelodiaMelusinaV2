import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_native_lake.json"
rep = {}
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()

# cleanup debug ghosts
for a in list(svc.get_all_level_actors()):
    try:
        if a.get_actor_label() in ("Dbg_NativeLake_DELETE",):
            svc.destroy_actor(a)
            rep["dbg_cleared"] = True
    except Exception:
        pass


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


try:
    nc = getattr(unreal, "OceanologyLake", None)
    lx, ly = -950.0, 2300.0
    gz = trace_z(lx, ly)
    lz = (gz + 10.0) if gz is not None else -640.0
    lake = unreal.EditorLevelLibrary.spawn_actor_from_class(
        nc, unreal.Vector(lx, ly, lz), unreal.Rotator(0, 0, 0))
    if lake is None:
        rep["ok"] = False
    else:
        lake.set_actor_label("Morning_SheepDell_Lake")
        try:
            org, ext = lake.get_actor_bounds(False)
            width = max(float(ext.x) * 2.0, 1.0)
            s = max(0.02, min(560.0 / width, 3.0))
        except Exception:
            s = 0.15
        lake.set_actor_scale3d(unreal.Vector(s, s, 1.0))
        rep.update({"ok": True, "loc": [lx, ly, lz], "scale": s})
except Exception as e:
    rep.update({"ok": False, "err": str(e)[:200]})

open(OUT, "w").write(json.dumps(rep, indent=1))
print("NATIVELAKE_WROTE " + OUT)
