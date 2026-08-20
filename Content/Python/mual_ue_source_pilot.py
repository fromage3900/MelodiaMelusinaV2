"""UE-side staging/import/retarget audit for one MUAL-2 source clip.

Run with the editor closed when using ``UnrealEditor-Cmd.exe``::

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
      -script=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/mual_ue_source_pilot.py \
      -unattended -nop4 -nosplash

The script is idempotent: source import uses one deterministic package and
retarget uses overwrite-existing output. It never promotes into a BlendSpace
or montage unless the manifest, skeleton, unit probe, root-motion policy, and
contact audit all pass explicitly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal


TOOLS = Path(unreal.Paths.project_dir()).resolve() / "Tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
PIPELINE_TOOLS = TOOLS / "animation_import_pipeline"
if str(PIPELINE_TOOLS) not in sys.path:
    sys.path.insert(0, str(PIPELINE_TOOLS))
from melusina_anim_unit_guard import classify_spine_translation  # noqa: E402
from manifest_v2 import validate_v2  # noqa: E402


PROJECT = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
FBX = Path(os.environ.get("MUAL_PILOT_FBX", PROJECT / "Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.fbx"))
MANIFEST = Path(os.environ.get("MUAL_PILOT_MANIFEST", FBX.with_suffix(".manifest.json")))
REPORT = PROJECT / "Saved/Audit/melusina_ue_source_pilot.json"

SOURCE_MESH = "/Game/Melodia/Mocap/Source/SK_Source_Melusina"
TARGET_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
RETARGETER = "/Game/Melodia/Mocap/Retarget/RTG_Source_to_Melusina"
STAGING = "/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted"
CONTROL_CASE = "/Game/Melodia/Mocap/Source/Anims/A_Src_RunCycle"
CONTROL_SKELETON = "/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton"
EXPECTED_FPS = 30.0
PROBE_BONE = "c_spine_02_x"
CONTROL_PROBE_BONE = "brennan_spine1"
ROOT_BONES = ("root", "root_x")


def asset_path(value) -> str:
    return value.get_path_name() if value else ""


def load(path: str):
    value = unreal.EditorAssetLibrary.load_asset(path)
    if value is None:
        raise RuntimeError(f"asset missing: {path}")
    return value


def resolve_source_import_skeleton() -> str:
    """Resolve the USkeleton owned by the authoritative source-rig mesh.

    ``SK_Source_Melusina`` is intentionally the source-rig *mesh* contract;
    it is not itself a ``USkeleton`` object.  The existing asset's Skeleton
    property is authoritative and must be used for FBX import rather than
    guessing or creating a second skeleton asset.
    """
    source_mesh = load(SOURCE_MESH)
    skeleton = source_mesh.get_editor_property("skeleton")
    path = asset_path(skeleton).split(".", 1)[0]
    if not path:
        raise RuntimeError(f"source mesh has no Skeleton property: {SOURCE_MESH}")
    return path


def editor_property(obj, name: str, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def probe_units(sequence, bone: str = PROBE_BONE, frame: int = 0) -> dict:
    """Probe a local animation translation using the project's existing guard."""
    try:
        pose = unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, bone, frame, False)
        translation = pose.translation
        y = float(translation.y)
        return {
            "bone": bone,
            "frame": frame,
            "translation": {
                "x": float(translation.x),
                "y": y,
                "z": float(translation.z),
            },
            "classification": classify_spine_translation(y),
            "spine_y": y,
        }
    except Exception as exc:
        return {
            "bone": bone,
            "frame": frame,
            "classification": "unknown",
            "spine_y": None,
            "error": str(exc),
        }


