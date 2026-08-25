#!/usr/bin/env python3
"""Closed-editor Lane A guard for SK_Melusina_Skeleton.

Reject meter-scale or dotted-name FBX on the live skeleton. Lane A has no
retargeter. New ARP/Blender/Cascadeur sources fail on four independent axes
(dots vs underscores, 432/463 vs 465 bones, meters vs cm, 24 vs 30 fps).

Mocap works because it never imports onto SK_Melusina:
  Rokoko -> SK_MocapSource -> IK_MocapSource -> RTG_Mocap_to_Melusina
  -> IK_Melusina_Body -> A_Mocap_*
  Docs/ROKOKO_MELUSINA_MOCAP.md

Split meshes: re-skin onto SK_Melusina_Skeleton and leader-pose via
MelodiaWardrobe. Do not use V2Test ARP static pieces for gameplay.
  Docs/MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md

This module does not import Unreal or Blender. Run:

    python Tools/melusina_anim_unit_guard.py --inbox
    python Tools/melusina_anim_unit_guard.py --fbx path/to/clip.fbx
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = PROJECT_DIR / "Imports" / "Animations" / "Cascadeur" / "Inbox"
DEFAULT_REPORT = PROJECT_DIR / "Saved" / "Audit" / "melusina_anim_unit_guard.json"

TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
MOCAP_SPINE_Y_CM = -12.838751792907715
BLENDER_SPINE_Y_M = -0.12838755548000336
CM_ABS_MIN = 5.0
METER_ABS_MIN = 0.01
METER_ABS_MAX = 2.0

FORBIDDEN_SKELETON_MARKERS = (
    "ual1",
    "quaternius",
    "sk_source_melusina",
    "ual1_standard_skeleton",
)
FORBIDDEN_SOURCE_MARKERS = (
    "quaternius",
    "ual1",
    "universal animation library",
)

LIVE_BONE_COUNT = 465
LIVE_FPS = 30

DOTTED_BONE_MARKERS = (
    b"DEF_eye.L",
    b"DEF_eye.R",
    b"c_kilt_master.x",
    b"c_hand_ik.l",
    b"c_spine_02.x",
    b"c_root.x",
)
UNDERSCORE_CONTRACT_MARKERS = (
    b"DEF_eye_L",
    b"c_kilt_master_x",
    b"c_hand_ik_l",
    b"c_spine_02_x",
)

AUTHOR_HINT = (
    "Do not import this FBX onto SK_Melusina_Skeleton (Lane A, no retargeter). "
    "Animation: Rokoko -> SK_MocapSource -> IK_MocapSource -> RTG_Mocap_to_Melusina "
    "-> IK_Melusina_Body -> A_Mocap_* (Docs/ROKOKO_MELUSINA_MOCAP.md). "
    "Split meshes: re-skin to SK_Melusina_Skeleton (465, underscore, cm) and "
    "leader-pose via MelodiaWardrobe - not V2Test ARP statics "
    "(Docs/MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md)."
)

# Blender FBX: 1 scene unit = 1 m writes UnitScaleFactor 100 (cm per unit).
# remap_arp_fbx_to_ue.py global_scale=100 then writes ~10000. Unreal still
# stored meter keys; header scale is a warning, not proof of cm tracks.
BLENDER_METER_UNIT_SCALE = 100.0
REMAPPED_METER_UNIT_SCALE = 10000.0


def classify_spine_translation(y: float | None) -> str:
    """Classify a local-space spine translation as cm, meters, zero, or unknown."""
    if y is None:
        return "unknown"
    try:
        mag = abs(float(y))
    except (TypeError, ValueError):
        return "unknown"
    if mag < 1e-6:
        return "zero"
    if mag >= CM_ABS_MIN:
        return "cm"
    if METER_ABS_MIN <= mag <= METER_ABS_MAX:
        return "meters"
    return "unknown"


def spine_matches_mocap_cm(y: float | None, tolerance: float = 1.0) -> bool:
    if y is None:
        return False
    try:
        return abs(float(y) - MOCAP_SPINE_Y_CM) <= tolerance
    except (TypeError, ValueError):
        return False


def find_sidecar(fbx_path: Path) -> Path | None:
    """Accept either foo.json or foo.manifest.json next to an FBX."""
    candidates = (
        fbx_path.with_suffix(".json"),
        fbx_path.with_name(fbx_path.stem + ".manifest.json"),
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def read_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "manifest root must be a JSON object"
    return value, None


def _haystack(manifest: dict[str, Any]) -> str:
    parts = [
        str(manifest.get("expected_skeleton") or ""),
        str(manifest.get("source_name") or ""),
        str(manifest.get("clip_id") or ""),
        str(manifest.get("clip_name") or ""),
    ]
    return " ".join(parts).lower()


def live_skeleton_preflight(bone_names: list[str]) -> dict[str, Any]:
    """Prep check for character_rig / wardrobe export. No Unreal import."""
    dotted = [name for name in bone_names if "." in name]
    count = len(bone_names)
    errors: list[str] = []
    if dotted:
        sample = ", ".join(dotted[:6])
        errors.append(
            f"dotted ARP names ({len(dotted)}), e.g. {sample}. "
            "Rename . -> _ onto SK_Melusina_Skeleton. Do not use V2Test ARP statics."
        )
    if count and count != LIVE_BONE_COUNT:
        errors.append(
            f"bone_count {count} != live SK_Melusina_Skeleton {LIVE_BONE_COUNT}"
        )
    return {
        "bone_count": count,
        "live_contract_bone_count": LIVE_BONE_COUNT,
        "dotted_name_count": len(dotted),
        "ok": not errors,
        "errors": errors,
        "ue_import": False,
        "rename_rule": "replace '.' with '_' (DEF_eye.L -> DEF_eye_L)",
        "unit_rule": "meters -> cm (translation ×100); do not trust FBX UnitScaleFactor alone",
        "fps_rule": f"author at {LIVE_FPS} fps or resample; 24 fps desyncs live clips",
        "plan": AUTHOR_HINT,
    }


def forbidden_lane_a_reasons(manifest: dict[str, Any] | None, fbx_name: str = "") -> list[str]:
    """Quaternius / UAL1 / wrong skeleton are not Lane A."""
    errors: list[str] = []
    blob = f"{fbx_name} {_haystack(manifest or {})}".lower()
    if any(marker in blob for marker in FORBIDDEN_SOURCE_MARKERS):
        errors.append(
            f"{fbx_name or 'clip'}: Quaternius/UAL1 is not Lane A; "
            "do not send it through import_cascadeur_animation.py"
        )
    expected = (manifest or {}).get("expected_skeleton")
    if expected and expected != TARGET_SKELETON:
        errors.append(
            f"{fbx_name or 'clip'}: expected_skeleton is {expected!r}, "
            f"not {TARGET_SKELETON!r}"
        )
    if expected and any(marker in str(expected).lower() for marker in FORBIDDEN_SKELETON_MARKERS):
        if not any("expected_skeleton" in item for item in errors):
            errors.append(
                f"{fbx_name or 'clip'}: expected_skeleton {expected!r} is not SK_Melusina"
            )
    return errors


def read_fbx_unit_scale_factor(path: Path) -> float | None:
    """Read GlobalSettings UnitScaleFactor from a binary FBX, if present."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    idx = 0
    while True:
        idx = data.find(b"UnitScaleFactor", idx)
        if idx < 0:
            return None
        if idx >= 8 and data[idx - 8 : idx] == b"Original":
            idx += len(b"UnitScaleFactor")
            continue
        window = data[idx : idx + 192]
        marker = window.find(b"double")
        if marker < 0:
            return None
        dpos = window.find(b"D", marker)
        if dpos < 0 or dpos + 9 > len(window):
            return None
        try:
            return float(struct.unpack_from("<d", window, dpos + 1)[0])
        except struct.error:
            return None


