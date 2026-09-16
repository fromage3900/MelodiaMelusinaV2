import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_vol_freeze.json"
rep = {}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CANDS = ("b_generate_on_load", "generate_on_load", "bGenerateOnLoad")
for a in svc.get_all_level_actors():
    try:
        lbl = a.get_actor_label()
    except Exception:
        continue
    if lbl not in ("Morning_Dell_Banks", "Morning_Brook_Arpeggio",
                   "PCG_MelodiaOpening_Morning_Dressing"):
        continue
    comp = a.get_component_by_class(unreal.PCGComponent)
    if comp is None:
        rep[lbl] = "no_comp"
        continue
    hit = None
    for prop in CANDS:
        try:
            val = comp.get_editor_property(prop)
            comp.set_editor_property(prop, False)
            hit = {prop: str(val)}
            break
        except Exception:
            continue
    rep[lbl] = hit if hit else "prop_not_found"
open(OUT, "w").write(json.dumps(rep, indent=1))
print("VOLFREEZE_WROTE " + json.dumps(rep))
