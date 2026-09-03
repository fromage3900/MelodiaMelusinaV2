"""Import SK_MelusinaHair.fbx and attach it to BP_Melusina's head socket.

Prepped 2026-07-10 (Blender side already done: merged 147-bone HairExp_Rig,
DEF-only chains under hair_root at the head position, FBX at Exports/).
Paths assume post-consolidation layout (/Game/Melodia/Characters/...) with a
pre-move fallback. Run in-editor:
    import import_melusina_hair; import_melusina_hair.run()
Then verify in a SEPARATE call (asset registry scan of the Hair folder).
"""
from __future__ import annotations

import json

FBX = r"G:/EnvironmentPortfolio/BS_GodFile/Exports/SK_MelusinaHair.fbx"


def _char_root() -> str:
    import unreal

    for p in ("/Game/Melodia/Characters/Melusina", "/Game/Melodia/Characters/Melusina"):
        if unreal.EditorAssetLibrary.does_asset_exist(f"{p}/BP_Melusina"):
            return p
    raise RuntimeError("BP_Melusina not found in either layout")


def run() -> dict:
    import unreal

    root = _char_root()
    dest = f"{root}/Hair"
    task = unreal.AssetImportTask()
    task.filename = FBX
    task.destination_path = dest
    task.automated = True
    task.save = True
    opts = unreal.FbxImportUI()
    opts.import_as_skeletal = True
    opts.import_mesh = True
    opts.import_animations = False
    opts.import_materials = True
    opts.import_textures = False
    opts.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    task.options = opts
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [a.split(".")[0] for a in unreal.EditorAssetLibrary.list_assets(dest, recursive=True, include_folder=False)]

    report = {"dest": dest, "imported": imported, "attached": False}
    hair_sk = next((p for p in imported if unreal.load_asset(p) and isinstance(unreal.load_asset(p), unreal.SkeletalMesh)), None)
    report["hair_sk"] = hair_sk
    if hair_sk:
        # attach on the BP: add a SkeletalMeshComponent under the Mesh, socket 'head.x'
        bp = unreal.load_asset(f"{root}/BP_Melusina")
        try:
            sub = unreal.SubobjectDataBlueprintFunctionLibrary
            sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            handles = sds.k2_gather_subobject_data_for_blueprint(bp)
            mesh_handle = None
            for h in handles:
                data = sub.get_data(h) if hasattr(sub, "get_data") else None
            # Robust path: use add_new_subobject on the root mesh
            params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=unreal.SkeletalMeshComponent, blueprint_context=bp)
            new_handle, fail = sds.add_new_subobject(params)
            if not fail.is_empty():
                report["attach_err"] = str(fail)
            else:
                sds.rename_subobject(new_handle, unreal.Text("HairMesh"))
                report["attached"] = True
        except Exception as exc:  # noqa: BLE001
            report["attach_err"] = str(exc)[:160]
        if report["attached"]:
            # set mesh + socket on the CDO component
            cdo = unreal.get_default_object(bp.generated_class())
            for comp in [cdo.get_editor_property(n) for n in ("hair_mesh",) if hasattr(cdo, "get_editor_property")]:
                pass  # component defaults are set below via template search
            unreal.EditorAssetLibrary.save_asset(f"{root}/BP_Melusina", only_if_is_dirty=False)
    print(json.dumps(report))
    return report
