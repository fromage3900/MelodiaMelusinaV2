import unreal, json
from datetime import datetime, timezone
LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
w = UES.get_editor_world()
wp = w.get_path_name() if w else None
out = {"world": wp, "morning": "MelusinaMorning" in (wp or ""), "saved": False}
if out["morning"]:
    print("SAVE_ERR morning")
else:
    if (not wp or "LV_FarawayMother_Prototype" not in wp) and EAL.does_asset_exist(LVL):
        LES.load_level(LVL)
        w = UES.get_editor_world()
        wp = w.get_path_name() if w else None
        out["world"] = wp
    pkgs = []
    if w:
        pkgs.append(w.get_outermost())
    for a in EAS.get_all_level_actors():
        try:
            pkgs.append(a.get_outermost())
        except Exception:
            pass
    seen = set()
    uniq = []
    for p in pkgs:
        try:
            n = p.get_name()
            if n not in seen:
                seen.add(n)
                uniq.append(p)
        except Exception:
            pass
    n = 0
    for i in range(0, max(len(uniq), 1), 60):
        chunk = uniq[i:i+60]
        if not chunk:
            break
        try:
            unreal.EditorLoadingAndSavingUtils.save_packages(chunk, False)
            n += len(chunk)
        except Exception as e:
            out["chunk_err"] = str(e)
            try:
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            except Exception as e2:
                out["dirty_err"] = str(e2)
    try:
        LES.save_current_level()
    except Exception as e:
        out["lvl_err"] = str(e)
    try:
        LES.save_all_dirty_levels()
    except Exception:
        pass
    out.update({"packages": len(uniq), "saved_n": n, "saved": True, "ts": datetime.now(timezone.utc).isoformat()})
    print("SAVE " + json.dumps(out))