def measure_root_motion(sequence, duration: float, *, allow_static_pose: bool = False) -> dict:
    """Measure planar root travel in UE centimetres when the clip exposes it.

    Root-locked sequences intentionally report ``verified: false`` rather than
    pretending that an unknowable authored speed is zero.  That matches the
    project's existing Monolith locomotion audit.
    """
    enabled = editor_property(sequence, "enable_root_motion", None)
    if enabled is False and not allow_static_pose:
        return {
            "status": "unknowable_root_locked",
            "verified": False,
            "speed_cm_s": None,
            "note": "root motion disabled; authored locomotion speed is unknowable",
        }
    try:
        # UE's Python AnimationLibrary reports the last frame index here;
        # include the endpoint when iterating poses.
        frame_count = int(unreal.AnimationLibrary.get_num_frames(sequence)) + 1
    except Exception:
        try:
            frame_count = int(sequence.get_number_of_frames())
        except Exception:
            frame_count = 0
    if duration <= 0.0 or frame_count < 2:
        return {"status": "undefined", "verified": False, "speed_cm_s": None, "frame_count": frame_count}
    if enabled is False and allow_static_pose:
        # A speed-zero idle is the one legitimate exception to the
        # root-locked-speed rule.  Prove it is actually static by sampling the
        # available root track across the whole sequence; do not infer zero
        # from an absent track or from the manifest alone.
        samples = max(2, frame_count)
        for bone in ROOT_BONES:
            try:
                poses = [
                    unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, bone, frame, False).translation
                    for frame in range(samples)
                ]
            except Exception:
                continue
            first = poses[0]
            max_planar_delta = max(
                (((float(p.x) - float(first.x)) ** 2) + ((float(p.y) - float(first.y)) ** 2)) ** 0.5
                for p in poses
            )
            max_vertical_delta = max(abs(float(p.z) - float(first.z)) for p in poses)
            if max_planar_delta <= 0.01 and max_vertical_delta <= 0.01:
                return {
                    "status": "verified_static_pose",
                    "verified": True,
                    "speed_cm_s": 0.0,
                    "bone": bone,
                    "frame_count": frame_count,
                    "delta_cm": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "max_planar_delta_cm": max_planar_delta,
                    "max_vertical_delta_cm": max_vertical_delta,
                    "note": "manifest-declared speed-zero idle; UE root-track constancy verified",
                }
        return {
            "status": "static_pose_not_proven",
            "verified": False,
            "speed_cm_s": None,
            "frame_count": frame_count,
            "note": "static-pose declaration was present but root-track constancy failed",
        }
    for bone in ROOT_BONES:
        try:
            first = unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, bone, 0, False).translation
            last = unreal.AnimationLibrary.get_bone_pose_for_frame(sequence, bone, frame_count - 1, False).translation
            dx = float(last.x) - float(first.x)
            dy = float(last.y) - float(first.y)
            speed = ((dx * dx + dy * dy) ** 0.5) / duration
            return {
                "status": "measured",
                "verified": True,
                "bone": bone,
                "frame_count": frame_count,
                "delta_cm": {"x": dx, "y": dy},
                "speed_cm_s": speed,
            }
        except Exception:
            continue
    return {
        "status": "root_track_unavailable",
        "verified": False,
        "speed_cm_s": None,
        "frame_count": frame_count,
        "root_bones_tried": list(ROOT_BONES),
    }


def save_confirmation(path: str) -> dict:
    """Record a real package save attempt for the staging artifact."""
    try:
        saved = bool(unreal.EditorAssetLibrary.save_asset(path, False))
        return {"asset": path, "attempted": True, "saved": saved}
    except Exception as exc:
        return {"asset": path, "attempted": True, "saved": False, "error": str(exc)}


