
"""Finalize rainbow field wind against recipe + live level inventory.

- Restore per-band MelodiaWindHueSeed and MelodiaWindRevealTint from recipe
- Clamp MelodiaWindResponse to recipe 0.5
- Keep shared stable SpeedTree Shared/Branch1/Ripple scalars
- Ensure a WindDirectionalSource exists in the loaded level
- Verify PCG ISMs still reference MI_RainbowSpeedTree_*
- Report Nikki availability on Universal petal lane vs active wind lane
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

BANDS = [
    ('B0_Red', (1.0, 0.18, 0.22)),
    ('B1_Orange', (1.0, 0.45, 0.1)),
    ('B2_Gold', (1.0, 0.8, 0.2)),
    ('B3_Green', (0.35, 0.95, 0.45)),
    ('B4_Blue', (0.3, 0.55, 1.0)),
    ('B5_Indigo', (0.45, 0.3, 0.95)),
    ('B6_Violet', (0.75, 0.35, 1.0)),
]
PREFIX = '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_'
RESPONSE = 0.5

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
SWITCHES = {
    'SharedEnable': True,
    'Branch1Enable': True,
    'RippleEnable': True,
    'RippleShimmerEnable': False,
    'Branch2Enable': False,
}


def _scalars(mi):
    out = {}
    for e in (mi.get_editor_property('scalar_parameter_values') or []):
        out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = float(
            e.get_editor_property('parameter_value'))
    return out


def _vectors(mi):
    out = {}
    for e in (mi.get_editor_property('vector_parameter_values') or []):
        v = e.get_editor_property('parameter_value')
        out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = [
            float(v.r), float(v.g), float(v.b), float(v.a)]
    return out


def ensure_wind_source():
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = list(subsystem.get_all_level_actors())
    except Exception:
        actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
        subsystem = None
    existing = []
    for a in actors:
        cn = a.get_class().get_name()
        if 'WindDirectionalSource' in cn:
            existing.append({'label': a.get_actor_label(), 'path': a.get_path_name(), 'class': cn})
    if existing:
        return {'created': False, 'sources': existing}
    # spawn one at field anchor-ish
    loc = unreal.Vector(0.0, 0.0, 200.0)
    try:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.WindDirectionalSource, loc, unreal.Rotator(0.0, 0.0, 0.0))
    except Exception as ex:
        return {'created': False, 'error': str(ex), 'sources': []}
    if not actor:
        return {'created': False, 'error': 'spawn returned None', 'sources': []}
    try:
        actor.set_actor_label('WC_MorningFlowerField_WindSource')
    except Exception:
        pass
    # strength / speed via component
    try:
        comps = actor.get_components_by_class(unreal.WindDirectionalSourceComponent)
        for c in comps or []:
            try:
                c.set_editor_property('strength', 0.35)
                c.set_editor_property('speed', 0.25)
                c.set_editor_property('minimum_gust_amount', 0.05)
            except Exception:
                pass
    except Exception:
        pass
    return {'created': True, 'sources': [{'label': actor.get_actor_label(), 'path': actor.get_path_name()}]}


def inventory_ism():
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = list(subsystem.get_all_level_actors())
    except Exception:
        actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    rows = []
    for a in actors:
        if a.get_actor_label() != 'WC_morning_rainbow_bloom_Field':
            continue
        for cls in (unreal.InstancedStaticMeshComponent, unreal.HierarchicalInstancedStaticMeshComponent):
            try:
                comps = list(a.get_components_by_class(cls) or [])
            except Exception:
                comps = []
            for c in comps:
                mats = []
                try:
                    for i in range(c.get_num_materials()):
                        m = c.get_material(i)
                        if m:
                            mats.append(m.get_path_name())
                except Exception:
                    pass
                mesh = None
                try:
                    mesh = c.get_editor_property('static_mesh')
                except Exception:
                    pass
                try:
                    n = int(c.get_instance_count())
                except Exception:
                    n = None
                rows.append({
                    'mesh': mesh.get_path_name() if mesh else None,
                    'materials': mats,
                    'instances': n,
                })
    return rows


def tune_band(idx, label, tint):
    path = PREFIX + label
    mi = EAL.load_asset(path)
    if not mi:
        return {'path': path, 'ok': False}
    # SpeedTree shared motion
    for k, v in STABLE.items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for k, v in SWITCHES.items():
        try:
            MEL.set_material_instance_static_switch_parameter_value(mi, k, bool(v))
        except Exception:
            pass
    # Recipe Melodia wind
    hue = float(idx + 1) / 14.0  # matches prior live 0.0714 on B0
    MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindResponse', RESPONSE)
    MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindSpatialScale', 0.04)
    MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindTravelSpeed', 1.0)
    MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindHueSeed', hue)
    r, g, b = tint
    MEL.set_material_instance_vector_parameter_value(
        mi, 'MelodiaWindRevealTint', unreal.LinearColor(float(r), float(g), float(b), 1.0))
    MEL.update_material_instance(mi)
    EAL.save_asset(path)
    sc = _scalars(mi)
    vec = _vectors(mi)
    return {
        'path': path,
        'ok': True,
        'parent': mi.get_editor_property('parent').get_path_name() if mi.get_editor_property('parent') else None,
        'MelodiaWindResponse': sc.get('MelodiaWindResponse'),
        'MelodiaWindHueSeed': sc.get('MelodiaWindHueSeed'),
        'MelodiaWindRevealTint': vec.get('MelodiaWindRevealTint'),
        'SharedOscillation': sc.get('SharedOscillation'),
        'SharedIndependence': sc.get('SharedIndependence'),
        'Branch1StretchLimit': sc.get('Branch1StretchLimit'),
    }


def audit_nikki_lanes():
    out = {}
    for kind, prefix in (
        ('speedtree_active', PREFIX),
        ('petal_universal', '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_'),
        ('petal_wind', '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_'),
    ):
        path = prefix + 'B0_Red'
        if not EAL.does_asset_exist(path):
            out[kind] = {'path': path, 'exists': False}
            continue
        mi = EAL.load_asset(path)
        sc = _scalars(mi)
        nikki = {k: v for k, v in sc.items() if any(h in k for h in (
            'Dream', 'Pastel', 'Nikki', 'FlowerShadow', 'MossConcavity', 'ShadowDream'))}
        out[kind] = {
            'path': path,
            'exists': True,
            'parent': mi.get_editor_property('parent').get_path_name() if mi.get_editor_property('parent') else None,
            'nikki_like': nikki,
            'melodia': {k: v for k, v in sc.items() if k.startswith('Melodia')},
        }
    return out


def main():
    wind = ensure_wind_source()
    tuned = [tune_band(i, label, tint) for i, (label, tint) in enumerate(BANDS)]
    # Align parent flower MI response to recipe ceiling so inheritance is sane
    parent_path = '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1'
    parent = EAL.load_asset(parent_path)
    parent_rec = {}
    if parent:
        MEL.set_material_instance_scalar_parameter_value(parent, 'MelodiaWindResponse', RESPONSE)
        MEL.set_material_instance_scalar_parameter_value(parent, 'MelodiaWindSpatialScale', 0.04)
        MEL.set_material_instance_scalar_parameter_value(parent, 'MelodiaWindTravelSpeed', 1.0)
        MEL.update_material_instance(parent)
        EAL.save_asset(parent_path)
        parent_rec = {'path': parent_path, 'scalars': _scalars(parent)}

    ism = inventory_ism()
    nikki = audit_nikki_lanes()
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'recipe': {
            'active_lane': 'wind',
            'response': RESPONSE,
            'mi_prefix': PREFIX,
            'note': 'Children of staged SpeedTree flower MI; SpeedTree wind on; hue reveal only',
        },
        'wind_source': wind,
        'tuned_bands': tuned,
        'parent_flower': parent_rec,
        'level_ism': ism,
        'ism_instances': sum((r.get('instances') or 0) for r in ism),
        'nikki_lanes': nikki,
        'stable_speedtree_preset': STABLE,
        'gaps': [],
    }
    if not any('RainbowSpeedTree' in (m or '') for r in ism for m in (r.get('materials') or [])):
        report['gaps'].append('PCG field ISMs not referencing RainbowSpeedTree mats')
    if not nikki.get('speedtree_active', {}).get('nikki_like'):
        report['gaps'].append('Active SpeedTree wind lane has no Universal Nikki Dream* params by design')
    if nikki.get('petal_universal', {}).get('nikki_like'):
        report['nikki_note'] = 'Universal Nikki Dream* live on MI_RainbowPetal_* (inactive lane while active_lane=wind)'
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'rainbow_speedtree_finalize_2026-09-19.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    summary = {
        'wind_source': wind,
        'bands_ok': all(t.get('ok') for t in tuned),
        'response': [t.get('MelodiaWindResponse') for t in tuned],
        'hue_seeds': [t.get('MelodiaWindHueSeed') for t in tuned],
        'ism_instances': report['ism_instances'],
        'ism_comps': len(ism),
        'gaps': report['gaps'],
        'report': str(out),
    }
    print('RAINBOW_FINAL ' + json.dumps(summary))
    unreal.log('RAINBOW_FINAL ' + json.dumps(summary))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
