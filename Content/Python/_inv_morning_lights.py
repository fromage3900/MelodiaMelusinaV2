
import unreal, json
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = list(svc.get_all_level_actors())
lights = []
ppvs = []
for a in actors:
    cn = a.get_class().get_name()
    label = a.get_actor_label()
    if 'Light' in cn or 'Sky' in cn or 'Exponential' in cn or 'Directional' in cn:
        rec = {'label': label, 'class': cn}
        try:
            comps = a.get_components_by_class(unreal.LightComponent)
            for c in comps or []:
                try:
                    rec['intensity'] = float(c.get_editor_property('intensity'))
                except Exception: pass
                try:
                    rec['indirect'] = float(c.get_editor_property('indirect_lighting_intensity'))
                except Exception: pass
        except Exception: pass
        lights.append(rec)
    if 'PostProcess' in cn or 'PPV' in label:
        ppvs.append({'label': label, 'class': cn})
print('LIGHTS', json.dumps(lights, indent=2)[:2500])
print('PPV', json.dumps(ppvs, indent=2)[:1500])
