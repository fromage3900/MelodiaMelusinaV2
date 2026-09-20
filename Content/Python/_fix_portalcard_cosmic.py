import unreal, json
from pathlib import Path

MAT = "/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_CosmicPortal"
LABEL = "WC_GreySpire_PortalCard"
EAL = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

mat = EAL.load_asset(MAT) if EAL.does_asset_exist(MAT) else None
if not mat:
    print("PORTAL_FIX", json.dumps({"ok": False, "err": "missing_mat"}))
    raise SystemExit(1)

actor = None
for a in svc.get_all_level_actors():
    if lab(a) == LABEL:
        actor = a
        break
if not actor:
    print("PORTAL_FIX", json.dumps({"ok": False, "err": "actor_missing"}))
    raise SystemExit(1)

slots = []
for c in actor.get_components_by_class(unreal.StaticMeshComponent) or []:
    try:
        n = c.get_num_materials()
    except Exception:
        n = 0
    for i in range(max(n, 1)):
        try:
            c.set_material(i, mat)
            slots.append(i)
        except Exception as e:
            slots.append(f"err{i}:{e}")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out = {"ok": True, "label": LABEL, "mat": MAT, "slots_set": slots, "saved": True}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/belvedere_portalcard_fix_2026-09-20.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8")
print("PORTAL_FIX", json.dumps(out))
