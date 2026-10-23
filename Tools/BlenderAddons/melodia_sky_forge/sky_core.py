# Melodia Sky Forge - pure-Python core (no bpy).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Loads/validates the sky theme library, computes sun direction vectors, and
# flattens a theme into the TouchDesigner/UE sidecar parameter dict. Everything
# here must import without Blender so `python -m unittest` can guard it and so a
# TD-side reader can reuse the same flattening rules.

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

LIBRARY_RELPATH = Path("specs") / "sky_themes" / "melodia_sky_themes.v1.json"
SCHEMA_ID = "melodia.sky_theme.v1"
LIBRARY_SCHEMA_ID = "melodia.sky_theme_library.v1"

# Same vocabulary as specs/schemas/world_recipe.v1.schema.json identity block.
MODE_IDS = ("ionian", "dorian", "lydian", "aeolian", "phrygian")

# v1.1 band profiles: mode flavor of the band SHAPE (step count stays
# banding_steps). 'auto' in a theme resolution falls through to this map.
MODE_BAND_PROFILES = {
    "ionian": "wide",        # big soft steps, open feel
    "dorian": "gradual",     # even steps
    "lydian": "halo",        # elevated bloom band above the sun
    "aeolian": "narrow",     # tight dark bands
    "phrygian": "cracked",   # hard semitone-tension step pair
}
BAND_PROFILES = ("auto", "wide", "gradual", "halo", "narrow", "cracked")
SUN_KEYING_MODES = ("explicit", "root_pitch_class")


