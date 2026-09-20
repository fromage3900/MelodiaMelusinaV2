"""Destroy SalonA shells; verify stubs; inventory snapshot."""
import json
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

destroyed = []
for a in list(svc.get_all_level_actors()):
    L = lab(a)
    if L.startswith("WC_HouseRoomShell_SalonA_"):
        z = float(a.get_actor_location().z)
        if svc.destroy_actor(a):
            destroyed.append({"label": L, "z": z})

# ensure stubs
PCG = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
BP = "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell"
notes = []
if not EAL.does_asset_exist(PCG):
    src = "/Game/EnvSandbox/PCG/_Dev/_probe_pcgex"
    if EAL.does_asset_exist(src):
        EAL.duplicate_asset(src, PCG)
        notes.append("dup_pcg")
    else:
        notes.append("no_pcg_src")
if not EAL.does_asset_exist(BP):
    try:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("ParentClass", unreal.Actor)
        ATL = unreal.AssetToolsHelpers.get_asset_tools()
        ATL.create_asset("BP_MelusinaRoomShell", "/Game/EnvSandbox/Blueprints/House", unreal.Blueprint, factory)
        notes.append("created_bp")
    except Exception as e:
        notes.append(f"bp_err:{e}")

hits = []
for root in ["/Game/EnvSandbox/PCG", "/Game/Melodia"]:
    try:
        if not EAL.does_directory_exist(root):
            continue
        for p in EAL.list_assets(root, True, False) or []:
            pl = p.lower()
            if "pcgex" in pl or "roomshell" in pl or "melusinaroom" in pl or ("pcg_" in pl and "melusina" in pl):
                hits.append(p)
    except Exception:
        pass

room2 = None
for a in svc.get_all_level_actors():
    if lab(a) == "SM_room_2":
        t = a.get_actor_location()
        room2 = [float(t.x), float(t.y), float(t.z)]
        break

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("PREP", json.dumps({
    "destroyed_n": len(destroyed),
    "destroyed_z": [d["z"] for d in destroyed[:8]],
    "pcg": EAL.does_asset_exist(PCG),
    "bp": EAL.does_asset_exist(BP),
    "hits": hits[:25],
    "room2": room2,
    "notes": notes,
}, default=str))
