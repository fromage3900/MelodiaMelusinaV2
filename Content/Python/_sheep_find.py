# Read-only: locate the Choral Sheep actor(s), print transforms + bounds. Prints only.
import unreal

eas = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
try:
    gw = eas.get_game_world()
    print('SH gw:', gw.get_name() if gw else None)
except Exception as e:
    print('SH gw err', e)

actors = []
try:
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
except Exception as e:
    print('SH subsys err', e)
    try:
        actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    except Exception as e2:
        print('SH legacy err', e2)

hits = []
for a in actors:
    try:
        lbl = a.get_actor_label()
    except Exception:
        lbl = ''
    try:
        nm = a.get_name()
    except Exception:
        nm = ''
    cl = ''
    try:
        cl = a.get_class().get_name()
    except Exception:
        pass
    hay = (lbl + '|' + nm + '|' + cl).lower()
    if 'sheep' in hay or 'choral' in hay:
        hits.append(a)

print('SH hits:', len(hits))
for a in hits:
    print('SH actor:', a.get_actor_label(), '|', a.get_name(), '|', a.get_class().get_name())
    try:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print('  loc:', loc, '| rot:', rot)
    except Exception as e:
        print('  loc err', e)
    try:
        o, ext = a.get_actor_bounds(False, True)
        print('  bounds origin:', o, '| extent:', ext)
        print('  bounds bottom Z:', round(o.z - ext.z, 2), '| top Z:', round(o.z + ext.z, 2))
    except Exception as e:
        print('  bounds err', e)
    try:
        print('  folder:', a.get_folder_path())
    except Exception:
        pass
    try:
        print('  parent:', a.get_attach_parent_actor())
    except Exception:
        pass
print('SH done')