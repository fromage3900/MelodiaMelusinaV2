
"""Inventory flower/foliage/SpeedTree-related actors and materials in the loaded editor level."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
EDITOR = unreal.EditorLevelLibrary
SUB = unreal.EditorActorSubsystem
ASSET = unreal.EditorAssetLibrary

KEYWORDS = (
    'flower', 'foliage', 'grass', 'plant', 'speedtree', 'meadow', 'bloom',
    'petal', 'weed', 'bush', 'tree', 'card', 'rainbow', 'melodia plant',
)


def _low(s):
    return (s or '').lower()


def _hit(s):
    l = _low(s)
    return any(k in l for k in KEYWORDS)


def _actor_label(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ''


def _class_name(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ''


def _path_name(obj):
    try:
        return obj.get_path_name() if obj else ''
    except Exception:
        return ''


def _mesh_from_actor(a):
    info = {'static_mesh': None, 'materials': [], 'instance_count': None, 'comp_class': None}
    try:
        comps = a.get_components_by_class(unreal.PrimitiveComponent)
    except Exception:
        comps = []
    for c in comps or []:
        cname = c.get_class().get_name()
        info['comp_class'] = cname
        mesh = None
        try:
            if hasattr(c, 'static_mesh'):
                mesh = c.static_mesh
            elif hasattr(c, 'get_editor_property'):
                try:
                    mesh = c.get_editor_property('static_mesh')
                except Exception:
                    mesh = None
        except Exception:
            mesh = None
        if mesh:
            info['static_mesh'] = _path_name(mesh)
        # materials
        try:
            n = c.get_num_materials()
            for i in range(n):
                mat = c.get_material(i)
                if mat:
                    info['materials'].append(_path_name(mat))
        except Exception:
            pass
        # HISMC / ISM count
        try:
            if hasattr(c, 'get_instance_count'):
                info['instance_count'] = int(c.get_instance_count())
            else:
                try:
                    info['instance_count'] = int(c.get_editor_property('instance_count')) if False else None
                except Exception:
                    pass
            if info['instance_count'] is None and 'Instanced' in cname:
                try:
                    transforms = c.get_editor_property('per_instance_sm_data') or []
                    info['instance_count'] = len(transforms)
                except Exception:
                    try:
                        info['instance_count'] = len(c.instance_bodies) if hasattr(c, 'instance_bodies') else None
                    except Exception:
                        pass
        except Exception:
            pass
        # Foliage
        try:
            if 'Foliage' in cname or 'Hierarchical' in cname:
                if info['instance_count'] is None:
                    try:
                        info['instance_count'] = int(c.get_instance_count())
                    except Exception:
                        pass
        except Exception:
            pass
    return info


def _world_name():
    try:
        w = EDITOR.get_editor_world()
        return w.get_path_name() if w else None
    except Exception:
        try:
            w = unreal.UnrealEditorSubsystem().get_editor_world()
            return w.get_path_name() if w else None
        except Exception:
            return None


def main():
    world = _world_name()
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors = list(subsystem.get_all_level_actors())
    except Exception:
        actors = list(EDITOR.get_all_level_actors())

    relevant = []
    mat_counter = Counter()
    mesh_counter = Counter()
    class_counter = Counter()
    pcg_like = []
    wind_sources = []

    for a in actors:
        label = _actor_label(a)
        cname = _class_name(a)
        path = _path_name(a)
        class_counter[cname] += 1
        if 'Wind' in cname or 'wind' in _low(label):
            wind_sources.append({'label': label, 'class': cname, 'path': path})
        info = _mesh_from_actor(a)
        blob = ' '.join([label, cname, path, info.get('static_mesh') or '', ' '.join(info.get('materials') or [])])
        is_rel = _hit(blob) or (info.get('instance_count') or 0) > 0 and _hit(blob)
        # also catch any actor using SpeedTree/plant materials
        mats = info.get('materials') or []
        if any(_hit(m) or 'SpeedTree' in m or 'FoliageCards' in m or '/Plants/' in m for m in mats):
            is_rel = True
        if any(_hit(info.get('static_mesh') or '') or 'FoliageCards' in (info.get('static_mesh') or '') for _ in [0]):
            if info.get('static_mesh'):
                is_rel = is_rel or _hit(info['static_mesh']) or 'FoliageCards' in info['static_mesh']
        if 'PCG' in cname or 'pcg' in _low(label) or 'Houdini' in cname:
            pcg_like.append({'label': label, 'class': cname, 'path': path, **info})
        if not is_rel and cname not in ('InstancedFoliageActor', 'HierarchicalInstancedStaticMeshActor'):
            # InstancedFoliageActor always inspect
            if cname != 'InstancedFoliageActor':
                continue
            is_rel = True
        if not is_rel:
            continue
        entry = {
            'label': label,
            'class': cname,
            'path': path,
            'static_mesh': info.get('static_mesh'),
            'materials': mats,
            'instance_count': info.get('instance_count'),
            'comp_class': info.get('comp_class'),
        }
        relevant.append(entry)
        if info.get('static_mesh'):
            mesh_counter[info['static_mesh']] += 1
        for m in mats:
            mat_counter[m] += 1

    # Foliage actor deep dive
    foliage_detail = []
    for a in actors:
        if _class_name(a) != 'InstancedFoliageActor':
            continue
        detail = {'label': _actor_label(a), 'components': []}
        try:
            comps = a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
        except Exception:
            comps = []
        for c in comps or []:
            mesh = None
            try:
                mesh = c.get_editor_property('static_mesh')
            except Exception:
                mesh = getattr(c, 'static_mesh', None)
            mats = []
            try:
                for i in range(c.get_num_materials()):
                    mat = c.get_material(i)
                    if mat:
                        mats.append(_path_name(mat))
            except Exception:
                pass
            count = None
            try:
                count = int(c.get_instance_count())
            except Exception:
                count = None
            detail['components'].append({
                'mesh': _path_name(mesh),
                'materials': mats,
                'instance_count': count,
            })
            if mesh:
                mesh_counter[_path_name(mesh)] += count or 1
            for m in mats:
                mat_counter[m] += count or 1
        foliage_detail.append(detail)

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'world': world,
        'actor_count': len(actors),
        'relevant_count': len(relevant),
        'class_histogram_top': class_counter.most_common(40),
        'relevant_actors': relevant[:200],
        'foliage_detail': foliage_detail,
        'pcg_like': pcg_like[:80],
        'wind_sources': wind_sources,
        'materials_used': mat_counter.most_common(60),
        'meshes_used': mesh_counter.most_common(60),
    }
    out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'flower_field_level_inventory_2026-09-19.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    summary = {
        'world': world,
        'actors': len(actors),
        'relevant': len(relevant),
        'foliage_actors': len(foliage_detail),
        'foliage_components': sum(len(f['components']) for f in foliage_detail),
        'top_mats': mat_counter.most_common(15),
        'top_meshes': mesh_counter.most_common(15),
        'wind_sources': len(wind_sources),
        'pcg_like': len(pcg_like),
        'report': str(out),
    }
    print('LEVEL_INV ' + json.dumps(summary))
    unreal.log('LEVEL_INV ' + json.dumps(summary))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
