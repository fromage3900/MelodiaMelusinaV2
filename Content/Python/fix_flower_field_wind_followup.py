
"""Follow-up: clear remaining extreme foliage wind; verify flower textures; restore tint."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AUDIT = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit'

EXTRA = [
    '/Game/EnvSandbox/Library/FoliageCards/GenericTreeMeshCard_Mat1',
    '/Game/EnvSandbox/Library/FoliageCards/GenericTreeMeshCard_Mat',
    '/Game/EnvSandbox/Library/FoliageCards/GenericTree_001_Mat',
    '/Game/EnvSandbox/Library/FoliageCards/SimpleGrass_Mat',
]

STAGED = [
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1',
    '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlowerTall',
    '/Game/Melodia/_PROJECT/04_Materials/Plants/GrassBundles/MI_Plant_Grass_Simple',
]

MOTION_KEYS = (
    'branch', 'oscill', 'ripple', 'gust', 'turbulence',
    'flexibility', 'independence', 'stretch', 'sway', 'shared',
)
# intentionally exclude bare 'wind' so MelodiaWind* is preserved


def _is_speedtree_motion(name: str) -> bool:
    low = name.lower()
    if low.startswith('melodia'):
        return False
    return any(k in low for k in MOTION_KEYS) or low in ('winddirection',)


def _clear(mi):
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
            if _is_speedtree_motion(name):
                try:
                    if MEL.set_material_instance_parameter_override(mi, parameter_name, False):
                        removed.append(name)
                except Exception:
                    pass
    if removed:
        MEL.update_material_instance(mi)
    return removed


def _textures(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('texture_parameter_values') or []):
            name = str(e.get_editor_property('parameter_info').get_editor_property('name'))
            tex = e.get_editor_property('parameter_value')
            out[name] = tex.get_path_name() if tex else None
    except Exception as exc:
        out['_error'] = str(exc)
    return out


def _scalars(mi):
    out = {}
    try:
        for e in (mi.get_editor_property('scalar_parameter_values') or []):
            out[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = float(
                e.get_editor_property('parameter_value')
            )
    except Exception as exc:
        out['_error'] = str(exc)
    return out


def main():
    changed = []
    for path in EXTRA:
        if not EAL.does_asset_exist(path):
            continue
        mi = EAL.load_asset(path)
        before = {k: v for k, v in _scalars(mi).items() if _is_speedtree_motion(k)}
        removed = _clear(mi)
        if removed:
            EAL.save_asset(path)
        after = {k: v for k, v in _scalars(mi).items() if _is_speedtree_motion(k)}
        changed.append({'path': path, 'before_motion': before, 'cleared': removed, 'after_motion': after})

    # Re-assert Melodia preset + restore reveal tint if missing
    responses = {
        '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlower1': 0.80,
        '/Game/Melodia/_PROJECT/04_Materials/Plants/Flowers/MI_Plant_Flower_GenericFlowerTall': 0.75,
        '/Game/Melodia/_PROJECT/04_Materials/Plants/GrassBundles/MI_Plant_Grass_Simple': 0.55,
    }
    verify = []
    for path in STAGED:
        mi = EAL.load_asset(path)
        if not mi:
            verify.append({'path': path, 'ok': False})
            continue
        resp = responses[path]
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindResponse', resp)
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindSpatialScale', 0.04)
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindTravelSpeed', 1.0)
        MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindHueSeed', 0.0)
        MEL.set_material_instance_vector_parameter_value(
            mi, 'MelodiaWindRevealTint', unreal.LinearColor(0.83, 0.62, 0.62, 1.0)
        )
        MEL.update_material_instance(mi)
        EAL.save_asset(path)
        verify.append({
            'path': path,
            'ok': True,
            'textures': _textures(mi),
            'scalars': _scalars(mi),
            'has_color_opacity': 'ColorOpacity' in _textures(mi) and _textures(mi).get('ColorOpacity') is not None,
        })

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'extra_cleared': changed,
        'staged_verify': verify,
    }
    out = AUDIT / 'flower_field_speedtree_wind_followup_2026-09-19.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('FOLLOWUP', json.dumps({
        'extra': [(c['path'], len(c['cleared'])) for c in changed],
        'staged': [(v['path'], v.get('has_color_opacity'), v.get('scalars', {}).get('MelodiaWindResponse')) for v in verify],
        'report': str(out),
    }))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
