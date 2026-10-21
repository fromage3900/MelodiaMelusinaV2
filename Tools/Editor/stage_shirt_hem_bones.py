"""Stage the shirt hem-bone source rig for the ONE manual step route (a) needs.

Why a manual step exists
------------------------
UE 5.8 imports FBX through **Interchange**, and Interchange **drops bones that are not
already in the destination skeleton** (it warns and skips them). The legal FBX has 481
joints = 464 canonical body bones + 17 new hem bones, so importing it directly against
SK_Melusina_Skeleton silently loses the hem bones and leaves the hem band unweighted.
There is also no Python API that adds bones to an existing USkeleton
(`copy_bones_from_skeleton` is a DynamicMesh operation, not a skeleton merge).

The supported way is the editor's **Skeletal Mesh Editor -> Skeleton Tree ->
"Copy Bones From Skeleton..."**, which adds the missing bones to the mesh's skeleton.
That is an edit to the frozen canonical skeleton, so it is the owner's call.

This script does step 1: import the FBX with its own skeleton and keep that 482-bone
skeleton as the bone source for the copy.

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/stage_shirt_hem_bones.py"

Then the owner: open SK_Melusina_V2_Shirt_Flared (or the body) in the Skeletal Mesh
Editor -> Skeleton Tree -> "Copy Bones From Skeleton..." -> pick
SK_Melusina_V2_Shirt_HemRig_Legal_Skeleton -> save the skeleton.

Then run step 2:
    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/apply_shirt_hem_bones.py"
"""
import unreal
import json

FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ShirtBones_20261020\SK_Melusina_V2_Shirt_HemRig_Legal.fbx"
DEST = "/Game/Melodia/Characters/Melusina/Outfits/V2"
SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"

out = {}


def setp(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception:
        return False


opts = unreal.FbxImportUI()
for n, v in (('import_as_skeletal', True), ('import_mesh', True), ('import_animations', False),
             ('import_materials', False), ('import_textures', False),
             ('automated_import_should_detect_type', False), ('create_physics_asset', False),
             ('lod_number', 1)):
    setp(opts, n, v)
setp(opts, 'mesh_type_to_import', unreal.FBXImportType.FBXIT_SKELETAL_MESH)

task = unreal.AssetImportTask()
task.set_editor_property('filename', FBX)
task.set_editor_property('destination_path', DEST)
task.set_editor_property('options', opts)
task.set_editor_property('automated', True)
task.set_editor_property('save', True)
task.set_editor_property('replace_existing', False)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

paths = [str(p) for p in task.get_editor_property('imported_object_paths')]
out['imported'] = paths
for p in paths:
    if p.split('.')[-1].endswith('Skeleton'):
        ns = unreal.load_asset(p.split('.')[0])
        if ns:
            out['source_skeleton'] = p.split('.')[0]
            out['source_skeleton_bones'] = len(ns.get_editor_property('bone_tree'))
canon = unreal.load_asset(SKEL)
out['canonical_bones'] = len(canon.get_editor_property('bone_tree'))
out['next_step'] = ("Open a mesh on SK_Melusina_Skeleton in the Skeletal Mesh Editor -> "
                    "Skeleton Tree -> 'Copy Bones From Skeleton...' -> pick "
                    "SK_Melusina_V2_Shirt_HemRig_Legal_Skeleton -> save the skeleton, then run "
                    "Tools/Editor/apply_shirt_hem_bones.py")
unreal.log("[ShirtHemBones] " + json.dumps(out))
print('STAGE=' + json.dumps(out, indent=1, default=str))