def sequence_report(
    path: str,
    expected_skeleton: str,
    probe_bone: str = PROBE_BONE,
    *,
    allow_static_speed: bool = False,
) -> dict:
    sequence = unreal.EditorAssetLibrary.load_asset(path.split(".", 1)[0])
    if sequence is None:
        return {"asset": path, "loaded": False, "errors": ["sequence not found"]}
    skeleton = sequence.get_editor_property("skeleton")
    skeleton_path = asset_path(skeleton)
    errors = []
    if expected_skeleton not in skeleton_path:
        errors.append(f"skeleton is {skeleton_path}, expected {expected_skeleton}")
    try:
        duration = float(sequence.get_editor_property("sequence_length"))
    except Exception:
        duration = 0.0
    if duration <= 0.0:
        errors.append("sequence duration is not positive")
    try:
        frame_rate = sequence.get_editor_property("sampling_frame_rate")
        fps = float(frame_rate.numerator) / float(frame_rate.denominator)
    except Exception:
        fps = None
    looping = bool(editor_property(sequence, "loop", editor_property(sequence, "is_looping", False)))
    enable_root_motion = editor_property(sequence, "enable_root_motion", None)
    root_motion_root_lock = editor_property(sequence, "root_motion_root_lock", None)
    unit_probe = probe_units(sequence, probe_bone)
    root_motion_measurement = measure_root_motion(
        sequence,
        duration,
        allow_static_pose=allow_static_speed,
    )
    sampled_frames = None
    try:
        sampled_frames = int(unreal.AnimationLibrary.get_num_frames(sequence))
        if duration > 0.0:
            # UE stores sequence_length as last-frame-time, so N frame steps
            # over that duration represent N / duration samples per second.
            fps = float(sampled_frames) / duration
    except Exception:
        pass
    if fps is None:
        errors.append("sampling frame rate is unavailable")
    elif abs(fps - EXPECTED_FPS) > 0.01:
        errors.append(f"sampling frame rate is {fps:g}, expected {EXPECTED_FPS:g}")
    if unit_probe.get("classification") != "cm":
        errors.append(
            "centimetre track probe did not classify as cm: "
            f"{unit_probe.get('classification')} (spine_y={unit_probe.get('spine_y')})"
        )
    return {
        "asset": path,
        "loaded": True,
        "skeleton": skeleton_path,
        "duration": duration,
        "sampled_frames": sampled_frames,
        "fps": fps,
        "loop": looping,
        "enable_root_motion": enable_root_motion,
        "root_motion_root_lock": str(root_motion_root_lock) if root_motion_root_lock is not None else None,
        "unit_probe": unit_probe,
        "root_motion_measurement": root_motion_measurement,
        "errors": errors,
    }


def apply_sequence_policy(path: str, manifest: dict) -> dict:
    """Apply only declared loop/root policy to a new staging sequence."""
    sequence = load(path)
    expected_root = manifest.get("root_motion") == "root"
    changes = {"asset": path, "loop": bool(manifest.get("loop")), "enable_root_motion": expected_root}
    sequence.set_editor_property("loop", changes["loop"])
    sequence.set_editor_property("enable_root_motion", expected_root)
    return changes


