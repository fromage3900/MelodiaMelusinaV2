"""Audit + stabilize flower-field SpeedTree wind; check Nikki/MF availability.

Run via Monolith execute_file. Keeps SpeedTree wind chain intact.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

PROJECT = Path(unreal.Paths.project_dir())
AUDIT = PROJECT / 'Saved' / 'Audit'
AUDIT.mkdir(parents=True, exist_ok=True)

SPEEDTREE_PARENT = '/SpeedTreeImporter/SpeedTree9/SpeedTreeMaster'
MELODIA_MASTER = '/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind'
MF_HUE = '/Game/Melodia/_PROJECT/04_Materials/Functions/MF_MelodiaWindHueReveal'
MF_FOLIAGE_WPO = '/Game/EnvSandbox/Materials/Functions/MF_FoliageWindWPO'
PALETTE = '/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette'
DRIVER = '/Game/Melodia/Cymatics/MPC_Cymatics_Driver'

MOTION_KEYS = (
    'branch', 'oscill', 'ripple', 'wind', 'gust', 'turbulence',
    'flexibility', 'independence', 'stretch', 'sway', 'shared',
)
NIKKI_KEYS = (
    'DreamSaturation', 'DreamShadowLift', 'PastelLift', 'MossConcavityStrength',
    'FlowerShadow', 'Nikki', 'Dream', 'Pastel',
)

FLOWER_SOURCES = [
    '/Game/EnvSandbox/Library/FoliageCards/GenericFlower1_Mat',
    '/Game/EnvSandbox/Library/FoliageCards/GenericFlowerTall_Mat',
]
STAGED_FLOWERS = [
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1',
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlowerTall',
]
STAGED_FIELD = [
    '/Game/Melodia/_PROJECT/04_Materials/Plants/GrassBundles/MI_Plant_Grass_Simple',
] + STAGED_FLOWERS

PRESET = {
    'MelodiaWindSpatialScale': 0.04,
    'MelodiaWindTravelSpeed': 1.0,
}
RESPONSE_BY_ASSET = {
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1': 0.80,
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlowerTall': 0.75,
    '/Game/Melodia/_PROJECT/04_Materials/Plants/GrassBundles/MI_Plant_Grass_Simple': 0.55,
}


def _is_motion(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in MOTION_KEYS)


def _parent_path(mi) -> str:
    try:
        p = mi.get_editor_property('parent')
        return p.get_path_name() if p else ''
    except Exception:
        return ''


def _scalar_map(mi) -> dict:
    out = {}
    try:
        for e in (mi.get_editor_property('scalar_parameter_values') or []):
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = float(
                e.get_editor_property('parameter_value')
            )
    except Exception as exc:
        out['_error'] = str(exc)
    return out


def _vector_map(mi) -> dict:
    out = {}
    try:
        for e in (mi.get_editor_property('vector_parameter_values') or []):
            v = e.get_editor_property('parameter_value')
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = [
                float(v.r), float(v.g), float(v.b), float(v.a)
            ]
    except Exception as exc:
        out['_error'] = str(exc)
    return out


def _motion_overrides(mi) -> dict:
    scalars = _scalar_map(mi)
    vectors = _vector_map(mi)
    return {
        'scalars': {k: v for k, v in scalars.items() if k != '_error' and _is_motion(k)},
        'vectors': {k: v for k, v in vectors.items() if k != '_error' and _is_motion(k)},
        'nikki_like': {
            k: v for k, v in scalars.items()
            if k != '_error' and any(n.lower() in k.lower() for n in NIKKI_KEYS)
        },
        'melodia_wind': {k: v for k, v in scalars.items() if k.startswith('MelodiaWind')},
        'all_scalar_count': len([k for k in scalars if k != '_error']),
    }


def _clear_motion_overrides(mi) -> list:
    removed = []
    for getter in (
        MEL.get_scalar_parameter_names,
        MEL.get_vector_parameter_names,
        MEL.get_static_switch_parameter_names,
    ):
        try:
            names = getter(mi)
        except Exception:
            continue
        for parameter_name in names:
            name = str(parameter_name)
            if _is_motion(name):
                try:
                    if MEL.set_material_instance_parameter_override(mi, parameter_name, False):
                        removed.append(name)
                except Exception:
                    pass
    if removed:
        MEL.update_material_instance(mi)
    return removed


def _audit_asset(path: str) -> dict:
    mi = EAL.load_asset(path)
    if not mi:
        return {'path': path, 'ok': False, 'error': 'missing'}
    info = _motion_overrides(mi)
    info.update({
        'path': path,
        'ok': True,
        'parent': _parent_path(mi),
        'class': mi.get_class().get_name(),
    })
    return info


def _mpc_scalar_names(path: str) -> list:
    mpc = EAL.load_asset(path)
    if not mpc:
        return []
    try:
        entries = mpc.get_editor_property('scalar_parameters') or []
        return [str(e.get_editor_property('parameter_name')) for e in entries]
    except Exception:
        return []


def main() -> int:
    audit = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'assets': {},
        'infra': {},
        'actions': [],
    }

    audit['infra'] = {
        'MF_MelodiaWindHueReveal': EAL.does_asset_exist(MF_HUE),
        'MF_FoliageWindWPO': EAL.does_asset_exist(MF_FOLIAGE_WPO),
        'M_MelodiaPlant_Wind': EAL.does_asset_exist(MELODIA_MASTER),
        'palette_wind_lanes': [n for n in _mpc_scalar_names(PALETTE) if 'Wind' in n],
        'driver_wind_lanes': [n for n in _mpc_scalar_names(DRIVER) if 'Wind' in n],
    }

    targets = list(dict.fromkeys(FLOWER_SOURCES + STAGED_FIELD))
    for path in targets:
        audit['assets'][path] = _audit_asset(path)

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    scanned_st = 0
    extreme = []
    for data in registry.get_assets_by_path('/Game/EnvSandbox/Library/FoliageCards', recursive=True):
        if data.get_editor_property('asset_class_path').asset_name != 'MaterialInstanceConstant':
            continue
        asset_path = f"{data.get_editor_property('package_name')}.{data.get_editor_property('asset_name')}"
        mi = EAL.load_asset(asset_path)
        if not mi:
            continue
        parent = _parent_path(mi)
        if 'SpeedTreeMaster' not in parent and 'MelodiaPlant_Wind' not in parent:
            continue
        scanned_st += 1
        info = _motion_overrides(mi)
        motion = info['scalars']
        bad = {k: v for k, v in motion.items() if abs(float(v)) > 2.0}
        if bad:
            extreme.append({'path': asset_path, 'extreme': bad, 'all_motion': motion})

    audit['foliage_cards_speedtree_scanned'] = scanned_st
    audit['extreme_motion_overrides'] = extreme

    changed = []
    for path in FLOWER_SOURCES:
        mi = EAL.load_asset(path)
        if not mi:
            continue
        removed = _clear_motion_overrides(mi)
        if removed:
            EAL.save_asset(path)
            changed.append({'path': path, 'cleared_motion': removed})
            audit['actions'].append({'clear_motion': path, 'removed': removed})

    for path in STAGED_FIELD:
        mi = EAL.load_asset(path)
        if not mi:
            audit['actions'].append({'skip_missing': path})
            continue
        parent = _parent_path(mi)
        before = _motion_overrides(mi)
        removed = _clear_motion_overrides(mi)
        resp = float(RESPONSE_BY_ASSET.get(path, 0.70))
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindResponse', resp)
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindSpatialScale', PRESET['MelodiaWindSpatialScale'])
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindTravelSpeed', PRESET['MelodiaWindTravelSpeed'])
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindHueSeed', 0.0)
        except Exception:
            pass
        MEL.update_material_instance(mi)
        EAL.save_asset(path)
        after = _motion_overrides(mi)
        entry = {
            'path': path,
            'parent': parent,
            'cleared_motion': removed,
            'preset_response': resp,
            'preset': PRESET,
            'before_melodia': before.get('melodia_wind'),
            'after_melodia': after.get('melodia_wind'),
            'after_motion_scalars': after.get('scalars'),
            'nikki_like_after': after.get('nikki_like'),
        }
        changed.append(entry)
        audit['actions'].append({'tune_staged': entry})

    nikki_status = {
        'speedtree_can_hold_universal_nikki_scalars': False,
        'reason': 'Flower SpeedTree MIs parent to SpeedTreeMaster or M_MelodiaPlant_Wind; Nikki/FlowerShadow groups live on M_Master_Toon_Universal. Reparenting would break SpeedTree wind.',
        'mf_hue_reveal': audit['infra']['MF_MelodiaWindHueReveal'],
        'mf_foliage_wind_wpo': audit['infra']['MF_FoliageWindWPO'],
        'companion_nikki_foliage_paths_checked': [],
    }
    for cand in (
        '/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ForestFoliage',
        '/Game/EnvSandbox/Materials/Instances/MI_Show_ForestFoliage',
        '/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/MI_Show_ForestFoliage',
    ):
        if EAL.does_asset_exist(cand):
            mi = EAL.load_asset(cand)
            nikki_status['companion_nikki_foliage_paths_checked'].append({
                'path': cand,
                'parent': _parent_path(mi) if mi else None,
                'nikki_like': _motion_overrides(mi).get('nikki_like') if mi else None,
                'scalars_sample': dict(list(_scalar_map(mi).items())[:25]) if mi else None,
            })

    after_assets = {path: _audit_asset(path) for path in targets}

    tune_receipt = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'ok': True,
        'preset': PRESET,
        'response_by_asset': RESPONSE_BY_ASSET,
        'changed': changed,
        'nikki_mf_status': nikki_status,
        'infra': audit['infra'],
        'extreme_before_count': len(extreme),
        'after_assets': after_assets,
        'gaps': [],
    }
    if not audit['infra']['MF_MelodiaWindHueReveal']:
        tune_receipt['gaps'].append('MF_MelodiaWindHueReveal missing')
    if not audit['infra']['MF_FoliageWindWPO']:
        tune_receipt['gaps'].append('MF_FoliageWindWPO missing on disk (optional; SpeedTree uses plugin SpeedTreeWind)')
    if not audit['infra']['palette_wind_lanes']:
        tune_receipt['gaps'].append('Palette wind lanes missing')
    if not any(a.get('melodia_wind') for a in after_assets.values() if a.get('ok')):
        tune_receipt['gaps'].append('No MelodiaWind* params on staged flower MIs after tune')

    audit_path = AUDIT / 'flower_field_speedtree_wind_audit_2026-09-19.json'
    tune_path = AUDIT / 'flower_field_speedtree_wind_tune_2026-09-19.json'
    audit_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')
    tune_path.write_text(json.dumps(tune_receipt, indent=2), encoding='utf-8')

    summary = {
        'ok': True,
        'tuned_staged': [c['path'] for c in changed if 'preset_response' in c],
        'extreme_before': len(extreme),
        'gaps': tune_receipt['gaps'],
        'audit': str(audit_path),
        'tune': str(tune_path),
        'infra': audit['infra'],
    }
    unreal.log('FLOWER_WIND_TUNE ' + json.dumps(summary))
    print('FLOWER_WIND_TUNE ' + json.dumps(summary))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
