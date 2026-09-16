import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_ground_audit2.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
rep = {"float": [], "buried": [], "ok": 0, "checked": 0}


def trace_down(x, y, z):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z + 10.0), unreal.Vector(x, y, z - 800.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = hit.to_dict() if hit is not None else {}
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


for a in list(svc.get_all_level_actors()):
    try:
        lbl = a.get_actor_label()
        cls = a.get_class().get_name()
    except Exception:
        continue
    if cls == "PCGVolume":
        continue
    if not (lbl.startswith("MH_") or "Music Node" in lbl):
        continue
    rep["checked"] += 1
    l = a.get_actor_location()
    gz = trace_down(float(l.x), float(l.y), float(l.z))
    if gz is None:
        rep["float"].append({"label": lbl, "issue": "no_ground_800_below"})
    elif float(l.z) - gz > 200.0:
        rep["float"].append({"label": lbl, "gap": round(float(l.z) - gz, 1)})
    elif gz - float(l.z) > 200.0:
        rep["buried"].append({"label": lbl, "depth": round(gz - float(l.z), 1)})
    else:
        rep["ok"] += 1

open(OUT, "w").write(json.dumps(rep, indent=1))
print("GROUNDAUDIT2_WROTE checked=%d float=%d buried=%d" % (
    rep["checked"], len(rep["float"]), len(rep["buried"])))
