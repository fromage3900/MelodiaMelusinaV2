"""Fail-closed Melusina retarget presentation gate.

The gate makes the proven shoulder and WaveHarp fixes reusable without
silently applying the capture-only 55% shoulder correction to every clip.
UE probes provide measured identity/track/montage data; this module owns the
deterministic accept/reject policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DEFAULT_CONTRACT = PROJECT / "specs/anim_presets/melusina_retarget_presentation_contract.json"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate_probe(probe: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    target = contract["target"]
    for key in ("skeleton", "body", "skirt", "anim_blueprint", "slot"):
        if probe.get("target", {}).get(key) != target[key]:
            errors.append(f"target.{key} does not match canonical contract")

    shoulders = probe.get("shoulders", {})
    pathology = (
        shoulders.get("controller_tracks_static_at_reference") is True
        and shoulders.get("deform_tracks_animated") is True
    )
    normalized = shoulders.get("normalization_applied") is True
    visually_passed = shoulders.get("visual_review_passed") is True
    if pathology and not normalized:
        errors.append("static controller shoulders with animated deform shoulders requires normalization")
    if normalized and not visually_passed:
        errors.append("shoulder normalization requires visual review")
    if shoulders.get("capture_only_reference_promoted") is True:
        errors.append("capture-only shoulder reference cannot be promoted as production animation")

    montage = probe.get("montage", {})
    try:
        duration = float(montage.get("duration_seconds", 0.0))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0.0:
        errors.append("montage duration must be positive")

    bow = probe.get("bow", {})
    expected_bow = contract["bow"]
    if bow.get("asset") != expected_bow["asset"]:
        errors.append("bow asset does not match canonical R07 asset")
    if bow.get("socket") != expected_bow["socket"]:
        errors.append("bow socket must be hand_l")
    if bow.get("scale") != expected_bow["scale"]:
        errors.append("bow scale does not match canonical 0.9 scale")
    if bow.get("draw_world_rotation_pitch_yaw_roll") != expected_bow["draw_world_rotation_pitch_yaw_roll"]:
        errors.append("bow draw orientation does not match canonical world rotation")

    form = probe.get("harp_to_bow", {})
    if form.get("implementation") != "static_mesh_visibility_swap":
        errors.append("harp-to-bow implementation must be the verified static mesh visibility swap")
    if form.get("continuous_morph_claimed") is True:
        errors.append("continuous harp-to-bow morph is not proven")

    return {
        "schema": "melodia.melusina_retarget_presentation_gate.v1",
        "profile": contract["profile"],
        "ok": not errors,
        "promotion_allowed": not errors,
        "errors": errors,
    }


def validate_reference_evidence(contract: dict[str, Any]) -> dict[str, Any]:
    capture_path = PROJECT / contract["evidence"]["portfolio_capture"]
    waveharp_path = PROJECT / contract["evidence"]["waveharp_transform"]
    capture = _read(capture_path)
    waveharp = _read(waveharp_path)
    errors: list[str] = []
    if capture.get("runtime", {}).get("gate_ok") is not True:
        errors.append("portfolio reference capture is not accepted")
    if capture.get("shoulder_fix", {}).get("capture_only") is not True:
        errors.append("shoulder reference must remain capture-only")
    accepted = waveharp.get("accepted_bow_attachment", {})
    expected = contract["bow"]
    rotation = accepted.get("draw_world_rotation", {})
    if accepted.get("socket") != expected["socket"] or accepted.get("scale") != expected["scale"]:
        errors.append("WaveHarp reference attachment differs from contract")
    if [rotation.get("pitch"), rotation.get("yaw"), rotation.get("roll")] != expected["draw_world_rotation_pitch_yaw_roll"]:
        errors.append("WaveHarp reference orientation differs from contract")
    boundary = waveharp.get("proof_boundary", {})
    if boundary.get("ue_form_swap_verified") is not True or boundary.get("continuous_shape_key_morph_verified") is not False:
        errors.append("WaveHarp proof boundary differs from contract")
    return {
        "schema": "melodia.melusina_retarget_reference_gate.v1",
        "profile": contract["profile"],
        "ok": not errors,
        "promotion_allowed": False,
        "reference_only": True,
        "errors": errors,
        "evidence": [str(capture_path), str(waveharp_path)],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, help="UE-produced production promotion probe")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    contract = _read(args.contract.resolve())
    report = validate_probe(_read(args.probe.resolve()), contract) if args.probe else validate_reference_evidence(contract)
    if args.output:
        args.output.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
