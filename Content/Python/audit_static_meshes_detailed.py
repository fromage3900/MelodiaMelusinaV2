import unreal, sys, json
L = unreal.log_warning

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
all_assets = ar.get_all_assets()

# Get all StaticMesh assets under /Game (project content only)
sm = [a for a in all_assets if 'StaticMesh' in str(a.asset_class_path) and 'StaticMeshActor' not in str(a.asset_class_path) and str(a.package_path).startswith('/Game') and not '__ExternalActors__' in str(a.package_path) and not '__ExternalObjects__' in str(a.package_path)]
L('Project StaticMesh: {}'.format(len(sm)))

# Group by subfolder
from collections import Counter
subfolders = Counter()
for a in sm:
    pp = str(a.package_path)
    parts = pp.split('/')
    if len(parts) >= 3:
        sub = '/'.join(parts[:3])
    else:
        sub = pp
    subfolders[sub] += 1

L('By subfolder:')
for f, n in subfolders.most_common():
    L('  {}: {}'.format(f, n))

# Now deeply check broken references in project meshes
L('')
L('=== DEEP BROKEN REF SCAN ===')
broken_by_folder = {}
for ad in sm:
    try:
        m = ad.get_asset()
        slots = m.get_editor_property('static_materials')
        for s in slots:
            mi = s.get_editor_property('material_interface')
            if mi is None:
                sn = str(s.material_slot_name)
                pp = str(ad.package_path)
                folder = '/'.join(pp.split('/')[:3])
                if folder not in broken_by_folder:
                    broken_by_folder[folder] = []
                broken_by_folder[folder].append((str(ad.asset_name), sn))
    except:
        pass

for f, items in sorted(broken_by_folder.items()):
    L('{}: {} broken slots across {} meshes'.format(f, len(items), len(set(i[0] for i in items))))
    # Show unique material names referenced
    mats = set(i[1] for i in items)
    L('  Materials referenced: {}'.format(', '.join(sorted(mats)[:10])))
    if len(mats) > 10:
        L('  ... and {} more'.format(len(mats)-10))

# Also check: do any project meshes have MATERIAL_FUNCTION references or TEXTURE references?
# Check which meshes have materials that actually exist
L('')
L('=== CHECKING EXISTING MATERIAL PATHS IN BROKEN SLOTS ===')
eas = unreal.EditorAssetLibrary
for f, items in list(broken_by_folder.items())[:5]:
    mats = set(i[1] for i in items)
    L('Folder {} has references to:'.format(f))
    for mat_name in sorted(list(mats)[:8]):
        # Try to find this material in the same folder
        found_in_same = eas.does_asset_exist(f + '/' + mat_name)
        found_in_materials = eas.does_asset_exist(f + '/Materials/' + mat_name)
        found_anywhere = False
        for root in ['/Game/EnvSandbox/Materials', '/Game/Melodia', '/Game/Library']:
            if eas.does_asset_exist(root + '/' + mat_name):
                found_anywhere = True
                break
        L('    {}: same={}, materials_sub={}, anywhere_else={}'.format(mat_name, found_in_same, found_in_materials, found_anywhere))

L('SCAN_COMPLETE')
