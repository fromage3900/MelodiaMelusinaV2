"""Version 2 contract and compatibility helpers for the Melusina animation library.

The v2 sidecar is deliberately stricter than the historical 1.0 sidecar.  A
legacy sidecar can be read for cataloguing, but it is never silently upgraded
to a canonical source-rig clip.  Callers must use :func:`to_v2_manifest` and
then pass the resulting artifact through the v2 preflight.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
CANONICAL_RIG = "SK_Source_Melusina"
CANONICAL_SKELETON_PATH = "/Game/Melodia/Mocap/Source/SK_Source_Melusina"
TARGET_SKELETON_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
TARGET_MESH_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
RETARGET_PROFILE = "RTG_Source_to_Melusina"

SOURCE_TYPES = {
    "cascadeur",
    "blender",
    "quaternius",
    "rokoko",
    "foreign",
    "ue_source",
}
STATUSES = {"canonical", "manual_required", "blocked", "legacy", "promoted"}
ROOT_MOTION = {"in_place", "root"}
CONSUMERS = {"blendspace", "state_machine", "montage", "additive_layer", "pose_search"}
CONTEXTS = {"locomotion", "battle", "cinematic", "additive", "emote", "dialogue", "exploration"}


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object with the BOM tolerance required for old sidecars."""

    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return value or "Unnamed"


def deterministic_clip_id(source_type: str, source_name: str, clip_name: str) -> str:
    """Return a readable, path-independent, deterministic clip identifier."""

    source = _slug(source_type).upper()
    # IDs are intentionally upper-case so the registry, JSON schema, and
    # Unreal asset names share one portable identifier alphabet.
    clip = _slug(clip_name).upper()
    digest = hashlib.sha1(
        "|".join((source_type.lower(), source_name.strip().lower(), clip_name.strip().lower())).encode("utf-8")
    ).hexdigest()[:8].upper()
    readable = f"LIB_{source}_{clip}"
    if len(readable) > 72:
        readable = f"LIB_{source}_{clip[:52].rstrip('_')}"
    return f"{readable}_{digest}"


def classify_source(source_file: str | Path = "", source_name: str = "", clip_name: str = "") -> str:
    blob = " ".join((str(source_file), source_name, clip_name)).lower().replace("\\", "/")
    if "quaternius" in blob or "ual1" in blob:
        return "quaternius"
    if "rokoko" in blob or "mocap" in blob:
        return "rokoko"
    if "blender" in blob or "/exports/melusinaanim/" in blob or clip_name.lower().startswith("a_bl_"):
        return "blender"
    if "/source/anims/" in blob or "ue_source" in blob or clip_name.lower().startswith("a_src_"):
        return "ue_source"
    if "cascadeur" in blob or clip_name.lower().startswith("a_cas_"):
        return "cascadeur"
    return "foreign"


def _infer_status(source_type: str, source_file: str, raw: dict[str, Any]) -> tuple[str, list[str]]:
    blob = f"{source_file} {raw.get('expected_skeleton', '')} {raw.get('source_name', '')}".lower()
    reasons: list[str] = []
    if source_type in {"quaternius", "foreign"} or "ual1" in blob:
        return "manual_required", ["foreign source requires the Cascadeur manual retarget/contact gate"]
    if source_type == "cascadeur" and "source_melusina" not in blob:
        return "manual_required", ["Cascadeur output is not declared as canonical source-rig output"]
    if source_type == "blender":
        if "_raw" in Path(source_file).stem.lower() or "meter" in blob:
            return "blocked", ["meter-scale or raw Blender artifact; export through the v2 source-rig exporter"]
        if "_cm" in Path(source_file).stem.lower() or "melusina_skeleton" in blob:
            return "legacy", ["direct-target Blender artifact is retained for rollback, not the universal lane"]
        return "blocked", ["Blender artifact has no proven canonical source-rig contract"]
    if source_type == "ue_source":
        return "canonical", ["existing UE source animation retained as the control case"]
    if "melusina_skeleton" in blob and "source_melusina" not in blob:
        return "legacy", ["direct target animation retained as rollback"]
    reasons.append("legacy artifact requires explicit v2 normalization evidence")
    return "legacy", reasons


