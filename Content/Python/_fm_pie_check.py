import unreal, json
out = {}
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_editor_world()
    out["editor_world"] = w.get_path_name() if w else None
except Exception as e:
    out["editor_world_err"] = str(e)
try:
    # PIE world
    pie = None
    for attr in ("get_game_world", "get_editor_world"):
        pass
    # World.is_in_play_in_editor on any world
    w = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
except Exception as e:
    out["ell_err"] = str(e)
# check play world
try:
    gw = unreal.GameplayStatics.get_game_instance(unreal.EditorLevelLibrary.get_editor_world()) if False else None
except Exception:
    pass
try:
    # UE5: EditorLevelLibrary.get_pie_world_context or similar
    methods = [m for m in dir(unreal) if "pie" in m.lower() or "Play" in m][:30]
    out["pie_ish"] = methods
except Exception as e:
    out["pie_dir_err"] = str(e)
# SystemLibrary get_frame_count etc
try:
    from unreal import EditorActorSubsystem
    eas = unreal.get_editor_subsystem(EditorActorSubsystem)
    out["actor_count_try"] = len(list(eas.get_all_level_actors())) if eas else None
except Exception as e:
    out["actor_err"] = str(e)
print("PIECHK " + json.dumps(out, default=str)[:4000])