def import_source(manifest: dict, source_skeleton: str) -> tuple[str, dict]:
    clip = manifest["clip_name"]
    source_name = f"{clip}__MUAL_SRC"
    expected = f"{STAGING}/{source_name}"
    source_skeleton_asset = load(source_skeleton)
    if unreal.EditorAssetLibrary.does_asset_exist(expected):
        return expected, {"reused": True, "asset": expected}
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(FBX))
    task.set_editor_property("destination_path", STAGING)
    task.set_editor_property("destination_name", source_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("skeleton", source_skeleton_asset)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    # UE 5.8 routes FBX tasks through Interchange unless the animation-only
    # import type is explicit.  The existing solved MUAL importer uses this
    # setting; without it an armature-only FBX reports "nothing to import".
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    anim_data = options.get_editor_property("anim_sequence_import_data")
    if anim_data:
        anim_data.set_editor_property("remove_redundant_keys", False)
        anim_data.set_editor_property("convert_scene", True)
        anim_data.set_editor_property("use_default_sample_rate", False)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        raise RuntimeError("source FBX import returned no assets")
    return imported[0].split(".", 1)[0], {"reused": False, "imported": imported}


def retarget_source(source_asset: str, manifest: dict) -> tuple[str, dict]:
    retargeter = load(RETARGETER)
    source_mesh = load(SOURCE_MESH)
    target_mesh = load(TARGET_MESH)
    load(TARGET_SKELETON)
    # The project already has the source/target setup. The pilot verifies the
    # known null-skeleton failure mode but never repairs a production mesh as
    # a side effect of staging.
    current_skeleton = target_mesh.get_editor_property("skeleton")
    current_path = asset_path(current_skeleton)
    if TARGET_SKELETON not in current_path:
        raise RuntimeError(f"target mesh skeleton is {current_path or '<none>'}; expected {TARGET_SKELETON}")
    # The existing RTG_Source_to_Melusina chain is authoritative. Do not
    # auto-map or recreate it on every pilot run; a missing/invalid chain must
    # fail the batch retarget and be repaired explicitly by its owner.
    source_data = unreal.EditorAssetLibrary.find_asset_data(source_asset)
    inputs = unreal.IKRetargetBatchOperationInputs()
    inputs.set_editor_property("assets_to_retarget", [source_data])
    inputs.set_editor_property("source_mesh", source_mesh)
    inputs.set_editor_property("target_mesh", target_mesh)
    inputs.set_editor_property("ik_retarget_asset", retargeter)
    inputs.set_editor_property("target_path", STAGING)
    inputs.set_editor_property("search", "__MUAL_SRC")
    inputs.set_editor_property("replace", "__MUAL_TARGET")
    inputs.set_editor_property("overwrite_existing_files", True)
    inputs.set_editor_property("use_source_path", False)
    created = unreal.IKRetargetBatchOperation().run_batch_retarget(inputs) or []
    expected = f"{STAGING}/{manifest['clip_name']}__MUAL_TARGET"
    paths = [str(item.package_name) for item in created]
    if paths:
        expected = paths[0].split(".", 1)[0]
    if not unreal.EditorAssetLibrary.does_asset_exist(expected):
        raise RuntimeError(f"retarget created no deterministic target asset: {paths}")
    return expected, {
        "created": paths,
        "retargeter": RETARGETER,
        "target_mesh_skeleton_before": current_path,
        "target_mesh_skeleton_after": asset_path(target_mesh.get_editor_property("skeleton")),
    }


def root_motion_check(sequence_report_value: dict, manifest: dict) -> dict:
    declared = manifest.get("root_motion")
    expected_enabled = declared == "root"
    actual_enabled = sequence_report_value.get("enable_root_motion")
    passed = isinstance(actual_enabled, bool) and actual_enabled == expected_enabled
    return {
        "declared": declared,
        "expected_enable_root_motion": expected_enabled,
        "actual_enable_root_motion": actual_enabled,
        "root_motion_root_lock": sequence_report_value.get("root_motion_root_lock"),
        "passed": passed,
    }


def contact_audit_check(manifest: dict) -> dict:
    audit = manifest.get("foot_contact_audit")
    audit = audit if isinstance(audit, dict) else {}
    status = audit.get("status")
    audited_consumer = audit.get("audited_consumer")
    # A static-pose exception is intentionally consumer-scoped.  If the
    # sidecar was audited for a montage, it must not silently unlock the
    # locomotion/BlendSpace lane.
    passed = status == "passed" and (not audited_consumer or audited_consumer == manifest.get("consumer"))
    return {
        "status": status,
        "audited_consumer": audited_consumer,
        "required_for_promotion": bool(audit.get("required_for_promotion", True)),
        "passed": passed,
    }


def pie_smoke_check() -> dict:
    """Consume the explicit PIE evidence artifact produced by ``pie-smoke``."""
    evidence_path = os.environ.get("MUAL_PIE_SMOKE_REPORT", "")
    if not evidence_path:
        evidence_path = str(PROJECT / "Saved/Audit/mual_pie_smoke.json")
    path = Path(evidence_path)
    if not path.is_file():
        return {"status": "missing", "ok": False, "path": str(path), "reason": "PIE smoke evidence was not supplied"}
    try:
        evidence = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "ok": False, "path": str(path), "error": str(exc)}
    clip_matches = evidence.get("clip_name") in {None, FBX.stem}
    return {
        "status": "verified_external",
        "ok": evidence.get("ok") is True and clip_matches,
        "path": str(path),
        "clip_matches": clip_matches,
        "evidence": evidence,
    }


