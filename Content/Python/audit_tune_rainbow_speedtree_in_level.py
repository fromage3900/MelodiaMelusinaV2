
"""Audit + stabilize MI_RainbowSpeedTree_* used by WC_morning_rainbow_bloom_Field.

Methodical:
1) Find PCG/ISM components in level using RainbowSpeedTree mats; count instances.
2) Audit each band MI parent, motion scalars, switches, MelodiaWind*, Nikki-like, textures.
3) Apply a shared stable SpeedTree motion preset (modest, identical across bands).
4) Keep band tints; disable wind branches the flower kit lacks if switches exist.
5) Write receipts under Saved/Audit.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

RAINBOW_MIS = [
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B1_Orange',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B2_Gold',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B3_Green',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B4_Blue',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B5_Indigo',
    '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B6_Violet',
]
PETAL_WIND_MIS = [
    f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_B{i}_{n}'
    for i, n in enumerate(['Red','Orange','Gold','Green','Blue','Indigo','Violet'])
]

# Stable meadow preset for flower cards (SpeedTree scalars).
# Goal: gentle shared sway, low independence, no extreme stretch/oscillation.
STABLE = {
    'SharedBend': 0.35,
    'SharedOscillation': 0.15,
    'SharedSpeed': 0.08,
    'SharedTurbulence': 0.05,
    'SharedFlexibility': 0.35,
    'SharedIndependence': 0.05,
    'SharedStartHeight': 0.05,
    'Branch1Bend': 0.25,
    'Branch1Oscillation': 0.12,
    'Branch1Speed': 0.10,
    'Branch1Turbulence': 0.04,
    'Branch1Flexibility': 0.40,
    'Branch1Independence': 0.05,
    'Branch1StretchLimit': 0.15,
    'RipplePlanar': 0.08,
    'RippleDirectional': 0.05,
    'RippleSpeed': 0.12,
    'RippleFlexibility': 0.25,
    'RippleIndependence': 0.05,
    'RippleShimmer': 0.02,
}
# Switches: enable shared+branch1 ripple lightly; disable branch2 if flower kit lacks data
SWITCHES = {
    'SharedEnable': True,
    'Branch1Enable': True,
    'RippleEnable': True,
    'RippleShimmerEnable': False,
    'Branch2Enable': False,
}

NIKKI_HINTS = ('Dream', 'Pastel', 'Nikki', 'FlowerShadow', 'MossConcavity', 'ShadowDream')


def _parent(mi):
    try:
        p = mi.get_editor_property('parent')
        return p.get_path_name() if p else ''
    except Exception:
        return ''


def _scalars(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('scalar_parameter_values') or []):
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = float(
                e.get_editor_property('parameter_value'))
    except Exception as ex:
        out['_error'] = str(ex)
    return out


def _vectors(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('vector_parameter_values') or []):
            v = e.get_editor_property('parameter_value')
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = [float(v.r), float(v.g), float(v.b), float(v.a)]
    except Exception as ex:
        out['_error'] = str(ex)
    return out


def _textures(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('texture_parameter_values') or []):
            name = str(e.get_editor_property('parameter_info').get_editor_property('name'))
            tex = e.get_editor_property('parameter_value')
            out[name] = tex.get_path_name() if tex else None
    except Exception as ex:
        out['_error'] = str(ex)
    return out


def _switches(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('static_switch_parameter_values') or []):
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = bool(
                e.get_editor_property('value') if hasattr(e, 'value') else e.get_editor_property('parameter_value'))
    except Exception:
        # fallback via library
        try:
            for n in MEL.get_static_switch_parameter_names(mi):
                # no direct getter; skip
                out[str(n)] = 'present'
        except Exception as ex:
            out['_error'] = str(ex)
    return out


def _nikki_like(scalars):
    return {k: v for k, v in scalars.items() if any(h.lower() in k.lower() for h in NIKKI_HINTS)}


def _melodia(scalars):
    return {k: v for k, v in scalars.items() if k.startswith('Melodia')}


def audit_mi(path):
    if not EAL.does_asset_exist(path):
        return {'path': path, 'ok': False, 'error': 'missing'}
    mi = EAL.load_asset(path)
    sc = _scalars(mi)
    return {
        'path': path,
        'ok': True,
        'parent': _parent(mi),
        'scalars': sc,
        'vectors': _vectors(mi),
        'textures': _textures(mi),
        'switches': _switches(mi),
        'motion': {k: v for k, v in sc.items() if any(x in k.lower() for x in (
            'shared', 'branch', 'ripple', 'wind', 'gust', 'stretch', 'oscill', 'turb', 'flex', 'indep')) and not k.startswith('Melodia')},
        'melodia': _melodia(sc),
        'nikki_like': _nikki_like(sc),
        'extremes': {k: v for k, v in sc.items() if isinstance(v, float) and abs(v) > 2.0 and any(
            x in k.lower() for x in ('shared', 'branch', 'ripple', 'stretch', 'oscill'))},
    }


def inventory_level():
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = list(subsystem.get_all_level_actors())
    except Exception:
        actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name()
    except Exception:
        world = None

    field = None
    ism = []
    for a in actors:
        try:
            label = a.get_actor_label()
        except Exception:
            label = ''
        if label == 'WC_morning_rainbow_bloom_Field':
            field = {'label': label, 'class': a.get_class().get_name(), 'path': a.get_path_name()}
        # any HISM/ISM with rainbow mats
        try:
            comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
        except Exception:
            comps = []
        try:
            comps += list(a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or [])
        except Exception:
            pass
        for c in comps:
            mats = []
            try:
                for i in range(c.get_num_materials()):
                    m = c.get_material(i)
                    if m:
                        mats.append(m.get_path_name())
            except Exception:
                pass
            if not any('RainbowSpeedTree' in m or 'RainbowPetal' in m for m in mats):
                continue
            mesh = None
            try:
                mesh = c.get_editor_property('static_mesh')
            except Exception:
                mesh = getattr(c, 'static_mesh', None)
            count = None
            try:
                count = int(c.get_instance_count())
            except Exception:
                count = None
            ism.append({
                'actor': label,
                'actor_class': a.get_class().get_name(),
                'comp': c.get_class().get_name(),
                'mesh': mesh.get_path_name() if mesh else None,
                'materials': mats,
                'instances': count,
            })
    return {'world': world, 'field': field, 'ism_components': ism,
            'ism_total_instances': sum((x.get('instances') or 0) for x in ism)}


def apply_stable(path, also_clear_extremes=True):
    mi = EAL.load_asset(path)
    if not mi:
        return {'path': path, 'ok': False}
    before = _scalars(mi)
    applied = {}
    for k, v in STABLE.items():
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
            applied[k] = float(v)
        except Exception as ex:
            applied[k] = f'err:{ex}'
    switch_applied = {}
    for k, v in SWITCHES.items():
        try:
            MEL.set_material_instance_static_switch_parameter_value(mi, k, bool(v))
            switch_applied[k] = bool(v)
        except Exception as ex:
            switch_applied[k] = f'err:{ex}'
    # Ensure Melodia wind response modest and shared if present on parent
    for k, v in {
        'MelodiaWindResponse': 0.45,
        'MelodiaWindSpatialScale': 0.04,
        'MelodiaWindTravelSpeed': 1.0,
        'MelodiaWindHueSeed': 0.0,
    }.items():
        # only set if parameter exists on parent (setting unknown may still create override)
        try:
            names = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
            if k in names:
                MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
                applied[k] = float(v)
        except Exception:
            pass
    MEL.update_material_instance(mi)
    EAL.save_asset(path)
    after = _scalars(mi)
    return {
        'path': path,
        'ok': True,
        'parent': _parent(mi),
        'applied_scalars': applied,
        'applied_switches': switch_applied,
        'before_motion_subset': {k: before.get(k) for k in STABLE},
        'after_motion_subset': {k: after.get(k) for k in STABLE},
        'after_extremes': {k: v for k, v in after.items() if isinstance(v, float) and abs(v) > 2.0 and any(
            x in k.lower() for x in ('shared', 'branch', 'ripple', 'stretch', 'oscill'))},
        'melodia_after': _melodia(after),
        'nikki_after': _nikki_like(after),
        'textures': _textures(mi),
    }


def main():
    level = inventory_level()
    before = {p: audit_mi(p) for p in RAINBOW_MIS}
    petal_wind = {p: audit_mi(p) for p in PETAL_WIND_MIS}

    # Infra
    infra = {
        'MF_MelodiaWindHueReveal': EAL.does_asset_exist('/Game/Melodia/_PROJECT/04_Materials/Functions/MF_MelodiaWindHueReveal'),
        'M_MelodiaPlant_Wind': EAL.does_asset_exist('/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind'),
        'M_SpeedTreeMaster_project': EAL.does_asset_exist('/Game/EnvSandbox/Materials/Masters/M_SpeedTreeMaster'),
    }

    changed = [apply_stable(p) for p in RAINBOW_MIS]
    # Also stabilize petal wind lane MIs if they share the field path
    petal_changed = []
    for p in PETAL_WIND_MIS:
        if EAL.does_asset_exist(p):
            petal_changed.append(apply_stable(p))

    after = {p: audit_mi(p) for p in RAINBOW_MIS}

    audit_path = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'rainbow_speedtree_level_audit_2026-09-19.json'
    tune_path = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'rainbow_speedtree_level_tune_2026-09-19.json'
    audit = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'level': level,
        'infra': infra,
        'before': before,
        'petal_wind_before': petal_wind,
    }
    tune = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'preset': STABLE,
        'switches': SWITCHES,
        'level': level,
        'changed': changed,
        'petal_wind_changed': petal_changed,
        'after': after,
        'gaps': [],
    }
    # gaps
    parents = {a.get('parent') for a in after.values() if a.get('ok')}
    if not level.get('ism_components'):
        tune['gaps'].append('No ISM/HISM components found with RainbowSpeedTree mats — PCG may store mats on volume only; visual instances may be under generated PCG component hierarchy')
    if any(a.get('extremes') for a in after.values()):
        tune['gaps'].append('extremes remain after tune')
    if not any(a.get('nikki_like') for a in after.values()):
        tune['gaps'].append('RainbowSpeedTree MIs have no Nikki Dream* scalars (parent is SpeedTree path)')
    audit_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
    tune_path.write_text(json.dumps(tune, indent=2), encoding='utf-8')
    summary = {
        'world': level.get('world'),
        'ism_components': len(level.get('ism_components') or []),
        'ism_instances': level.get('ism_total_instances'),
        'tuned': [c['path'] for c in changed if c.get('ok')],
        'parents': list(parents),
        'remaining_extremes': {p: a.get('extremes') for p, a in after.items() if a.get('extremes')},
        'gaps': tune['gaps'],
        'audit': str(audit_path),
        'tune': str(tune_path),
    }
    print('RAINBOW_TUNE ' + json.dumps(summary))
    unreal.log('RAINBOW_TUNE ' + json.dumps(summary))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
