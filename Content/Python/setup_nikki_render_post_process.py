"""Configure the canonical post-process stack: ink outline + grade + starry night.

Editor-only. Covers gameplay certification levels plus lookdev/regression levels.

Blendable stack (per-level, via PPV_NikkiDream):
  1. dreamprint_ink — ink + vine + halftone outline replacement (weight 1.0)
  2. melusina_grade — MI_MeluColorGrade_PortfolioHero (weight 0.69)
  3. starry_night   — MI_StarryNight_Hero (weight 1.0)

The dreamprint ink (M_PP_MelodiaInk) replaces the old storybook outline with
ink + vine + halftone effects. Starry night overlay (M_PP_StarryNightOverlay_Candidate)
reads UDS time-of-day, lighting, and wind, and paints Van Gogh-style brush strokes
and stars on top of the UDS sky via the post-process pipeline.

NOT unconditionally idempotent on values: if a level's PPV_NikkiDream
already has its grade overridden, a normal run leaves the existing tuning
alone and only attaches any missing blendable materials. Pass force=True
to explicitly reassert the canonical preset over existing tuning.

Color-grading overrides (saturation/contrast/shadow-highlight gain) were
removed because they duplicated M_Master_Toon_Universal's own Nikki parameter
group. Scene-wide cohesion belongs on MPC_Melodia_Palette; this volume carries
post-process lens character and the configured blendables.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from ppv_contract import GAMEPLAY_PPV_CERTIFICATION_LEVELS, LOOKDEV_REGRESSION_LEVELS

LEVELS = GAMEPLAY_PPV_CERTIFICATION_LEVELS + LOOKDEV_REGRESSION_LEVELS

BLENDABLES = (
    ("dreamprint_ink", (
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_PortfolioHero",
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard",
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk",
    )),
    ("melusina_grade", (
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero",
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard",
        "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",
    )),
    ("starry_night", (
        "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StarryNight_Hero",
        "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StarryNightOverlay_Candidate_Inst",
        "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StarryNightOverlay_Candidate",
    )),
)
REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "nikki_post_process_audit.json"

def _asset(unreal, path: str):
    return unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None

def _configure(unreal, level: str, force: bool = False) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    leaf = level.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
        return {"level": level, "status": "missing"}
    if not les.load_level(level):
        return {"level": level, "status": "load_failed"}
    ppv = next((a for a in eas.get_all_level_actors() or [] if a.get_actor_label() == "PPV_NikkiDream"), None)
    is_new = ppv is None
    if ppv is None:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label("PPV_NikkiDream")
    settings = ppv.get_editor_property("settings")
    already_tuned = bool(settings.get_editor_property("override_bloom_intensity"))
    values_written = False
    if force or not already_tuned:
        ppv.set_editor_property("unbound", True)
        ppv.set_editor_property("priority", 10.0)
        def override(name, value):
            settings.set_editor_property(f"override_{name}", True)
            settings.set_editor_property(name, value)
        override("bloom_intensity", 1.0)
        override("vignette_intensity", 0.0)
        override("film_grain_intensity", 0.0)
        override("scene_fringe_intensity", 0.0)
        values_written = True
    loaded, missing, blend_objects = [], [], []
    for role, candidates in BLENDABLES:
        for path in candidates:
            mat = _asset(unreal, path)
            if mat:
                loaded.append({"role": role, "path": path, "name": mat.get_name(),
                               "preferred": path == candidates[0]})
                blend_objects.append((role, mat))
                break
        else:
            missing.append({"role": role, "candidates": list(candidates)})
    role_weights = {"dreamprint_ink": 1.0, "melusina_grade": 0.69, "starry_night": 1.0}
    settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
        [unreal.WeightedBlendable(role_weights.get(role, 1.0), mat)
         for role, mat in blend_objects]))
    ppv.set_editor_property("settings", settings)
    les.save_current_level()
    status = "configured" if (is_new or values_written) else "blendables_only"
    return {"level": level, "status": status, "actor": ppv.get_actor_label(),
            "values_written": values_written, "blendables": loaded, "missing": missing}

def main(force: bool = False) -> int:
    import unreal
    results = [_configure(unreal, level, force=force) for level in LEVELS]
    report = {"ok": all(r["status"] in ("configured", "blendables_only", "missing") for r in results),
              "timestamp": datetime.now(timezone.utc).isoformat(), "levels": results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
