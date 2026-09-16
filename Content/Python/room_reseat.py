import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/room_reseat.v1.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ed.get_editor_world()
rep = {"moved": [], "skipped": [], "saved": None, "dirty_after": None}


def trace(x, y, z0, depth, ignore):
    h = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z0), unreal.Vector(x, y, z0 - depth),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore or [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = h.to_dict() if h is not None else {}
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


def seat(a, x, y, z):
    a.modify()
    a.set_actor_location(unreal.Vector(x, y, z), False, True)
    l = a.get_actor_location()
    rep["moved"].append({"label": a.get_actor_label(),
                         "to": [round(float(l.x), 1), round(float(l.y), 1),
                                round(float(l.z), 1)]})


# 1. buried hillside grasses -> surface + clearance
for a in list(svc.get_all_level_actors()):
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    if lbl != "MH_bank_grass":
        continue
    l = a.get_actor_location()
    x, y, z = float(l.x), float(l.y), float(l.z)
    if z >= 150.0:
        continue
    sup = trace(x, y, z + 100.0, 1200.0, [a])
    if sup is not None and sup > z + 5.0:
        seat(a, x, y, sup + 20.0)
    else:
        rep["skipped"].append({"label": lbl, "z": round(z, 1),
                               "why": "no_surface_above"})

# 2. bookshelf -> bedside, measured floor first
shelf = None
for a in list(svc.get_all_level_actors()):
    try:
        if a.get_actor_label() == "SM_Bookshelf":
            shelf = a
            break
    except Exception:
        continue
if shelf is not None:
    sx, sy = 1150.0, 2321.0
    floor = trace(sx, sy, -21.2, 4000.0, [shelf])
    if floor is not None:
        seat(shelf, sx, sy, floor + 183.0)
    else:
        rep["skipped"].append({"label": "SM_Bookshelf", "why": "no_floor_at_home"})

# 3. SM_room_2 (greybox shell) -> hands off, owner's call
rep["skipped"].append({"label": "SM_room_2", "why": "greybox_shell_owner_call"})

ok = unreal.EditorLevelLibrary.save_current_level()
rep["saved"] = bool(ok)
open(OUT, "w").write(json.dumps(rep, indent=1))
print("RESEAT_WROTE moved=%d skipped=%d saved=%s" % (
    len(rep["moved"]), len(rep["skipped"]), rep["saved"]))
