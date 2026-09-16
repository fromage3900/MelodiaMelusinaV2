import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_ground_audit.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
rep = {"floaters": [], "buried": [], "ok": 0, "checked": 0}


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
    except Exception:
        continue
    if not (lbl.startswith("MH_") or lbl in (
            "Morning_SheepDell_Lake", "Morning_Dell_Terrace",
            "Morning_SheepDell_PondBed", "Morning_Dell_Banks",
            "Morning_Brook_Arpeggio") or "Music Node" in lbl):
        continue
    rep["checked"] += 1
    l = a.get_actor_location()
    try:
        org, ext = a.get_actor_bounds(False)
        bottom = float(org.z) - float(ext.z)
    except Exception:
        bottom = float(l.z)
    gz = trace_down(float(l.x), float(l.y), float(l.z))
    if gz is None:
        rep["floaters"].append({"label": lbl, "loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)],
                                "issue": "no_ground_800_below"})
    elif bottom - gz > 150.0:
        rep["floaters"].append({"label": lbl, "gap": round(bottom - gz, 1)})
    elif gz - bottom > 120.0:
        rep["buried"].append({"label": lbl, "depth": round(gz - bottom, 1)})
    else:
        rep["ok"] += 1

open(OUT, "w").write(json.dumps(rep, indent=1))
print("GROUNDAUDIT_WROTE checked=%d floaters=%d buried=%d" % (
    rep["checked"], len(rep["floaters"]), len(rep["buried"])))
