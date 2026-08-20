"""Guarded Unreal-Python fallback for one MUAL BlendSpace promotion.

The normal universal-lane writer is ``Tools/animation_import_pipeline/live_promotion.py``
through Monolith.  This commandlet exists for the documented case where the
interactive editor is open but its Monolith port is temporarily unavailable.
It performs the same fail-closed checks in-process, backs up the live sample
array, mutates one speed-zero sample only, saves the BlendSpace package, and
verifies the result before updating the v2 manifest.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
MANIFEST = PROJECT / "Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.manifest.json"
UE_REPORT = PROJECT / "Saved/Audit/melusina_ue_source_pilot.json"
PLAN = PROJECT / "Saved/Audit/mual_promotion_blender_idle.json"
OUTPUT = PROJECT / "Saved/Audit/mual_live_promotion_blendspace.json"
BACKUP_DIR = PROJECT / "Saved/Audit/mual_promotion_backups"
BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
ANIMATION = "/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/A_BL_Source_Idle_Loop__MUAL_TARGET"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
SPEED = 0.0


def path_of(value) -> str:
    return value.get_path_name().split(".", 1)[0] if value else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def samples_of(blend) -> list[dict]:
    rows = []
    for index, sample in enumerate(prop(blend, "sample_data", []) or []):
        value = prop(sample, "sample_value")
        rows.append({
            "index": index,
            "animation": path_of(prop(sample, "animation")),
            "x": float(value.x) if value else None,
            "y": float(value.y) if value else None,
            "z": float(value.z) if value else None,
            "rate_scale": float(prop(sample, "rate_scale", 1.0) or 1.0),
        })
    return rows


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def update_manifest() -> None:
    manifest = read_json(MANIFEST)
    targets = list(manifest.get("promotion_targets") or [])
    prior = str(manifest.get("promotion_target") or "")
    if prior and prior not in targets:
        targets.append(prior)
    if BLENDSPACE not in targets:
        targets.append(BLENDSPACE)
    manifest["status"] = "promoted"
    manifest["promotion_targets"] = targets
    manifest["promotion_target"] = BLENDSPACE
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    report = {
        "schema": "melodia.mual_live_promotion.v1",
        "backend": "unreal_python_commandlet",
        "apply": True,
        "manifest": str(MANIFEST),
        "ue_report": str(UE_REPORT),
        "plan": str(PLAN),
        "animation": ANIMATION,
        "consumer": "blendspace",
        "started_at": started,
        "ok": False,
        "promotion_allowed": False,
        "errors": [],
        "blockers": [],
    }
    try:
        manifest = read_json(MANIFEST)
        ue_report = read_json(UE_REPORT)
        plan = read_json(PLAN)
        required_manifest = {
            "status": {"canonical", "promoted"},
            "canonical_rig": "SK_Source_Melusina",
            "canonical_skeleton": "/Game/Melodia/Mocap/Source/SK_Source_Melusina",
            "target_skeleton": TARGET_SKELETON,
            "target_mesh": "/Game/Melodia/Characters/Melusina/SK_Melusina",
            "retarget_profile": "RTG_Source_to_Melusina",
            "fps": 30,
            "units": "cm",
        }
        for key, expected in required_manifest.items():
            actual = manifest.get(key)
            if isinstance(expected, set):
                if actual not in expected:
                    raise RuntimeError(f"manifest {key} is {actual!r}")
            elif actual != expected:
                raise RuntimeError(f"manifest {key} is {actual!r}, expected {expected!r}")
        if not ue_report.get("ok") or not ue_report.get("staging_ok"):
            raise RuntimeError("UE staging/retarget report is not successful")
        if not plan.get("promotion_allowed") or not plan.get("replace_existing_speed"):
            raise RuntimeError("offline speed-zero replacement plan is not allowed")
        measured = plan.get("measured_speed")
        if measured is None or abs(float(measured) - SPEED) > 0.01:
            raise RuntimeError(f"plan speed {measured!r} is not the verified speed-zero idle")

        blend = unreal.load_asset(BLENDSPACE)
        animation = unreal.load_asset(ANIMATION)
        if not blend or not animation:
            raise RuntimeError("BlendSpace or target animation is missing")
        blend_skeleton = path_of(prop(blend, "skeleton"))
        animation_skeleton = path_of(prop(animation, "skeleton"))
        if blend_skeleton != TARGET_SKELETON or animation_skeleton != TARGET_SKELETON:
            raise RuntimeError(f"target skeleton mismatch: blend={blend_skeleton!r}, animation={animation_skeleton!r}")

        before = samples_of(blend)
        if any(row["animation"] == ANIMATION for row in before):
            raise RuntimeError("target animation is already a live BlendSpace sample")
        replacements = [row for row in before if row["x"] is not None and abs(row["x"] - SPEED) < 0.01]
        if len(replacements) != 1:
            raise RuntimeError(f"expected exactly one speed-zero sample, found {len(replacements)}")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = BACKUP_DIR / f"{stamp}_blendspace_headless.json"
        write_json(backup, {
            "consumer": "blendspace",
            "asset": BLENDSPACE,
            "backend": "unreal_python_commandlet",
            "before": before,
            "replacement_rows": replacements,
            "manifest": str(MANIFEST),
        })

        kept = []
        replaced = False
        for sample in list(prop(blend, "sample_data", []) or []):
            value = prop(sample, "sample_value")
            x = float(value.x) if value else None
            if not replaced and x is not None and abs(x - SPEED) < 0.01:
                sample.set_editor_property("animation", animation)
                sample.set_editor_property("rate_scale", 1.0)
                replaced = True
            kept.append(sample)
        if not replaced:
            raise RuntimeError("speed-zero sample disappeared before mutation")
        blend.modify()
        blend.set_editor_property("sample_data", kept)
        if hasattr(blend, "validate_sample_data"):
            blend.validate_sample_data()
        if hasattr(blend, "resample_data"):
            blend.resample_data()
        package = blend.get_outermost()
        saved = bool(unreal.EditorLoadingAndSavingUtils.save_packages([package], False))
        saved_loaded = bool(unreal.EditorAssetLibrary.save_loaded_asset(blend, False))
        if not saved or not saved_loaded:
            raise RuntimeError("BlendSpace package save failed; another editor likely owns the package lock")
        after = samples_of(blend)
        matches = [row for row in after if row["animation"] == ANIMATION and row["x"] is not None and abs(row["x"] - SPEED) < 0.01]
        old_animation = replacements[0]["animation"]
        old_still_present = any(row["animation"] == old_animation and row["x"] is not None and abs(row["x"] - SPEED) < 0.01 for row in after)
        if len(matches) != 1 or len(after) != len(before) or old_still_present:
            raise RuntimeError("BlendSpace verification failed after save")

        update_manifest()
        report.update({
            "ok": True,
            "promotion_allowed": True,
            "rollback_backup": str(backup),
            "result": {
                "consumer": "blendspace",
                "asset": BLENDSPACE,
                "animation": ANIMATION,
                "measured_speed": SPEED,
                "skeleton": blend_skeleton,
                "before": before,
                "after": after,
                "replaced": replacements,
                "saved": saved,
                "saved_loaded": saved_loaded,
                "manifest_updated": True,
            },
        })
    except Exception as exc:
        report["errors"].append(str(exc))
        report["blockers"].append("live_promotion_not_verified")
    write_json(OUTPUT, report)
    unreal.log("[MUAL] " + json.dumps(report, separators=(",", ":")))
    return report


if __name__ == "__main__":
    main()