def to_v2_manifest(raw: dict[str, Any], source_file: str | Path = "", *, status: str | None = None) -> dict[str, Any]:
    """Normalize a legacy sidecar or partial metadata object into a v2 record."""

    source_file_text = str(source_file).replace("\\", "/")
    clip_name = str(raw.get("clip_name") or raw.get("clip_id") or Path(source_file_text).stem)
    source_name = str(raw.get("source_name") or raw.get("provenance") or clip_name)
    source_type = str(raw.get("source_type") or classify_source(source_file_text, source_name, clip_name))
    if source_type not in SOURCE_TYPES:
        source_type = "foreign"
    inferred_status, reasons = _infer_status(source_type, source_file_text, raw)
    final_status = status or str(raw.get("status") or inferred_status)
    if final_status not in STATUSES:
        final_status = "blocked"

    fps_raw = raw.get("fps", 30)
    try:
        fps = int(fps_raw)
    except (TypeError, ValueError):
        fps = 0
    start = int(raw.get("start_frame", raw.get("frame_start", 0)) or 0)
    end = int(raw.get("end_frame", raw.get("frame_end", start)) or start)
    expected = str(raw.get("expected_skeleton") or "")
    canonical_declared = CANONICAL_RIG.lower() in expected.lower() or CANONICAL_SKELETON_PATH.lower() in expected.lower()
    canonical_rig = CANONICAL_RIG if canonical_declared else str(raw.get("canonical_rig") or "")
    units = str(raw.get("units") or raw.get("unit_system") or "cm").lower()
    if units in {"centimeters", "centimetres", "centimeter", "centimetre"}:
        units = "cm"
    context = str(raw.get("context") or "locomotion")
    if context not in CONTEXTS:
        context = "locomotion"
    consumer = str(raw.get("consumer") or ("blendspace" if context == "locomotion" else "montage"))
    if consumer not in CONSUMERS:
        consumer = "montage"
    root_motion = str(raw.get("root_motion") or "in_place")
    if root_motion not in ROOT_MOTION:
        root_motion = "in_place"

    record = {
        "schema_version": SCHEMA_VERSION,
        "clip_id": deterministic_clip_id(source_type, source_name, clip_name),
        "clip_name": clip_name,
        "display_name": str(raw.get("display_name") or clip_name),
        "source_type": source_type,
        "source_file": source_file_text,
        "source_name": source_name,
        "provenance": str(raw.get("provenance") or source_name),
        "license": str(raw.get("license") or "unknown"),
        "canonical_rig": canonical_rig,
        "canonical_skeleton": CANONICAL_SKELETON_PATH,
        "target_skeleton": TARGET_SKELETON_PATH,
        "target_mesh": TARGET_MESH_PATH,
        "retarget_profile": RETARGET_PROFILE,
        "fps": fps,
        "units": units,
        "frame_start": start,
        "frame_end": end,
        "loop": bool(raw.get("loop", False)),
        "root_motion": root_motion,
        "context": context,
        "consumer": consumer,
        "animation_only": bool(raw.get("animation_only", True)),
        "one_clip_per_file": bool(raw.get("one_clip_per_file", True)),
        "status": final_status,
        "status_reasons": list(raw.get("status_reasons") or reasons),
        "promotion_target": str(raw.get("promotion_target") or ""),
        "notify_contract": list(raw.get("notify_contract") or []),
        "foot_contact_audit": (
            dict(raw.get("foot_contact_audit"))
            if isinstance(raw.get("foot_contact_audit"), dict)
            else {"status": "pending_manual", "required_for_promotion": True}
        ),
        "speed_evidence": (
            dict(raw.get("speed_evidence"))
            if isinstance(raw.get("speed_evidence"), dict)
            else {}
        ),
    }
    if final_status == "canonical" and not canonical_rig:
        record["status"] = "blocked"
        record["status_reasons"] = ["canonical status requires canonical_rig=SK_Source_Melusina"]
    return record


