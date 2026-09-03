"""REVERT 2026-08-18 — restore the pre-run PPV_NikkiDream stack on every level.

setup_nikki_render_post_process.py was re-run 2026-08-18 04:57 without owner
sign-off; it swapped outline/grade profiles and attached the ink layer live.
This restores the exact pre-run state (per nikki_post_process_audit.json
2026-08-01): outline=MI_PP_StorybookOutline@1.0, grade=M_PP_MeluColorGrade@0.69,
no ink. L_Template's PPV_NikkiDream (spawned by that run) is removed. The
editor is left on ZenForestTest (where the user was).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "ppv_stack_revert_2026_08_18.json"

LEVELS = (
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/ZenForestTest",
    "/Game/EnvSandbox/_Template/L_Template",
)

OUTLINE = "/Game/EnvSandbox/Materials/PostProcess/MI_PP_StorybookOutline"
GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"


def main() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results: list[dict] = []

    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        rec = {"level": level, "status": "ok"}
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            rec["status"] = "missing"
            results.append(rec)
            continue
        les.load_level(level)
        ppv = next((a for a in eas.get_all_level_actors() or []
                    if a.get_actor_label() == "PPV_NikkiDream"), None)
        if leaf == "L_Template":
            if ppv is not None:
                eas.destroy_actor(ppv)
                rec["action"] = "removed_spawned_ppv"
            else:
                rec["action"] = "no_ppv_present"
            les.save_current_level()
            results.append(rec)
            continue
        if ppv is None:
            rec["status"] = "no_ppv"
            results.append(rec)
            continue
        settings = ppv.get_editor_property("settings")
        outline = unreal.load_asset(OUTLINE)
        grade = unreal.load_asset(GRADE)
        settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables([
            unreal.WeightedBlendable(1.0, outline),
            unreal.WeightedBlendable(0.69, grade),
        ]))
        ppv.set_editor_property("settings", settings)
        les.save_current_level()
        rec["action"] = "restored_outline+grade"
        results.append(rec)

    les.load_level("/Game/ZenForestTest")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "levels": results,
        "ok": all(r["status"] == "ok" for r in results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)