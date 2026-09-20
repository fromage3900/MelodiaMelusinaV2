
import unreal, json
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
uds = None
for a in svc.get_all_level_actors():
    if a.get_actor_label() == 'Ultra_Dynamic_Sky2':
        uds = a
        break
if not uds:
    print('NO_UDS')
else:
    props = []
    for name in ('Time of Day','TimeOfDay','time_of_day','Day of Year','Cloud Coverage','Overall Intensity','Sun Softness','Moon Intensity','Night Brightness','Stars Intensity','Fog Density','Animate Time of Day'):
        try:
            v = uds.get_editor_property(name.replace(' ', '_').lower())
            props.append((name, str(v)[:80]))
        except Exception:
            pass
    # brute common
    for name in dir(uds):
        if any(k in name.lower() for k in ('time', 'day', 'sun', 'intensity', 'cloud', 'fog')) and not name.startswith('_'):
            props.append(('dir:'+name, 'attr'))
    print('UDS_CLASS', uds.get_class().get_name())
    # component props
    try:
        for c in uds.get_components_by_class(unreal.ActorComponent):
            cn = c.get_class().get_name()
            if 'Sky' in cn or 'Light' in cn or 'Ultra' in cn:
                print('COMP', cn)
    except Exception as e:
        print('COMPERR', e)
    # try export / get all editor props via reflection-ish
    found = {}
    candidates = [
        'time_of_day','TimeOfDay','timeofday','day_of_year','cloud_coverage',
        'overall_intensity','sun_light_intensity','moon_light_intensity',
        'night_brightness','animate_time_of_day','dawn_time','dusk_time'
    ]
    # Blueprint generated classes often use get_editor_property with exact names from BP
    for cand in ['Time of Day', 'TimeOfDay', 'Cloud Coverage', 'Overall Intensity', 'Sun Light Intensity', 'Animate Time of Day', 'Night Brightness', 'Moon Intensity', 'Fog Density', 'Volumetric Clouds']:
        try:
            found[cand] = str(uds.get_editor_property(cand))
        except Exception as e:
            found[cand] = 'err'
    print('FOUND', json.dumps(found, indent=2))
