"""Configure the canonical post-process stack: ink outline + grade + starry night.

Editor-only. Covers all render test levels, gameplay levels, and L_Template.

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

NOT unconditionally idempotent on values as of 2026-08-01: if a level's
PPV_NikkiDream already has its grade overridden (override_bloom_intensity is
True), a normal run leaves the existing tuning alone and only attaches any
missing blendable materials. This was a real bug -- the previous version
silently reset every level's grade to the canonical preset on every run,
which is how L_FallenMoon's prior tuning got clobbered without any record of
what it was. Pass force=True to main() to explicitly reassert the canonical
preset over existing tuning (e.g. for a level being configured for the first
time in a way that skipped the guard, or a deliberate reset).

Color-grading overrides (saturation/contrast/shadow-highlight gain) were
REMOVED 2026-08-01: they duplicated M_Master_Toon_Universal's own "Nikki"
parameter group (DreamSaturation/DreamContrast/PastelLift/RimIntensity/etc,
see setup_master_universal.py), which is the project's real, already-built
grading system and defaults to neutral (0.0) by design. Stacking a second,
uncoordinated color grade on top of it via this PPV is what made the render
levels look dark/muddy -- confirmed by the owner toggling the volume
invisible and getting the correct look back. Scene-wide cohesion belongs on
MPC_Melodia_Palette (setup_portfolio_mpc.py), which the master material
already reads from, not on this volume. This volume now only carries what
post-process is actually for: bloom/vignette/grain/CA as lens character,
kept near-neutral by default.

Blendable stack replaced 2026-08-18: old storybook_outline removed,
dreamprint_ink takes over as the ink+vine+halftone outline replacement.
Starry Night sky (MI_StarryNight_Hero) added as the third blendable,
overlaying UDS via the M_PP_StarryNightOverlay_Candidate.

2026-08-01 (later): blendables are resolved from a preference list per role.
The explicit GameplayStandard profile instances are preferred, with the legacy
shared MI and foliage-safe/root masters retained only as fallbacks. Per-profile
tuning stays on instances; shared graph math stays on the authoritative masters.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

LEVELS = (
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto",
    # L_SakuraPath removed 2026-08-18: the level no longer exists in the project
    # (Sakura folder emptied; only L_Render_SakuraDream remains under _PROJECT).
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/ZenForestTest",
    "/Game/EnvSandbox/_Template/L_Template",
)
# Each role lists candidate paths in preference order; the first that loads wins.
# Instances are preferred over their master so per-level/per-shot grade tuning never
# requires editing the shared master material (which is also what makes the master
# safe to edit concurrently -- overrides for parameters the master later renames or
# drops are simply ignored by the instance).
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
    # Outline at full weight, grade restrained to 0.69, starry night at full weight.
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
    # "blendables_only" is a SUCCESS state, not a failure: it means the level already had
    # its grade tuned, the guard correctly left that tuning alone, and only the blendable
    # stack was refreshed. Omitting it here made a fully-successful run report ok=False.
    report = {"ok": all(r["status"] in ("configured", "blendables_only", "missing") for r in results),
              "timestamp": datetime.now(timezone.utc).isoformat(), "levels": results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
