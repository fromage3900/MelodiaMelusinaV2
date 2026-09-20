import unreal, json
from pathlib import Path

BP = '/Oceanology_Plugin/Design/Ocean/Blueprints/Ocean/BP_OceanologyInfiniteOcean'
EAL = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

notes = []
cls = None
try:
    cls = EAL.load_blueprint_class(BP)
    notes.append(f'load_blueprint_class={cls}')
except Exception as e:
    notes.append(f'load_blueprint_class err={e}')

if not cls:
    try:
        asset = EAL.load_asset(BP)
        notes.append(f'asset={asset}')
        if asset:
            cls = asset.generated_class()
            notes.append(f'generated_class={cls}')
    except Exception as e:
        notes.append(f'generated err={e}')

if not cls:
    for trial in [
        BP + '.' + 'BP_OceanologyInfiniteOcean_C',
        '/Oceanology_Plugin/Design/Ocean/Blueprints/Ocean/BP_OceanologyInfiniteOcean.BP_OceanologyInfiniteOcean_C',
        '/Script/Oceanology.OceanologyInfiniteOcean',
    ]:
        try:
            c = unreal.load_class(None, trial)
            notes.append(f'load_class {trial} -> {c}')
            if c:
                cls = c
                break
        except Exception as e:
            notes.append(f'load_class {trial} err={e}')

spawned = []
if cls:
    for label, z in [('SeaAbove_InfiniteOcean_Canopy', 0.0), ('SeaAbove_InfiniteOcean_Canopy2', -5000.0)]:
        # destroy duplicate labels first
        for a in list(svc.get_all_level_actors()):
            if (a.get_actor_label() or '') == label:
                svc.destroy_actor(a)
        try:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                cls, unreal.Vector(0.0, 0.0, z), unreal.Rotator(0, 0, 0))
        except Exception as e:
            notes.append(f'spawn exception {label}: {e}')
            actor = None
        if not actor:
            try:
                actor = svc.spawn_actor_from_class(cls, unreal.Vector(0.0, 0.0, z), unreal.Rotator(0, 0, 0))
            except Exception as e:
                notes.append(f'svc spawn {label}: {e}')
        if actor:
            actor.set_actor_label(label)
            try:
                actor.set_folder_path('Water/Oceanology')
            except Exception:
                pass
            spawned.append(label)
        else:
            notes.append(f'still none {label}')

# Also try Lake BP as fallback visibility? NO - user asked ocean only

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

after = []
for a in svc.get_all_level_actors():
    L = a.get_actor_label() or ''
    C = a.get_class().get_name()
    if 'ocean' in L.lower() or 'Oceanology' in C or 'Oceanology' in L or 'Infinite' in C:
        t = a.get_actor_transform()
        hid = False
        try:
            hid = bool(a.is_temporarily_hidden_in_editor())
        except Exception:
            pass
        after.append({'label': L, 'class': C, 'z': t.translation.z, 'hidden': hid})

out = {
    'cls': str(cls),
    'spawned': spawned,
    'notes': notes,
    'after': after,
}
Path(unreal.Paths.project_dir()).joinpath('Saved/Audit/restore_ocean_retry_2026-09-20.json').write_text(
    json.dumps(out, indent=2, default=str), encoding='utf-8')
print('OCEAN_RETRY', json.dumps(out, default=str))
