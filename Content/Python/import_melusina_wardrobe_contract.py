# -*- coding: utf-8 -*-
"""Import re-skinned Melusina wardrobe pieces onto SK_Melusina_Skeleton (Lane A).

Run AFTER Tools/remap_melusina_rig_to_contract.py + Tools/export_melusina_wardrobe.py
in Blender. This is the editor-side half of the V2 split-mesh integration.

Contract (plan of record, Docs/MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md):
  - FBX must be skinned to contract bone names (465, underscore, cm).
  - Import as SKELETAL mesh with skeleton = existing SK_Melusina_Skeleton
    (options.skeleton). This binds by name — no new skeleton, no retarget,
    no redirector.
  - Verify: imported mesh bone set is a SUBSET of the contract skeleton,
    shared_bones > 0, mesh skeleton path == SK_Melusina_Skeleton.
  - Never overwrite live /Game/Melodia/Characters/Melusina/SK_Melusina.

This script only imports NEW pieces under
  /Game/Melodia/Characters/Melusina/Outfits/V2/
and writes Saved/Audit/melusina_wardrobe_contract_import.json.

Run in the editor (one editor only):
  python Content/Python/import_melusina_wardrobe_contract.py --all-v2
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = PROJECT_ROOT / "Exports" / "MelusinaClothes"
DEST_ROOT = "/Game/Melodia/Characters/Melusina/Outfits/V2"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "melusina_wardrobe_contract_import.json"
MATERIAL_MAP_PATH = PROJECT_ROOT / "specs" / "anim_presets" / "melusina_v2_material_map.json"
LIVE_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
LIVE_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
TARGET_BONE_COUNT = 465
# The finalizer writes actual centimetre coordinates.  UE's FBX conversion
# still applies the file's metre-to-centimetre conversion, so compensate once
# at import; otherwise a normal ~193 cm body arrives at ~19,300 cm.
IMPORT_UNIFORM_SCALE = 0.01
APPROVED_EXPORTERS = {
    # ARP is used for the source-stage export/preflight.  ARP's panel emits a
    # reduced M-ped table, so the final gameplay FBX is written by the native
    # Blender contract finalizer and then checked by the actual-FBX audit.
    "bpy.ops.arp.arp_export_fbx_panel+bpy.ops.export_scene.fbx(contract_finalize)",
}
V2_PIECES = ("Body", "Shirt", "Skirt", "Boots", "Accessories")
HIERARCHY_PROBES = {
    "root": None,
    "c_pos": "root",
    "c_traj": "c_pos",
    "root_x": "c_traj",
    "arm_twist_l": "arm_stretch_l",
    "arm_twist_r": "arm_stretch_r",
    "thigh_twist_l": "thigh_stretch_l",
    "thigh_twist_r": "thigh_stretch_r",
}


def _log(msg: str) -> None:
    line = f"[wardrobe-import] {msg}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def parse_args() -> tuple[str | None, bool, bool, bool]:
    args = _argv()
    outfit_id = None
    verify_only = "--verify-only" in args
    all_v2 = "--all-v2" in args
    replace_existing = "--replace-existing" in args
    if "--outfit-id" in args:
        i = args.index("--outfit-id")
        if i + 1 < len(args):
            outfit_id = args[i + 1].strip()
    return outfit_id, verify_only, all_v2, replace_existing


def contract_bone_set() -> set[str] | None:
    sk = unreal.load_asset(LIVE_SKELETON)
    if not sk:
        return None
    try:
        names = [str(n) for n in sk.get_reference_pose().get_bone_names()]
        return set(names)
    except Exception as exc:
        _log(f"WARN contract bone set: {exc}")
        return None


def referenced_skeleton_bone_set(mesh) -> set[str] | None:
    try:
        skel = mesh.get_editor_property("skeleton")
        if not skel:
            return None
        names = [str(n) for n in skel.get_reference_pose().get_bone_names()]
        return set(names)
    except Exception as exc:
        _log(f"WARN mesh bone set: {exc}")
        return None


def material_contract() -> dict:
    try:
        return json.loads(MATERIAL_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"material map unavailable: {MATERIAL_MAP_PATH}: {exc}") from exc


def material_is_rejected(name: str, reject_tokens: list[str]) -> bool:
    lowered = name.casefold()
    return any(token.casefold() in lowered for token in reject_tokens)


def mesh_material_paths(mesh) -> list[str | None]:
    result = []
    try:
        materials = list(mesh.get_editor_property("materials") or [])
    except Exception:
        return result
    for item in materials:
        try:
            material = item.get_editor_property("material_interface")
        except Exception:
            material = item
        try:
            result.append(material.get_path_name() if material else None)
        except Exception:
            result.append(None)
    return result


def apply_materials(
    mesh,
    game_path: str,
    approved_paths: list[str],
    source_materials: list[str] | None = None,
) -> list[str]:
    """Replace all imported slots with existing approved material instances."""
    errors = []
    source_materials = source_materials or []
    try:
        materials = list(mesh.get_editor_property("materials") or [])
    except Exception as exc:
        return [f"materials_read_failed_{exc}"]
    if not approved_paths:
        return ["approved_material_mapping_empty"]

    replacement_slots = []
    for index, path in enumerate(approved_paths):
        material = unreal.load_asset(path)
        if not material:
            errors.append(f"approved_material_load_failed_{path}")
            continue
        previous = materials[index] if index < len(materials) else (materials[-1] if materials else None)
        slot_name = source_materials[index] if index < len(source_materials) else f"Slot_{index}"
        uv_channel_data = None
        if previous:
            try:
                slot_name = previous.get_editor_property("material_slot_name") or slot_name
                uv_channel_data = previous.get_editor_property("uv_channel_data")
            except Exception:
                pass
        try:
            kwargs = {
                "material_interface": material,
                "material_slot_name": str(slot_name),
            }
            if uv_channel_data is not None:
                kwargs["uv_channel_data"] = uv_channel_data
            replacement_slots.append(unreal.SkeletalMaterial(**kwargs))
        except Exception as exc:
            try:
                replacement_slots.append(unreal.SkeletalMaterial(material_interface=material))
            except Exception as set_exc:
                errors.append(f"material_slot_{index}_assign_failed_{exc};{set_exc}")
    if not errors:
        try:
            mesh.set_editor_property("materials", replacement_slots)
            unreal.EditorAssetLibrary.save_asset(game_path)
        except Exception as exc:
            errors.append(f"materials_save_failed_{exc}")
    return errors


def verify_sidecar(sidecar_path: Path, contract: set[str]) -> dict:
    """Verify the exporter proved the actual mesh deform groups."""
    row = {"sidecar": str(sidecar_path), "errors": []}
    if not sidecar_path.is_file():
        row["errors"].append("missing_sidecar")
        return row
    try:
        data = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        row["errors"].append(f"sidecar_parse_failed_{exc}")
        return row
    row["exporter"] = data.get("exporter")
    row["units"] = data.get("units")
    row["cm_bake_factor"] = data.get("cm_bake_factor")
    row["export_bone_count"] = data.get("export_bone_count") or data.get("rig", {}).get("export_bone_count")
    row["actual_used_groups"] = data.get("used_deform_groups", [])
    if not row["actual_used_groups"]:
        row["actual_used_groups"] = data.get("rig", {}).get("group_reports", [{}])[0].get("used_deform_groups", [])
    if row["export_bone_count"] != TARGET_BONE_COUNT:
        row["errors"].append(f"export_bone_count_{row['export_bone_count']}")
    if str(row["exporter"] or "") not in APPROVED_EXPORTERS:
        row["errors"].append(f"unapproved_exporter_{row['exporter']}")
    if row["units"] != "centimeters_baked":
        row["errors"].append("sidecar_does_not_prove_baked_centimeters")
    if float(row["cm_bake_factor"] or 0.0) != 100.0:
        row["errors"].append("sidecar_cm_bake_factor_is_not_100")
    if set(row["actual_used_groups"]) - contract:
        row["errors"].append("unmatched_used_deform_groups")
    try:
        material_data = material_contract()
        source_materials = data.get("source_materials", [])
        row["source_materials"] = source_materials
        approved = material_data.get("approved_materials", {})
        reject_tokens = material_data.get("reject_tokens", [])
        approved_paths = []
        if not source_materials:
            row["errors"].append("missing_source_materials_proof")
        for name in source_materials:
            if not isinstance(name, str) or not name:
                row["errors"].append("null_source_material")
                continue
            if material_is_rejected(name, reject_tokens):
                row["errors"].append(f"placeholder_material_{name}")
                continue
            path = approved.get(name)
            if not path:
                row["errors"].append(f"unmapped_source_material_{name}")
                continue
            if not path.startswith("/Game/Melodia/Characters/Melusina/Materials/"):
                row["errors"].append(f"material_outside_approved_root_{path}")
            approved_paths.append(path)
        row["approved_material_paths"] = approved_paths
    except RuntimeError as exc:
        row["errors"].append(str(exc))
    row["ok"] = not row["errors"]
    return row


def verify_mesh(game_path: str, contract: set[str], sidecar_path: Path | None = None) -> dict:
    """Verify an imported piece binds to the contract skeleton by name.

    The referenced skeleton's 465-bone list is not treated as proof of the
    mesh's actual bone usage. That proof comes from the exporter sidecar.
    """
    row: dict = {"dest": game_path, "ok": False, "errors": []}
    mesh = unreal.load_asset(game_path)
    if not mesh:
        row["errors"].append("load_failed")
        return row
    row["class"] = str(mesh.get_class().get_name())
    if row["class"] != "SkeletalMesh":
        row["errors"].append(f"class_is_{row['class']}_not_skeletal")
        return row
    skel = mesh.get_editor_property("skeleton")
    skel_path = skel.get_path_name() if skel else None
    skeleton_package = str(skel_path).split(".", 1)[0] if skel_path else None
    row["skeleton"] = skel_path
    row["skeleton_package"] = skeleton_package
    if skeleton_package != LIVE_SKELETON:
        row["errors"].append(f"skeleton_is_{skel_path}_not_live")
    bones = referenced_skeleton_bone_set(mesh) or set()
    row["referenced_skeleton_bone_count"] = len(bones)
    row["unmatched_referenced_bones"] = sorted(bones - contract)
    if not bones:
        row["errors"].append("no_referenced_skeleton_bones")
    if row["unmatched_referenced_bones"]:
        row["errors"].append(f"unmatched_referenced_bones_{len(row['unmatched_referenced_bones'])}")
    hierarchy = {}
    for bone_name, expected_parent in HIERARCHY_PROBES.items():
        try:
            actual_parent = mesh.get_bone_parent(bone_name)
            actual_parent = str(actual_parent) if actual_parent is not None else None
            # Unreal's Python binding returns the root parent as the literal
            # string "None" on some UE 5.8 builds. Treat that as the same
            # no-parent value returned as Python None by other builds.
            if actual_parent == "None":
                actual_parent = None
        except Exception as exc:
            actual_parent = f"<error:{exc}>"
        hierarchy[bone_name] = {"actual": actual_parent, "expected": expected_parent}
        if actual_parent != expected_parent:
            row["errors"].append(
                f"hierarchy_{bone_name}_parent_{actual_parent}_not_{expected_parent}"
            )
    row["hierarchy_probe"] = hierarchy
    if sidecar_path:
        sidecar = verify_sidecar(sidecar_path, contract)
        row["sidecar"] = sidecar
        row["errors"].extend(sidecar.get("errors", []))
        expected_materials = sidecar.get("approved_material_paths", [])
        if expected_materials:
            row["material_paths"] = mesh_material_paths(mesh)
            if len(row["material_paths"]) < len(expected_materials):
                row["errors"].append("imported_material_slots_missing")
            else:
                for index, expected in enumerate(expected_materials):
                    if row["material_paths"][index] != expected:
                        row["errors"].append(f"material_{index}_is_{row['material_paths'][index]}_not_{expected}")
    row["ok"] = not row["errors"] and skeleton_package == LIVE_SKELETON
    return row


def import_one(
    asset_id: str,
    fbx_path: Path,
    contract: set[str],
    replace_existing: bool = False,
) -> dict:
    dest_dir = DEST_ROOT
    dest_name = f"SK_Melusina_V2_{asset_id}"
    game_path = f"{dest_dir}/{dest_name}"
    row: dict = {
        "fbx": str(fbx_path),
        "dest": game_path,
        "ok": False,
        "errors": [],
        "import_uniform_scale": IMPORT_UNIFORM_SCALE,
    }
    if not fbx_path.is_file():
        row["errors"].append("missing_fbx")
        return row
    sidecar_path = fbx_path.with_suffix(".json")
    sidecar = verify_sidecar(sidecar_path, contract)
    row["sidecar"] = sidecar
    if not sidecar.get("ok"):
        row["errors"].extend(sidecar.get("errors", []))
        return row
    if unreal.EditorAssetLibrary.does_asset_exist(game_path) and not replace_existing:
        row["skipped"] = "already_exists"
        row["ok"] = True
        row.update(verify_mesh(game_path, contract, sidecar_path))
        return row

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx_path))
    task.set_editor_property("destination_path", dest_dir)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", replace_existing)

    try:
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_as_skeletal", True)
        options.set_editor_property("import_animations", False)
        # Preserve FBX material sections/indices during import.  The created
        # material assets are temporary; every imported slot is replaced by an
        # approved existing Melusina material instance immediately afterward.
        options.set_editor_property("import_materials", True)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("automated_import_should_detect_type", False)
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        options.set_editor_property("create_physics_asset", False)
        options.set_editor_property("skeleton", unreal.load_asset(LIVE_SKELETON))
        sk = options.get_editor_property("skeletal_mesh_import_data")
        if sk:
            sk.set_editor_property("import_morph_targets", True)
            sk.set_editor_property("convert_scene", True)
            sk.set_editor_property("force_front_x_axis", False)
            sk.set_editor_property("import_uniform_scale", IMPORT_UNIFORM_SCALE)
        task.set_editor_property("options", options)
    except Exception as exc:
        row["errors"].append(f"options_failed_{exc}")

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        row["imported_paths"] = imported
        if not imported:
            row["errors"].append("import_returned_empty")
            return row
    except Exception as exc:
        row["errors"].append(str(exc))
        return row

    material_errors = apply_materials(
        unreal.load_asset(game_path), game_path,
        sidecar.get("approved_material_paths", []),
        sidecar.get("source_materials", []),
    )
    def package_path(path: str) -> str:
        # AssetImportTask reports Package.Asset while the importer inputs and
        # EditorAssetLibrary checks commonly use the package-only form.
        return str(path).split(".", 1)[0]

    approved_paths = set(sidecar.get("approved_material_paths", []))
    keep_packages = {package_path(game_path)} | {package_path(p) for p in approved_paths}
    for imported_path in row.get("imported_paths", []):
        if package_path(imported_path) in keep_packages:
            continue
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(imported_path):
                unreal.EditorAssetLibrary.delete_asset(imported_path)
        except Exception as exc:
            row["errors"].append(f"temporary_material_cleanup_failed_{imported_path}_{exc}")
    row.update(verify_mesh(game_path, contract, sidecar_path))
    if material_errors:
        row["errors"].extend(material_errors)
        row["ok"] = False
    return row


def main() -> int:
    outfit_id, verify_only, all_v2, replace_existing = parse_args()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_melusina_wardrobe_contract.py",
        "live_skeleton": LIVE_SKELETON,
        "target_bone_count": TARGET_BONE_COUNT,
        "live_mesh_untouched": LIVE_MESH,
        "ok": False,
    }
    if unreal is None:
        payload["error"] = "not_in_unreal"
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return 2
    if not outfit_id and not all_v2:
        payload["error"] = "missing_outfit_id_or_all_v2"
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return 2

    contract = contract_bone_set()
    if not contract:
        payload["error"] = f"live_skeleton_load_failed_{LIVE_SKELETON}"
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return 2
    payload["contract_bone_count"] = len(contract)

    ids = list(V2_PIECES) if all_v2 else ["".join(c if c.isalnum() or c in "-_" else "_" for c in outfit_id)]
    rows = []
    for asset_id in ids:
        fbx_path = EXPORTS_DIR / "V2" / f"SK_Melusina_V2_{asset_id}.fbx"
        game_path = f"{DEST_ROOT}/SK_Melusina_V2_{asset_id}"
        row = (
            verify_mesh(game_path, contract, fbx_path.with_suffix(".json"))
            if verify_only
            else import_one(asset_id, fbx_path, contract, replace_existing=replace_existing)
        )
        rows.append(row)

    payload["outfit_ids"] = ids
    payload["result"] = rows
    payload["ok"] = bool(rows) and all(row.get("ok") for row in rows)
    payload["note"] = (
        "V2 pieces import as separate SkeletalMeshes on the EXISTING SK_Melusina_Skeleton. "
        "No new skeleton, no retarget, no redirector. Attach via MelodiaWardrobe slot "
        "components with SetLeaderPoseComponent(bodyMesh). Live SK_Melusina untouched."
    )
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)
    _log(f"audit {AUDIT_PATH} ok={payload['ok']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
