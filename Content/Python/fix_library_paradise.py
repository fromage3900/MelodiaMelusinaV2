"""Fix Magician's Library + Paradise mesh material assignments.

A. Magician's Library (EnvSandbox/Library/Migrated/MagiciansLibrary + Library/Migrated):
   every SM_* with a slot on a shared fallback (MI_Universal_*) gets that slot
   assigned to the prop's own MI_M_<name> when it exists (per folder).

B. Paradise (Rooms_Paradise_* in EnvSandbox/Meshes/Environment root):
   - import the CrystalCrossroads pack textures (Atlas_01_Albedo, Atlas_01_Trans,
     Atlas_01_Glass, Seam_Floor_Albedo, Seam_Sand_Albedo, Seam_Shadows_01) into
     /Game/EnvSandbox/Textures/CrystalCrossroads/
   - route Albedo on the pack MICs (Atlas_01_Mat, Atlas_01_Trans_Mat, Outliner_Mat,
     Shadows_Mat, Seam_Floor_Mat, Seam_Sand_Mat) from those textures + TextureWeight=1.0
   - reassign every Rooms_Paradise_* mesh slot from the shared pack MI to its
     slot-named pack material (Atlas_01_Mat, Atlas_01_Trans_Mat, Outliner_Mat,
     Shadows_Mat, Seam_Floor_Mat, Seam_Sand_Mat)

Writes Saved/Audit/fix_library_paradise.json (--dry-run safe).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
PACK_TEX_SRC = ROOT / "Imports" / "Environment" / "CrystalCrossroads_PolygonalMind" / "extracted" / "Textures"
PACK_TEX_DEST = "/Game/EnvSandbox/Textures/CrystalCrossroads"
OUT = ROOT / "Saved" / "Audit" / "fix_library_paradise.json"

LIB_ROOTS = [
    "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "/Game/Library/Migrated/MagiciansLibrary",
]

PARADISE_MATS = {
    "Atlas_01_Mat": "T_Atlas_01_Albedo",
    "Atlas_01_Trans_Mat": "T_Atlas_01_Trans",
    "Outliner_Mat": "T_Atlas_01_Albedo",
    "Shadows_Mat": "T_Seam_Shadows_01",
    "Seam_Floor_Mat": "T_Seam_Floor_Albedo",
    "Seam_Sand_Mat": "T_Seam_Sand_Albedo",
}

PACK_TEX = {
    "T_Atlas_01_Albedo": "Atlas_01_Albedo.png",
    "T_Atlas_01_Trans": "Atlas_01_Trans.tif",
    "T_Atlas_01_Glass": "Atlas_01_Glass.tif",
    "T_Atlas_01_Glass_emissive": "Atlas_01_Glass_emissive.png",
    "T_Seam_Floor_Albedo": "Seam_Floor_Albedo.tif",
    "T_Seam_Sand_Albedo": "Seam_Sand_Albedo.png",
    "T_Seam_Shadows_01": "Seam_Shadows_01.tif",
}


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    lib = unreal.MaterialEditingLibrary
    rows = []

    # ---- A. Magician's Library ----
    mag_assigned = mag_missing = 0
    for root in LIB_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if "/StaticMeshes/" in path or not path.rsplit("/", 1)[-1].startswith("SM_"):
                continue
            mesh = unreal.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                continue
            prop_dir = path.rsplit("/", 1)[0]
            stem = path.rsplit("/", 1)[-1].split(".", 1)[0]
            # candidate per-prop MI: same stem, or M_<stem> prefixed MI
            candidates = [f"{prop_dir}/MI_{stem}", f"{prop_dir}/MI_M_{stem.removeprefix('SM_')}"]
            target = next((c for c in candidates if unreal.EditorAssetLibrary.does_asset_exist(c)), None)
            if not target:
                # try any MI_M_* in the folder
                for cand in unreal.EditorAssetLibrary.list_assets(prop_dir, recursive=False, include_folder=False):
                    if cand.rsplit("/", 1)[-1].startswith("MI_M_"):
                        target = cand
                        break
            if not target and root.startswith("/Game/Library/"):
                # Library/ tree has no MIs -> fall back to the EnvSandbox migrated copy
                env_cands = [f"/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/{prop_dir.rsplit('/',1)[-1]}/MI_{stem}",
                             f"/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/{prop_dir.rsplit('/',1)[-1]}/MI_M_{stem.removeprefix('SM_')}"]
                target = next((c for c in env_cands if unreal.EditorAssetLibrary.does_asset_exist(c)), None)
                if not target:
                    folder = f"/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/{prop_dir.rsplit('/',1)[-1]}"
                    if unreal.EditorAssetLibrary.does_directory_exist(folder):
                        for cand in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
                            if cand.rsplit("/", 1)[-1].startswith("MI_M_"):
                                target = cand
                                break
            if not target:
                mag_missing += 1
                continue
            changed = []
            for i, s in enumerate(mesh.static_materials or []):
                cur = str(s.material_interface.get_path_name()) if s.material_interface else ""
                if "MI_Universal" in cur or "ImportedPacks/MI_Env" in cur:
                    if not dry:
                        mesh.set_material(i, unreal.load_asset(target))
                    changed.append({"slot": i, "name": str(s.material_slot_name), "to": target})
                    mag_assigned += 1
            if changed:
                if not dry:
                    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
                rows.append({"kind": "magician", "mesh": path, "changes": changed})

    # ---- B. Paradise ----
    imported_tex = {}
    if not dry:
        for tex_name, src_name in PACK_TEX.items():
            src = PACK_TEX_SRC / src_name
            if not src.exists():
                continue
            dest = f"{PACK_TEX_DEST}/{tex_name}"
            if unreal.EditorAssetLibrary.does_asset_exist(dest):
                imported_tex[tex_name] = dest
                continue
            task = unreal.AssetImportTask()
            task.set_editor_property("automated", True)
            task.set_editor_property("filename", str(src))
            task.set_editor_property("destination_path", PACK_TEX_DEST)
            task.set_editor_property("destination_name", tex_name)
            task.set_editor_property("replace_existing", False)
            task.set_editor_property("save", False)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            if unreal.EditorAssetLibrary.does_asset_exist(dest):
                imported_tex[tex_name] = dest
    else:
        imported_tex = {t: f"{PACK_TEX_DEST}/{t}" for t in PACK_TEX}

    # route pack MICs
    mic_routed = 0
    if not dry:
        for mat_name, tex_name in PARADISE_MATS.items():
            tex_path = imported_tex.get(tex_name)
            if not tex_path:
                continue
            mat = unreal.load_asset(f"/Game/EnvSandbox/Meshes/Environment/{mat_name}")
            if not isinstance(mat, unreal.MaterialInstanceConstant):
                continue
            tex = unreal.load_asset(tex_path)
            lib.set_material_instance_texture_parameter_value(mat, "Albedo", tex)
            lib.set_material_instance_scalar_parameter_value(mat, "TextureWeight", 1.0)
            unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
            mic_routed += 1

    # reassign paradise meshes
    par_assigned = par_missing = 0
    for p in sorted(ENV_DIR.glob("Rooms_Paradise*.uasset")):
        game = "/Game/EnvSandbox/Meshes/Environment/" + p.stem
        mesh = unreal.load_asset(game)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        changed = []
        for i, s in enumerate(mesh.static_materials or []):
            slot_name = str(s.material_slot_name)
            cur = str(s.material_interface.get_path_name()) if s.material_interface else ""
            target_mat = slot_name if slot_name in PARADISE_MATS else None
            if target_mat:
                target = f"/Game/EnvSandbox/Meshes/Environment/{target_mat}"
                if cur.startswith(target.split(".")[0]):
                    continue
                if not dry:
                    mesh.set_material(i, unreal.load_asset(target))
                changed.append({"slot": i, "name": slot_name, "to": target})
                par_assigned += 1
            else:
                par_missing += 1
        if changed:
            if not dry:
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
            rows.append({"kind": "paradise", "mesh": game, "changes": changed})

    report = {
        "generated": "2026-08-13",
        "dry_run": dry,
        "rows": rows,
        "summary": {
            "magician_assigned": mag_assigned,
            "magician_missing": mag_missing,
            "paradise_mic_routed": mic_routed,
            "paradise_assigned": par_assigned,
            "paradise_missing": par_missing,
        },
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
