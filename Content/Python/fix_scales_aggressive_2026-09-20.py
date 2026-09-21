"""Aggressive scale cleanup: any StaticMeshActor / dress / BP with max scale >= 3 gets normalized."""
import unreal, json
from pathlib import Path
from datetime import datetime, timezone

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def cls(a):
    try: return a.get_class().get_name()
    except: return ''

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Leave these alone (intentional volume/deck scales)
LEAVE_PREFIX = (
    'WC_EscherWalk_', 'WC_Lookdev_', 'WC_HeroCorner_', 'WC_morning_rainbow',
    'WC_NS_Morning_', 'WC_MorningFlower', 'Ultra_Dynamic', 'PPV_', 'NavMesh',
    'BrushifyIsland_', 'Landscape', 'PCGWorld', 'WC_NavMesh',
)
LEAVE_CLASS = {
    'PCGVolume', 'PCGWorldActor', 'PostProcessVolume', 'NavMeshBoundsVolume',
    'WindDirectionalSource', 'ExponentialHeightFog', 'SkyAtmosphere', 'SkyLight',
    'DirectionalLight', 'WorldSettings', 'DefaultPhysicsVolume', 'OceanologyLake',
}

# Target uniform-ish scales by category
def target_for(lab, cn):
    if lab.startswith('WC_PortfolioDress_') or lab.startswith('WC_HeroCornerDress_'):
        return 1.0
    if 'Rock' in lab or 'Pebble' in lab or 'Boulder' in lab:
        return 1.2
    if 'Bush' in lab or 'Overgrowth' in lab or 'Shrub' in lab:
        return 0.95
    if lab.startswith('SM_Greybox_') or 'Greybox' in lab:
        return 1.0
    if lab.startswith('GB_Morning_'):
        return 1.0
    if 'Canyon' in lab or 'Ridge' in lab or 'Sandstone' in lab:
        return 2.5  # still large env, not 20x
    if lab.startswith('SM_wall') or 'Wall' in lab:
        return 1.0
    if 'Pillar' in lab or 'Plinth' in lab:
        return 1.0
    if 'Rug' in lab:
        return 1.5
    if lab.startswith('BP_'):
        return 1.0
    if 'Houdini' in lab:
        return 1.0
    return 1.0

fixed = []
hidden = []
report_all = []

for a in list(svc.get_all_level_actors()):
    lab = label(a)
    cn = cls(a)
    if cn in LEAVE_CLASS:
        continue
    # Allow HeroCornerDress but not HeroCorner cams/PCG
    if any(lab.startswith(p) for p in LEAVE_PREFIX):
        if not lab.startswith('WC_HeroCornerDress_'):
            continue
    try:
        s = a.get_actor_scale3d()
    except Exception:
        continue
    mx = max(abs(s.x), abs(s.y), abs(s.z))
    mn = min(abs(s.x), abs(s.y), abs(s.z))
    if mx < 3.0 and (mn == 0 or mx / max(mn, 1e-6) < 15):
        continue
    report_all.append({'label': lab, 'before': [s.x, s.y, s.z], 'max': mx})

    # 80-250 → /100
    if 80 <= mx <= 250:
        ns = unreal.Vector(s.x/100.0, s.y/100.0, s.z/100.0)
        action = 'div100'
    else:
        tgt = target_for(lab, cn)
        # scale uniformly toward target based on max axis
        factor = mx / tgt if mx > 0 else 1.0
        ns = unreal.Vector(s.x/factor, s.y/factor, s.z/factor)
        action = f'norm_to_{tgt}'

    # clamp components
    def clampv(v, lo=0.15, hi=3.5):
        av = abs(v)
        if av < lo: return lo if v >= 0 else -lo
        if av > hi: return hi if v >= 0 else -hi
        return v
    # canyon can be a bit bigger
    hi = 4.0 if ('Canyon' in lab or 'Ridge' in lab) else 3.0
    ns = unreal.Vector(clampv(ns.x, 0.2, hi), clampv(ns.y, 0.2, hi), clampv(ns.z, 0.15, hi))
    a.set_actor_scale3d(ns)
    after = a.get_actor_scale3d()
    fixed.append({'label': lab, 'action': action, 'before': [s.x,s.y,s.z], 'after': [after.x,after.y,after.z]})

    if lab.startswith(('SM_Greybox_', 'SM_PM3D_Sphere3D', 'Houdini_')) or 'Greybox' in lab:
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
        hidden.append(lab)

# Also scan ISM instance scales on HeroCorner PCG + morning field — clamp extreme instances
ism_fixed = 0
for a in svc.get_all_level_actors():
    lab = label(a)
    if not (lab.startswith('WC_HeroCorner_') or lab == 'WC_morning_rainbow_bloom_Field'):
        continue
    try:
        comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
    except Exception:
        comps = []
    for c in comps:
        try:
            n = int(c.get_instance_count())
        except Exception:
            continue
        for i in range(n):
            try:
                xf = c.get_instance_transform(i, True)
                sc = xf.scale3d
                mx = max(abs(sc.x), abs(sc.y), abs(sc.z))
                if mx < 4.0:
                    continue
                # normalize to ~1
                f = mx / 1.0
                new_xf = unreal.Transform()
                new_xf.translation = xf.translation
                new_xf.rotation = xf.rotation
                new_xf.scale3d = unreal.Vector(sc.x/f, sc.y/f, sc.z/f)
                # use rotator form
                try:
                    rot = xf.rotation.rotator() if hasattr(xf.rotation, 'rotator') else unreal.Rotator(0,0,0)
                except Exception:
                    rot = unreal.Rotator(0,0,0)
                nt = unreal.Transform(xf.translation, rot, unreal.Vector(max(0.4, abs(sc.x)/f), max(0.4, abs(sc.y)/f), max(0.4, abs(sc.z)/f)))
                c.update_instance_transform(i, nt, True, True, True)
                ism_fixed += 1
            except Exception:
                continue
        try:
            c.mark_render_state_dirty()
        except Exception:
            pass

# Remaining statics >= 3
remain = []
for a in svc.get_all_level_actors():
    if cls(a) not in ('StaticMeshActor',):
        # also BP
        if not cls(a).endswith('_C') and cls(a) != 'StaticMeshActor':
            continue
    lab = label(a)
    if any(lab.startswith(p) for p in LEAVE_PREFIX) and not lab.startswith('WC_HeroCornerDress_'):
        continue
    if cls(a) in LEAVE_CLASS:
        continue
    s = a.get_actor_scale3d()
    mx = max(abs(s.x), abs(s.y), abs(s.z))
    if mx >= 3.0:
        remain.append({'label': lab, 'scale': [s.x,s.y,s.z], 'max': mx})
remain.sort(key=lambda x: -x['max'])

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    saved = True
except Exception as e:
    saved = str(e)

out = Path(unreal.Paths.project_dir())/'Saved'/'Audit'/'scale_fix_aggressive_2026-09-20.json'
report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'fixed': fixed, 'ism_fixed': ism_fixed, 'hidden': hidden, 'remain': remain[:30], 'saved': saved}
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('SCALE2', json.dumps({'fixed_n': len(fixed), 'ism_fixed': ism_fixed, 'hidden_n': len(hidden), 'remain_n': len(remain), 'remain_top': remain[:12], 'fixed_sample': fixed[:12], 'saved': saved}, default=str))