def validate_v2(manifest: dict[str, Any]) -> list[str]:
    """Return deterministic contract errors; an empty list means v2-valid."""

    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be integer 2")
    for key in (
        "clip_id", "clip_name", "source_type", "source_file", "source_name",
        "provenance", "license", "canonical_rig", "status",
    ):
        if not isinstance(manifest.get(key), str) or not manifest.get(key):
            errors.append(f"{key} is required")
    clip_id = str(manifest.get("clip_id", ""))
    if clip_id and not re.fullmatch(r"LIB_[A-Z0-9_]+", clip_id):
        errors.append("clip_id must match LIB_[A-Z0-9_]+")
    if clip_id and manifest.get("source_name") and manifest.get("clip_name"):
        expected_id = deterministic_clip_id(
            str(manifest.get("source_type", "")),
            str(manifest.get("source_name", "")),
            str(manifest.get("clip_name", "")),
        )
        if clip_id != expected_id:
            errors.append("clip_id is not deterministic for source_type/source_name/clip_name")
    if manifest.get("source_type") not in SOURCE_TYPES:
        errors.append(f"source_type must be one of {sorted(SOURCE_TYPES)}")
    if manifest.get("status") not in STATUSES:
        errors.append(f"status must be one of {sorted(STATUSES)}")
    if manifest.get("fps") != 30:
        errors.append("fps must be 30")
    if manifest.get("units") != "cm":
        errors.append("units must be cm")
    if manifest.get("canonical_rig") != CANONICAL_RIG:
        errors.append("canonical_rig must be SK_Source_Melusina")
    if manifest.get("canonical_skeleton") != CANONICAL_SKELETON_PATH:
        errors.append("canonical_skeleton must reference SK_Source_Melusina")
    if manifest.get("target_skeleton") != TARGET_SKELETON_PATH:
        errors.append("target_skeleton must reference SK_Melusina_Skeleton")
    if manifest.get("target_mesh") != TARGET_MESH_PATH:
        errors.append("target_mesh must reference SK_Melusina")
    if manifest.get("retarget_profile") != RETARGET_PROFILE:
        errors.append("retarget_profile must be RTG_Source_to_Melusina")
    if manifest.get("root_motion") not in ROOT_MOTION:
        errors.append("root_motion must be in_place or root")
    if manifest.get("consumer") not in CONSUMERS:
        errors.append("consumer is not a supported UE consumer")
    if not isinstance(manifest.get("loop"), bool):
        errors.append("loop must be boolean")
    if manifest.get("animation_only") is not True:
        errors.append("animation_only must be true")
    if manifest.get("one_clip_per_file") is not True:
        errors.append("one_clip_per_file must be true")
    foot_audit = manifest.get("foot_contact_audit")
    if not isinstance(foot_audit, dict):
        errors.append("foot_contact_audit must be an object")
    elif not isinstance(foot_audit.get("status"), str) or not isinstance(foot_audit.get("required_for_promotion"), bool):
        errors.append("foot_contact_audit requires status and required_for_promotion")
    speed_evidence = manifest.get("speed_evidence", {})
    if speed_evidence is not None and not isinstance(speed_evidence, dict):
        errors.append("speed_evidence must be an object when present")
    elif isinstance(speed_evidence, dict) and speed_evidence:
        mode = speed_evidence.get("mode")
        if mode not in {"root_track", "static_pose"}:
            errors.append("speed_evidence.mode must be root_track or static_pose")
        if "speed_cm_s" in speed_evidence and speed_evidence["speed_cm_s"] is not None:
            try:
                if float(speed_evidence["speed_cm_s"]) < 0.0:
                    errors.append("speed_evidence.speed_cm_s must be non-negative")
            except (TypeError, ValueError):
                errors.append("speed_evidence.speed_cm_s must be numeric")
    try:
        start, end = int(manifest["frame_start"]), int(manifest["frame_end"])
        if start < 0 or end < start:
            errors.append("frame range is invalid")
    except (KeyError, TypeError, ValueError):
        errors.append("frame_start/frame_end must be integers with end >= start")
    return errors


def load_as_v2(path: Path, source_file: str | Path = "") -> tuple[dict[str, Any], list[str], bool]:
    """Load a sidecar, returning (manifest, errors, was_legacy)."""

    raw = read_json(path)
    if raw.get("schema_version") == SCHEMA_VERSION:
        manifest = raw
        return manifest, validate_v2(manifest), False
    manifest = to_v2_manifest(raw, source_file)
    return manifest, ["legacy sidecar schema; normalized for catalog only"], True
