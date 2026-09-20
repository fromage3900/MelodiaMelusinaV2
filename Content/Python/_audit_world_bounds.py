"""Find meshes whose world bounds are huge (asset size * scale), not just actor scale."""
import unreal, json, math
from pathlib import Path

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
huge = []
for a in svc.get_all_level_actors():
    if a.get_class().get_name() != 'StaticMeshActor':
        continue
    lab = label(a)
    if lab.startswith(('WC_EscherWalk_', 'BrushifyIsland_', 'WC_Lookdev_', 'WC_HeroCorner_')) and not lab.startswith('WC_HeroCornerDress_'):
        continue
    try:
        comps = a.get_components_by_class(unreal.StaticMeshComponent) or []
    except Exception:
        continue
    for c in comps:
        try:
            mesh = c.get_editor_property('static_mesh')
            if not mesh: continue
            # get bounds
            origin = unreal.Vector(0,0,0); extent = unreal.Vector(0,0,0)
            # use get_local_bounds or get_bounds
            try:
                box = mesh.get_bounding_box()
                mn = box.min; mx = box.max
                ex = unreal.Vector((mx.x-mn.x)*0.5, (mx.y-mn.y)*0.5, (mx.z-mn.z)*0.5)
            except Exception:
                continue
            s = a.get_actor_scale3d()
            # world half-extent approx
            wx = abs(ex.x * s.x); wy = abs(ex.y * s.y); wz = abs(ex.z * s.z)
            world_max = max(wx, wy, wz)
            # flag if larger than ~8m half-extent (800cm) for props, or 25m for env
            thresh = 2500.0 if ('Canyon' in lab or 'Island' in lab or 'Cliff' in lab) else 800.0
            if world_max >= thresh:
                huge.append({
                    'label': lab,
                    'mesh': mesh.get_name(),
                    'scale': [s.x,s.y,s.z],
                    'local_ext_cm': [ex.x, ex.y, ex.z],
                    'world_half_m': [wx/100, wy/100, wz/100],
                    'world_max_m': world_max/100,
                })
        except Exception:
            continue
huge.sort(key=lambda x: -x['world_max_m'])
print('BOUNDS', json.dumps({'n': len(huge), 'top': huge[:40]}, default=str)[:12000])
