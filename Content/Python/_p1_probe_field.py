import unreal, json, math
from pathlib import Path

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
field = next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)
out = {'field': label(field) if field else None, 'isms': [], 'islands': [], 'rocks': []}
if field:
    for c in list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or []):
        mesh = c.get_editor_property('static_mesh')
        mats = []
        try:
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                mats.append(m.get_path_name() if m else None)
        except Exception:
            pass
        out['isms'].append({
            'mesh': mesh.get_path_name() if mesh else None,
            'count': int(c.get_instance_count()),
            'mats': mats[:4],
        })
for a in svc.get_all_level_actors():
    lab = label(a)
    if lab.startswith('BrushifyIsland_'):
        loc = a.get_actor_location()
        out['islands'].append({'label': lab, 'loc':[loc.x,loc.y,loc.z]})
    if any(k in lab.lower() for k in ('rock','boulder','shrub','bush','fern','cliff')) and 'Greybox' not in lab:
        if len(out['rocks']) < 40:
            loc = a.get_actor_location()
            mesh=None
            try:
                for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
                    mesh=c.get_editor_property('static_mesh'); break
            except: pass
            out['rocks'].append({'label':lab,'mesh': mesh.get_path_name() if mesh else None,'loc':[loc.x,loc.y,loc.z]})

# asset registry sample for rock/shrub
ar = unreal.AssetRegistryHelpers.get_asset_registry()
cands = []
for filt in ('/Game/Brushify', '/Game/EnvSandbox', '/Game/Melodia'):
    try:
        assets = ar.get_assets_by_path(filt, True)
    except Exception:
        assets = []
    for a in assets or []:
        name = str(a.asset_name)
        path = f"{a.package_name}.{a.asset_name}"
        if a.asset_class_path.asset_name != 'StaticMesh':
            continue
        low = name.lower()
        if any(k in low for k in ('rock','boulder','pebble','shrub','bush','fern','clump','grass_clump')):
            cands.append(str(a.package_name))
            if len(cands) >= 30:
                break
    if len(cands) >= 30:
        break
out['mesh_cands'] = cands[:30]
print('P1PROBE', json.dumps(out)[:8000])
