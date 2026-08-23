"""Prepare or explicitly import a Melusina offline world-gen bundle.

Safe offline check::

    python Content/Python/import_melusina_offline_world.py \
        --bundle Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900/bundle.json \
        --dry-run \
        --report Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900/ue_import_plan.json

UE apply (only from a healthy serialized editor session)::

    py Content/Python/import_melusina_offline_world.py -- \
        --bundle <bundle.json> --apply

The default is dry-run.  ``--apply`` imports one explicit static FBX only; it
does not spawn actors, apply PCG, edit maps, or write gameplay/save state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_DESTINATION_TOKENS = (
    "rendertests",
    "l_wp_sakuradream",
    "headquarters bfg",
    "my-site-clean",
)
EXPECTED_BUNDLE_FORMAT = "melodia_melusina_offline_world_bundle"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_bundle(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("bundle root is not an object")
    return value


def build_import_plan(bundle_path: str | Path) -> dict[str, Any]:
    bundle_file = Path(bundle_path).resolve()
    errors: list[str] = []
    if not bundle_file.is_file():
        return {
            "format": "melodia_melusina_offline_world_import_plan",
            "schema_version": 1,
            "ok": False,
            "bundle": str(bundle_file),
            "errors": [f"bundle is missing: {bundle_file}"],
        }

    try:
        bundle = _load_bundle(bundle_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "format": "melodia_melusina_offline_world_import_plan",
            "schema_version": 1,
            "ok": False,
            "bundle": str(bundle_file),
            "errors": [f"bundle could not be read: {exc}"],
        }

    if bundle.get("format") != EXPECTED_BUNDLE_FORMAT:
        errors.append("unexpected offline world bundle format")
    if bundle.get("ok") is not True:
        errors.append("offline world bundle is not validated")
    boundary = bundle.get("runtime_boundary", {})
    for key in ("offline_only", "does_not_call_unreal", "does_not_write_gameplay_save", "does_not_modify_protected_maps"):
        if boundary.get(key) is not True:
            errors.append(f"bundle boundary is not true: {key}")

    ue_import = bundle.get("ue_import", {})
    if ue_import.get("performed") is not False:
        errors.append("bundle must describe an unapplied UE import")
    recommended_destination = str(ue_import.get("recommended_content_path") or "")
    destination_lower = recommended_destination.lower()
    for token in FORBIDDEN_DESTINATION_TOKENS:
        if token in destination_lower:
            errors.append(f"protected destination token present: {token}")
    if not recommended_destination.startswith("/Game/"):
        errors.append("recommended destination is not a /Game path")

    fbx_record = bundle.get("artifacts", {}).get("blender_fbx") or ue_import.get("source_fbx")
    fbx_path = Path(str(fbx_record.get("path"))) if isinstance(fbx_record, dict) else Path()
    fbx_exists = fbx_path.is_file()
    if not fbx_exists:
        errors.append(f"Blender FBX is missing: {fbx_path}")
    expected_hash = fbx_record.get("sha256") if isinstance(fbx_record, dict) else None
    actual_hash = _sha256(fbx_path) if fbx_exists else None
    if expected_hash and actual_hash != expected_hash:
        errors.append("Blender FBX SHA-256 does not match the bundle")

    asset_name = fbx_path.stem if fbx_path.name else "MelodiaMIDIEnvironment"
    destination_parts = recommended_destination.rstrip("/").rsplit("/", 1)
    if destination_parts and destination_parts[-1] == asset_name:
        content_path = destination_parts[0] or "/Game"
        asset_path = recommended_destination.rstrip("/")
    else:
        content_path = recommended_destination.rstrip("/")
        asset_path = f"{content_path}/{asset_name}"
    return {
        "format": "melodia_melusina_offline_world_import_plan",
        "schema_version": 1,
        "ok": not errors,
        "bundle": str(bundle_file),
        "bundle_version": bundle.get("bundle_version"),
        "world": bundle.get("world", {}),
        "source_fbx": {
            "path": str(fbx_path),
            "exists": fbx_exists,
            "sha256": actual_hash,
            "expected_sha256": expected_hash,
        },
        "destination": {
            "content_path": content_path,
            "asset_path": asset_path,
            "asset_name": asset_name,
            "static_mesh_only": True,
            "import_animations": False,
            "import_materials": False,
            "import_textures": False,
            "replace_existing": False,
        },
        "apply": {
            "requested": False,
            "performed": False,
            "spawns_actors": False,
            "applies_pcg": False,
            "maps_touched": False,
            "gameplay_save_written": False,
        },
        "errors": errors,
    }


def _import_in_unreal(plan: dict[str, Any]) -> dict[str, Any]:
    try:
        import unreal  # type: ignore
    except Exception as exc:
        return {**plan, "ok": False, "errors": [*plan.get("errors", []), f"unreal module unavailable: {exc}"]}

    source = plan["source_fbx"]["path"]
    destination = plan["destination"]["content_path"]
    asset_name = plan["destination"]["asset_name"]
    asset_path = plan["destination"]["asset_path"]
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return {**plan, "ok": False, "errors": [*plan.get("errors", []), f"destination already exists: {asset_path}"]}

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", False)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    static_data = options.get_editor_property("static_mesh_import_data")
    if static_data:
        static_data.set_editor_property("combine_meshes", True)
        static_data.set_editor_property("auto_generate_collision", True)
        static_data.set_editor_property("convert_scene", True)
        static_data.set_editor_property("force_front_x_axis", False)
        static_data.set_editor_property("import_uniform_scale", 1.0)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    ok = bool(imported) or bool(unreal.EditorAssetLibrary.load_asset(asset_path))
    return {
        **plan,
        "ok": ok,
        "errors": [] if ok else [*plan.get("errors", []), "UE import returned no asset"],
        "imported_object_paths": imported,
        "apply": {
            **plan["apply"],
            "requested": True,
            "performed": ok,
        },
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the import plan without Unreal")
    parser.add_argument("--apply", action="store_true", help="Import the single FBX inside Unreal Editor")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.dry_run and args.apply:
        print("ERROR: choose --dry-run or --apply, not both", file=sys.stderr)
        return 2
    plan = build_import_plan(args.bundle)
    if args.apply and plan.get("ok"):
        plan = _import_in_unreal(plan)
    plan["generated_at"] = datetime.now(timezone.utc).isoformat()
    plan["apply"]["requested"] = bool(args.apply)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": plan.get("ok"),
        "bundle": plan.get("bundle"),
        "source_fbx": plan.get("source_fbx", {}).get("path"),
        "destination": plan.get("destination", {}).get("asset_path"),
        "apply_requested": plan.get("apply", {}).get("requested"),
        "apply_performed": plan.get("apply", {}).get("performed"),
        "maps_touched": plan.get("apply", {}).get("maps_touched"),
        "errors": plan.get("errors", []),
    }, indent=2))
    return 0 if plan.get("ok") else 1


if __name__ == "__main__":
    raw = sys.argv[1:]
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    raise SystemExit(main(raw))
