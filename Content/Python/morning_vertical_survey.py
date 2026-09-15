import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_vertical_survey.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
rep = {"climbables": []}


def top_z(x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 3000.0), unreal.Vector(x, y, -3000.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = hit.to_dict() if hit is not None else {}
    if d.get("blocking_hit"):
        return round(float(d["impact_point"].z), 1)
    return None


KEYS = ("Bed", "Shelf", "Wardrobe", "Rafter", "Beam", "Window", "Ledge",
        "Bookshelf", "Door", "Cliff", "Wall", "Plinth", "Pillar", "Arch")
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    if not any(k.lower() in lbl.lower() for k in KEYS):
        continue
    l = a.get_actor_location()
    x, y = round(l.x, 1), round(l.y, 1)
    try:
        org, ext = a.get_actor_bounds(False)
        top = round(float(org.z) + float(ext.z), 1)
    except Exception:
        top = None
    rep["climbables"].append({"label": lbl, "loc": [x, y, round(l.z, 1)],
                              "top_z": top, "traced_z": top_z(x, y)})
rep["climbables"].sort(key=lambda r: (r["top_z"] is None, -(r["top_z"] or 0)))
open(OUT, "w").write(json.dumps(rep, indent=1))
print("VERTSURVEY_WROTE " + str(len(rep["climbables"])))
