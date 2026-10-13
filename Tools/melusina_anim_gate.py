"""Melusina runtime-clip gate. Run inside the editor (Claireon python_execute / Monolith run_python).

Contract (Jev 2026-10-02, Saved/Audit/ArcheryGoalSession_20261001/JevConverge_20261002.json):
  * Clips drive DEFORM bones only. No control-bone (c_*) or twist-bone rewrites, no per-clip fixes.
  * One skeleton: SK_Melusina_Skeleton (wardrobe leader-pose slots refuse any other).
  * Root height, face/eye rest and hand roll are measured against the proven baseline, not guessed.

Baseline measured 2026-10-02 over 61 production clips: root_x world z = 88 +/- 12; eye bones at rest;
hand roll (wrapped, vs ref) 10-52 deg locomotion, <=80 deg bow draw, 105 Death (outlier);
forearm twist bones static in every proven clip.

Usage:  import melusina_anim_gate as g; g.run(["/Game/.../A_Clip", ...])  -> list of dict rows with 'fail' reasons.
"""
import math
import json
import re
from collections import deque
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None  # The reference gate can also run outside the editor.

BODY = "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body"
SKELETON_TAG = "SK_Melusina_Skeleton"
ROOT_Z, ROOT_TOL = 88.0, 12.0
EYE_MAX_DEG = 1.0
HAND_ROLL_MAX_DEG = 110.0  # proven Death clip = 105; Sparrow draw/fire = 92-103 (source motion)
TWIST_MUST_BE_STATIC = True


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _roll(q):
    return _wrap(math.degrees(2.0 * math.atan2(q.y, q.w)))


def _qconj(q):
    return unreal.Quat(-q.x, -q.y, -q.z, q.w)


def _qmul(a, b):
    return unreal.Quat(
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z)


def _ang(q1, q2):
    d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))


def measure(path, samples=(0.0, 0.33, 0.66, 1.0)):
    if unreal is None:
        raise RuntimeError("Pose measurement requires the Unreal editor")
    mesh = unreal.load_asset(BODY)
    seq = unreal.load_asset(path)
    W, L = unreal.AnimPoseSpaces.WORLD, unreal.AnimPoseSpaces.LOCAL
    ln = seq.get_play_length()
    opt = unreal.AnimPoseEvaluationOptions()
    opt.set_editor_property("optional_skeletal_mesh", mesh)
    row = {"clip": path.split("/")[-1], "root_z_dev": 0.0, "eye_deg": 0.0, "hand_roll": 0.0, "twist_moved": 0.0}
    for s in samples:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, min(ln * s, ln - 0.001), opt)
        P = unreal.AnimPoseExtensions
        dz = P.get_bone_pose(pose, "root_x", W).translation.z - ROOT_Z
        row["root_z_dev"] = max(row["root_z_dev"], abs(dz))
        for b in ("eye_l", "eye_r", "def_eye_l", "def_eye_r"):
            row["eye_deg"] = max(row["eye_deg"], _ang(P.get_bone_pose(pose, b, L).rotation, P.get_ref_bone_pose(pose, b, L).rotation))
        for side in ("l", "r"):
            def rel(b):
                return _roll(_qmul(_qconj(P.get_ref_bone_pose(pose, b, L).rotation), P.get_bone_pose(pose, b, L).rotation))
            row["hand_roll"] = max(row["hand_roll"], abs(rel("hand_" + side)))
            row["twist_moved"] = max(row["twist_moved"], abs(rel("forearm_twist_" + side)) + abs(rel("forearm_twist_2_" + side)))
    return row


def run(paths):
    out = []
    for p in paths:
        r = measure(p)
        fail = []
        if r["root_z_dev"] > ROOT_TOL:
            fail.append("root_z %.0f off" % r["root_z_dev"])
        if r["eye_deg"] > EYE_MAX_DEG:
            fail.append("eyes keyed %.1f deg" % r["eye_deg"])
        if r["hand_roll"] > HAND_ROLL_MAX_DEG:
            fail.append("hand roll %.0f deg" % r["hand_roll"])
        if TWIST_MUST_BE_STATIC and r["twist_moved"] > 1.0:
            fail.append("twist bones keyed (%.0f deg) - contract is deform-only" % r["twist_moved"])
        r["fail"] = fail
        out.append(r)
    return out


