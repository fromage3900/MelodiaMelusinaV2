"""Finalize the cinematic/lookdev PPV stack on regression maps.

Captured live state on ZenForestTest 2026-08-27 (per
`Saved/Audit/ppv_live_state_zenforesttest_2026-08-27.json`):

  PPV_NikkiDream
    unbound=True, enabled=True, priority=10.0
    weighted_blendables (4):
      1.0  MI_StorybookOutline_Premium_Hero_Dream
      1.0  MI_StarryNight_Hero
      1.0  MI_MeluColorGrade_PortfolioHero
      0.31 MI_MelodiaInk_PortfolioHero
    scene overrides: bloom 1.0, vignette 0, scene_fringe 0, film_grain 0

This script is deliberately not the gameplay shipping author. It applies the
StarryNight hero stack to the two lookdev/regression maps only:

  /Game/EnvSandbox/Environments/L_FallenMoon
  /Game/EnvSandbox/_Template/L_Template

It is IDEMPOTENT: re-running it leaves existing PPV_NikkiDream actors
configured correctly (it doesn't add a second one, doesn't change the
blendable order, doesn't bump priority above 10).

What it does:
  1. Load each level (un-attended; saves not called on load).
  2. Find or spawn PPV_NikkiDream.
  3. Set unbound=True, enabled=True, priority=10.0.
  4. Build WeightedBlendables with the 4 MIs at the exact weights.
  5. Strip 7 color-grading scene overrides (vignette, scene_fringe,
     film_grain, color_saturation, color_contrast, color_gain_shadows,
     color_gain_highlights) to keep the master Nikki group as the
     single source of scene-wide grading.
     (Bloom 1.0 is preserved as lens character.)
  6. Save the level.
  7. Write a per-level result row to the consolidated manifest.
  8. At the end, write Saved/Audit/ppv_shipping_hero_2026-08-27.json with
     the full report.

This script is intended to be run once via:
  python -c "import finalize_ppv_hero_stack as f; f.main()"
after first running strip_ppv_color_overrides-style code in the live editor.

Per BS_GodFile/_AGENT_WORKING_AGREEMENT.md: this script is a single,
additive change to the project. It does not edit M_Master_Toon_Universal,
does not edit any C++ source, does not introduce a new system.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ppv_shipping_hero_2026-08-27.json"

from ppv_contract import LOOKDEV_REGRESSION_LEVELS

# StarryNight remains cinematic/lookdev-only.
SHIPPING_LEVELS = LOOKDEV_REGRESSION_LEVELS

# Live ZenForestTest 4-blendable hero stack (captured 2026-08-27)
HERO_BLENDABLES = (
    ("MI_StorybookOutline_Premium_Hero_Dream", 1.0,
     "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_Premium_Hero_Dream.MI_StorybookOutline_Premium_Hero_Dream"),
    ("MI_StarryNight_Hero", 1.0,
     "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StarryNight_Hero.MI_StarryNight_Hero"),
    ("MI_MeluColorGrade_PortfolioHero", 1.0,
     "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero.MI_MeluColorGrade_PortfolioHero"),
    ("MI_MelodiaInk_PortfolioHero", 0.31,
     "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_PortfolioHero.MI_MelodiaInk_PortfolioHero"),
)

# Properties to STRIP (set override_*=False, restore engine default)
# Color-grading scene overrides duplicate the master Nikki group.
GRADING_PROPS = (
    "vignette_intensity",
    "scene_fringe_intensity",
    "film_grain_intensity",
    "color_saturation",
    "color_contrast",
    "color_gain_shadows",
    "color_gain_highlights",
)


def _ensure_assets() -> list[str]:
    """Pre-flight: every blendable asset must exist before we touch any level."""
    import unreal
    missing = []
    for (_name, _w, path) in HERO_BLENDABLES:
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            missing.append(path)
    return missing


def _apply_to_level(level: str) -> dict:
    """Apply the hero stack to one level. Caller guarantees the editor is open."""
    import unreal
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    leaf = level.rsplit("/", 1)[-1]
    if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
        return {"level": level, "status": "missing"}
    if not les.load_level(level):
        return {"level": level, "status": "load_failed"}
    ppv = next((a for a in eas.get_all_level_actors() or []
                if a.get_actor_label() == "PPV_NikkiDream"), None)
    spawned = False
    if ppv is None:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label("PPV_NikkiDream")
        spawned = True
    ppv.set_editor_property("unbound", True)
    ppv.set_editor_property("enabled", True)
    ppv.set_editor_property("priority", 10.0)
    settings = ppv.get_editor_property("settings")
    # Build the 4-blendable stack
    blendables = []
    for (_name, weight, path) in HERO_BLENDABLES:
        mat = unreal.load_asset(path)
        if mat is None:
            return {"level": level, "status": "blendable_missing", "missing": path,
                    "spawned": spawned}
        blendables.append(unreal.WeightedBlendable(weight, mat))
    settings.set_editor_property("weighted_blendables",
                                 unreal.WeightedBlendables(blendables))
    # Strip 7 grading scene overrides; bloom_intensity is left as-is.
    stripped = []
    for prop in GRADING_PROPS:
        try:
            if settings.get_editor_property(f"override_{prop}"):
                settings.set_editor_property(f"override_{prop}", False)
                stripped.append(prop)
        except Exception as exc:
            stripped.append(f"{prop}:ERR({exc})")
    ppv.set_editor_property("settings", settings)
    les.save_current_level()
    return {
        "level": level,
        "status": "applied",
        "spawned": spawned,
        "priority": 10.0,
        "blendable_count": len(blendables),
        "stripped_overrides": stripped,
    }


def main() -> int:
    import unreal
    missing = _ensure_assets()
    if missing:
        unreal.log_error(f"[PPV hero] missing blendable assets: {missing}")
        return 1
    results = []
    for level in SHIPPING_LEVELS:
        row = _apply_to_level(level)
        results.append(row)
    report = {
        "schema": "ppv.shipping_hero.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": "ZenForestTest live state 2026-08-27",
        "levels": results,
        "blendable_template": [
            {"name": n, "weight": w, "path": p} for (n, w, p) in HERO_BLENDABLES
        ],
        "ok": all(r.get("status") == "applied" for r in results),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[PPV hero] manifest -> {REPORT_PATH}")
    for r in results:
        unreal.log(f"  {r.get('level')}: {r.get('status')}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
