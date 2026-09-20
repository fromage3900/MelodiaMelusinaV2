import unreal, json
from pathlib import Path

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary

candidates = []
for a in svc.get_all_level_actors():
    L = lab(a)
    C = a.get_class().get_name()
    if not any(k in L for k in ("SM_room", "SM_corridor", "SM_wallhi", "SM_wallmid", "SM_wallshort", "SM_gazebo", "SM_SurrealRoof", "SM_venetian", "SM_Greybox_Wall", "PCG_Melusina")):
        # also mesh path check
        mesh_path = None
        try:
            for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                if c.static_mesh:
                    mesh_path = c.static_mesh.get_path_name()
                    break
        except Exception:
            pass
        if not mesh_path or not any(k in mesh_path for k in ("MelusinasHouse", "houseassets", "SM_room", "SM_corridor", "wallhi")):
            continue
    else:
        mesh_path = None
        try:
            for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                if c.static_mesh:
                    mesh_path = c.static_mesh.get_path_name()
                    break
        except Exception:
            pass
    t = a.get_actor_transform()
    try:
        o, e = a.get_actor_bounds(False, False)
        extent = [round(e.x,1), round(e.y,1), round(e.z,1)]
        max_h = round(max(e.x, e.y), 1)
    except Exception:
        extent = None; max_h = 0
    candidates.append({
        "label": L, "class": C, "mesh": mesh_path,
        "loc": [round(t.translation.x,1), round(t.translation.y,1), round(t.translation.z,1)],
        "scale": [round(t.scale3d.x,3), round(t.scale3d.y,3), round(t.scale3d.z,3)],
        "extent": extent, "max_horiz_cm": max_h,
    })

candidates.sort(key=lambda r: -(r.get("max_horiz_cm") or 0))

# proposed bases: largest room/corridor/wallhi floors
proposed = [c for c in candidates if any(k in (c["label"] or "") for k in ("SM_room", "SM_corridor")) or (c.get("max_horiz_cm") or 0) > 300]

pcg = "/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell"
assets = {
    "SM_room1": EAL.does_asset_exist("/Game/_PROJECT/MelusinasHouse/SM_room1"),
    "SM_room2": EAL.does_asset_exist("/Game/_PROJECT/MelusinasHouse/SM_room2"),
    "SM_corridor": EAL.does_asset_exist("/Game/_PROJECT/MelusinasHouse/SM_corridor"),
    "PCG_MorningDell": EAL.does_asset_exist(pcg),
    "BP_RoadBuilder": EAL.does_asset_exist("/Game/Actor_BP/BP_RoadBuilder"),
}

report = {
    "schema": "melodia.melusina_house_room_bases_inventory.v1",
    "mode": "read_only",
    "note": "No dedicated UE RoomBuilder BP; room shells are MelusinasHouse meshes + Blender GN builders in docs. Live bases below.",
    "assets": assets,
    "pcg_path": pcg,
    "live_candidates": candidates,
    "proposed_long_floor_bases": proposed[:15],
    "suggested_labels_destroy_only": ["WC_HouseRoom_*"],
    "stay_off": ["WC_SpireRamp_*", "Morning_SheepDell_Lake", "HeroCorner", "PCG volumes unless MorningDell"],
}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/melusina_house_room_bases_inventory_2026-09-20.json").write_text(
    json.dumps(report, indent=2, default=str), encoding="utf-8")
print("BASES", json.dumps({
    "candidates": len(candidates),
    "proposed": [{"label": p["label"], "max_horiz": p["max_horiz_cm"], "loc": p["loc"], "mesh": p.get("mesh")} for p in proposed[:10]],
    "assets": assets,
}, default=str))
