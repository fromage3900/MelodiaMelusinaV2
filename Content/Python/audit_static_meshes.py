import unreal, sys, json
L = unreal.log_warning

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
all_assets = ar.get_all_assets()
L('Total assets: {}'.format(len(all_assets)))

# Class distribution for context
from collections import Counter
classes = Counter()
for a in all_assets:
    c = str(a.asset_class_path)
    if c.startswith('/Script/') or c.startswith('Script/'):
        classes[c.split('.')[-1]] = classes.get(c.split('.')[-1], 0) + 1

# Show all mesh-related classes
mesh_classes = [k for k in classes if 'esh' in k or 'Mesh' in k or 'Skeletal' in k]
L('Mesh classes: ' + str(mesh_classes))

# Get all StaticMesh assets (not StaticMeshActor level instances)
sm = [a for a in all_assets if 'StaticMesh' in str(a.asset_class_path) and 'StaticMeshActor' not in str(a.asset_class_path) and not 'Cached' in str(a.package_path)]
L('StaticMesh count: {}'.format(len(sm)))

# Group by root folder
folders = Counter()
for a in sm:
    pp = str(a.package_path)
    parts = pp.split('/')
    root = parts[1] if len(parts) > 1 else pp
    folders[root] += 1

L('By root folder:')
for f, n in folders.most_common():
    L('  {}: {}'.format(f, n))

# Check for broken references - load each mesh, check material slots
broken = []
fixed_total = 0
for ad in sm:
    try:
        m = ad.get_asset()
        slots = m.get_editor_property('static_materials')
        for s in slots:
            mi = s.get_editor_property('material_interface')
            if mi is None:
                sn = str(s.material_slot_name)
                pp = str(ad.package_path)
                broken.append((str(ad.asset_name), sn, pp))
    except Exception as e:
        pass

L('Meshes with broken material slots: {}'.format(len(broken)))
for name, slot, path in broken[:50]:
    L('  {} -> {} [in {}]'.format(name, slot, path))

L('SCAN_COMPLETE')
