"""Configure the canonical Infinity Nikki render post-process stack.

Editor-only. Originally limited to render/test levels; extended 2026-07-31
(night render-polish pass) to also cover the 4 gameplay levels used for the
website render archive (Docs/WebsiteRenderArchive/), so they share the one
grade authority instead of drifting per-level.

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

Blendable stack replaced 2026-08-01: M_PP_ToonOutline + M_PP_StorybookVines_Inst
(two materials, duplicated edge-detection work) consolidated into one
M_PP_StorybookOutline -- real depth+normal multi-tap edge detection (not the
old single-axis ddx()-only version), CustomStencil-driven per-object style
presets, UDS time-of-day tint via the existing Day_to_Night_Color bridge, and
a merged vine-growth overlay sharing the same edge mask. Built using this
project's existing Art of Shader material-function library
(MF_StencilDepthAlpha, MF_PostProcessBlend) rather than raw duplicate logic.
M_PP_MeluColorGrade stays in the stack for its palette/framing job (not folded in --
separate scope, see Docs/Handoffs/PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md).
Old M_PP_ToonOutline/M_PP_StorybookVines/M_PP_StorybookVines_Inst quarantined,
not deleted.

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
    "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/ZenForestTest",
)
# Each role lists candidate paths in preference order; the first that loads wins.
# Instances are preferred over their master so per-level/per-shot grade tuning never
# requires editing the shared master material (which is also what makes the master
# safe to edit concurrently -- overrides for parameters the master later renames or
# drops are simply ignored by the instance).
BLENDABLES = (
    ("storybook_outline", (
        "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard",
        "/Game/EnvSandbox/Materials/PostProcess/MI_PP_StorybookOutline",
        "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_FoliageSafe_Candidate",
    )),
    ("melusina_grade", (
        "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard",
        "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",
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
    # Keep outline authoritative at full weight. The gameplay grade is deliberately
    # restrained to the established 0.69 stack weight.
    role_weights = {"storybook_outline": 1.0, "melusina_grade": 0.69}
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
