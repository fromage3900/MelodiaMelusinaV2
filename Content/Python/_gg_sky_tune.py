"""Sky tune only — serene tropical Glassgarden day. No sleep, no PCG generate."""
import unreal, json

LEVEL = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/LV_Glassgarden_Shoals"
UDS_TUNES = [
    ("Animate Time of Day", False),
    ("Time of Day", 1030.0),
    ("Cloud Coverage", 1.6),
    ("Sun Light Intensity", 3.8),
    ("Overall Intensity", 1.05),
]
UDW_TUNES = [
    ("Cloud Coverage", 1.6),
    ("Wind Intensity", 0.15),
]
out = {"steps": {}}
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_editor_world() if ues else None
except Exception:
    w = unreal.EditorLevelLibrary.get_editor_world()
cur = w.get_path_name().split(".")[0] if w else None
if cur != LEVEL:
    out["load"] = {"ok": bool(les.load_level(LEVEL)), "from": cur}
else:
    out["load"] = {"ok": True, "already": cur}

actors = {a.get_actor_label(): a for a in (eas.get_all_level_actors() or [])}
out["actor_count"] = len(actors)
out["labels"] = sorted(actors.keys())

def apply(actor, tunes):
    changed, failed = [], []
    for k, v in tunes:
        try:
            try:
                before = actor.get_editor_property(k)
            except Exception:
                before = None
            actor.set_editor_property(k, v)
            try:
                after = actor.get_editor_property(k)
            except Exception:
                after = v
            changed.append({"key": k, "from": before, "to": after})
        except Exception as e:
            failed.append({"key": k, "error": str(e)[:120]})
    return {"changed": changed, "failed": failed}

uds = actors.get("Glassgarden_UDS")
udw = actors.get("Glassgarden_UDW")
out["uds"] = {"present": uds is not None}
out["udw"] = {"present": udw is not None}
if uds:
    out["uds"].update(apply(uds, UDS_TUNES))
    probed = {}
    for k in ("Time of Day", "Cloud Coverage", "Sun Light Intensity", "Overall Intensity", "Animate Time of Day"):
        try:
            probed[k] = uds.get_editor_property(k)
        except Exception as e:
            probed[k] = "unreadable:" + str(e)[:60]
    out["uds"]["probed"] = probed
if udw:
    out["udw"].update(apply(udw, UDW_TUNES))

fog = actors.get("Glassgarden_ExponentialHeightFog")
if fog:
    try:
        comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            try:
                comp.set_editor_property("fog_density", 0.015)
            except Exception:
                pass
            out["fog"] = {"tuned": True, "fog_density": 0.015}
    except Exception as e:
        out["fog"] = {"error": str(e)[:120]}

# MeshPartition presence check
mps = [lbl for lbl, a in actors.items() if a.get_class().get_name() == "MeshPartition"]
out["meshpartition_labels"] = mps
out["has_sma"] = "Glassgarden_MeshTerrain_SMA" in actors
out["has_fog"] = "Glassgarden_ExponentialHeightFog" in actors
out["pcg_labels"] = [l for l in actors if l.startswith("Glassgarden_PCG_")]
out["save_current"] = bool(unreal.EditorLevelLibrary.save_current_level())
print(json.dumps(out, default=str))
