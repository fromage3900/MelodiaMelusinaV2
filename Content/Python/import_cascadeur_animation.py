"""Import Cascadeur body animations directly onto Melusina's production skeleton.

Lane A does NOT retarget. FBX must already match SK_Melusina_Skeleton
(465 bones, underscore names, centimeters, 30 fps). Meter-scale or dotted-name
ARP/Blender FBX is rejected by Tools/melusina_anim_unit_guard.py.

Animation that is not already on that skeleton must use the mocap chain:
  Rokoko → SK_MocapSource → IK_MocapSource → RTG_Mocap_to_Melusina
  → IK_Melusina_Body → A_Mocap_*
  Docs/ROKOKO_MELUSINA_MOCAP.md

Do not send Quaternius UAL1 Inbox takes here. Do not import V2Test ARP statics.

Run inside the Unreal Editor Python console:

    import import_cascadeur_animation as pipeline
    report = pipeline.main()

Or run headless with Tools/run_cascadeur_import.ps1 after the editor is closed.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import unreal

_TOOLS = Path(__file__).resolve().parents[2] / "Tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from melusina_anim_unit_guard import (  # noqa: E402
    classify_spine_translation,
    find_sidecar,
    lane_a_contract_errors,
)


PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
INBOX = PROJECT_DIR / "Imports" / "Animations" / "Cascadeur" / "Inbox"
REPORT = PROJECT_DIR / "Saved" / "Audit" / "cascadeur_import_report.json"

TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
TARGET_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
OUT_DIR = "/Game/Melodia/Characters/Melusina/Animations/Cascadeur"
PREFIX = "A_CAS_Melusina_"
CONTEXT_VALUES = {"exploration", "battle", "vn", "cinematic"}
ROOT_MOTION_VALUES = {"in_place", "root_motion", "explicit_review_required"}


def _asset_path(value: Any) -> str:
    if not value:
        return ""
    try:
        return value.get_path_name().split(".", 1)[0]
    except Exception:
        return str(value).split(".", 1)[0]


def _set_if_supported(obj: Any, name: str, value: Any) -> None:
    try:
        obj.set_editor_property(name, value)
    except Exception as exc:
        unreal.log_warning(f"[Cascadeur] Could not set {name}: {exc}")


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return token or "Take"


def _stem(path: Path) -> str:
    return _safe_token(path.stem)


def _sidecar_path(fbx_path: Path) -> Path:
    found = find_sidecar(fbx_path)
    return found if found else fbx_path.with_suffix(".json")


def _read_sidecar(fbx_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    sidecar = _sidecar_path(fbx_path)
    if not sidecar.is_file():
        return None, [f"No sidecar manifest found for {fbx_path.name}"]
    try:
        value = json.loads(sidecar.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"Invalid sidecar manifest {sidecar}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"Sidecar manifest must be a JSON object: {sidecar}"]
    return value, []


def _validate_sidecar(manifest: dict[str, Any] | None, fbx_path: Path) -> list[str]:
    if manifest is None:
        return []

    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append(f"{fbx_path.name}: schema_version must be 1")

    clip_id = manifest.get("clip_id")
    if not isinstance(clip_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_]{0,63}", clip_id):
        errors.append(f"{fbx_path.name}: clip_id must be an ASCII identifier")

    context = manifest.get("context")
    if context not in CONTEXT_VALUES:
        errors.append(f"{fbx_path.name}: context must be one of {sorted(CONTEXT_VALUES)}")

    expected = manifest.get("expected_skeleton", TARGET_SKELETON)
    if expected != TARGET_SKELETON:
        errors.append(
            f"{fbx_path.name}: expected_skeleton is {expected!r}, "
            f"not {TARGET_SKELETON!r}"
        )

    fps = manifest.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        errors.append(f"{fbx_path.name}: fps must be a positive number")

    root_motion = manifest.get("root_motion", "in_place")
    if root_motion not in ROOT_MOTION_VALUES:
        errors.append(f"{fbx_path.name}: unsupported root_motion value {root_motion!r}")

    start = manifest.get("start_frame")
    end = manifest.get("end_frame")
    if not isinstance(start, int) or not isinstance(end, int) or end < start:
        errors.append(f"{fbx_path.name}: start_frame/end_frame are invalid")

    if not isinstance(manifest.get("loop"), bool):
        errors.append(f"{fbx_path.name}: loop must be boolean")

    consumer = manifest.get("consumer")
    if not isinstance(consumer, str) or not consumer:
        errors.append(f"{fbx_path.name}: consumer must be a non-empty string")

    if root_motion == "root_motion" and context in {"exploration", "battle"}:
        errors.append(f"{fbx_path.name}: exploration and battle clips must remain in_place")

    notify_contract = manifest.get("notify_contract", {})
    if not isinstance(notify_contract, dict):
        errors.append(f"{fbx_path.name}: notify_contract must be an object")
    else:
        notify_count = notify_contract.get("count", 0)
        if not isinstance(notify_count, int) or notify_count < 0:
            errors.append(f"{fbx_path.name}: notify_contract.count must be non-negative")
        if notify_count != 0:
            errors.append(f"{fbx_path.name}: gameplay notifies belong in the UE montage, not the FBX")

    return errors


def list_inbox_fbx() -> list[Path]:
    if not INBOX.is_dir():
        return []
    return sorted(path for path in INBOX.iterdir() if path.suffix.lower() == ".fbx")


def _destination_name(fbx_path: Path, manifest: dict[str, Any] | None) -> str:
    clip_id = manifest.get("clip_id") if manifest else None
    return PREFIX + _safe_token(str(clip_id or _stem(fbx_path)))


def _import_one(fbx_path: Path, manifest: dict[str, Any] | None, replace_existing: bool) -> dict[str, Any]:
    destination_name = _destination_name(fbx_path, manifest)
    entry: dict[str, Any] = {
        "fbx": str(fbx_path),
        "sidecar": str(_sidecar_path(fbx_path)) if _sidecar_path(fbx_path).is_file() else None,
        "destination_name": destination_name,
        "imported_object_paths": [],
        "skeleton": None,
        "ok": False,
        "errors": [],
        "warnings": [],
    }

    sidecar_errors = _validate_sidecar(manifest, fbx_path)
    if sidecar_errors:
        entry["errors"].extend(sidecar_errors)
        return entry
    if manifest is None:
        entry["errors"].append(
            f"No sidecar (.json or .manifest.json) for {fbx_path.name}; "
            "Inbox UAL1 takes must not import onto SK_Melusina_Skeleton"
        )
        return entry
    entry["errors"].extend(lane_a_contract_errors(fbx_path, manifest))
    if entry["errors"]:
        return entry

    skeleton = unreal.load_asset(TARGET_SKELETON)
    target_mesh = unreal.load_asset(TARGET_MESH)
    if not skeleton:
        entry["errors"].append(f"Target skeleton could not be loaded: {TARGET_SKELETON}")
        return entry
    if not target_mesh:
        entry["errors"].append(f"Target mesh could not be loaded: {TARGET_MESH}")
        return entry

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx_path))
    task.set_editor_property("destination_path", OUT_DIR)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("replace_existing", replace_existing)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("skeleton", skeleton)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    _set_if_supported(options, "skeletal_mesh", target_mesh)
    task.set_editor_property("options", options)

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    except Exception as exc:
        entry["errors"].append(f"FBX import raised an exception: {exc}")
        return entry

    imported = task.get_editor_property("imported_object_paths") or []
    entry["imported_object_paths"] = [str(path) for path in imported]
    if not imported:
        entry["errors"].append("FBX import returned no imported object paths")
        return entry

    animation_paths = [str(path).split(".", 1)[0] for path in imported]
    sequence_path = animation_paths[0]
    sequence = unreal.EditorAssetLibrary.load_asset(sequence_path)
    if not sequence:
        entry["errors"].append(f"Imported animation could not be loaded: {sequence_path}")
        return entry

    actual_skeleton = _asset_path(_get_property(sequence, "skeleton"))
    entry["skeleton"] = actual_skeleton
    if actual_skeleton != TARGET_SKELETON:
        entry["errors"].append(
            f"Imported animation uses {actual_skeleton or '<none>'}; expected {TARGET_SKELETON}"
        )
        return entry

    entry["sequence_length_seconds"] = _number_property(sequence, "sequence_length")
    entry["rate_scale"] = _number_property(sequence, "rate_scale")
    entry["frame_count"] = _number_method(sequence, "get_number_of_frames")
    unit = _probe_import_units(sequence)
    entry["unit"] = unit
    if unit.get("class") == "meters":
        entry["errors"].append(
            f"Meter-scale tracks on cm skeleton (c_spine_02_x Y={unit.get('spine_y')}). "
            "Rejecting; do not play this clip on SK_Melusina."
        )
        return entry
    entry["ok"] = True
    return entry


def _probe_import_units(sequence: Any) -> dict[str, Any]:
    try:
        pose = unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, "c_spine_02_x", 0, False)
        y = float(pose.translation.y)
    except Exception as exc:
        return {"class": "unknown", "spine_y": None, "warn": str(exc)}
    return {"class": classify_spine_translation(y), "spine_y": y}


def _get_property(obj: Any, name: str) -> Any:
    try:
        return obj.get_editor_property(name)
    except Exception:
        return None


def _number_property(obj: Any, name: str) -> float | None:
    value = _get_property(obj, name)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _number_method(obj: Any, name: str) -> int | None:
    method = getattr(obj, name, None)
    if not callable(method):
        return None
    try:
        return int(method())
    except (TypeError, ValueError, RuntimeError):
        return None


def _write_report(report: dict[str, Any]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Cascadeur] Wrote import report: {REPORT}")


def main(fbx_paths: list[str] | None = None, replace_existing: bool | None = None) -> dict[str, Any]:
    paths = [Path(path).resolve() for path in fbx_paths] if fbx_paths else list_inbox_fbx()
    if replace_existing is None:
        replace_existing = os.environ.get("CASCADEUR_REPLACE_EXISTING", "0") == "1"

    report: dict[str, Any] = {
        "schema_version": 1,
        "pipeline": "cascadeur_direct_skeleton",
        "target_skeleton": TARGET_SKELETON,
        "target_mesh": TARGET_MESH,
        "output_directory": OUT_DIR,
        "replace_existing": bool(replace_existing),
        "fbx_count": len(paths),
        "imports": [],
        "ok": False,
    }

    if not paths:
        report["warnings"] = [f"No FBX files found in {INBOX}"]
        _write_report(report)
        unreal.log_warning(f"[Cascadeur] No FBX files found in {INBOX}")
        return report

    for fbx_path in paths:
        if not fbx_path.is_file():
            report["imports"].append({"fbx": str(fbx_path), "ok": False, "errors": ["File not found"]})
            continue
        manifest, manifest_warnings = _read_sidecar(fbx_path)
        entry = _import_one(fbx_path, manifest, bool(replace_existing))
        entry["warnings"].extend(manifest_warnings)
        report["imports"].append(entry)

    report["ok"] = bool(report["imports"]) and all(item.get("ok") for item in report["imports"])
    _write_report(report)
    unreal.log(
        f"[Cascadeur] Direct imports: {sum(1 for item in report['imports'] if item.get('ok'))}/"
        f"{len(report['imports'])} valid"
    )
    if not report["ok"]:
        unreal.log_error("[Cascadeur] One or more imports failed. No retarget was attempted.")
    return report


if __name__ == "__main__":
    main()