def main() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    report = {
        "schema": "melodia.mual_ue_source_pilot.v1",
        "fbx": str(FBX),
        "manifest": str(MANIFEST),
        "source_skeleton_contract": SOURCE_MESH,
        "source_import_skeleton": "resolved from SK_Source_Melusina.Skeleton",
        "target_skeleton": TARGET_SKELETON,
        "target_mesh": TARGET_MESH,
        "retargeter": RETARGETER,
        "staging": STAGING,
        "control_case": CONTROL_CASE,
        "control_skeleton": CONTROL_SKELETON,
        "ok": False,
        "promotion_allowed": False,
        "errors": [],
        "promotion_blockers": [],
        "stage_mutation": "UE staging assets only; no BlendSpace/montage promotion",
    }
    try:
        if not FBX.is_file() or not MANIFEST.is_file():
            raise RuntimeError("pilot FBX or manifest is missing")
        manifest_errors = validate_v2(manifest)
        report["manifest_errors"] = manifest_errors
        if manifest_errors:
            raise RuntimeError("manifest v2 contract failed: " + "; ".join(manifest_errors))
        source_import_skeleton = resolve_source_import_skeleton()
        report["source_import_skeleton"] = source_import_skeleton
        source_asset, import_report = import_source(manifest, source_import_skeleton)
        report["source_import"] = import_report
        report["source_policy"] = apply_sequence_policy(source_asset, manifest)
        report["source_sequence"] = sequence_report(source_asset, source_import_skeleton)
        report["control_case_sequence"] = sequence_report(CONTROL_CASE, CONTROL_SKELETON, CONTROL_PROBE_BONE)
        target_asset, retarget_report = retarget_source(source_asset, manifest)
        report["retarget"] = retarget_report
        report["target_policy"] = apply_sequence_policy(target_asset, manifest)
        speed_evidence = manifest.get("speed_evidence")
        try:
            declared_speed = float(speed_evidence.get("speed_cm_s")) if isinstance(speed_evidence, dict) else -1.0
        except (TypeError, ValueError):
            declared_speed = -1.0
        allow_static_speed = (
            isinstance(speed_evidence, dict)
            and speed_evidence.get("mode") == "static_pose"
            and declared_speed == 0.0
        )
        report["target_sequence"] = sequence_report(
            target_asset,
            TARGET_SKELETON,
            allow_static_speed=allow_static_speed,
        )
        report["source_save"] = save_confirmation(source_asset)
        report["target_save"] = save_confirmation(target_asset)
        report["root_motion_policy"] = root_motion_check(report["target_sequence"], manifest)
        report["measured_speed"] = report["target_sequence"].get("root_motion_measurement", {})
        report["contact_audit"] = contact_audit_check(manifest)
        report["pie_smoke"] = pie_smoke_check()
        report["checks"] = {
            "source_sequence": not report["source_sequence"]["errors"],
            "control_case": not report["control_case_sequence"]["errors"],
            "target_sequence": not report["target_sequence"]["errors"],
            "target_skeleton": TARGET_SKELETON in report["target_sequence"].get("skeleton", ""),
            "source_manifest_canonical": manifest.get("canonical_rig") == "SK_Source_Melusina",
            "target_mesh": (
                TARGET_MESH.endswith("SK_Melusina")
                and TARGET_SKELETON in report["retarget"].get("target_mesh_skeleton_after", "")
            ),
            "source_save": report["source_save"].get("saved") is True,
            "target_save": report["target_save"].get("saved") is True,
            "root_motion_policy_runtime": report["root_motion_policy"]["passed"],
            "measured_speed": report["measured_speed"].get("verified") is True,
            "foot_contact_audit": report["contact_audit"]["passed"],
            "pie_smoke": report["pie_smoke"]["ok"],
        }
        report["staging_ok"] = all(
            report["checks"][key]
            for key in (
                "source_sequence", "control_case", "target_sequence", "target_skeleton",
                "source_manifest_canonical", "target_mesh", "source_save",
                "target_save", "root_motion_policy_runtime",
            )
        )
        report["ok"] = report["staging_ok"]
        report["promotion_blockers"] = [
            key for key, passed in report["checks"].items() if not passed
        ]
        report["promotion_allowed"] = report["ok"] and not report["promotion_blockers"]
    except Exception as exc:
        report["errors"].append(str(exc))
        report["promotion_blockers"] = ["pilot_execution_failed"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("[MUAL] " + json.dumps(report))
    return report


main()