def repo_root() -> Path:
    """Active checkout is authority - walk up from this file to the .uproject."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "BS_GodFile.uproject").is_file():
            return parent
    raise RuntimeError("BS_GodFile.uproject not found above " + str(here))


def default_library_path() -> Path:
    return repo_root() / LIBRARY_RELPATH


def load_library(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else default_library_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    errors = validate_library(data)
    if errors:
        raise ValueError("sky theme library invalid:\n  " + "\n  ".join(errors))
    return data


def validate_theme(theme: dict[str, Any], prefix: str = "theme") -> list[str]:
    errors: list[str] = []

    def err(msg: str) -> None:
        errors.append(f"{prefix}: {msg}")

    if theme.get("schema") != SCHEMA_ID:
        err(f"schema must be {SCHEMA_ID!r}")
    theme_id = theme.get("theme_id")
    if not isinstance(theme_id, str) or not theme_id[:1].islower() or not theme_id.replace("_", "a").isalnum():
        err("theme_id must be snake_case")

    musical = theme.get("musical")
    if not isinstance(musical, dict):
        err("musical block missing")
    else:
        if musical.get("mode_id") not in MODE_IDS:
            err(f"musical.mode_id must be one of {MODE_IDS}")
        rpc = musical.get("root_pitch_class")
        if not isinstance(rpc, int) or not 0 <= rpc <= 11:
            err("musical.root_pitch_class must be an int in [0,11]")
        bpm = musical.get("bpm")
        if bpm is not None and (not isinstance(bpm, int) or not 40 <= bpm <= 220):
            err("musical.bpm must be an int in [40,220]")

    sky = theme.get("sky")
    if not isinstance(sky, dict):
        err("sky block missing")
        return errors

    def check_rgb(value: Any, name: str) -> None:
        if (not isinstance(value, list) or len(value) != 3
                or any(not isinstance(c, (int, float)) or not 0.0 <= c <= 1.0 for c in value)):
            err(f"{name} must be [r,g,b] floats in 0..1")

    grad = sky.get("gradient")
    if not isinstance(grad, dict):
        err("sky.gradient missing")
    else:
        for key in ("zenith", "horizon", "nadir"):
            check_rgb(grad.get(key), f"sky.gradient.{key}")
        steps = grad.get("banding_steps", 0)
        if not isinstance(steps, int) or not 0 <= steps <= 32:
            err("sky.gradient.banding_steps must be an int in [0,32]")
        profile = grad.get("banding_profile", "auto")
        if profile not in BAND_PROFILES:
            err(f"sky.gradient.banding_profile must be one of {BAND_PROFILES}")

    motion = sky.get("motion", {})
    if not isinstance(motion, dict):
        err("sky.motion must be an object")
    else:
        for mkey, lo, hi in (("cloud_drift_per_beat", 0.0, 8.0), ("aurora_pulse_per_beat", 0.0, 1.0)):
            val = motion.get(mkey, 0.0)
            if not isinstance(val, (int, float)) or not lo <= val <= hi:
                err(f"sky.motion.{mkey} must be a number in [{lo},{hi}]")

    sun = sky.get("sun")
    if not isinstance(sun, dict):
        err("sky.sun missing")
    else:
        az, el = sun.get("azimuth_deg"), sun.get("elevation_deg")
        if not isinstance(az, (int, float)) or not 0 <= az <= 360:
            err("sky.sun.azimuth_deg must be in [0,360]")
        if not isinstance(el, (int, float)) or not -10 <= el <= 90:
            err("sky.sun.elevation_deg must be in [-10,90]")
        check_rgb(sun.get("color"), "sky.sun.color")
        keying = sun.get("keying", {})
        if not isinstance(keying, dict):
            err("sky.sun.keying must be an object")
        else:
            kmode = keying.get("mode", "explicit")
            if kmode not in SUN_KEYING_MODES:
                err(f"sky.sun.keying.mode must be one of {SUN_KEYING_MODES}")
            ksemi = keying.get("semitone_degrees", 30.0)
            if not isinstance(ksemi, (int, float)) or not 1 <= ksemi <= 60:
                err("sky.sun.keying.semitone_degrees must be a number in [1,60]")

    clouds = sky.get("clouds")
    if not isinstance(clouds, dict):
        err("sky.clouds missing")
    else:
        cov = clouds.get("coverage")
        if not isinstance(cov, (int, float)) or not 0 <= cov <= 1:
            err("sky.clouds.coverage must be in [0,1]")

    return errors


def validate_library(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != LIBRARY_SCHEMA_ID:
        errors.append(f"library schema must be {LIBRARY_SCHEMA_ID!r}")
    themes = data.get("themes")
    if not isinstance(themes, list) or not themes:
        return errors + ["library.themes must be a non-empty list"]
    seen: set[str] = set()
    for i, theme in enumerate(themes):
        if not isinstance(theme, dict):
            errors.append(f"themes[{i}] is not an object")
            continue
        tid = theme.get("theme_id", f"themes[{i}]")
        errors.extend(validate_theme(theme, prefix=str(tid)))
        if tid in seen:
            errors.append(f"duplicate theme_id {tid!r}")
        seen.add(tid)
    return errors


def get_theme(library: dict[str, Any], theme_id: str) -> dict[str, Any]:
    for theme in library.get("themes", []):
        if theme.get("theme_id") == theme_id:
            return theme
    raise KeyError(f"theme_id {theme_id!r} not in library")


def sun_direction(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    """Unit vector toward the sun. Azimuth 0 = +Y (north), clockwise; elevation from horizon.

    Matches the Blender world convention the builder uses (Generated-space Z up).
    """
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    ce = math.cos(el)
    return (ce * math.sin(az), -ce * math.cos(az), math.sin(el))


def band_profile(theme: dict[str, Any]) -> str:
    """Resolved band-shape profile: explicit override, else mode flavor."""
    grad = theme.get("sky", {}).get("gradient", {})
    profile = grad.get("banding_profile", "auto")
    if profile != "auto":
        return profile
    mode = theme.get("musical", {}).get("mode_id")
    return MODE_BAND_PROFILES.get(mode, "gradual")


def resolved_sun_azimuth(theme: dict[str, Any]) -> tuple[float, str]:
    """(azimuth_deg, keyed_by). Root-keyed themes rotate with the recipe key."""
    sun = theme.get("sky", {}).get("sun", {})
    keying = sun.get("keying", {})
    if keying.get("mode", "explicit") == "root_pitch_class":
        semi = keying.get("semitone_degrees", 30.0)
        rpc = theme["musical"]["root_pitch_class"]
        return ((rpc * semi) % 360.0, "root_pitch_class")
    return (sun["azimuth_deg"], "explicit")


def beat_offsets(
    frames: int,
    bpm: int,
    drift_per_beat: float = 0.0,
    aurora_pulse: float = 0.0,
    beats_per_bar: int = 4,
) -> list[dict[str, Any]]:
    """Per-frame values for a one-bar (4/4) loop bake.

    Frame 0 is the exact static sky (phase 0: zero drift, pulse multiplier 1)
    so `frames=1` renders byte-identical to a plain bake. TD maps its
    proven Beatphase input onto the phase fraction to pick a frame.
    """
    n = max(1, int(frames))
    spb = (60.0 / bpm) if bpm and bpm > 0 else 0.0
    beats: list[dict[str, Any]] = []
    for f in range(n):
        phase = f / n
        beats.append({
            "frame": f,
            "phase": phase,
            "seconds_in_bar": phase * spb * beats_per_bar,
            "cloud_w_offset": phase * drift_per_beat * beats_per_bar,
            "aurora_pulse_multiplier": 1.0 + aurora_pulse * math.sin(2.0 * math.pi * phase),
        })
    return beats


def flatten_for_td(theme: dict[str, Any]) -> dict[str, Any]:
    """Flat sidecar dict for TouchDesigner custom parameters / UE import.

    Nested theme -> flat scalar/vector keys with stable names (the TD contract).
    A TD GLSL TOP or COMP reads these; nothing here is gameplay truth.
    """
    errors = validate_theme(theme)
    if errors:
        raise ValueError("invalid theme:\n  " + "\n  ".join(errors))
    musical = theme["musical"]
    sky = theme["sky"]
    grad = sky["gradient"]
    sun = sky["sun"]
    clouds = sky["clouds"]
    stars = sky.get("stars", {})
    aurora = sky.get("aurora", {})

    az_resolved, keyed_by = resolved_sun_azimuth(theme)
    sx, sy, sz = sun_direction(az_resolved, sun["elevation_deg"])
    motion = sky.get("motion", {})
    flat: dict[str, Any] = {
        "schema": "melodia.sky_theme_flat.v1",
        "theme_id": theme["theme_id"],
        "mode_id": musical["mode_id"],
        "root_pitch_class": musical["root_pitch_class"],
        "bpm": musical.get("bpm", 0),
        "band_profile": band_profile(theme),
        "grad_zenith": list(grad["zenith"]),
        "grad_horizon": list(grad["horizon"]),
        "grad_nadir": list(grad["nadir"]),
        "grad_banding_steps": grad.get("banding_steps", 0),
        "sun_azimuth_deg": az_resolved,
        "sun_keyed_by": keyed_by,
        "sun_elevation_deg": sun["elevation_deg"],
        "sun_dir": [sx, sy, sz],
        "sun_color": list(sun["color"]),
        "sun_disc_radius_deg": sun.get("disc_radius_deg", 4.0),
        "sun_glow_strength": sun.get("glow_strength", 0.6),
        "cloud_coverage": clouds["coverage"],
        "cloud_scale": clouds.get("scale", 2.0),
        "cloud_softness": clouds.get("softness", 0.35),
        "cloud_seed": clouds.get("seed", 0),
        "cloud_lit": list(clouds.get("lit_color", [1.0, 1.0, 1.0])),
        "cloud_shadow": list(clouds.get("shadow_color", [0.5, 0.5, 0.5])),
        "star_density": stars.get("density", 0.0),
        "star_color": list(stars.get("color", [1.0, 1.0, 1.0])),
        "aurora_strength": aurora.get("strength", 0.0),
        "aurora_color_a": list(aurora.get("color_a", [0.4, 0.9, 0.7])),
        "aurora_color_b": list(aurora.get("color_b", [0.5, 0.6, 1.0])),
        "cloud_drift_per_beat": motion.get("cloud_drift_per_beat", 0.0),
        "aurora_pulse_per_beat": motion.get("aurora_pulse_per_beat", 0.0),
    }
    return flat
