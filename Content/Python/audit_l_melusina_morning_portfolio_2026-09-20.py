
"""Full portfolio-readiness audit of the loaded L_MelusinaMorning level."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary


def _label(a):
    try:
        return a.get_actor_label() or ''
    except Exception:
        return ''


def _cls(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ''


def _path(o):
    try:
        return o.get_path_name() if o else ''
    except Exception:
        return ''


def _loc(a):
    try:
        t = a.get_actor_location()
        return [round(t.x, 1), round(t.y, 1), round(t.z, 1)]
    except Exception:
        return None


def _hidden(a):
    out = {}
    try:
        out['hidden_in_game'] = bool(a.is_hidden())
    except Exception:
        try:
            out['hidden_in_game'] = bool(a.get_editor_property('b_hidden'))
        except Exception:
            pass
    try:
        out['temp_hidden_editor'] = bool(a.is_temporarily_hidden_in_editor())
    except Exception:
        pass
    return out


def main():
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        world_path = world.get_path_name() if world else None
    except Exception:
        world_path = None
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(svc.get_all_level_actors())

    by_class = Counter()
    folders = Counter()
    tags = Counter()
    lights = []
    ppvs = []
    cameras = []
    pcg = []
    niagara = []
    houdini = []
    foliage_ism = []
    static_notable = []
    wind = []
    volumes = []
    issues = []
    strengths = []

    for a in actors:
        cn = _cls(a)
        lab = _label(a)
        by_class[cn] += 1
        try:
            folders[str(a.get_folder_path() or '(root)')] += 1
        except Exception:
            folders['(unknown)'] += 1
        try:
            for t in (a.tags or []):
                tags[str(t)] += 1
        except Exception:
            pass
        hid = _hidden(a)

        if 'Light' in cn or cn.startswith('Ultra_Dynamic') or 'Sky' in cn and 'Light' in cn:
            rec = {'label': lab, 'class': cn, 'loc': _loc(a), **hid}
            try:
                for c in a.get_components_by_class(unreal.LightComponent) or []:
                    try:
                        rec['intensity'] = float(c.get_editor_property('intensity'))
                    except Exception:
                        pass
                    try:
                        rec['mobility'] = str(c.get_editor_property('mobility'))
                    except Exception:
                        pass
            except Exception:
                pass
            if 'Ultra_Dynamic_Sky' in cn or lab.startswith('Ultra_Dynamic'):
                for prop in ('Time of Day', 'Cloud Coverage', 'Overall Intensity', 'Sun Light Intensity', 'Animate Time of Day', 'Night Brightness'):
                    try:
                        rec[prop] = a.get_editor_property(prop)
                    except Exception:
                        pass
            lights.append(rec)

        if 'PostProcess' in cn:
            ppvs.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        if 'Camera' in cn or lab.startswith('WC_Lookdev_') or lab.startswith('CineCamera'):
            cameras.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        if 'PCG' in cn or lab.startswith('WC_morning') or 'PCG' in lab:
            pcg.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        if 'Niagara' in cn:
            ns = None
            try:
                for c in a.get_components_by_class(unreal.NiagaraComponent) or []:
                    try:
                        asset = c.get_editor_property('asset')
                        ns = _path(asset)
                    except Exception:
                        pass
            except Exception:
                pass
            niagara.append({'label': lab, 'class': cn, 'system': ns, 'loc': _loc(a), **hid})

        if 'Houdini' in cn or 'Houdini' in lab:
            houdini.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        if 'WindDirectional' in cn:
            wind.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        if 'Volume' in cn and 'PCG' not in cn:
            volumes.append({'label': lab, 'class': cn, 'loc': _loc(a), **hid})

        # ISM inventory for field
        try:
            comps = list(a.get_components_by_class(unreal.InstancedStaticMeshComponent) or [])
            comps += list(a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent) or [])
        except Exception:
            comps = []
        for c in comps:
            mats = []
            try:
                for i in range(c.get_num_materials()):
                    m = c.get_material(i)
                    if m:
                        mats.append(_path(m))
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
                n = 0
            if n > 0 or any('Rainbow' in m or 'Flower' in m or 'Foliage' in m for m in mats):
                foliage_ism.append({
                    'actor': lab, 'class': cn, 'comp': c.get_class().get_name(),
                    'mesh': _path(mesh), 'materials': mats, 'instances': n, **hid
                })

        if cn == 'StaticMeshActor' and any(k in lab for k in (
            'Brushify', 'Island', 'Rainbow', 'Dell', 'Sphere3D', 'Greybox', 'Proof', 'Castle', 'Zen', 'Melusina', 'WC_'
        )):
            mesh = None
            mats = []
            try:
                for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                    try:
                        mesh = c.get_editor_property('static_mesh')
                    except Exception:
                        pass
                    try:
                        for i in range(c.get_num_materials()):
                            m = c.get_material(i)
                            if m:
                                mats.append(_path(m))
                    except Exception:
                        pass
            except Exception:
                pass
            static_notable.append({
                'label': lab, 'loc': _loc(a), 'mesh': _path(mesh), 'materials': mats[:6], **hid
            })

    # Field summary
    field_instances = sum(x.get('instances') or 0 for x in foliage_ism)
    rainbow_mats = Counter()
    for x in foliage_ism:
        for m in x.get('materials') or []:
            if 'Rainbow' in m or 'Flower' in m:
                rainbow_mats[m.split('.')[-1]] += x.get('instances') or 1

    # UDS present?
    uds = [l for l in lights if 'Ultra_Dynamic' in l.get('class', '') or 'Ultra_Dynamic' in l.get('label', '')]
    lookdev_cams = [c for c in cameras if c['label'].startswith('WC_Lookdev_')]
    houdini_visible = [h for h in houdini if not h.get('temp_hidden_editor') and not h.get('hidden_in_game')]

    # Heuristic issues / strengths
    if world_path and 'L_MelusinaMorning' in world_path:
        strengths.append('Correct map loaded: L_MelusinaMorning')
    else:
        issues.append({'severity': 'high', 'id': 'wrong_map', 'detail': f'Loaded world is {world_path}'})

    if field_instances >= 500:
        strengths.append(f'PCG flower field is populated ({field_instances} ISM instances)')
    else:
        issues.append({'severity': 'high', 'id': 'thin_field', 'detail': f'Only {field_instances} field instances'})

    if uds:
        strengths.append('Ultra Dynamic Sky is present as lighting authority')
        tod = uds[0].get('Time of Day')
        if tod is not None and float(tod) < 800:
            issues.append({'severity': 'med', 'id': 'uds_too_dark', 'detail': f'Time of Day {tod} reads night/dawn-dark for portfolio'})
        if tod is not None and 900 <= float(tod) <= 1400:
            strengths.append(f'UDS Time of Day set for daytime lookdev ({tod})')
    else:
        issues.append({'severity': 'high', 'id': 'no_uds', 'detail': 'No Ultra Dynamic Sky actor found'})

    if any('PPV_NikkiDream' in p['label'] for p in ppvs):
        strengths.append('PPV_NikkiDream is in level for Nikki grading stack')
    else:
        issues.append({'severity': 'med', 'id': 'no_nikki_ppv', 'detail': 'PPV_NikkiDream missing'})

    if lookdev_cams:
        strengths.append(f'{len(lookdev_cams)} WC_Lookdev cameras staged for portfolio angles')
    else:
        issues.append({'severity': 'med', 'id': 'no_lookdev_cams', 'detail': 'No WC_Lookdev_* cameras'})

    if wind:
        strengths.append(f'WindDirectionalSource present ({[w["label"] for w in wind]})')
    else:
        issues.append({'severity': 'med', 'id': 'no_wind_source', 'detail': 'No WindDirectionalSource for SpeedTree physical wind'})

    if houdini_visible:
        issues.append({'severity': 'high', 'id': 'houdini_visible', 'detail': f'Houdini overlays visible: {[h["label"] for h in houdini_visible]} — contract says hide for beauty'})
    elif houdini:
        strengths.append('Houdini RainbowBloom overlays present but hidden (PCG field is beauty chorus)')

    if any('WorldGridMaterial' in (m or '') for s in static_notable for m in (s.get('materials') or [])):
        issues.append({'severity': 'med', 'id': 'worldgrid_mats', 'detail': 'Some notable static meshes still on WorldGridMaterial'})

    # Proof B leftovers
    proofish = [s for s in static_notable if any(k in (s.get('mesh') or '') + s['label'] for k in ('Greybox', 'Proof', 'Zen', 'Castle'))]
    if proofish:
        issues.append({'severity': 'low', 'id': 'proof_b_greybox', 'detail': f'{len(proofish)} greybox/proof actors may clutter portfolio frames', 'samples': [p['label'] for p in proofish[:12]]})

    # Sphere3D stand-ins
    spheres = [s for s in static_notable if 'Sphere3D' in s['label'] or 'Sphere3D' in (s.get('mesh') or '')]
    if spheres:
        issues.append({'severity': 'med', 'id': 'sphere3d_standins', 'detail': f'{len(spheres)} SM_PM3D_Sphere3D stand-ins still in level (often landscape placeholders)'})

    # Niagara morning FX
    morning_fx = [n for n in niagara if 'Morning' in n['label'] or 'morning' in n['label'] or 'windfront' in n['label'] or 'petal' in n['label'].lower()]
    if morning_fx:
        strengths.append(f'Morning Niagara FX present ({len(morning_fx)} actors)')
        hidden_fx = [n for n in morning_fx if n.get('temp_hidden_editor') or n.get('hidden_in_game')]
        if hidden_fx:
            issues.append({'severity': 'low', 'id': 'fx_hidden', 'detail': f'Some morning FX hidden: {[n["label"] for n in hidden_fx]}'})

    # Material lane check on one band
    band0 = '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red'
    mat_audit = {}
    if EAL.does_asset_exist(band0):
        mi = EAL.load_asset(band0)
        tex = {}
        for e in (mi.get_editor_property('texture_parameter_values') or []):
            n = str(e.get_editor_property('parameter_info').get_editor_property('name'))
            t = e.get_editor_property('parameter_value')
            tex[n] = t.get_path_name() if t else None
        sc = {}
        for e in (mi.get_editor_property('scalar_parameter_values') or []):
            sc[str(e.get_editor_property('parameter_info').get_editor_property('name'))] = float(e.get_editor_property('parameter_value'))
        mat_audit = {
            'path': band0,
            'parent': _path(mi.get_editor_property('parent')),
            'textures': tex,
            'melodia': {k: v for k, v in sc.items() if k.startswith('Melodia')},
            'has_coloropacity': bool(tex.get('ColorOpacity')),
            'dead_albedo_override': 'Albedo' in tex and tex.get('Albedo'),
        }
        if mat_audit['has_coloropacity']:
            strengths.append('Rainbow band MIs wire ColorOpacity (Melodia plant slot)')
        if mat_audit['dead_albedo_override']:
            issues.append({'severity': 'med', 'id': 'dead_albedo', 'detail': 'Rainbow MI still has Albedo override (unused by Melodia plant master)'})

    # Existing screens today
    screens = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'Screens'
    recent = []
    if screens.exists():
        for p in sorted(screens.glob('wc_morning_rainbow_bloom_*_2026-09-20.png')):
            recent.append({'file': str(p).replace('\\\\', '/'), 'bytes': p.stat().st_size})

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'world': world_path,
        'actor_count': len(actors),
        'class_histogram_top': by_class.most_common(35),
        'folder_histogram_top': folders.most_common(25),
        'tag_histogram_top': tags.most_common(25),
        'lights': lights,
        'ppvs': ppvs,
        'cameras': cameras,
        'lookdev_cameras': lookdev_cams,
        'pcg': pcg,
        'niagara': niagara,
        'houdini': houdini,
        'wind': wind,
        'volumes': volumes,
        'foliage_ism': foliage_ism,
        'field_instances_total': field_instances,
        'rainbow_mat_instance_weights': rainbow_mats.most_common(20),
        'static_notable_count': len(static_notable),
        'static_notable_sample': static_notable[:40],
        'sphere3d_count': len(spheres),
        'proofish_count': len(proofish),
        'material_band0': mat_audit,
        'recent_lookdev_screens': recent,
        'strengths': strengths,
        'issues': issues,
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'l_melusina_morning_portfolio_audit_2026-09-20.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    summary = {
        'world': world_path,
        'actors': len(actors),
        'field_instances': field_instances,
        'ism_comps': len(foliage_ism),
        'lights': len(lights),
        'ppvs': [p['label'] for p in ppvs],
        'lookdev_cams': [c['label'] for c in lookdev_cams],
        'uds': uds[0] if uds else None,
        'houdini': houdini,
        'wind': wind,
        'niagara_morning': [n['label'] for n in morning_fx],
        'strengths': strengths,
        'issues': issues,
        'screens': len(recent),
        'report': str(out),
    }
    print('MORNING_AUDIT ' + json.dumps(summary, default=str))
    unreal.log('MORNING_AUDIT ' + json.dumps(summary, default=str))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
