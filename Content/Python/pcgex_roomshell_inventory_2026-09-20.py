"""Clear SalonA shells + inventory PCGex/RoomShell assets in live editor."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
wname = world.get_name() if world else None

destroyed = []
for a in list(svc.get_all_level_actors()):
    L = lab(a)
    if L.startswith("WC_HouseRoomShell_SalonA_"):
        t = a.get_actor_location()
        if svc.destroy_actor(a):
            destroyed.append({"label": L, "z": float(t.z)})

# Asset inventory
paths_interest = []
roots = [
    "/Game/EnvSandbox/PCG",
    "/Game/Melodia",
    "/Game/Melodia/PCG",
    "/Game/Melodia/WorldCompiler",
    "/Game/EnvSandbox/Blueprints",
    "/Game/Actor_BP",
    "/Game/_PROJECT",
]
for root in roots:
    try:
        if not EAL.does_directory_exist(root):
            continue
        for p in EAL.list_assets(root, True, False) or []:
            pl = p.lower()
            name = p.rsplit("/", 1)[-1].lower()
            if any(k in pl for k in ("pcgex", "pcgextended", "melusinaroomshell", "roomshell", "pcg_melusina")):
                paths_interest.append(p)
            if "pcg_" in name and any(k in name for k in ("room", "house", "shell", "phyllo", "nikki")):
                paths_interest.append(p)
    except Exception as e:
        paths_interest.append(f"ERR:{root}:{e}")

seen=set(); uniq=[]
for p in paths_interest:
    if p not in seen:
        seen.add(p); uniq.append(p)

checks = {
    "BP_MelusinaRoomShell": [
        "/Game/Melodia/Blueprints/BP_MelusinaRoomShell",
        "/Game/EnvSandbox/Blueprints/BP_MelusinaRoomShell",
        "/Game/Actor_BP/BP_MelusinaRoomShell",
        "/Game/Melodia/House/BP_MelusinaRoomShell",
    ],
    "PCG_MelusinaRoomShell_PCGex": [
        "/Game/Melodia/PCG/PCG_MelusinaRoomShell_PCGex",
        "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex",
        "/Game/Melodia/House/PCG_MelusinaRoomShell_PCGex",
    ],
}
exists = {}
for key, cands in checks.items():
    exists[key] = {c: EAL.does_asset_exist(c) for c in cands}

# room2 still there?
room2 = None
for a in svc.get_all_level_actors():
    if lab(a) == "SM_room_2":
        t = a.get_actor_location()
        room2 = [float(t.x), float(t.y), float(t.z)]
        break

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    saved = True
except Exception as e:
    saved = str(e)

report = {
    "schema": "melodia.pcgex_roomshell_inventory.v1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "world": wname,
    "destroyed_SalonA": destroyed,
    "destroyed_n": len(destroyed),
    "asset_hits": uniq[:100],
    "asset_n": len(uniq),
    "target_exists": exists,
    "SM_room_2_loc": room2,
    "level_saved": saved,
}
out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "pcgex_roomshell_inventory_2026-09-20.json"
out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print("INV " + json.dumps({
    "world": wname,
    "destroyed_n": len(destroyed),
    "destroyed_z": [d["z"] for d in destroyed[:10]],
    "asset_n": len(uniq),
    "hits_head": uniq[:30],
    "targets": {k: any(v.values()) for k,v in exists.items()},
    "exists_detail": exists,
    "room2": room2,
    "saved": saved,
}, default=str))
