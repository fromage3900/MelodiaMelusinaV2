"""Emergency clear leftovers + NO GhostLotus/Overgrowth re-spawn."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

BAN_SUBSTR = ('GhostLotus', 'Overgrowth')
KILL_PREFIX = ('WC_MA_Dress_', 'WC_HeroDress_', 'WC_HeroCornerDress_')

def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    destroyed = []
    remaining_dress = []
    remaining_giants = []

    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        kill = False
        reason = ''
        if any(lab.startswith(p) for p in KILL_PREFIX):
            kill, reason = True, 'dress'
        elif lab.startswith('WC_PortfolioDress_') and any(b in lab for b in BAN_SUBSTR):
            kill, reason = True, 'portfolio_banned_mesh'
        elif 'StaticMesh' in a.get_class().get_name():
            try:
                o, e = a.get_actor_bounds(False, False)
                mx = float(max(e.x, e.y, e.z))
                safe = any(x in lab for x in (
                    'BrushifyIsland', 'Landscape', 'PCG', 'Sky', 'UDS', 'Nav', 'Volume',
                    'EscherWalk', 'Wall', 'Canyon', 'Cliff', 'Ground', 'UltraDynamic',
                    'PostProcess', 'Fog', 'Water', 'Ocean'))
                if mx > 3000 and not safe:
                    kill, reason = True, f'extent={mx:.0f}'
            except Exception:
                pass
        if kill:
            if svc.destroy_actor(a):
                destroyed.append({'label': lab, 'reason': reason})

    # verify
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if any(lab.startswith(p) for p in KILL_PREFIX):
            remaining_dress.append(lab)
        if 'StaticMesh' in a.get_class().get_name():
            try:
                o, e = a.get_actor_bounds(False, False)
                mx = float(max(e.x, e.y, e.z))
                if mx > 3000 and not any(x in lab for x in ('BrushifyIsland', 'Landscape', 'PCG', 'Sky', 'UDS', 'EscherWalk', 'Canyon', 'Cliff', 'UltraDynamic', 'Volume', 'Nav', 'Water')):
                    remaining_giants.append({'label': lab, 'extent': mx})
            except Exception:
                pass

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as ex:
        saved = str(ex)

    report = {
        'schema': 'melodia.emergency_clear_dress_finish.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'destroyed_this_pass': destroyed,
        'destroyed_count': len(destroyed),
        'remaining_dress': remaining_dress,
        'remaining_giants': remaining_giants[:30],
        'level_saved': saved,
        'policy': 'NO GhostLotus / Overgrowth until world-extent gate; rocks/bush/shamrock only',
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'emergency_clear_dress_finish_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('CLEAR_FINISH ' + json.dumps({
        'destroyed': len(destroyed),
        'remaining_dress': remaining_dress,
        'remaining_giants': remaining_giants[:10],
        'saved': saved,
    }, default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
