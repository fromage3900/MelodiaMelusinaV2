import unreal, json
from pathlib import Path

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
wname = world.get_name() if world else None

house=[]; floors=[]; longish=[]; builders=[]
for a in svc.get_all_level_actors():
    L = lab(a); C = a.get_class().get_name()
    key = (L + " " + C).lower()
    t = a.get_actor_transform()
    rec = {"label": L, "class": C, "loc": [round(t.translation.x,1), round(t.translation.y,1), round(t.translation.z,1)],
           "scale": [round(t.scale3d.x,3), round(t.scale3d.y,3), round(t.scale3d.z,3)]}
    try:
        o,e = a.get_actor_bounds(False, False)
        rec["extent"] = [round(e.x,1), round(e.y,1), round(e.z,1)]
        rec["max_horiz"] = round(max(e.x, e.y), 1)
    except Exception:
        rec["extent"] = None
    if any(k in key for k in ("melusina", "house", "cottage", "dwelling", "wallhi", "sm_wall")):
        house.append(rec)
    if "floor" in key or "deck" in key or "long" in key:
        floors.append(rec)
    if rec.get("max_horiz") and rec["max_horiz"] > 400 and "staticmesh" in C.lower():
        if any(k in key for k in ("house", "melusina", "wall", "floor", "deck", "plank", "hall")):
            longish.append(rec)
    if any(k in key for k in ("roombuilder", "room_builder", "bp_room", "pcg_house", "morningdell")):
        builders.append(rec)

# asset search
EAL = unreal.EditorAssetLibrary
bps=[]
for root in ["/Game/_PROJECT/MelusinasHouse", "/Game/Melodia/_PROJECT/MelusinasHouse", "/Game/EnvSandbox/PCG/House", "/Game/Actor_BP", "/Game/_PROJECT/houseassets"]:
    try:
        if not EAL.does_directory_exist(root):
            continue
        for p in EAL.list_assets(root, True, False) or []:
            pl = p.lower()
            if any(k in pl for k in ("floor", "room", "long", "builder", "module", "hall", "corridor")):
                bps.append(p)
    except Exception as e:
        bps.append(f"ERR {root}: {e}")

# sort longish by extent
longish.sort(key=lambda r: -(r.get("max_horiz") or 0))

out = {
    "world": wname,
    "house_actors_n": len(house),
    "house_sample": house[:40],
    "floor_label_hits": floors[:30],
    "long_house_meshes": longish[:25],
    "builder_actors": builders,
    "asset_hits": bps[:60],
}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/melusina_house_floors_inventory_2026-09-20.json").write_text(
    json.dumps(out, indent=2, default=str), encoding="utf-8")
print("HOUSE_INV", json.dumps({
    "world": wname,
    "house_n": len(house),
    "floor_n": len(floors),
    "long_n": len(longish),
    "long_top": [{"label": r["label"], "max_horiz": r.get("max_horiz"), "loc": r["loc"]} for r in longish[:12]],
    "builders": builders,
    "assets_head": bps[:25],
}, default=str))