def package_path(value):
    """Accept package paths, object paths and Unreal's quoted tag values."""
    text = str(value)
    if "'" in text:
        text = text.split("'", 2)[1]
    match = re.search(r"(/[A-Za-z0-9_]+/[A-Za-z0-9_/]+)", text)
    if not match:
        raise ValueError("Not an Unreal package/object path: %r" % value)
    return match.group(1)


def check_runtime_torso_order(receipt):
    """Check the existing live pose capture, never isolated clip or input proof.

    root_x is Melusina's common torso/leg ancestor, not a mannequin pelvis.
    A head/upper spine below it reproduced the layered combat inversion even
    while both arm lengths passed. Positive height alone is not visual acceptance.
    This checks supplied samples only: provenance, stable montage weight and
    transition coverage still require separate live verification.
    """
    required_phases = {"idle", "draw", "hold", "fire", "recovery",
                       "caster_draw", "caster_fire", "caster_recovery"}
    required_views = {"front", "side"}
    errors, rows, covered = [], [], set()
    samples = receipt.get("samples", []) if isinstance(receipt, dict) else []
    if not isinstance(samples, list):
        samples = []
        errors.append("samples must be an array")
    if isinstance(receipt, dict) and receipt.get("errors"):
        errors.append("Capture reported errors; incomplete diagnostic")
    for index, sample in enumerate(samples):
        try:
            phase, view = sample["phase"], sample["view"]
            positions = [sample["bones_cs"][bone]["p"] for bone in
                         ("root_x", "spine_03_x", "head_x")]
            if not all(isinstance(p, (list, tuple)) and len(p) == 3 and
                       all(isinstance(v, (int, float)) and not isinstance(v, bool)
                           and math.isfinite(v) for v in p) for p in positions):
                raise ValueError("positions must contain three finite numbers")
            if not isinstance(phase, str) or not isinstance(view, str):
                raise ValueError("phase/view must be strings")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append("Invalid pose sample %d: %s" % (index, exc))
            continue
        covered.add((phase, view))
        pelvis_z, spine_z, head_z = [p[2] for p in positions]
        row = {"sample": index, "phase": phase, "view": view,
               "spine_above_root_cm": spine_z - pelvis_z,
               "head_above_root_cm": head_z - pelvis_z}
        row["ok"] = row["spine_above_root_cm"] > 0 and row["head_above_root_cm"] > 0
        if not row["ok"]:
            errors.append("Torso inversion at sample %d (%s/%s)" % (index, phase, view))
        rows.append(row)
    missing = sorted((phase, view) for phase in required_phases for view in required_views
                     if (phase, view) not in covered)
    if missing:
        errors.append("Missing required phase/view coverage: " +
                      ", ".join("%s/%s" % pair for pair in missing))
    return {"schema": "melodia.melusina_runtime_torso_gate.v1",
            "evidence": "LIVE_POSE_DIAGNOSTIC_RECEIPT_CHECK",
            "input_proof": receipt.get("proof") if isinstance(receipt, dict) else None,
            "physical_input_acceptance": False, "visual_completion": False,
            "ok": not errors, "errors": errors, "samples": rows}


