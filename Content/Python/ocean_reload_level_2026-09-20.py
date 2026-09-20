import unreal, json
from pathlib import Path

MAP = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
notes = []

try:
    ok = les.load_level(MAP)
    notes.append(f"load_level={ok}")
except Exception as e:
    notes.append(f"load_level err={e}")
    try:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP)
        notes.append("load_map_ok")
    except Exception as e2:
        notes.append(f"load_map err={e2}")

hits = []
for a in svc.get_all_level_actors():
    L = a.get_actor_label() or ""
    C = a.get_class().get_name()
    if any(k in (L + C).lower() for k in ("ocean", "canopy", "infiniteocean", "oceanologywater", "oceanology")):
        t = a.get_actor_transform()
        hits.append({
            "label": L,
            "class": C,
            "loc": [t.translation.x, t.translation.y, t.translation.z],
            "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z],
        })

out = {"notes": notes, "hits": hits}
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/ocean_reload_level_2026-09-20.json").write_text(
    json.dumps(out, indent=2, default=str), encoding="utf-8"
)
print("OCEAN_LEVEL " + json.dumps(out, default=str))
