# Read-only probe v4: live PIE hair attach check for Melusina. Prints only.
import math
import unreal

eas = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = eas.get_game_world()
print('HR4 game_world:', gw.get_name() if gw else None)
if gw:
    als = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
    ml = [a for a in als if 'MelusinaJRPG' in a.get_class().get_name()]
    print('HR4 chars:', [(a.get_name(), a.get_actor_label()) for a in ml])
    for p in ml:
        comps = p.get_components_by_class(unreal.SceneComponent)
        print('HR4 all comps:', [c.get_name() for c in comps])
        sk = [c for c in comps if isinstance(c, unreal.SkeletalMeshComponent)]
        body = next((c for c in sk if c.get_name() == 'CharacterMesh0'), None)
        hair = next((c for c in sk if c.get_name() == 'WaterHairMesh'), None)
        print('HR4 body found:', bool(body), '| hair found:', bool(hair))
        if hair:
            try:
                print('HR4 hair rel_loc', hair.get_editor_property('relative_location'))
                print('HR4 hair rel_rot', hair.get_editor_property('relative_rotation'))
            except Exception as e:
                print('HR4 hair rel ERR', e)
            try:
                par = hair.get_attach_parent()
                print('HR4 hair parent:', par.get_name() if par else None)
            except Exception as e:
                print('HR4 hair parent ERR', e)
        if body and hair:
            try:
                hl = body.get_socket_location('head_x')
                hw = hair.get_world_location()
                d = math.sqrt((hw.x - hl.x) ** 2 + (hw.y - hl.y) ** 2 + (hw.z - hl.z) ** 2)
                print('HR4 head_x world', hl)
                print('HR4 hair world', hw)
                print('HR4 hair-to-headx dist cm', round(d, 2))
            except Exception as e:
                print('HR4 dist ERR', e)
        for nm in ('Regalia_Wings', 'Wings', 'RegaliaRoot', 'EyeIrises', 'Hat', 'SunHat'):
            c = next((x for x in comps if x.get_name() == nm), None)
            if c:
                try:
                    print('HR4 comp', nm, 'rel', c.get_editor_property('relative_location'),
                          'parent', c.get_attach_parent().get_name() if c.get_attach_parent() else None)
                except Exception as e:
                    print('HR4 comp', nm, 'ERR', e)
else:
    print('HR4 no PIE running')
print('HR4 done')