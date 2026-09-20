import unreal, json
from pathlib import Path
from datetime import datetime, timezone

GRAPH_PATH = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
out = {"graph_loaded": bool(graph), "steps": []}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = None
for a in svc.get_all_level_actors():
    if (a.get_actor_label() or "") == "WC_HouseRoomShell_SalonA":
        actor = a
        break
if not actor:
    out["error"] = "actor_missing"
    print("FORCE " + json.dumps(out))
else:
    comps = list(actor.get_components_by_class(unreal.PCGComponent) or [])
    out["steps"].append({"comps_found": len(comps)})
    for c in comps:
        try:
            if hasattr(c, "set_graph"):
                c.set_graph(graph)
                out["steps"].append({"set_graph": True})
            else:
                c.set_editor_property("graph", graph)
                out["steps"].append({"set_editor_property": True})
        except Exception as e:
            out["steps"].append({"assign_err": str(e)})
        try:
            c.set_editor_property(
                "generation_trigger",
                unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND,
            )
        except Exception as e:
            out["steps"].append({"trigger_err": str(e)})
        try:
            c.generate(True)
            out["steps"].append({"generate": True})
        except Exception as e:
            try:
                c.cleanup_local_generation()
                c.generate(True)
                out["steps"].append({"generate_after_cleanup": True})
            except Exception as e2:
                out["steps"].append({"generate_err": [str(e), str(e2)]})
        g = None
        try:
            g = c.get_editor_property("graph")
        except Exception:
            pass
        out["steps"].append({"graph_now": g.get_path_name() if g else None})
    # also re-assign on BP template
    bp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell")
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        library = unreal.SubobjectDataBlueprintFunctionLibrary
        for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
            data = library.get_data(handle)
            obj = library.get_object(data)
            if obj and isinstance(obj, unreal.PCGComponent):
                try:
                    obj.set_graph(graph)
                    out["steps"].append({"bp_template_set_graph": True})
                except Exception as e:
                    out["steps"].append({"bp_template_err": str(e)})
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell")
        out["steps"].append({"bp_resaved": True})
    except Exception as e:
        out["steps"].append({"bp_rewire_err": str(e)})
    # save level
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        out["steps"].append({"level_saved": True})
    except Exception as e:
        out["steps"].append({"level_save_err": str(e)})
    out["ok"] = True
    Path(unreal.Paths.project_saved_dir(), "Audit", "pcgex_roomshell_force_graph_2026-09-20.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), **out}, indent=2),
        encoding="utf-8",
    )
    print("FORCE " + json.dumps(out))
