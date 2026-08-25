"""Filesystem catalog for the Melusina Universal Animation Library."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from manifest_v2 import (
    CANONICAL_RIG,
    CANONICAL_SKELETON_PATH,
    RETARGET_PROFILE,
    TARGET_SKELETON_PATH,
    TARGET_MESH_PATH,
    deterministic_clip_id,
    read_json,
    to_v2_manifest,
)


REGISTRY_SCHEMA = "MUAL-2"


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sidecar_for(fbx: Path) -> Path | None:
    for candidate in (fbx.with_suffix(".manifest.json"), fbx.with_suffix(".json")):
        if candidate.is_file():
            return candidate
    return None


def _status_for_path(path: Path, raw: dict[str, Any], source_type: str) -> tuple[str, list[str]]:
    lower = path.as_posix().lower()
    if "a_melusina_idle_v22_arp" in lower:
        return "legacy", [
            "ARP pre-retarget export intermediate; retain the v22 stage receipt but do not treat this FBX as a UE clip",
        ]
    if "a_melusina_idle_v22" in lower:
        return "manual_required", [
            "authoritative v22 hand-keyed ARP export; import onto SK_Source_Melusina and pass the dedicated source-to-target IK retarget gate before canonical status",
        ]
    if "a_bl_source_idle_loop" in lower or "mual_target" in lower:
        return "blocked", [
            "rejected 2026-08-24: existing MUAL UE derivative is static bind pose at every sampled frame; it is not source-lineage evidence",
        ]
    if ".arp" in path.stem.lower():
        return "legacy", ["ARP operator audit intermediate; only the sibling v2 artifact enters the canonical lane"]
    if "/inbox/" in lower and ("quaternius" in lower or "ual1" in json.dumps(raw).lower()):
        return "manual_required", ["Quaternius/UAL1 must pass manual Cascadeur retarget, contact cleanup, and polish"]
    if "ual1_standard" in lower or "/quaternius/" in lower:
        return "manual_required", ["foreign source is preserved as a Cascadeur handoff input"]
    if path.name.lower().endswith("_raw.fbx") or source_type == "blender" and "raw" in path.stem.lower():
        return "blocked", ["raw Blender FBX is meter-scale/dotted and cannot enter the canonical lane"]
    if source_type == "blender" and "_cm" in path.stem.lower():
        return "legacy", ["centimetre export is a direct-target rollback artifact; it is not source-rig tagged"]
    if "cascadeur_target" in path.stem.lower():
        return "legacy", ["target reference FBX is a handoff reference, not an animation clip"]
    return ("manual_required", ["new source requires explicit canonical-manifest evidence"] if source_type in {"cascadeur", "foreign"} else ["catalogued until v2 source-rig evidence is attached"])


def _entry_for_fbx(path: Path, project_root: Path) -> dict[str, Any]:
    sidecar = _sidecar_for(path)
    raw: dict[str, Any] = {}
    sidecar_error = None
    if sidecar:
        try:
            raw = read_json(sidecar)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            sidecar_error = str(exc)
    source_type = str(raw.get("source_type") or "")
    provisional = to_v2_manifest(raw, _relative(path, project_root))
    source_type = provisional["source_type"]
    status, reasons = _status_for_path(path, raw, source_type)
    if sidecar_error:
        status = "blocked"
        reasons = [f"sidecar parse failed: {sidecar_error}"]
    elif raw.get("schema_version") == 2 and status not in {"blocked", "legacy"}:
        status = str(raw.get("status") or status)
        reasons = list(raw.get("status_reasons") or reasons)
    manifest = to_v2_manifest({**raw, "status": status, "status_reasons": reasons}, _relative(path, project_root), status=status)
    entry = {
        "clip_id": manifest["clip_id"],
        "clip_name": manifest["clip_name"],
        "source_type": manifest["source_type"],
        "artifact": _relative(path, project_root),
        "sidecar": _relative(sidecar, project_root) if sidecar else None,
        "status": manifest["status"],
        "reasons": manifest["status_reasons"],
        "manifest": manifest,
        "artifact_bytes": path.stat().st_size,
        "artifact_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }
    if path.stem.lower() == "a_melusina_idle_v22":
        entry["lineage"] = {
            "authority_receipt": "Saved/Audit/melusina_idle_v22_export.json",
            "stage_blend": "G:/EnvironmentPortfolio/BS_GodFile/Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend",
            "armature": "character_rig",
            "nla_track": "idle_animation",
            "strip": "characteridle_handkeyframed",
            "action": "character_rigAction",
            "frame_range": [8, 31],
            "ue_import": False,
            "requires_ik_retarget": True,
        }
    return entry


def _entry_for_ue_source(path: Path, project_root: Path) -> dict[str, Any]:
    clip_name = path.stem
    source_name = f"UE source control case: {clip_name}"
    manifest = to_v2_manifest(
        {
            "schema_version": 2,
            "clip_name": clip_name,
            "source_name": source_name,
            "source_type": "ue_source",
            "canonical_rig": CANONICAL_RIG,
            "status": "canonical",
            "fps": 30,
            "units": "cm",
            "frame_start": 0,
            "frame_end": 0,
            "loop": True,
            "root_motion": "in_place",
            "context": "locomotion",
            "consumer": "blendspace",
            "status_reasons": ["existing source animation is retained as the UE control case"],
        },
        _relative(path, project_root),
        status="canonical",
    )
    return {
        "clip_id": manifest["clip_id"],
        "clip_name": clip_name,
        "source_type": "ue_source",
        "artifact": _relative(path, project_root),
        "sidecar": None,
        "status": "canonical",
        "reasons": manifest["status_reasons"],
        "manifest": manifest,
        "artifact_bytes": path.stat().st_size,
        "artifact_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def catalog(project_root: Path) -> dict[str, Any]:
    """Catalog FBX handoffs plus existing UE source animations without editing them."""

    roots = [
        project_root / "Imports/Animations/Cascadeur/Inbox",
        project_root / "Imports/Animations/Cascadeur/Source",
        project_root / "Imports/Animations/Cascadeur/Takes",
        project_root / "Exports/MelusinaAnim",
        project_root / "Exports/MelusinaAnims",
        project_root / "Exports/AnimationLibrary",
    ]
    entries: list[dict[str, Any]] = []
    for root in roots:
        if root.is_dir():
            entries.extend(_entry_for_fbx(path, project_root) for path in sorted(root.rglob("*.fbx")))
    source_root = project_root / "Content/Melodia/Mocap/Source/Anims"
    if source_root.is_dir():
        entries.extend(_entry_for_ue_source(path, project_root) for path in sorted(source_root.glob("*.uasset")))
    entries.sort(key=lambda entry: entry["clip_id"])
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    return {
        "registry_schema": REGISTRY_SCHEMA,
        "library": "Melusina Universal Animation Source Library",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract": {
            "canonical_rig": CANONICAL_RIG,
            "canonical_skeleton": CANONICAL_SKELETON_PATH,
            "target_skeleton": TARGET_SKELETON_PATH,
            "target_mesh": TARGET_MESH_PATH,
            "retarget_profile": RETARGET_PROFILE,
            "fps": 30,
            "units": "cm",
            "format": "animation-only FBX, one clip per file",
        },
        "counts": counts,
        "entries": entries,
    }


def write_registry(project_root: Path, output: Path | None = None) -> Path:
    output = output or project_root / "generated/melusina_animation_library.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog(project_root), indent=2) + "\n", encoding="utf-8")
    return output
