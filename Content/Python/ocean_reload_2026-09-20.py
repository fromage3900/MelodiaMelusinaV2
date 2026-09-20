import unreal, json
from pathlib import Path

# Force reload current level / load all world partition cells around origin
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

notes = []
# Try WorldPartitionEditorSubsystem load
try:
    wpes = unreal.get_editor_subsystem(unreal.WorldPartitionEditorLoaderAdapter)
    notes.append(f'loader_adapter={wpes}')
except Exception as e:
    notes.append(f'no loader adapter: {e}')

try:
    wp = unreal.get_editor_subsystem(unreal.WorldPartitionSubsystem)
    notes.append(f'wp_sub={wp}')
except Exception as e:
    notes.append(f'no wp sub: {e}')

# EditorLoadingAndSavingUtils reload
try:
    # Reload package for restored actor
    pkg = '/Game/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning/C/Q3/LOL1EBLT0AWLXO87NRDQY0'
    ok = unreal.EditorLoadingAndSavingUtils.reload_packages([pkg], False)
    notes.append(f'reload_pkg={ok}')
except Exception as e:
    notes.append(f'reload err={e}')

# Load map fresh keeping dirty? Better: load external actors via EditorAssetLibrary
try:
    path = '/Game/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning/C/Q3/LOL1EBLT0AWLXO87NRDQY0'
    loaded = unreal.EditorAssetLibrary.load_asset(path)
    notes.append(f'load_asset={loaded}')
except Exception as e:
    notes.append(f'load_asset err={e}')

# Rescan actors
hits = []
for a in svc.get_all_level_actors():
    L = a.get_actor_label() or ''
    C = a.get_class().get_name()
    if any(k in (L+C).lower() for k in ('ocean', 'water', 'canopy', 'infinite')):
        t = a.get_actor_transform()
        hid = False
        try: hid = bool(a.is_temporarily_hidden_in_editor())
        except: pass
        hits.append({'label': L, 'class': C, 'loc': [t.translation.x, t.translation.y, t.translation.z], 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z], 'hidden': hid})

# Try editor undo? skip
out = {'notes': notes, 'hits': hits, 'hit_count': len(hits)}
Path(unreal.Paths.project_dir()).joinpath('Saved/Audit/ocean_reload_2026-09-20.json').write_text(json.dumps(out, indent=2, default=str), encoding='utf-8')
print('OCEAN_RELOAD', json.dumps(out, default=str)[:8000])
