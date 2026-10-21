"""Route (a) step 2: re-import the legal shirt FBX against the canonical skeleton.

Run this **after** the owner has added the 17 hem bones to SK_Melusina_Skeleton
(Skeletal Mesh Editor -> Skeleton Tree -> "Copy Bones From Skeleton...", picking
the source skeleton staged by Tools/Editor/stage_shirt_hem_bones.py).

It then:
  1. imports SK_Melusina_V2_Shirt_HemRig_Legal.fbx with Skeleton = SK_Melusina_Skeleton
     (now that the hem bones exist, Interchange keeps them and the hem weights land);
  2. verifies the skeleton bone count and the hem bones;
  3. removes the staging mesh and the staging skeleton;
  4. prints the remaining hand-off (wardrobe binding + Kawaii node).

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/apply_shirt_hem_bones.py"
"""
import unreal
import json

FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ShirtBones_20261020\SK_Melusina_V2_Shirt_HemRig_Legal.fbx"
DEST = "/Game/Melodia/Characters/Melusina/Outfits/V2"
SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
HEM_BONES = ["c_shirt_hem_master_x"] + \
            ["c_shirt_hem_%02d_%02d_x" % (s, l) for s in range(1, 9) for l in (1, 2)]

out = {}


def setp(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception:
        return False


def delete_asset(path):
    try:
        return bool(unreal.EditorAssetLibrary.delete_asset(path))
    except Exception as e:
        return 'err %s' % str(e)[:60]


canon = unreal.load_asset(SKEL)
out['canonical_bones_before'] = len(canon.get_editor_property('bone_tree'))

# the hem bones must already be there
try:
    paths = unreal.AnimationLibrary.find_bone_path_to_root(canon, HEM_BONES[0])
    out['hem_root_present'] = len(paths) > 0
except Exception as e:
    out['hem_root_present'] = 'err %s' % str(e)[:100]
out['hem_root_path'] = [str(p) for p in paths] if isinstance(paths, list) else None

if out.get('hem_root_present'):
    # clear any earlier import, then import against the canonical skeleton
    for a in unreal.EditorAssetLibrary.list_assets(DEST, True):
        p = str(a)
        if 'HemRig' in p and 'Skeleton' not in p:
            delete_asset(p.split('.')[0])

    opts = unreal.FbxImportUI()
    for n, v in (('import_as_skeletal', True), ('import_mesh', True), ('import_animations', False),
                 ('import_materials', False), ('import_textures', False),
                 ('automated_import_should_detect_type', False), ('create_physics_asset', False),
                 ('lod_number', 1)):
        setp(opts, n, v)
    setp(opts, 'mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    setp(opts, 'skeleton', canon)

    task = unreal.AssetImportTask()
    task.set_editor_property('filename', FBX)
    task.set_editor_property('destination_path', DEST)
    task.set_editor_property('options', opts)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    task.set_editor_property('replace_existing', False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    out['imported'] = [str(p) for p in task.get_editor_property('imported_object_paths')]

    mesh = unreal.load_asset(DEST + '/SK_Melusina_V2_Shirt_HemRig_Legal')
    if mesh:
        ms = mesh.get_editor_property('skeleton')
        out['final_mesh_skeleton'] = ms.get_path_name() if ms else None
        out['final_skeleton_bones'] = len(ms.get_editor_property('bone_tree')) if ms else None

    # drop the staging skeleton + staging mesh (the bones now live in the canonical one)
    for a in unreal.EditorAssetLibrary.list_assets(DEST, True):
        p = str(a)
        if 'HemRig' in p and ('Skeleton' in p or p.endswith('_Skeleton')):
            delete_asset(p.split('.')[0])

    out['canonical_bones_after'] = len(canon.get_editor_property('bone_tree'))
    out['saved_skeleton'] = bool(unreal.EditorAssetLibrary.save_asset(SKEL, only_if_is_dirty=False))
    out['handoff'] = [
        '1. Bind the wardrobe slot: DA_MelodiaCosmeticCatalog -> Cos_Shirt_MelusinaV2 -> SK_Melusina_V2_Shirt_HemRig_Legal',
        '2. Add a second KawaiiPhysics node on ABP_Melusina_Current rooted at c_shirt_hem_master_x '
        '(DummyBoneLength 3.0, collision DA cloned from DA_Melusina_SkirtCollisionLimits, profile '
        'damp 0.62 / stiff 0.72 / drag 0.24 / gravity 0.16 / wind 0.12 / radius 3 cm)',
        '3. PIE gate: walk/stop, arm raise, hold pose - hem lags and settles, no penetration, no thigh pull-through',
    ]
else:
    out['action'] = 'The 17 hem bones are not on SK_Melusina_Skeleton yet. Run stage_shirt_hem_bones.py first.'

unreal.log("[ShirtHemBones] " + json.dumps(out))
print('APPLY=' + json.dumps(out, indent=1, default=str))
