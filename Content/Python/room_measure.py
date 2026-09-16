import unreal, json, math
from unreal import EditorActorSubsystem

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/room_floor_field.v1.json"
svc = unreal.get_editor_subsystem(EditorActorSubsystem)
world = unreal.UnrealEditorSubsystem().get_editor_world()
rep = {"anchors": {}, "bounds": {}, "field": [], "audit": [],
       "float": [], "buried": [], "ok": 0}

ANCHOR_LABELS = ("Morning_Bed", "Dress_BedBedding",
                 "Morning_QuillTrigger_Wardrobe", "SM_room_2",
                 "SM_Bookshelf")

actors = list(svc.get_all_level_actors())
by_label = {}
for a in actors:
    try:
        by_label.setdefault(a.get_actor_label(), []).append(a)
    except Exception:
        pass

for lbl in ANCHOR_LABELS:
    cands = by_label.get(lbl, [])
    if cands:
        l = cands[0].get_actor_location()
        rep["anchors"][lbl] = [round(float(l.x), 1), round(float(l.y), 1),
                               round(float(l.z), 1)]
    else:
        rep["anchors"][lbl] = None

bed = rep["anchors"].get("Morning_Bed") or [1435.0, 2321.0, -421.2]
ward = rep["anchors"].get("Morning_QuillTrigger_Wardrobe") or bed
xs = [bed[0], ward[0]]
ys = [bed[1], ward[1]]
M = 600.0
rep["bounds"] = {"x0": round(min(xs) - M, 1), "x1": round(max(xs) + M, 1),
                 "y0": round(min(ys) - M, 1), "y1": round(max(ys) + M, 1),
                 "z_top": round(max(bed[2], ward[2]) + 400.0, 1)}


def trace_down(x, y, z_top):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, z_top), unreal.Vector(x, y, z_top - 4000.0),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0)
    d = hit.to_dict() if hit is not None else {}
    if d.get("blocking_hit"):
        return float(d["impact_point"].z)
    return None


STEP = 250.0
b = rep["bounds"]
gx, gy = b["x0"], b["y0"]
while gx <= b["x1"]:
    gy = b["y0"]
    while gy <= b["y1"]:
        gz = trace_down(gx, gy, b["z_top"])
        rep["field"].append({"x": round(gx, 1), "y": round(gy, 1), "z": gz})
        gy += STEP
    gx += STEP
rep["field_hit"] = sum(1 for c in rep["field"] if c["z"] is not None)


def field_z(x, y):
    best, bd = None, 1e18
    for c in rep["field"]:
        if c["z"] is None:
            continue
        d = (c["x"] - x) ** 2 + (c["y"] - y) ** 2
        if d < bd:
            bd, best = d, c["z"]
    return best


CLEAR = {"MH_path_bed_pond": 15.0, "MH_path_pond_window": 20.0,
         "MH_bank_pebble": 15.0, "MH_bank_flower": 25.0,
         "MH_bank_grass": 20.0, "MH_rosette": 25.0,
         "MH_hero_rock_0": 10.0, "MH_hero_rock_1": 10.0,
         "MH_hero_rock_2": 10.0, "MH_stump": 10.0}


def family(lbl):
    if lbl in CLEAR:
        return lbl
    for k in CLEAR:
        if lbl.startswith(k + "_") or lbl.startswith(k):
            return k
    return None


for a in actors:
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    fam = family(lbl)
    if fam is None and lbl not in ANCHOR_LABELS:
        continue
    l = a.get_actor_location()
    x, y, z = float(l.x), float(l.y), float(l.z)
    gz = field_z(x, y)
    if gz is None:
        gz = trace_down(x, y, b["z_top"])
    if gz is None:
        rep["audit"].append({"label": lbl, "issue": "no_ground"})
        continue
    gap = z - gz
    rec = {"label": lbl, "z": round(z, 1), "ground": round(gz, 1),
           "gap": round(gap, 1)}
    rep["audit"].append(rec)
    if gap > 200.0:
        rep["float"].append(rec)
    elif -gap > 200.0:
        rep["buried"].append(rec)
    else:
        rep["ok"] += 1

open(OUT, "w").write(json.dumps(rep, indent=1))
print("ROOMFIELD_WROTE anchors=%d cells=%d hit=%d checked=%d float=%d buried=%d" % (
    sum(1 for v in rep["anchors"].values() if v), len(rep["field"]),
    rep["field_hit"], len(rep["audit"]), len(rep["float"]), len(rep["buried"])))
