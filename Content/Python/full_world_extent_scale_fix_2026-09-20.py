"""Full-level world-extent scale audit + aggressive normalize.
Goal: props read human-scale; no multi-meter blowups from native mesh bounds.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

# World half-extent caps (cm)
CAP_PROP = 180.0          # rocks/bushes/dress/props ~ max ~3.6m tall/wide
CAP_FOLIAGE_ACCENT = 120.0
CAP_ENV_PIECE = 2500.0    # cliffs/islands can be large
CAP_ISM_INSTANCE = 200.0

SKIP_LABEL = (
    'UltraDynamic', 'UDS_', 'Sky', 'Fog', 'PostProcess', 'PPV_', 'Exponential',
    'DirectionalLight', 'SkyLight', 'PointLight', 'SpotLight', 'RectLight',
    'Camera', 'CineCamera', 'PlayerStart', 'NavMesh', 'NavModifier',
    'Landscape', 'WorldSettings', 'DefaultPhysicsVolume', 'Brush_',
    'WC_Lookdev_', 'WC_HeroCorner_', '_Cam', 'WindDirectional',
    'Niagara', 'NS_', 'Audio', 'AmbientSound', 'Trigger', 'BlockingVolume',
    'Lightmass', 'Reflection', 'SphereReflection', 'PlanarReflection',
    'PCGVolume', 'PCG_', # volumes themselves — shrink separately if needed
)

# Never auto-scale these labels (structural)
KEEP_LARGE = (
    'BrushifyIsland_', 'WC_EscherWalk_', 'Canyon', 'Cliff', 'Ocean', 'Water',
    'Terrain', 'GroundPlane',
)

def _label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def _cls(a):
    try: return a.get_class().get_name()
    except: return ''

def should_skip(lab, cls):
    if any(s in lab for s in SKIP_LABEL):
        return True
    if any(s in cls for s in ('Light', 'Camera', 'Volume', 'Sky', 'Fog', 'Landscape', 'Nav', 'Audio', 'Niagara', 'PCG')):
        # allow StaticMeshActor through
        if 'StaticMesh' in cls:
            return False
        return True
    return False

def mesh_local_half(mesh):
    try:
        box = mesh.get_bounding_box()
        hx = abs(box.max.x - box.min.x) * 0.5
        hy = abs(box.max.y - box.min.y) * 0.5
        hz = abs(box.max.z - box.min.z) * 0.5
        return max(hx, hy, hz), [hx, hy, hz]
    except Exception:
        return None, None

def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    fixed_actors = []
    destroyed = []
    ism_fixed = []
    audited_giants = []
    skipped_keep = []

    BAN_DESTROY = ('GhostLotus', 'Overgrowth')  # known multi-km assets — destroy if present as dress

    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        cls = _cls(a)
        if should_skip(lab, cls):
            continue

        # Destroy banned dress leftovers
        if any(b in lab for b in BAN_DESTROY) and (
            lab.startswith('WC_') or 'Dress' in lab or 'Portfolio' in lab
        ):
            if svc.destroy_actor(a):
                destroyed.append({'label': lab, 'reason': 'banned_mesh'})
            continue

        if 'StaticMesh' not in cls and 'StaticMeshActor' not in cls:
            # still check BP actors with SMC
            comps = []
            try:
                comps = list(a.get_components_by_class(unreal.StaticMeshComponent) or [])
            except Exception:
                pass
            if not comps:
                continue
        else:
            try:
                comps = list(a.get_components_by_class(unreal.StaticMeshComponent) or [])
            except Exception:
                comps = []

        # World bounds
        try:
            origin, extent = a.get_actor_bounds(False, False)
            wmax = float(max(extent.x, extent.y, extent.z))
        except Exception:
            continue

        if wmax < CAP_PROP:
            continue

        keep = any(k in lab for k in KEEP_LARGE)
        if keep:
            if wmax > 15000:  # even islands shouldn't be absurd from a prop mesh
                skipped_keep.append({'label': lab, 'extent': wmax, 'note': 'kept_structural'})
            continue

        # Cap for props
        cap = CAP_PROP
        if any(x in lab.lower() for x in ('bush', 'flower', 'shamrock', 'plant', 'foliage')):
            cap = CAP_FOLIAGE_ACCENT
        if any(x in lab for x in ('Rock', 'Mossy', 'Stone', 'Boulder')):
            cap = 220.0

        audited_giants.append({'label': lab, 'extent': wmax, 'class': cls})

        # Compute needed uniform scale-down from current scale
        s = a.get_actor_scale3d()
        cur = max(abs(s.x), abs(s.y), abs(s.z), 1e-6)
        # factor so world extent becomes ~cap
        factor = cap / wmax
        new_s = unreal.Vector(s.x * factor, s.y * factor, s.z * factor)
        # clamp absolute scale to sane range
        for axis in ('x', 'y', 'z'):
            v = getattr(new_s, axis)
            if abs(v) > 3.0:
                setattr(new_s, axis, 3.0 if v > 0 else -3.0)
            if abs(v) < 0.05 and abs(v) > 1e-8:
                setattr(new_s, axis, 0.05 if v > 0 else -0.05)

        # If after scale would still need factor < 0.02, destroy (unusable mesh)
        if factor < 0.02:
            if svc.destroy_actor(a):
                destroyed.append({'label': lab, 'reason': f'extent={wmax:.0f}_unfixable', 'extent': wmax})
            continue

        a.set_actor_scale3d(new_s)
        try:
            o2, e2 = a.get_actor_bounds(False, False)
            w2 = float(max(e2.x, e2.y, e2.z))
        except Exception:
            w2 = None
        fixed_actors.append({
            'label': lab,
            'extent_before': wmax,
            'extent_after': w2,
            'scale_before': [s.x, s.y, s.z],
            'scale_after': [new_s.x, new_s.y, new_s.z],
            'factor': factor,
        })

    # ISM instances inside PCG / foliage
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        try:
            comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
        except Exception:
            continue
        for c in comps:
            try:
                n = c.get_instance_count()
            except Exception:
                continue
            mesh = c.static_mesh
            local_half, _ = mesh_local_half(mesh) if mesh else (None, None)
            for i in range(n):
                try:
                    xf = c.get_instance_transform(i, True)  # world
                except Exception:
                    continue
                sc = xf.scale3d
                smx = max(abs(sc.x), abs(sc.y), abs(sc.z))
                # estimate world half from local * scale
                if local_half:
                    west = local_half * smx
                else:
                    west = smx * 100.0  # unknown
                if west <= CAP_ISM_INSTANCE and smx <= 4.0:
                    continue
                # target scale so west ~= CAP_ISM_INSTANCE
                if local_half and local_half > 1e-3:
                    target_s = CAP_ISM_INSTANCE / local_half
                else:
                    target_s = min(1.0, 4.0 / max(smx, 1e-6))
                target_s = max(0.15, min(target_s, 2.5))
                # preserve sign
                ns = unreal.Vector(
                    target_s if sc.x >= 0 else -target_s,
                    target_s if sc.y >= 0 else -target_s,
                    target_s if sc.z >= 0 else -target_s,
                )
                try:
                    new_xf = unreal.Transform(xf.translation, xf.rotation, ns)
                except Exception:
                    try:
                        new_xf = unreal.Transform(xf.translation, xf.rotator(), ns)
                    except Exception:
                        continue
                try:
                    c.update_instance_transform(i, new_xf, True, True, True)
                    ism_fixed.append({
                        'actor': lab,
                        'idx': i,
                        'mesh': mesh.get_path_name() if mesh else None,
                        'scale_before': [sc.x, sc.y, sc.z],
                        'scale_after': [ns.x, ns.y, ns.z],
                        'est_extent_before': west,
                    })
                except Exception:
                    pass
            try:
                c.mark_render_state_dirty()
            except Exception:
                pass

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # recount remaining giants
    still = []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        cls = _cls(a)
        if should_skip(lab, cls) or any(k in lab for k in KEEP_LARGE):
            continue
        if 'StaticMesh' not in cls:
            continue
        try:
            o, e = a.get_actor_bounds(False, False)
            w = float(max(e.x, e.y, e.z))
        except Exception:
            continue
        if w > CAP_PROP * 1.5:
            still.append({'label': lab, 'extent': w})
    still.sort(key=lambda x: -x['extent'])

    report = {
        'schema': 'melodia.full_world_extent_scale_fix.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'caps_cm': {'prop': CAP_PROP, 'foliage': CAP_FOLIAGE_ACCENT, 'ism': CAP_ISM_INSTANCE},
        'fixed_actors': fixed_actors,
        'fixed_actor_count': len(fixed_actors),
        'destroyed': destroyed,
        'ism_fixed_count': len(ism_fixed),
        'ism_fixed_sample': ism_fixed[:40],
        'still_oversized': still[:40],
        'skipped_keep_sample': skipped_keep[:20],
        'level_saved': saved,
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'full_world_extent_scale_fix_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print('SCALEFIX ' + json.dumps({
        'fixed_actors': len(fixed_actors),
        'destroyed': len(destroyed),
        'ism_fixed': len(ism_fixed),
        'still': len(still),
        'worst_fixed': sorted(fixed_actors, key=lambda r: -r['extent_before'])[:8],
        'still_top': still[:10],
        'saved': saved,
        'report': str(out),
    }, default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
