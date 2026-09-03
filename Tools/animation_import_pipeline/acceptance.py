"""Build the reproducible MUAL pilot acceptance matrix.

This is an evidence index, not a claim generator: any missing or failed live
UE artifact remains failed, and ``overall`` stays false until staging, control
case, PIE, audits, and guarded promotions have all produced passing reports.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT = PIPELINE_DIR.parents[1]
from manifest_v2 import read_json, validate_v2  # noqa: E402


def _read(path: Path) -> dict[str, Any] | None:
    try:
        return read_json(path) if path.is_file() else None
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _file(path: Path) -> dict[str, Any]:
    return {"path": str(path), "exists": path.is_file()}


def build_matrix() -> dict[str, Any]:
    registry_path = PROJECT / "generated/melusina_animation_library.json"
    manifest_path = PROJECT / "Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.manifest.json"
    blender_scan = _read(PROJECT / "Saved/Audit/mual_blender_idle_scan_verified.json")
    blender_report = _read(PROJECT / "Saved/Audit/melusina_blender_source_idle_report.json")
    ue_report = _read(PROJECT / "Saved/Audit/melusina_ue_source_pilot.json")
    pie_report = _read(PROJECT / "Saved/Audit/mual_pie_smoke.json")
    locomotion_plan = _read(PROJECT / "Saved/Audit/mual_promotion_blender_idle.json")
    montage_plan = _read(PROJECT / "Saved/Audit/mual_promotion_blender_montage.json")
    contact_report = _read(PROJECT / "Saved/Audit/mual_foot_contact_audit.json")
    montage_contact_report = _read(PROJECT / "Saved/Audit/mual_foot_contact_audit_montage.json")
    live_promotion = _read(PROJECT / "Saved/Audit/mual_live_promotion.json")
    live_promotion_blendspace = _read(PROJECT / "Saved/Audit/mual_live_promotion_blendspace.json")
    manifest = _read(manifest_path)
    registry = _read(registry_path)

    checks: dict[str, dict[str, Any]] = {}
    checks["registry"] = {**_file(registry_path), "ok": bool(registry and registry.get("registry_schema") == "MUAL-2")}
    checks["canonical_manifest"] = {**_file(manifest_path), "ok": bool(manifest and not validate_v2(manifest)), "errors": validate_v2(manifest) if manifest else ["manifest missing"]}
    checks["blender_scan"] = {**_file(PROJECT / "Saved/Audit/mual_blender_idle_scan_verified.json"), "ok": bool(blender_scan and blender_scan.get("lane_a_ready") is True)}
    checks["blender_stage_immutability"] = {**_file(PROJECT / "Saved/Audit/melusina_blender_source_idle_report.json"), "ok": bool(blender_report and blender_report.get("stage_saved") is False)}
    for name in ("Idle", "Walk"):
        path = PROJECT / f"Imports/Animations/Cascadeur/Inbox/A_CAS_Melusina_{name}_Loop.cascadeur.handoff.json"
        handoff = _read(path)
        checks[f"cascadeur_{name.lower()}_handoff"] = {**_file(path), "ok": bool(handoff and handoff.get("status") == "manual_required"), "status": handoff.get("status") if handoff else None}
    checks["ue_staging_retarget"] = {"ok": bool(ue_report and ue_report.get("ok") is True), "report": str(PROJECT / "Saved/Audit/melusina_ue_source_pilot.json")}
    checks["ue_control_case"] = {"ok": bool(ue_report and ue_report.get("checks", {}).get("control_case") is True)}
    checks["pie_smoke"] = {"ok": bool(pie_report and pie_report.get("ok") is True), "report": str(PROJECT / "Saved/Audit/mual_pie_smoke.json")}
    manifest_contact = (manifest or {}).get("foot_contact_audit") if manifest else None
    contact_ok = bool(contact_report and contact_report.get("ok") is True)
    montage_contact_ok = bool(montage_contact_report and montage_contact_report.get("ok") is True)
    manifest_contact_ok = bool(isinstance(manifest_contact, dict) and manifest_contact.get("status") == "passed")
    checks["foot_contact_audit"] = {
        "ok": contact_ok or montage_contact_ok or manifest_contact_ok,
        "reports": [
            str(PROJECT / "Saved/Audit/mual_foot_contact_audit.json"),
            str(PROJECT / "Saved/Audit/mual_foot_contact_audit_montage.json"),
        ],
        "manifest_scope": manifest_contact.get("audited_consumer") if isinstance(manifest_contact, dict) else None,
        "locomotion_contact_evidence": contact_ok,
        "montage_contact_evidence": montage_contact_ok or manifest_contact_ok,
    }
    locomotion_live_ok = bool(live_promotion_blendspace and live_promotion_blendspace.get("promotion_allowed") is True)
    montage_live_ok = bool(live_promotion and live_promotion.get("promotion_allowed") is True)
    checks["locomotion_promotion"] = {
        "ok": bool(locomotion_plan and locomotion_plan.get("promotion_allowed") is True and locomotion_live_ok),
        "offline_plan_ok": bool(locomotion_plan and locomotion_plan.get("promotion_allowed") is True),
        "live_ok": locomotion_live_ok,
    }
    checks["montage_promotion"] = {
        "ok": bool(montage_plan and montage_plan.get("promotion_allowed") is True and montage_live_ok),
        "offline_plan_ok": bool(montage_plan and montage_plan.get("promotion_allowed") is True),
        "live_ok": montage_live_ok,
    }
    checks["live_promotion"] = {
        "ok": montage_live_ok and locomotion_live_ok,
        "montage_report": str(PROJECT / "Saved/Audit/mual_live_promotion.json"),
        "blendspace_report": str(PROJECT / "Saved/Audit/mual_live_promotion_blendspace.json"),
        "montage_ok": bool(live_promotion and live_promotion.get("promotion_allowed") is True),
        "blendspace_ok": bool(live_promotion_blendspace and live_promotion_blendspace.get("promotion_allowed") is True),
    }
    checks["rollback_marker"] = {**_file(PROJECT / "Saved/Audit/mual_promotion_backups/README.md"), "ok": (PROJECT / "Saved/Audit/mual_promotion_backups/README.md").is_file()}
    failed = [name for name, check in checks.items() if check.get("ok") is not True]
    return {
        "schema": "melodia.mual_acceptance_matrix.v1",
        "overall": not failed,
        "checks": checks,
        "failed_checks": failed,
        "registry_counts": registry.get("counts") if registry else None,
        "canonical_clip_id": manifest.get("clip_id") if manifest else None,
        "notes": [
            "Cascadeur foreign inputs remain manual_required until an artist exports a polished canonical source-rig clip.",
            "No UE/runtime promotion is inferred from offline artifacts.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT / "Saved/Audit/mual_acceptance_matrix.json")
    args = parser.parse_args(argv)
    report = build_matrix()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "output": str(output), "failed_checks": report["failed_checks"]}, indent=2))
    return 0 if report["overall"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