def check_runtime_references(manifest, policy, extra_edges=()):
    """Fail on exact retired paths reached through hard, soft or native edges.

    Package reachability is deliberately conservative: a disconnected graph
    node is still a reference. This gate does not certify pose/contact quality.
    Native soft defaults must be supplied by a CDO/live binding extraction;
    source-string matches alone are not automatically made runtime edges.
    """
    assets = {package_path(p): row for p, row in manifest.get("assets", {}).items()}
    roots = [package_path(p) for p in policy.get("roots", [])]
    allowed = {package_path(p): note for p, note in policy.get("canonical_allowlist", {}).items()}
    retired = {package_path(p): reason for p, reason in policy.get("retired_denylist", {}).items()}
    errors = []
    if not roots:
        errors.append("No canonical runtime roots supplied")
    if manifest.get("registry_loading") is not False:
        errors.append("Asset Registry completion is unverified")
    collisions = sorted(set(allowed) & set(retired))
    if collisions:
        errors.append("Policy both allows and retires: " + ", ".join(collisions))
    for root in roots:
        if root not in assets:
            errors.append("Canonical root missing from extraction: " + root)
    dynamic = {}
    native_counts = {}
    native_fields = {}
    edge_rows = list(extra_edges or [])
    for index, edge in enumerate(edge_rows):
        label = "native binding edge %d" % index
        if not isinstance(edge, dict):
            errors.append("Malformed " + label + ": expected object")
            continue
        required_keys = {"source", "target", "consumer", "field", "required", "expected_skeleton", "target_skeleton"}
        missing = sorted(required_keys - set(edge))
        if missing:
            errors.append("Malformed %s: missing %s" % (label, ", ".join(missing)))
            continue
        if not isinstance(edge["consumer"], str) or not edge["consumer"].strip():
            errors.append("Malformed %s: consumer must be a non-empty string" % label)
            continue
        if not isinstance(edge["field"], str) or not edge["field"].strip():
            errors.append("Malformed %s: field must be a non-empty string" % label)
            continue
        if not isinstance(edge["required"], bool):
            errors.append("Malformed %s: required must be boolean" % label)
            continue
        owner, field = edge["consumer"], edge["field"]
        key = (owner, field)
        native_fields.setdefault(key, []).append((index, edge))
        native_counts[owner] = native_counts.get(owner, 0) + 1
        try:
            source = package_path(edge["source"])
            target = package_path(edge["target"]) if edge["target"] is not None else None
        except (TypeError, ValueError) as exc:
            errors.append("Malformed %s: %s" % (label, exc))
            continue
        if target is None:
            if edge["required"]:
                errors.append("Required native field has no target: %s.%s" % key)
            elif edge["target_skeleton"] is not None or edge["expected_skeleton"] is not None:
                errors.append("Optional empty native field must explicitly use null skeletons: %s.%s" % key)
            continue
        dynamic.setdefault(source, []).append(target)
        expected_value, actual_value = edge["expected_skeleton"], edge["target_skeleton"]
        if edge["required"] and (expected_value is None or actual_value is None):
            errors.append("Required native field has unknown skeleton: %s.%s" % key)
            continue
        if expected_value is not None or actual_value is not None:
            if expected_value is None or actual_value is None:
                if edge["required"]:
                    errors.append("Required native field has unknown skeleton: %s.%s" % key)
                continue
            try:
                expected_skeleton = package_path(expected_value)
                target_skeleton = package_path(actual_value)
            except (TypeError, ValueError) as exc:
                errors.append("Malformed %s skeleton contract: %s" % (label, exc))
                continue
            if expected_skeleton != target_skeleton:
                errors.append("Native field skeleton mismatch for %s.%s: expected %s, target %s" %
                              (owner, field, expected_skeleton, target_skeleton))

    for key, rows in native_fields.items():
        if len(rows) > 1:
            errors.append("Duplicate native binding field edge: %s.%s (%d rows)" % (key[0], key[1], len(rows)))
    required_native_fields = policy.get("required_native_fields", [])
    required_keys = set()
    for requirement in required_native_fields:
        if not isinstance(requirement, dict) or not isinstance(requirement.get("consumer"), str) or not isinstance(requirement.get("field"), str):
            errors.append("Malformed required_native_fields policy entry")
            continue
        key = (requirement["consumer"], requirement["field"])
        if key in required_keys:
            errors.append("Duplicate required native field policy: %s.%s" % key)
            continue
        required_keys.add(key)
        rows = native_fields.get(key, [])
        if not rows:
            errors.append("Required native field extraction missing: %s.%s" % key)
        elif len(rows) == 1 and not rows[0][1]["required"]:
            errors.append("Required native field marked optional: %s.%s" % key)
        elif len(rows) == 1:
            expected = requirement.get("expected_skeleton")
            if expected is not None:
                try:
                    if package_path(rows[0][1]["expected_skeleton"]) != package_path(expected):
                        errors.append("Native field expected skeleton disagrees with policy: %s.%s" % key)
                except (TypeError, ValueError) as exc:
                    errors.append("Malformed required native field skeleton policy for %s.%s: %s" % (*key, exc))
    # Keep legacy count assertions readable for older policies, but do not use
    # counts as a substitute for exact required-field coverage.
    for owner, minimum in policy.get("required_native_consumers", {}).items():
        if native_counts.get(owner, 0) < minimum:
            errors.append("Native binding extraction missing/incomplete: " + owner)
    parents = {root: None for root in roots}
    queue = deque(roots)
    while queue:
        current = queue.popleft()
        row = assets.get(current, {})
        deps = row.get("hard_dependencies", []) + row.get("soft_dependencies", []) + dynamic.get(current, [])
        for value in sorted(set(deps)):
            target = package_path(value)
            if target not in parents:
                parents[target] = current
                queue.append(target)
    violations = []
    for target in sorted(set(parents) & set(retired)):
        chain = [target]
        while parents[chain[-1]] is not None:
            chain.append(parents[chain[-1]])
        violations.append({"asset": target, "reason": retired[target], "reference_chain": list(reversed(chain))})
    if violations:
        errors.append("Canonical runtime graph references %d explicitly retired assets" % len(violations))
    animation_classes = {"AnimBlueprint", "AnimSequence", "AnimMontage", "AnimComposite", "BlendSpace", "BlendSpace1D", "AimOffsetBlendSpace", "AimOffsetBlendSpace1D", "PoseAsset", "Skeleton", "IKRigDefinition", "IKRetargeter", "ControlRigBlueprint"}
    unknown = sorted(p for p in parents if assets.get(p, {}).get("class") in animation_classes and p not in allowed and p not in retired)
    return {
        "schema": "melodia.melusina_anim_reference_gate.v1",
        "evidence": "ASSET_REFERENCE_EXTRACTION_ONLY",
        "ok": not errors,
        "visual_completion": False,
        "roots": roots,
        "reachable_count": len(parents),
        "violations": violations,
        "errors": errors,
        "allowlisted_reachable": sorted(set(parents) & set(allowed)),
        "unclassified_animation_assets": unknown,
        "retired_not_reachable": sorted(set(retired) - set(parents)),
        "native_binding_edge_count": sum(len(v) for v in dynamic.values()),
        "native_consumer_counts": native_counts,
    }


def reference_gate_main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Check Melusina animation references or captured runtime torso poses")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--references", type=Path)
    source.add_argument("--runtime-capture", type=Path)
    parser.add_argument("--policy", type=Path, default=Path(__file__).resolve().parents[1] / "specs/anim_presets/melusina_locomotion_blend.json")
    parser.add_argument("--native-bindings", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.runtime_capture:
        if args.native_bindings:
            parser.error("--native-bindings applies only to --references")
        report = check_runtime_torso_order(json.loads(args.runtime_capture.read_text(encoding="utf-8-sig")))
    else:
        manifest = json.loads(args.references.read_text(encoding="utf-8-sig"))
        policy = json.loads(args.policy.read_text(encoding="utf-8-sig"))
        policy = policy.get("runtime_reference_policy", policy)
        edges = json.loads(args.native_bindings.read_text(encoding="utf-8-sig")) if args.native_bindings else []
        report = check_runtime_references(manifest, policy, edges)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(reference_gate_main())
