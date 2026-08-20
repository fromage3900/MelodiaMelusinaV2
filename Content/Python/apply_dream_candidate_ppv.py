"""Apply the DREAM CANDIDATE stack as PPV_NikkiDream in all 9 levels.

Per owner direction 2026-08-18: the updated dream candidate (outline
GameplayStandard @1.0, grade GameplayStandard @0.69, ink GameplayStandard @1.0 —
the exact composition of setup_dreamprint_ab.ensure("GameplayStandard")) IS the
live PPV everywhere. L_Template gets a PPV_NikkiDream spawned. No grade tuning
values are touched. Manifest: Saved/Audit/dream_candidate_ppv_apply.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dream_candidate_ppv_apply.json"

LEVELS = (
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/ZenForestTest",
    "/Game/EnvSandbox/_Template/L_Template",
)

_CAND = "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles"
_GRADE = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles"

STACK = (
    (f"{_CAND}/MI_StorybookOutline_GameplayStandard", 1.0),
    (f"{_GRADE}/MI_MeluColorGrade_GameplayStandard", 0.69),
    (f"{_GRADE}/MI_MelodiaInk_GameplayStandard", 1.0),
)


def main() -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    mats = []
    for path, _w in STACK:
        mat = unreal.load_asset(path)
        if not mat:
            raise RuntimeError(f"missing stack asset: {path}")
        mats.append(mat)

    results = []
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        rec = {"level": level}
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            rec["status"] = "missing"
            results.append(rec)
            continue
        les.load_level(level)
        ppv = next((a for a in eas.get_all_level_actors() or []
                    if a.get_actor_label() == "PPV_NikkiDream"), None)
        if ppv is None:
            ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
            ppv.set_actor_label("PPV_NikkiDream")
            rec["spawned"] = True
        ppv.set_editor_property("unbound", True)
        ppv.set_editor_property("enabled", True)
        settings = ppv.get_editor_property("settings")
        settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
            [unreal.WeightedBlendable(w, m) for (_, _w), m in zip(STACK, mats) if (w := _w)]))
        ppv.set_editor_property("settings", settings)
        les.save_current_level()
        rec["status"] = "ok"
        results.append(rec)

    les.load_level("/Game/ZenForestTest")
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stack": [p for p, _ in STACK],
        "levels": results,
        "ok": all(r["status"] == "ok" for r in results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)