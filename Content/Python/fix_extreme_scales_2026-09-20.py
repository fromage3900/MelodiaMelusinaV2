"""Fix extreme mesh scales on L_MelusinaMorning.

Policy:
- scale ~100 (80–200 uniform-ish) → divide by 100 (cm/m import blowup)
- scale > 8 on StaticMeshActor / dress / greybox / GB_Morning / visible props → clamp to sane
- beauty-hide greybox / houdini that stay huge
- leave EscherWalk thin decks alone (intentionally small XY)
- leave PCGVolume / NavMesh / UDS / cameras alone
"""
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

LEAVE_PREFIX = (
    'WC_EscherWalk_', 'WC_Lookdev_', 'WC_HeroCorner_', 'WC_morning_rainbow',
    'WC_NS_Morning_', 'WC_MorningFlower', 'Ultra_Dynamic', 'PPV_', 'NavMesh',
    'BrushifyIsland_', 'Landscape', 'PCGWorld',
)
LEAVE_CLASS = {
    'PCGVolume', 'PCGWorldActor', 'PostProcessVolume', 'NavMeshBoundsVolume',
    'WindDirectionalSource', 'ExponentialHeightFog', 'SkyAtmosphere', 'SkyLight',
    'DirectionalLight', 'WorldSettings', 'DefaultPhysicsVolume',
}

fixed = []
hidden = []
skipped = []

for a in list(svc.get_all_level_actors()):
    lab = label(a)
    cn = cls(a)
    if cn in LEAVE_CLASS:
        continue
    if any(lab.startswith(p) for p in LEAVE_PREFIX) and not lab.startswith('WC_PortfolioDress_'):
        continue
    try:
        s = a.get_actor_scale3d()
    except Exception:
        continue
    mx = max(abs(s.x), abs(s.y), abs(s.z))
    mn = min(abs(s.x), abs(s.y), abs(s.z))
    if mx < 5.0:
        continue

    action = None
    new_s = None

    # Classic 100x import blowup
    if 80.0 <= mx <= 220.0 and mn >= 40.0:
        new_s = unreal.Vector(s.x / 100.0, s.y / 100.0, s.z / 100.0)
        action = 'div100'
    # Mid blowups 15–80
    elif 15.0 <= mx < 80.0:
        # canyon ridges at ~20 may be intentional — only fix props/greybox/GB/dress/BP
        if (lab.startswith(('SM_Greybox_', 'GB_Morning_', 'WC_PortfolioDress_', 'SM_wall', 'BP_'))
                or 'Greybox' in lab or 'Pillar' in lab or 'Plinth' in lab or 'Rug' in lab
                or 'Spawner' in lab or 'Starskiff' in lab):
            factor = 10.0 if mx >= 30 else (mx / 2.5)
            new_s = unreal.Vector(s.x / factor, s.y / factor, s.z / factor)
            # clamp result
            def clamp_comp(v):
                av = abs(v)
                if av < 0.2: return 0.2 if v >= 0 else -0.2
                if av > 3.0: return 3.0 if v >= 0 else -3.0
                return v
            new_s = unreal.Vector(clamp_comp(new_s.x), clamp_comp(new_s.y), clamp_comp(new_s.z))
            action = f'div_mid:{factor:.1f}'
        else:
            skipped.append({'label': lab, 'scale': [s.x, s.y, s.z], 'reason': 'possible intentional large env'})
            continue
    # 5–15: clamp PortfolioDress / bushes / rocks only
    elif 5.0 <= mx < 15.0:
        if lab.startswith('WC_PortfolioDress_') or 'Bush' in lab or 'Rock' in lab or 'Overgrowth' in lab:
            sc = min(1.4, max(0.6, 2.5 / mx * ((abs(s.x)+abs(s.y)+abs(s.z))/3)))
            # simpler: set uniform 1.0
            new_s = unreal.Vector(1.0, 1.0, 1.0)
            action = 'dress_norm_1'
        else:
            skipped.append({'label': lab, 'scale': [s.x, s.y, s.z], 'reason': 'mild large env'})
            continue
    else:
        continue

    if new_s is not None:
        before = [s.x, s.y, s.z]
        a.set_actor_scale3d(new_s)
        after = a.get_actor_scale3d()
        fixed.append({'label': lab, 'class': cn, 'action': action, 'before': before, 'after': [after.x, after.y, after.z]})

    # Beauty hide remaining greybox / houdini / sphere after fix
    if lab.startswith(('SM_Greybox_', 'SM_PM3D_Sphere3D', 'Houdini_')) or 'Greybox' in lab:
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
        hidden.append(lab)

# Also hide BP_Starskiff if still huge after fix, and PhysicsPlacementSpawner
for a in svc.get_all_level_actors():
    lab = label(a)
    if lab in ('BP_PhysicsPlacementSpawner',) or lab.startswith('BP_Starskiff'):
        try:
            s = a.get_actor_scale3d()
            if max(abs(s.x), abs(s.y), abs(s.z)) > 5:
                a.set_is_temporarily_hidden_in_editor(True)
                a.set_actor_hidden_in_game(True)
                hidden.append(lab + ':still_large_hidden')
        except Exception:
            pass

# Re-audit remaining extremes on StaticMeshActor
remain = []
for a in svc.get_all_level_actors():
    if cls(a) != 'StaticMeshActor':
        continue
    lab = label(a)
    if any(lab.startswith(p) for p in LEAVE_PREFIX):
        continue
    s = a.get_actor_scale3d()
    mx = max(abs(s.x), abs(s.y), abs(s.z))
    if mx >= 8.0:
        remain.append({'label': lab, 'scale': [s.x, s.y, s.z], 'max': mx})
remain.sort(key=lambda x: -x['max'])

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    saved = True
except Exception as e:
    saved = str(e)

report = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'fixed_n': len(fixed),
    'fixed': fixed,
    'hidden': hidden,
    'skipped_sample': skipped[:20],
    'remaining_static_ge8': remain[:25],
    'level_saved': saved,
}
out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'scale_fix_2026-09-20.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('SCALE_FIX', json.dumps({
    'fixed_n': len(fixed),
    'hidden_n': len(hidden),
    'remain_n': len(remain),
    'fixed_sample': fixed[:15],
    'remain_top': remain[:10],
    'saved': saved,
    'report': str(out),
}, default=str))
