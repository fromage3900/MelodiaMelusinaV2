import unreal, json
from pathlib import Path
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in svc.get_all_level_actors():
    L = a.get_actor_label() or ""
    C = a.get_class().get_name()
    if any(k in (L+C).lower() for k in ("ocean", "lake", "water")):
        try:
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
        except Exception:
            pass
        t = a.get_actor_transform()
        try:
            o, e = a.get_actor_bounds(False, False)
            ext = float(max(e.x, e.y, e.z))
        except Exception:
            ext = None
        out.append({"label": L, "class": C, "loc": [t.translation.x, t.translation.y, t.translation.z], "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z], "extent": ext})
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
Path(unreal.Paths.project_dir()).joinpath("Saved/Audit/ocean_verify_2026-09-20.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("VERIFY", json.dumps(out, default=str))
