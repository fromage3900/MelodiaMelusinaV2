import unreal, json
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_resnap.json"
rep = {"moved": 0, "checked": 0, "no_ground": []}
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()

CLEAR = {"MH_bank_pebble": 15.0, "MH_bank_flower": 25.0, "MH_bank_grass": 20.0,
         "MH_rosette": 25.0, "MH_path_bed_pond": 15.0, "MH_path_pond_window": 20.0,
         "MH_hero_rock_0": 10.0, "MH_hero_rock_1": 10.0, "MH_hero_rock_2": 10.0,
         "MH_stump": 10.0}


def trace_low(x, y):
    # start BELOW the canopy (~+150) so only true floor answers
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 150.0), unreal.Vector(x, y, -3000.0),
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
    kind = next((k for k in CLEAR if lbl == k or lbl.startswith(k + "_")), None)
    # labels repeat (MH_path_bed_pond xN): match by prefix family
    fam = None
    for k in CLEAR:
        if lbl == k or (lbl.startswith("MH_") and k.startswith(lbl)):
            fam = k
            break
    if fam is None:
        if lbl.startswith("MH_path_bed_pond"):
            fam = "MH_path_bed_pond"
        elif lbl.startswith("MH_path_pond_window"):
            fam = "MH_path_pond_window"
        elif lbl.startswith("MH_bank_"):
            fam = "MH_bank_pebble"
        elif lbl.startswith("MH_rosette"):
            fam = "MH_rosette"
        elif lbl.startswith("MH_hero_rock"):
            fam = "MH_hero_rock_0"
        elif lbl.startswith("MH_stump"):
            fam = "MH_stump"
        else:
            continue
    rep["checked"] += 1
    l = a.get_actor_location()
    gz = trace_low(float(l.x), float(l.y))
    if gz is None:
        rep["no_ground"].append(lbl)
        continue
    a.set_actor_location(unreal.Vector(float(l.x), float(l.y), gz + CLEAR[fam]), False, True)
    rep["moved"] += 1

open(OUT, "w").write(json.dumps(rep, indent=1))
print("RESNAP_WROTE moved=%d checked=%d noground=%d" % (
    rep["moved"], rep["checked"], len(rep["no_ground"])))
