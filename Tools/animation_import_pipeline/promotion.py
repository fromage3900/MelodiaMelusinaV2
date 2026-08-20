"""Fail-closed promotion planner for MUAL-2 locomotion and montages.

This command only writes a promotion report. The live UE mutation remains an
explicit editor action after the report passes, so missing runtime evidence
cannot silently replace the existing rollback assets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from manifest_v2 import read_json


PROJECT = Path(__file__).resolve().parents[1].parent
BLENDSPACE_PRESET = PROJECT / "specs/anim_presets/melusina_locomotion_blend.json"
DEFAULT_REPORT = PROJECT / "Saved/Audit/mual_promotion_plan.json"
ROLLBACK_DIR = PROJECT / "Saved/Audit/mual_promotion_backups"


def _asset_path(value: str) -> str:
    return value.split(".", 1)[0].replace("\\", "/")


def _existing_samples() -> list[dict[str, Any]]:
    data = read_json(BLENDSPACE_PRESET)
    return list(data.get("samples") or [])


def build_plan(
    manifest: dict[str, Any],
    ue_report: dict[str, Any],
    *,
    animation: str,
    consumer: str,
    speed: float | None = None,
    montage_target: str = "",
    replace_existing_speed: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    blockers: list[str] = []
    if manifest.get("status") not in {"canonical", "promoted"}:
        errors.append("only canonical/promoted manifests can be promoted")
    if manifest.get("target_skeleton") != "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton":
        errors.append("manifest target skeleton is not SK_Melusina_Skeleton")
    if manifest.get("target_mesh") != "/Game/Melodia/Characters/Melusina/SK_Melusina":
        errors.append("manifest target mesh is not SK_Melusina")
    contact = manifest.get("foot_contact_audit") or {}
    audited_consumer = contact.get("audited_consumer")
    if not ue_report.get("ok"):
        blockers.append("UE staging/retarget report is not successful")
    elif ue_report.get("staging_ok") is False:
        blockers.append("UE staging/retarget gates are not complete")
    # The UE pilot reports the union of all possible consumer gates.  A
    # static montage must not be blocked by the locomotion-only speed gate,
    # while a BlendSpace sample must still require measured speed and
    # bilateral contact evidence.
    ue_blockers = list(ue_report.get("promotion_blockers") or [])
    for item in ue_blockers:
        if consumer == "montage" and item == "measured_speed":
            continue
        if consumer == audited_consumer and item == "foot_contact_audit":
            continue
        blockers.append(f"UE:{item}")
    if not ROLLBACK_DIR.is_dir():
        blockers.append("rollback backup marker directory is missing")
    if manifest.get("root_motion") not in {"in_place", "root"}:
        errors.append("root-motion policy is missing")
    if contact.get("status") != "passed":
        blockers.append("foot/contact marker audit has not passed")
    if contact.get("status") == "passed" and audited_consumer and audited_consumer != consumer:
        blockers.append(f"foot/contact audit is scoped to {audited_consumer}, not {consumer}")
    plan: dict[str, Any] = {
        "schema": "melodia.mual_promotion_plan.v1",
        "animation": _asset_path(animation),
        "consumer": consumer,
        "manifest_clip_id": manifest.get("clip_id"),
        "contact_audit_consumer": audited_consumer,
        "errors": errors,
        "blockers": blockers,
        "promotion_allowed": False,
        "replace_existing_speed": bool(replace_existing_speed),
    }
    if consumer == "blendspace":
        speed_source = "cli"
        measured_evidence = ue_report.get("measured_speed")
        if not isinstance(measured_evidence, dict) or measured_evidence.get("verified") is not True:
            blockers.append("UE measured locomotion-speed evidence is missing or unknowable")
        if speed is None:
            measured = measured_evidence
            if isinstance(measured, dict) and measured.get("verified") is True:
                try:
                    speed = float(measured["speed_cm_s"])
                    speed_source = "ue_report"
                except (KeyError, TypeError, ValueError):
                    speed = None
        elif isinstance(measured_evidence, dict) and measured_evidence.get("verified") is True:
            try:
                if abs(float(measured_evidence["speed_cm_s"]) - float(speed)) > 0.01:
                    errors.append("CLI speed does not match the UE-measured locomotion speed")
            except (KeyError, TypeError, ValueError):
                blockers.append("UE measured locomotion-speed evidence is malformed")
        samples = _existing_samples()
        duplicate_assets = [row for row in samples if _asset_path(str(row.get("animation", ""))) == plan["animation"]]
        duplicate_speeds = [row for row in samples if speed is not None and abs(float(row.get("speed", 0.0)) - speed) < 0.01]
        plan["existing_samples"] = samples
        plan["duplicate_asset_samples"] = duplicate_assets
        plan["duplicate_speed_samples"] = duplicate_speeds
        if duplicate_assets:
            errors.append("animation is already a BlendSpace sample")
        if duplicate_speeds:
            static_speed_replacement = (
                replace_existing_speed
                and speed == 0.0
                and isinstance(manifest.get("speed_evidence"), dict)
                and manifest.get("speed_evidence", {}).get("mode") == "static_pose"
                and manifest.get("speed_evidence", {}).get("status") in {"declared", "verified"}
                and audited_consumer == "blendspace"
            )
            if static_speed_replacement:
                plan["replacement_samples"] = duplicate_speeds
            else:
                errors.append("speed already has a BlendSpace sample; refuse duplicate placement")
        if speed is None:
            blockers.append("measured locomotion speed is missing")
        elif speed < 0.0 or speed > 750.0:
            errors.append("measured speed is outside the canonical 0–750 axis")
        plan["measured_speed"] = speed
        plan["measured_speed_source"] = speed_source if speed is not None else None
        plan["axis_range"] = [0.0, 750.0]
    elif consumer == "montage":
        if not montage_target:
            blockers.append("montage target is missing")
        plan["montage_target"] = _asset_path(montage_target) if montage_target else ""
        # A montage may be authored either in-place or with extracted root
        # motion.  The contract already requires one of these explicit
        # policies above; requiring `root` here would reject valid in-place
        # montage clips (idle, hit-react, emote) for no technical reason.
    else:
        errors.append(f"unsupported promotion consumer: {consumer}")
    plan["promotion_allowed"] = not errors and not blockers
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("ue_report", type=Path)
    parser.add_argument("--animation", required=True)
    parser.add_argument("--consumer", choices=("blendspace", "montage"), required=True)
    parser.add_argument("--speed", type=float)
    parser.add_argument("--replace-existing-speed", action="store_true", help="Replace one existing sample at the requested speed after a guarded backup (speed-zero idle only).")
    parser.add_argument("--montage-target", default="")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    manifest = read_json(args.manifest.resolve())
    ue_report = read_json(args.ue_report.resolve())
    report = build_plan(
        manifest,
        ue_report,
        animation=args.animation,
        consumer=args.consumer,
        speed=args.speed,
        montage_target=args.montage_target,
        replace_existing_speed=args.replace_existing_speed,
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["promotion_allowed"], "output": str(output), "errors": report["errors"], "blockers": report["blockers"]}, indent=2))
    return 0 if report["promotion_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