def scan_fbx_name_style(path: Path) -> dict[str, Any]:
    """Detect ARP dotted names vs live names on binary FBX Model nodes.

    Blender embeds ARP controller names in custom-property JSON. Searching the
    whole binary for those strings falsely classified otherwise normalized
    source-rig exports as mixed. Only a marker occurring in the local FBX
    ``Model`` node context is treated as a bone-name hit; arbitrary metadata is
    ignored.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return {
            "name_style": "unknown",
            "dotted_hits": [],
            "underscore_hits": [],
            "error": "unreadable",
        }
    def model_node_contains(marker: bytes) -> bool:
        start = 0
        while True:
            position = data.find(marker, start)
            if position < 0:
                return False
            # Binary FBX model records carry the model name shortly after the
            # ASCII "Model" property. ARP custom-property JSON does not.
            context_start = max(0, position - 256)
            context = data[context_start:position]
            if b"Model" in context:
                return True
            start = position + len(marker)

    dotted = [marker.decode("ascii") for marker in DOTTED_BONE_MARKERS if model_node_contains(marker)]
    underscore = [
        marker.decode("ascii") for marker in UNDERSCORE_CONTRACT_MARKERS if model_node_contains(marker)
    ]
    if dotted and not underscore:
        style = "dotted"
    elif underscore and not dotted:
        style = "underscore"
    elif dotted and underscore:
        style = "mixed"
    else:
        style = "unknown"
    return {
        "name_style": style,
        "dotted_hits": dotted,
        "underscore_hits": underscore,
    }


def lane_a_contract_errors(
    fbx_path: Path,
    manifest: dict[str, Any] | None = None,
) -> list[str]:
    """Reject meter-scale / dotted-name / Quaternius FBX on SK_Melusina_Skeleton."""
    errors: list[str] = []
    errors.extend(forbidden_lane_a_reasons(manifest, fbx_path.name))
    if not fbx_path.is_file():
        return errors
    names = scan_fbx_name_style(fbx_path)
    if names.get("name_style") in {"dotted", "mixed"}:
        hits = ", ".join(names.get("dotted_hits") or []) or "dotted ARP tokens"
        errors.append(
            f"{fbx_path.name}: dotted bone names ({hits}); live SK uses "
            f"underscores (DEF_eye_L, c_kilt_master_x). 0 bones align by name. "
            f"{AUTHOR_HINT}"
        )
    header = classify_fbx_header_units(fbx_path)
    if header.get("header_class") in {"blender_meters", "blender_meters_x100_header"}:
        errors.append(
            f"{fbx_path.name}: meter-scale FBX header ({header.get('header_class')}, "
            f"UnitScaleFactor={header.get('unit_scale_factor')}); live SK is cm. "
            f"100× collapse (idle Y ≈ -0.128 vs mocap -12.84). {AUTHOR_HINT}"
        )
    return errors


def classify_fbx_header_units(path: Path) -> dict[str, Any]:
    """Classify Blender FBX header units. Does not prove animation-track units."""
    factor = read_fbx_unit_scale_factor(path)
    report: dict[str, Any] = {
        "path": str(path),
        "unit_scale_factor": factor,
        "header_class": "unknown",
        "safe_for_sk_melusina_without_key_scale": False,
        "needs_post_import_cm_probe": True,
    }
    if factor is None:
        return report
    if abs(factor - 1.0) < 0.01:
        report["header_class"] = "centimeters"
        report["safe_for_sk_melusina_without_key_scale"] = True
        report["needs_post_import_cm_probe"] = True
        return report
    if abs(factor - BLENDER_METER_UNIT_SCALE) < 0.1:
        report["header_class"] = "blender_meters"
        return report
    if abs(factor - REMAPPED_METER_UNIT_SCALE) < 1.0:
        report["header_class"] = "blender_meters_x100_header"
        report["note"] = (
            "remap_arp_fbx_to_ue.py wrote global_scale=100 into UnitScaleFactor "
            "(~10000). Unreal still imported c_spine_02_x at meter scale; "
            "post-import key x100 is required."
        )
        return report
    report["header_class"] = "other"
    return report


def preflight_fbx(
    fbx_path: Path,
    require_sidecar: bool = True,
    lane_a: bool = True,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "fbx": str(fbx_path),
        "sidecar": None,
        "ok": False,
        "errors": [],
        "warnings": [],
        "header": None,
        "name_style": None,
        "author_hint": AUTHOR_HINT,
    }
    if not fbx_path.is_file():
        result["errors"].append(f"FBX not found: {fbx_path}")
        return result

    sidecar = find_sidecar(fbx_path)
    result["sidecar"] = str(sidecar) if sidecar else None
    manifest: dict[str, Any] | None = None
    if sidecar is None:
        message = f"No sidecar (.json or .manifest.json) for {fbx_path.name}"
        if require_sidecar:
            result["errors"].append(message)
        else:
            result["warnings"].append(message)
    else:
        manifest, read_error = read_json_object(sidecar)
        if read_error:
            result["errors"].append(f"{sidecar.name}: {read_error}")

    result["header"] = classify_fbx_header_units(fbx_path)
    result["name_style"] = scan_fbx_name_style(fbx_path)
    if lane_a:
        result["errors"].extend(lane_a_contract_errors(fbx_path, manifest))
    elif manifest is not None:
        result["errors"].extend(forbidden_lane_a_reasons(manifest, fbx_path.name))
        header_class = (result["header"] or {}).get("header_class")
        if header_class in {"blender_meters", "blender_meters_x100_header"}:
            result["warnings"].append(
                f"{fbx_path.name}: FBX header is {header_class}; "
                "do not play on SK_Melusina_Skeleton until c_spine_02_x local Y is ~-12.84"
            )

    result["ok"] = not result["errors"]
    return result


def inbox_preflight(inbox: Path | None = None, require_sidecar: bool = True) -> dict[str, Any]:
    root = Path(inbox) if inbox else DEFAULT_INBOX
    files = sorted(path for path in root.glob("*.fbx")) if root.is_dir() else []
    entries = [preflight_fbx(path, require_sidecar=require_sidecar) for path in files]
    report = {
        "schema_version": 1,
        "pipeline": "melusina_anim_unit_guard",
        "target_skeleton": TARGET_SKELETON,
        "inbox": str(root),
        "fbx_count": len(files),
        "ok": bool(files) and all(item.get("ok") for item in entries),
        "files": entries,
        "errors": [error for item in entries for error in item.get("errors", [])],
        "warnings": [warning for item in entries for warning in item.get("warnings", [])],
    }
    if not root.is_dir():
        report["errors"].append(f"Inbox does not exist: {root}")
        report["ok"] = False
    elif not files:
        report["warnings"].append(f"No FBX files in {root}")
        report["ok"] = False
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox", nargs="?", const=str(DEFAULT_INBOX), default=None)
    parser.add_argument("--fbx", action="append", default=[])
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--allow-missing-sidecar", action="store_true")
    args = parser.parse_args(argv)

    require_sidecar = not args.allow_missing_sidecar
    report: dict[str, Any] = {
        "schema_version": 1,
        "ok": True,
        "checks": [],
    }
    if args.inbox:
        inbox_report = inbox_preflight(Path(args.inbox), require_sidecar=require_sidecar)
        report["inbox"] = inbox_report
        report["ok"] = report["ok"] and bool(inbox_report.get("ok"))
    for raw in args.fbx:
        entry = preflight_fbx(Path(raw).resolve(), require_sidecar=require_sidecar)
        report["checks"].append(entry)
        report["ok"] = report["ok"] and bool(entry.get("ok"))
    if not args.inbox and not args.fbx:
        inbox_report = inbox_preflight(DEFAULT_INBOX, require_sidecar=require_sidecar)
        report["inbox"] = inbox_report
        report["ok"] = bool(inbox_report.get("ok"))

    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for entry in report.get("checks", []):
        status = "OK" if entry.get("ok") else "FAIL"
        print(f"{status}: {entry.get('fbx')}")
        for error in entry.get("errors", []):
            print(f"  ERROR: {error}")
        for warning in entry.get("warnings", []):
            print(f"  WARNING: {warning}")
    inbox = report.get("inbox")
    if inbox:
        print(
            f"Inbox {inbox.get('fbx_count', 0)} FBX: "
            f"{'OK' if inbox.get('ok') else 'FAIL'}"
        )
        for error in inbox.get("errors", [])[:12]:
            print(f"  ERROR: {error}")
        extra = max(0, len(inbox.get("errors", [])) - 12)
        if extra:
            print(f"  ... {extra} more errors")
    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
