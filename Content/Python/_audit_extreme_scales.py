"""Audit extreme actor/ISM scales on L_MelusinaMorning and clamp offenders."""
import unreal, json, math
from pathlib import Path
from datetime import datetime, timezone

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def cls(a):
    try: return a.get_class().get_name()
    except: return ''

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Collect extreme scales
EXTREME_LO = 0.05
EXTREME_HI = 8.0  # report above this
CLAMP_LO = 0.35
CLAMP_HI = 2.5
# PCG volumes use large scale intentionally (box size) — don't clamp those the same way
SKIP_CLASSES = {'PCGVolume', 'PCGWorldActor', 'Brush', 'WorldSettings', 'UltraDynamicSky', 'PostProcessVolume', 'ExponentialHeightFog', 'SkyAtmosphere', 'SkyLight', 'DirectionalLight', 'WindDirectionalSource'}
SKIP_PREFIX = ('Ultra_Dynamic', 'PPV_', 'WC_Lookdev_', 'WC_HeroCorner_', 'NavMesh', 'Landscape')

actors_bad = []
ism_bad = []
for a in svc.get_all_level_actors():
    lab = label(a)
    cn = cls(a)
    if cn in SKIP_CLASSES:
        continue
    if any(lab.startswith(p) for p in SKIP_PREFIX):
        # still check PortfolioDress and HeroCorner dress if any; skip cams/volumes
        if not lab.startswith('WC_PortfolioDress_'):
            # allow checking non-cam hero stuff later
            if 'Cam' in lab or lab.endswith('_PCG') or lab.endswith('_Field'):
                continue
    try:
        s = a.get_actor_scale3d()
        mx = max(abs(s.x), abs(s.y), abs(s.z))
        mn = min(abs(s.x), abs(s.y), abs(s.z))
        if mx >= EXTREME_HI or (mn > 0 and mn <= EXTREME_LO) or mx / max(mn, 1e-6) > 20:
            actors_bad.append({
                'label': lab, 'class': cn,
                'scale': [s.x, s.y, s.z],
                'max': mx, 'min': mn,
            })
    except Exception:
        pass
    # ISM instance scales
    try:
        comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
        comps += list(a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or [])
    except Exception:
        comps = []
    for c in comps:
        try:
            n = int(c.get_instance_count())
        except Exception:
            continue
        mesh = None
        try:
            mesh = c.get_editor_property('static_mesh')
            mesh = mesh.get_name() if mesh else None
        except Exception:
            mesh = None
        step = 1 if n <= 3000 else max(1, n // 2000)
        for i in range(0, n, step):
            try:
                xf = c.get_instance_transform(i, True)
                sc = xf.scale3d
                mx = max(abs(sc.x), abs(sc.y), abs(sc.z))
                mn = min(abs(sc.x), abs(sc.y), abs(sc.z))
                if mx >= EXTREME_HI or (mn > 0 and mn <= EXTREME_LO) or mx / max(mn, 1e-6) > 25:
                    ism_bad.append({
                        'actor': lab, 'mesh': mesh, 'idx': i,
                        'scale': [sc.x, sc.y, sc.z], 'max': mx,
                    })
            except Exception:
                break

# Sort worst first
actors_bad.sort(key=lambda x: -x['max'])
ism_bad.sort(key=lambda x: -x['max'])

print('SCALE_AUDIT', json.dumps({
    'actor_extreme_n': len(actors_bad),
    'actor_top': actors_bad[:40],
    'ism_extreme_n': len(ism_bad),
    'ism_top': ism_bad[:40],
}, default=str)[:12000])
