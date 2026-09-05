"""Strip residual color-grading scene overrides from PPV_NikkiDream actors.

The 2026-08-01 owner decision (`setup_nikki_render_post_process.py:30-41`) was
that scene-wide color-grading overrides on the PPV actor duplicate the master
Nikki parameter group. The production script no longer writes them, but legacy
`build_ppv_nikkidream.py:44-51` does. If that script was ever run against a
live level, the actor still carries:

  override_bloom_intensity=True   (value 0.7)
  override_vignette_intensity=True (value 0.35)
  override_scene_fringe_intensity=True (value 1.2)
  override_film_grain_intensity=True   (value 0.12)
  override_color_saturation=True       (value (1.05, 1.05, 1.08, 1.0))
  override_color_contrast=True         (value (1.04, 1.04, 1.06, 1.0))
  override_color_gain_shadows=True     (value (0.96, 0.97, 1.04, 1.0))
  override_color_gain_highlights=True  (value (1.04, 1.00, 0.98, 1.0))

This script:
  1. Discovers PPV_NikkiDream actors in the 4 gameplay certification levels.
  2. For each one, audits which overrides are set.
  3. With --apply, strips them to engine defaults (override_*=False, value=engine-default).
  4. Reports per-level what was changed, written to
     `Saved/Audit/ppv_overrides_strip.json`.

The script never touches blendable weights. The Aug-18 owner-approved
3-blendable stack (Outline + Grade + Ink) is preserved verbatim.

Manifest: Saved/Audit/ppv_overrides_strip.json

Run in editor (Monolith run_python):
    import strip_ppv_color_overrides as s
    s.audit()                 # report only
    s.apply()                 # strip on the currently open level
    s.apply_all()             # strip on every live shipping level
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ppv_contract import GAMEPLAY_PPV_CERTIFICATION_LEVELS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ppv_overrides_strip.json"

# Gameplay PPV certification surface; lookdev/regression maps are intentionally
# excluded from shipping certification.
SHIPPING_LEVELS = GAMEPLAY_PPV_CERTIFICATION_LEVELS

# Properties to audit/strip. The 8 color-grading values are scoped to PPV actor.
# Bloom is also a lens character, but the 2026-08-01 owner kept it (1.0) as a
# non-grading value, so we audit it but do not strip.
GRADING_PROPS = (
    "vignette_intensity",
    "scene_fringe_intensity",
    "film_grain_intensity",
    "color_saturation",
    "color_contrast",
    "color_gain_shadows",
    "color_gain_highlights",
)


def _get_ppv_actor(eas, label: str = "PPV_NikkiDream"):
    """Return the PPV actor in the current level, or None."""
    import unreal
    for a in eas.get_all_level_actors() or []:
        if a.get_actor_label() == label:
            return a
    return None


def _audit_ppv(ppv) -> dict:
    """Return which grading overrides are set on a PPV_NikkiDream actor."""
    import unreal
    settings = ppv.get_editor_property("settings")
    out = {"actor": ppv.get_actor_label(), "grading_overrides": {}, "bloom_intensity": None}
    for prop in GRADING_PROPS:
        ov_key = f"override_{prop}"
        try:
            if settings.get_editor_property(ov_key):
                out["grading_overrides"][prop] = {
                    "overridden": True,
                    "value": _stringify(settings.get_editor_property(prop)),
                }
        except Exception as exc:
            out["grading_overrides"][prop] = {"overridden": None, "error": str(exc)}
    if settings.get_editor_property("override_bloom_intensity"):
        out["bloom_intensity"] = {
            "overridden": True,
            "value": _stringify(settings.get_editor_property("bloom_intensity")),
        }
    return out


def _strip_ppv(ppv) -> dict:
    """Set all grading override_* to False, restoring engine defaults.

    Bloom_intensity override is left as-is (lens character, not grading).
    Blendable weights are not touched (Aug-18 stack preserved).
    """
    import unreal
    settings = ppv.get_editor_property("settings")
    changes = []
    for prop in GRADING_PROPS:
        ov_key = f"override_{prop}"
        try:
            if settings.get_editor_property(ov_key):
                settings.set_editor_property(ov_key, False)
                changes.append(prop)
        except Exception as exc:
            changes.append(f"{prop}:ERR({exc})")
    ppv.set_editor_property("settings", settings)
    return {"actor": ppv.get_actor_label(), "stripped": changes}


def _stringify(v) -> str:
    try:
        if hasattr(v, "x") and hasattr(v, "y"):
            return f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f}, {v.w:.3f})"
        return f"{v:.3f}"
    except Exception:
        return str(v)


def audit() -> dict:
    """Audit the current level. No writes."""
    import unreal
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ppv = _get_ppv_actor(eas)
    if ppv is None:
        return {"status": "no_ppv", "level": unreal.EditorLevelLibrary.get_editor_world().get_name()}
    return _audit_ppv(ppv)


def apply() -> dict:
    """Strip overrides on the current level. Saves the level."""
    import unreal
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ppv = _get_ppv_actor(eas)
    if ppv is None:
        return {"status": "no_ppv", "level": unreal.EditorLevelLibrary.get_editor_world().get_name()}
    pre = _audit_ppv(ppv)
    result = _strip_ppv(ppv)
    les.save_current_level()
    return {"status": "applied", "pre": pre, "post": result}


def apply_all() -> dict:
    """Iterate gameplay certification levels, strip overrides, and save each.

    Skips any level that fails to load (caller can inspect the per-level
    result row). Writes a single JSON report.
    """
    import unreal
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results: list[dict] = []
    for level in SHIPPING_LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        row = {"level": level}
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            row["status"] = "missing"
            results.append(row)
            continue
        if not les.load_level(level):
            row["status"] = "load_failed"
            results.append(row)
            continue
        ppv = _get_ppv_actor(eas)
        if ppv is None:
            row["status"] = "no_ppv"
            results.append(row)
            continue
        row.update(_strip_ppv(ppv))
        les.save_current_level()
        row["status"] = "applied"
        results.append(row)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "levels": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if apply_all() else 1)
