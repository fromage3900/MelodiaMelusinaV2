"""Prepare, but do not prematurely activate, Melusina's current-skeleton AnimBP.

The existing BP_Melusina mesh uses SK_Melusina_Skeleton while ABP_Melusina was
authored against SK_Melusina_Skeleton_OLD. This script preserves that source
ABP, duplicates it for the runtime skeleton, and validates the existing
BS_Melusina_Locomotion samples. The new ABP is intentionally not assigned to
BP_Melusina until its AnimGraph has been authored and manually verified.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/Melodia/Characters/Melusina"
SOURCE_ABP = f"{ROOT}/ABP_Melusina"
CURRENT_ABP = f"{ROOT}/ABP_Melusina_Current"
SKELETON = f"{ROOT}/SK_Melusina_Skeleton"
BLENDSPACE = f"{ROOT}/Animations/BS_Melusina_Locomotion"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Melodia" / "melusina_current_locomotion_prepare.json"


def path_of(value) -> str:
    return value.get_path_name() if value else ""


def main() -> bool:
    report: dict[str, object] = {"ok": False, "steps": [], "warnings": [], "errors": []}
    skeleton = unreal.load_asset(SKELETON)
    blendspace = unreal.load_asset(BLENDSPACE)
    source_abp = unreal.load_asset(SOURCE_ABP)
    if not skeleton or not blendspace or not source_abp:
        report["errors"].append("Missing canonical skeleton, authored blendspace, or source AnimBP.")
    else:
        samples = []
        for sample in blendspace.get_editor_property("sample_data") or []:
            animation = sample.get_editor_property("animation")
            animation_skeleton = animation.get_editor_property("skeleton") if animation else None
            samples.append({
                "animation": path_of(animation),
                "skeleton": path_of(animation_skeleton),
                "sample_value": str(sample.get_editor_property("sample_value")),
                "valid": animation_skeleton == skeleton,
            })
        report["blendspace"] = {"path": BLENDSPACE, "samples": samples}
        if len(samples) < 3 or not all(item["valid"] for item in samples):
            report["errors"].append("Locomotion blendspace lacks three canonical-skeleton samples.")

        current_abp = unreal.load_asset(CURRENT_ABP)
        if not current_abp:
            if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE_ABP, CURRENT_ABP):
                report["errors"].append("Failed to duplicate ABP_Melusina into ABP_Melusina_Current.")
            else:
                current_abp = unreal.load_asset(CURRENT_ABP)
                report["steps"].append("Duplicated ABP_Melusina as ABP_Melusina_Current.")

        if current_abp:
            try:
                current_abp.set_editor_property("target_skeleton", skeleton)
                unreal.EditorAssetLibrary.save_asset(CURRENT_ABP, only_if_is_dirty=False)
                report["steps"].append("Set ABP_Melusina_Current target skeleton to SK_Melusina_Skeleton.")
            except Exception as exc:
                report["errors"].append(f"Could not set current AnimBP skeleton: {exc}")
            report["current_abp"] = {
                "path": CURRENT_ABP,
                "target_skeleton": path_of(current_abp.get_editor_property("target_skeleton")),
            }

        report["next_editor_step"] = (
            "In ABP_Melusina_Current, drive BS_Melusina_Locomotion from Speed in the default "
            "AnimGraph state; then assign ABP_Melusina_Current to BP_Melusina and verify in PIE."
        )
        report["ok"] = not report["errors"]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"[MelusinaLocomotion] Wrote {REPORT}")
    unreal.log(f"[MelusinaLocomotion] ok={report['ok']}")
    return bool(report["ok"])


if __name__ == "__main__":
    main()
