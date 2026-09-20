"""Restore SeaAbove Oceanology InfiniteOcean actors only."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary

CANDIDATES = [
    '/Oceanology_Plugin/Blueprints/BP_OceanologyInfiniteOcean',
    '/Oceanology_Plugin/Blueprints/Oceanology/BP_OceanologyInfiniteOcean',
    '/Game/Oceanology/BP_OceanologyInfiniteOcean',
    '/Oceanology_Plugin/Core/BP_OceanologyInfiniteOcean',
]

# Known live labels from lookdev brief
TARGETS = [
    {'label': 'SeaAbove_InfiniteOcean_Canopy', 'loc': (0.0, 0.0, 0.0), 'scale': (1.0, 1.0, 1.0)},
    {'label': 'SeaAbove_InfiniteOcean_Canopy2', 'loc': (0.0, 0.0, -5000.0), 'scale': (1.0, 1.0, 1.0)},
]

def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def find_bp():
    for p in CANDIDATES:
        if EAL.does_asset_exist(p):
            return p, EAL.load_blueprint_class(p) if hasattr(EAL, 'load_blueprint_class') else None
    # scan plugin dir
    for root in ['/Oceanology_Plugin', '/Game']:
        try:
            if not EAL.does_directory_exist(root):
                continue
            for p in EAL.list_assets(root, True, False) or []:
                if 'infiniteocean' in p.lower() and (p.endswith('BP_OceanologyInfiniteOcean') or 'InfiniteOcean' in p):
                    return p, None
        except Exception:
            pass
    return None, None

def load_class(path):
    # Try multiple load strategies
    try:
        return unreal.EditorAssetLibrary.load_blueprint_class(path)
    except Exception:
        pass
    asset = EAL.load_asset(path)
    if asset is None:
        return None
    try:
        return unreal.load_class(None, path + '_C')
    except Exception:
        pass
    try:
        gen = asset.generated_class()
        return gen
    except Exception:
        pass
    # Soft object path
    try:
        return unreal.EditorAssetLibrary.load_blueprint_class(path)
    except Exception as e:
        return None

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = [_label(a) for a in svc.get_all_level_actors()]
    ocean_like = [L for L in existing if 'ocean' in L.lower() or 'Oceanology' in L]

    bp_path, _ = find_bp()
    # broader search for InfiniteOcean bp
    found_paths = []
    for root in ['/Oceanology_Plugin', '/Game/EnvSandbox', '/Game/Melodia']:
        try:
            if not EAL.does_directory_exist(root):
                continue
            for p in (EAL.list_assets(root, True, False) or []):
                pl = p.lower()
                if 'infiniteocean' in pl.replace(' ', ''):
                    found_paths.append(p)
                elif 'oceanology' in pl and 'ocean' in pl and 'bp_' in pl:
                    found_paths.append(p)
        except Exception as e:
            found_paths.append(f'ERR:{root}:{e}')

    cls = None
    used = None
    for p in ([bp_path] if bp_path else []) + found_paths:
        if not p or p.startswith('ERR'):
            continue
        c = load_class(p)
        if c:
            cls = c
            used = p
            break

    spawned = []
    notes = []
    if not cls:
        notes.append('could_not_load_InfiniteOcean_BP')
        # Try spawn by class name via unreal.load_object
        for trial in [
            '/Script/Oceanology.OceanologyInfiniteOcean',
            '/Oceanology_Plugin/Blueprints/BP_OceanologyInfiniteOcean.BP_OceanologyInfiniteOcean_C',
        ]:
            try:
                c = unreal.load_object(None, trial)
                if c:
                    cls = c if not hasattr(c, 'generated_class') else c
                    used = trial
                    break
            except Exception as e:
                notes.append(f'load_object {trial}: {e}')
        # Class lookup
        try:
            c = unreal.load_class(None, '/Script/Oceanology.OceanologyInfiniteOcean')
            if c:
                cls = c
                used = '/Script/Oceanology.OceanologyInfiniteOcean'
        except Exception as e:
            notes.append(f'load_class native: {e}')

    if cls:
        for t in TARGETS:
            if t['label'] in existing:
                # unhide / reset scale if present
                a = next(x for x in svc.get_all_level_actors() if _label(x) == t['label'])
                try:
                    a.set_is_temporarily_hidden_in_editor(False)
                    a.set_actor_hidden_in_game(False)
                except Exception:
                    pass
                spawned.append({'label': t['label'], 'action': 'unhid_existing'})
                continue
            loc = unreal.Vector(*t['loc'])
            try:
                actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, unreal.Rotator(0, 0, 0))
            except Exception as e:
                notes.append(f'spawn fail {t["label"]}: {e}')
                actor = None
            if actor:
                actor.set_actor_label(t['label'])
                actor.set_actor_scale3d(unreal.Vector(*t['scale']))
                try:
                    actor.set_folder_path('Water/Oceanology')
                except Exception:
                    pass
                spawned.append({'label': t['label'], 'action': 'spawned', 'loc': list(t['loc']), 'class': str(cls)})
            else:
                notes.append(f'no actor for {t["label"]}')
    else:
        notes.append('NO_CLASS')

    # Unhide manager
    for a in svc.get_all_level_actors():
        if 'Oceanology' in _label(a) or 'Oceanology' in a.get_class().get_name():
            try:
                a.set_is_temporarily_hidden_in_editor(False)
                a.set_actor_hidden_in_game(False)
            except Exception:
                pass

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # verify
    after = []
    for a in svc.get_all_level_actors():
        L = _label(a)
        C = a.get_class().get_name()
        if 'ocean' in L.lower() or 'Oceanology' in C or 'Oceanology' in L:
            t = a.get_actor_transform()
            after.append({'label': L, 'class': C, 'loc': [t.translation.x, t.translation.y, t.translation.z],
                          'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z]})

    report = {
        'schema': 'melodia.restore_ocean.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'bp_used': used,
        'found_paths': found_paths[:40],
        'before_ocean_like': ocean_like,
        'spawned': spawned,
        'notes': notes,
        'after': after,
        'level_saved': saved,
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'restore_ocean_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('RESTORE_OCEAN ' + json.dumps({
        'used': used,
        'spawned': spawned,
        'after_count': len(after),
        'after': after,
        'notes': notes[:10],
        'found': found_paths[:15],
        'saved': saved,
    }, default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
