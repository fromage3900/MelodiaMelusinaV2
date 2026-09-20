"""Emergency: remove oversized HeroCorner / MA dress that obscures the level."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def _cls(a):
    try: return a.get_class().get_name()
    except: return ''

PREFIXES = (
    'WC_MA_Dress_',
    'WC_HeroDress_',
    'WC_HeroCornerDress_',
)

def world_extent(actor):
    try:
        origin, extent = actor.get_actor_bounds(False, False)
        return float(max(extent.x, extent.y, extent.z)), [origin.x, origin.y, origin.z], [extent.x, extent.y, extent.z]
    except Exception:
        return None, None, None

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    destroyed = []
    oversized_kept = []
    scanned = []

    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if not lab:
            continue
        is_dress = any(lab.startswith(p) for p in PREFIXES)
        ext, origin, extent = world_extent(a)
        scale = a.get_actor_scale3d()
        mx = max(abs(scale.x), abs(scale.y), abs(scale.z))
        # Destroy ALL MA/Hero dress immediately (user says level ruined)
        if is_dress:
            mesh = None
            try:
                for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                    sm = c.static_mesh
                    if sm:
                        mesh = sm.get_path_name()
                        break
            except Exception:
                pass
            rec = {'label': lab, 'scale_max': mx, 'extent_max': ext, 'mesh': mesh, 'origin': origin}
            if svc.destroy_actor(a):
                destroyed.append(rec)
            continue
        # Also flag any other static mesh with insane world extent (>40m half) for report
        if ext and ext > 4000 and 'StaticMesh' in _cls(a):
            if not any(x in lab for x in ('PCG', 'Landscape', 'UDS', 'Sky', 'BrushifyIsland', 'Nav', 'Volume', 'PostProcess', 'UltraDynamic')):
                oversized_kept.append({'label': lab, 'class': _cls(a), 'extent_max': ext, 'scale_max': mx, 'origin': origin})

    # Also shrink HeroCorner PCG volumes if they ballooned
    shrunk = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith('WC_HeroCorner_') and lab.endswith('_PCG'):
            s = a.get_actor_scale3d()
            mx = max(abs(s.x), abs(s.y), abs(s.z))
            if mx > 3.5:
                ns = unreal.Vector(min(abs(s.x), 2.5), min(abs(s.y), 2.5), min(abs(s.z), 2.2))
                a.set_actor_scale3d(ns)
                shrunk.append({'label': lab, 'from': [s.x, s.y, s.z], 'to': [ns.x, ns.y, ns.z]})

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        'schema': 'melodia.emergency_clear_dress.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'destroyed_count': len(destroyed),
        'destroyed': destroyed,
        'other_oversized_static': oversized_kept[:40],
        'pcg_volumes_shrunk': shrunk,
        'level_saved': saved,
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'emergency_clear_dress_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('EMERGENCY_CLEAR ' + json.dumps({
        'destroyed': len(destroyed),
        'other_oversized': len(oversized_kept),
        'pcg_shrunk': len(shrunk),
        'saved': saved,
        'worst_destroyed': sorted(destroyed, key=lambda r: -(r.get('extent_max') or 0))[:8],
        'other_sample': oversized_kept[:8],
    }, default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
