import unreal, json
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
wname = world.get_name() if world else None
# broader water/lake hunt + count actors
lake=[]; roads=[]; walks=[]; splines=0; total=0
for a in svc.get_all_level_actors():
    total += 1
    L = a.get_actor_label() or ''
    C = a.get_class().get_name()
    k = (L+' '+C).lower()
    if any(x in k for x in ('lake','ocean','water','sheep')):
        t=a.get_actor_transform()
        lake.append({'label':L,'class':C,'loc':[round(t.translation.x,1),round(t.translation.y,1),round(t.translation.z,1)]})
    if any(x in k for x in ('road','trail','street','highway')):
        roads.append({'label':L,'class':C})
    if 'escherwalk' in k or 'walk' in L.lower():
        if len(walks)<25: walks.append({'label':L,'class':C})
    try:
        if a.get_components_by_class(unreal.SplineComponent):
            splines += 1
    except: pass
print('WORLD', json.dumps({'world':wname,'total_actors':total,'spline_actors':splines,'lake_water':lake,'roads':roads[:30],'walks':walks}, default=str))
