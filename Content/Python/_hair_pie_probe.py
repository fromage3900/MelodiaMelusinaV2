# Read-only PIE hair attach probe for Melusina. Prints only. No writes, no saves.
import math
import unreal

print('HR4 game_world:')
eas = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = None
try:
    gw = eas.get_game_world()
except Exception as e:
    print('ERR subsys', e)
print(gw.get_name() if gw else None)
if not gw:
    print('HR4 no PIE running')
    print('HR4 done')
else:
    try:
        chars = []
        try:
            for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Pawn):
                nm = a.get_name()
                cl = a.get_class().get_name()
                if 'Melusina' in cl or 'Melusina' in nm or 'Melusina' in (a.get_actor_label() if hasattr(a, 'get_actor_label') else ''):
                    chars.append(a)
        except Exception as e:
            print('ERR find pawns', e)
        if not chars:
            try:
                pc = unreal.GameplayStatics.get_player_controller(gw, 0)
                pp = pc.get_pawn() if pc else None
                if pp:
                    chars.append(pp)
            except Exception as e:
                print('ERR pc pawn', e)
        print('HR4 chars:', [(a.get_name(), a.get_class().get_name()) for a in chars])
        for p in chars[:3]:
            comps = []
            try:
                comps = list(p.get_components_by_class(unreal.SkeletalMeshComponent))
            except Exception as e:
                print('ERR sk comps', e)
            print('HR4 sk:', [c.get_name() for c in comps])
            try:
                allc = list(p.get_components_by_class(unreal.SceneComponent))
                print('HR4 comps:', [c.get_name() for c in allc][:48])
            except Exception as e:
                print('ERR scene comps', e)
            body = None
            for c in comps:
                n = c.get_name()
                if n in ('CharacterMesh0', 'MEL_body', 'MEL_body01') or 'Body' in n:
                    body = c if body is None else body
            hair = [c for c in comps if 'Hair' in c.get_name()]
            for c in comps + [x for x in p.get_components_by_class(unreal.SceneComponent) if 'Hat' in x.get_name()]:
                try:
                    rel = c.get_editor_property('relative_location')
                except Exception:
                    rel = 'n/a'
                try:
                    rot = c.get_editor_property('relative_rotation')
                except Exception:
                    rot = 'n/a'
                try:
                    par = c.get_attach_parent()
                    parn = par.get_name() if par else None
                except Exception:
                    parn = 'ERR'
                try:
                    sock = c.get_editor_property('attach_socket_name')
                except Exception:
                    sock = 'n/a'
                print('HR4 comp', c.get_name(), '| parent:', parn, '| socket:', sock, '| rel:', rel, '| rot:', rot)
            if body:
                for h in hair:
                    try:
                        hl = body.get_socket_location('head_x')
                        hw = h.get_world_location()
                        d = math.sqrt((hw.x - hl.x) ** 2 + (hw.y - hl.y) ** 2 + (hw.z - hl.z) ** 2)
                        print('HR4 dist', h.get_name(), 'head_x->', round(d, 2), 'cm')
                        print('HR4 headx_world', hl)
                        print('HR4 hair_world', hw)
                    except Exception as e:
                        print('HR4 dist ERR', h.get_name(), e)
            try:
                for c in comps:
                    if 'seg_' in c.get_name() or 'Ball_' in c.get_name() or 'Gear_' in c.get_name():
                        w = c.get_world_location()
                        print('HR4 dollpart', c.get_name(), 'world:', w)
            except Exception as e:
                print('ERR dollparts', e)
    except Exception as e:
        print('HR4 FATAL', e)
    print('HR4 done')