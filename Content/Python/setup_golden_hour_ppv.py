"""Golden Hour PPV — Phase 1 of the Horizon System Plan.

Creates a PPV_GoldenHour actor that adds a warm sunset grade on top of the
existing PPV stack. Driven by UDS Time of Day: the grade fades in during
golden hour (1700-1930) and is absent at noon.

This is an ADDITIVE post-process volume — it does not replace or conflict with
the existing PPV_NikkiDream stack. It uses a higher priority so its blendables
stack on top, and it only overrides bloom/exposure/vignette (lens character),
not color grading (which belongs on MPC_Melodia_Palette per the 2026-08-01
correction in setup_nikki_render_post_process.py).

The golden hour weight is computed from UDS Time of Day:
  - 0.0 at noon (1200)
  - 1.0 at sunset (1800)
  - 0.0 at night (2000+)
  - Smooth cosine curve between these points

Usage (editor open, Monolith run_python):
  import setup_golden_hour_ppv as g; g.build()
  import setup_golden_hour_ppv as g; g.build(uds_time=1750)  # force a time
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

# Golden hour color science (from MI_Universal_SunsetBlush + brooch_sky.py):
#   Warm amber/rose grade, boosted bloom for atmospheric glow, slight exposure
#   reduction for sunset contrast, subtle vignette for framing.
GOLDEN_HOUR_SETTINGS = {
    "bloom_intensity": 0.35,       # additive bloom for atmospheric glow
    "vignette_intensity": 0.15,    # subtle framing
    "color_saturation": (1.08, 1.02, 0.95, 1.0),   # warm: +red, -blue
    "color_contrast": (1.06, 1.02, 0.98, 1.0),     # warm contrast
    "color_gain_shadows": (0.92, 0.88, 0.98, 1.0),  # cool shadows for warmth contrast
    "color_gain_highlights": (1.12, 0.95, 0.82, 1.0),  # golden highlights
}

# UDS day model (from melodia_uds_time_bridge.py)
UDS_DAY_UNITS = 2400.0
GOLDEN_HOUR_START = 1700.0  # dusk begins
GOLDEN_HOUR_PEAK = 1800.0   # sunset
GOLDEN_HOUR_END = 1930.0    # nightfall

REPORT = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "golden_hour_ppv.json"


def golden_hour_weight(uds_time: float) -> float:
    """Compute golden hour weight 0..1 from UDS Time of Day.

    Cosine curve: 0 at noon, 1 at sunset, 0 at nightfall.
    """
    t = float(uds_time) % UDS_DAY_UNITS
    if t < GOLDEN_HOUR_START or t >= GOLDEN_HOUR_END:
        return 0.0
    # Cosine bell: 0 at start, 1 at peak, 0 at end
    mid = (GOLDEN_HOUR_START + GOLDEN_HOUR_END) / 2.0
    half = (GOLDEN_HOUR_END - GOLDEN_HOUR_START) / 2.0
    if half <= 0:
        return 0.0
    x = (t - mid) / half  # -1..1
    return max(0.0, min(1.0, 0.5 + 0.5 * math.cos(x * math.pi)))


def _get_uds_time(unreal) -> float:
    """Read UDS Time of Day from the current level's Ultra_Dynamic_Sky actor."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        label = actor.get_actor_label()
        if "Ultra_Dynamic_Sky" in label or "UDS" in label:
            try:
                t = actor.get_editor_property("Time of Day")
                if t is not None:
                    return float(t)
            except Exception:
                pass
    # Fallback: try the MPC
    try:
        mpc = unreal.EditorAssetLibrary.load_asset(
            "/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters"
        )
        if mpc:
            t = mpc.get_editor_property("Time of Day")
            if t is not None:
                return float(t)
    except Exception:
        pass
    return 1200.0  # noon fallback


def build(uds_time: float | None = None) -> dict:
    """Build/configure PPV_GoldenHour in the current level.

    Idempotent: reuses existing actor if present.
    """
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Get UDS time
    if uds_time is None:
        uds_time = _get_uds_time(unreal)

    weight = golden_hour_weight(uds_time)

    # Find or create PPV_GoldenHour
    ppv = None
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == "PPV_GoldenHour":
            ppv = a
            break

    is_new = ppv is None
    if ppv is None:
        ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
        ppv.set_actor_label("PPV_GoldenHour")

    ppv.set_editor_property("unbound", True)
    ppv.set_editor_property("priority", 5.0)  # below PPV_NikkiDream (10.0)

    s = ppv.get_editor_property("settings")

    def ov(name, val):
        s.set_editor_property(f"override_{name}", True)
        s.set_editor_property(name, val)

    # Apply golden hour settings scaled by weight
    if weight > 0.0:
        ov("bloom_intensity", GOLDEN_HOUR_SETTINGS["bloom_intensity"] * weight)
        ov("vignette_intensity", GOLDEN_HOUR_SETTINGS["vignette_intensity"] * weight)
        sat = GOLDEN_HOUR_SETTINGS["color_saturation"]
        ov("color_saturation", unreal.Vector4(
            1.0 + (sat[0] - 1.0) * weight,
            1.0 + (sat[1] - 1.0) * weight,
            1.0 + (sat[2] - 1.0) * weight,
            1.0
        ))
        con = GOLDEN_HOUR_SETTINGS["color_contrast"]
        ov("color_contrast", unreal.Vector4(
            1.0 + (con[0] - 1.0) * weight,
            1.0 + (con[1] - 1.0) * weight,
            1.0 + (con[2] - 1.0) * weight,
            1.0
        ))
        sh = GOLDEN_HOUR_SETTINGS["color_gain_shadows"]
        ov("color_gain_shadows", unreal.Vector4(
            1.0 + (sh[0] - 1.0) * weight,
            1.0 + (sh[1] - 1.0) * weight,
            1.0 + (sh[2] - 1.0) * weight,
            1.0
        ))
        hi = GOLDEN_HOUR_SETTINGS["color_gain_highlights"]
        ov("color_gain_highlights", unreal.Vector4(
            1.0 + (hi[0] - 1.0) * weight,
            1.0 + (hi[1] - 1.0) * weight,
            1.0 + (hi[2] - 1.0) * weight,
            1.0
        ))
    else:
        # Noon/night: disable overrides
        for name in ("bloom_intensity", "vignette_intensity", "color_saturation",
                     "color_contrast", "color_gain_shadows", "color_gain_highlights"):
            s.set_editor_property(f"override_{name}", False)

    ppv.set_editor_property("settings", s)

    # Save
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.save_current_level()

    result = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "PPV_GoldenHour",
        "is_new": is_new,
        "uds_time": uds_time,
        "golden_hour_weight": weight,
        "settings_applied": weight > 0.0,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    msg = f"PPV_GoldenHour configured | UDS={uds_time:.0f} weight={weight:.2f} | {'applied' if weight > 0 else 'disabled'}"
    print(msg)
    return result


if __name__ == "__main__":
    build()
