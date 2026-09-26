"""Generate one Glassgarden PCG volume. Arg via env GG_PCG_LABEL or default first. No sleep."""
import unreal, json, os

LEVEL = "/Game/EnvSandbox/Monoliths/GlassgardenShoals/Prototype/LV_Glassgarden_Shoals"
LABEL = os.environ.get("GG_PCG_LABEL", "Glassgarden_PCG_PCG_SeaAbove_East_Scree")
out = {"label": LABEL}
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    w = ues.get_editor_world() if ues else None
except Exception:
    w = unreal.EditorLevelLibrary.get_editor_world()
cur = w.get_path_name().split(".")[0] if w else None
if cur != LEVEL:
    out["load"] = bool(les.load_level(LEVEL))
actors = {a.get_actor_label(): a for a in (eas.get_all_level_actors() or [])}
vol = actors.get(LABEL)
out["present"] = vol is not None
if not vol:
    print(json.dumps(out))
else:
    comp = vol.get_component_by_class(unreal.PCGComponent)
    out["has_comp"] = comp is not None
    notes = []
    if comp:
        try:
            trig = getattr(unreal.PCGComponentGenerationTrigger, "GENERATE_ON_DEMAND", None)
            if trig is not None:
                comp.set_editor_property("generation_trigger", trig)
        except Exception as e:
            notes.append("trigger=" + str(e)[:80])
        try:
            comp.cleanup_local(False)
            notes.append("cleanup_ok")
        except Exception as e:
            notes.append("cleanup=" + str(e)[:80])
        try:
            comp.generate_local(True)
            notes.append("generate_local_ok")
            out["generated"] = True
        except Exception as e:
            notes.append("generate_local=" + str(e)[:120])
            out["generated"] = False
            try:
                comp.generate(True)
                notes.append("generate_ok")
                out["generated"] = True
            except Exception as e2:
                notes.append("generate=" + str(e2)[:120])
    # instance counts on this volume
    inst = 0
    comps = 0
    if vol:
        for ccls in (unreal.InstancedStaticMeshComponent, unreal.HierarchicalInstancedStaticMeshComponent):
            for c in vol.get_components_by_class(ccls) or []:
                comps += 1
                try:
                    inst += int(c.get_instance_count())
                except Exception:
                    pass
    out["ism_comps"] = comps
    out["instances"] = inst
    out["notes"] = notes
    # level-wide quick count
    total_i = 0
    total_c = 0
    for a in (eas.get_all_level_actors() or []):
        for ccls in (unreal.InstancedStaticMeshComponent, unreal.HierarchicalInstancedStaticMeshComponent):
            for c in a.get_components_by_class(ccls) or []:
                total_c += 1
                try:
                    total_i += int(c.get_instance_count())
                except Exception:
                    pass
    out["level_ism_comps"] = total_c
    out["level_instances"] = total_i
    out["save_current"] = bool(unreal.EditorLevelLibrary.save_current_level())
    print(json.dumps(out, default=str))
