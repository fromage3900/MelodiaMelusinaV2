"""Audit foot/contact evidence for one retargeted MUAL clip.

The project already ships a deterministic Monolith implementation of
``derive_foot_sync_markers``.  This wrapper uses its read-only ``dry_run``
mode, records the result, and only updates a v2 sidecar when the derived
left/right contact evidence is present and the caller explicitly passes
``--apply``.  Foreign Cascadeur inputs still require the artist gate; this
tool does not claim visual polish or replace that gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT = PIPELINE_DIR.parents[1]
TOOLS = PROJECT / "Tools"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from manifest_v2 import read_json, validate_v2  # noqa: E402
from mcp_client import monolith  # noqa: E402


DEFAULT_OUTPUT = PROJECT / "Saved/Audit/mual_foot_contact_audit.json"


class ContactAuditError(RuntimeError):
    pass


def _call(action: str, params: dict[str, Any]) -> dict[str, Any]:
    raw = monolith("animation_query", {"action": action, "params": params}, timeout=120)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise ContactAuditError(raw)
    try:
        result = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ContactAuditError(f"invalid Monolith response: {raw!r}") from exc
    if not isinstance(result, dict):
        raise ContactAuditError(f"Monolith response is not an object: {result!r}")
    if result.get("success") is False or result.get("ok") is False or result.get("error"):
        raise ContactAuditError(str(result.get("error") or result))
    return result


def _count(result: dict[str, Any], side: str) -> int:
    value = result.get(side)
    if isinstance(value, dict):
        try:
            return int(value.get("count", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def audit(
    manifest_path: Path,
    animation: str,
    output: Path,
    *,
    method: str,
    apply: bool,
    consumer: str | None = None,
    reuse_static_report: Path | None = None,
) -> int:
    manifest = read_json(manifest_path)
    errors = validate_v2(manifest)
    effective_consumer = consumer or str(manifest.get("consumer") or "")
    report: dict[str, Any] = {
        "schema": "melodia.mual_foot_contact_audit.v1",
        "manifest": str(manifest_path),
        "animation": animation.split(".", 1)[0].replace("\\", "/"),
        "method": method,
        "consumer": effective_consumer,
        "dry_run": True,
        "apply": apply,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "status": "pending",
        "errors": list(errors),
    }
    try:
        if errors:
            raise ContactAuditError("manifest v2 contract failed: " + "; ".join(errors))
        if reuse_static_report:
            reused = read_json(reuse_static_report)
            if reused.get("animation") != report["animation"]:
                raise ContactAuditError("reused contact report targets a different animation")
            if reused.get("static_pose") is not True:
                raise ContactAuditError("reused contact report is not a static-pose audit")
            result = dict(reused.get("evidence") or {})
            report["reused_from"] = str(reuse_static_report)
        else:
            result = _call(
                "derive_foot_sync_markers",
                {
                    "asset_path": report["animation"],
                    "method": method,
                    "dry_run": True,
                    "clear_existing": False,
                },
            )
        left_count = _count(result, "left")
        right_count = _count(result, "right")
        notes = [str(note) for note in (result.get("notes") or [])]
        static_pose = any("static pose" in note.lower() and "no plants" in note.lower() for note in notes)
        # A static idle has no plant transitions to mark.  It is valid for a
        # montage and for the speed-zero BlendSpace sample, but never unlocks a
        # dynamic locomotion sample.  The latter is additionally tied to an
        # explicit idle/static speed declaration so a walk cannot silently
        # masquerade as a zero-speed clip.
        static_speed_declared = (
            isinstance(manifest.get("speed_evidence"), dict)
            and manifest.get("speed_evidence", {}).get("mode") == "static_pose"
            and str(manifest.get("speed_evidence", {}).get("status", "")) in {"declared", "verified"}
        )
        static_idle_name = "idle" in str(manifest.get("clip_name", "")).lower()
        static_pose_allowed = static_pose and (
            effective_consumer == "montage"
            or (effective_consumer == "blendspace" and static_idle_name and static_speed_declared)
        )
        passed = (left_count > 0 and right_count > 0) or static_pose_allowed
        report["evidence"] = result
        report["left_count"] = left_count
        report["right_count"] = right_count
        report["static_pose"] = static_pose
        report["static_pose_allowed"] = static_pose_allowed
        report["status"] = "passed" if passed else "manual_required"
        report["ok"] = passed
        if not passed:
            report["errors"].append("both left and right foot contact evidence are required")
        if passed and apply:
            manifest["foot_contact_audit"] = {
                "status": "passed",
                "required_for_promotion": True,
                "method": result.get("source") or method,
                "left_count": left_count,
                "right_count": right_count,
                "audited_consumer": effective_consumer,
                "mode": "static_pose" if static_pose_allowed else "bilateral_contacts",
                "evidence_report": str(output),
            }
            if static_pose_allowed and effective_consumer == "blendspace":
                manifest["speed_evidence"] = {
                    "mode": "static_pose",
                    "status": "declared",
                    "speed_cm_s": 0.0,
                    "method": "static_pose_root_track_requires_ue_constancy_probe",
                    "evidence_report": str(output),
                }
            manifest_errors = validate_v2(manifest)
            if manifest_errors:
                raise ContactAuditError("updated manifest failed validation: " + "; ".join(manifest_errors))
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            report["manifest_updated"] = True
    except ContactAuditError as exc:
        report["errors"].append(str(exc))
        report["status"] = "manual_required" if "evidence" in report else "blocked"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(output), "status": report["status"], "errors": report["errors"]}, indent=2))
    return 0 if report["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--animation", required=True)
    parser.add_argument("--method", choices=("auto", "from_bones", "existing", "notifies", "contact", "phase", "footspeed"), default="auto")
    parser.add_argument("--consumer", choices=("blendspace", "montage"), help="consumer gate for static-pose clips")
    parser.add_argument("--reuse-static-report", type=Path, help="Reuse a matching prior static-pose evidence report when the UE bridge is offline.")
    parser.add_argument("--apply", action="store_true", help="write passed contact evidence into the sidecar")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    return audit(
        args.manifest.resolve(),
        args.animation,
        args.output.resolve(),
        method=args.method,
        apply=args.apply,
        consumer=args.consumer,
        reuse_static_report=args.reuse_static_report.resolve() if args.reuse_static_report else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
