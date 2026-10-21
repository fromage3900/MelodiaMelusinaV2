#!/usr/bin/env python
"""In-editor sampler for Sir Melodious's flight mechanics.

Run inside the editor (or PIE) with:

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/sir_flight_probe.py"

It registers a per-frame callback and writes a JSON receipt to
Saved/Audit/SirFlight_20261021/sir_flight_probe.json continuously, so the
receipt is current whenever the run is inspected. Nothing is asserted here:
the receipt is evidence, and the pass/fail judgement is made by reading it.

What is sampled, per tick:
  - the possessed pawn's class, world Z and vertical velocity
  - the character movement's MaxFlySpeed (cruise vs boost)
  - the height-axis flags and the vertical rate cap
  - the perch state and the crest-raise weight

Real key input is delivered separately by Tools/Editor/sir_flight_keys.py,
through the editor's own window-message path, so the bindings and the edge
detection are exercised rather than bypassed.
"""
from __future__ import annotations

import json
import os
import time

import unreal

OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\SirFlight_20261021"
OUT_FILE = os.path.join(OUT_DIR, "sir_flight_probe.json")
SAMPLE_INTERVAL = 0.05

_samples = []
_last_write = 0.0
_started = time.time()
_run_id = "sir-flight-probe-%d" % int(_started)


def _player_pawn():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if world is None:
        world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
    if world is None:
        return None, None
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    if controller is None:
        return None, world
    return controller.get_pawn(), world


def _read(pawn, name, default=None):
    try:
        return pawn.get_editor_property(name)
    except Exception:
        return default


def _call(pawn, fn_name, default=None):
    """Call a BlueprintPure accessor on the pawn, falling back to a property."""
    fn = getattr(pawn, fn_name, None)
    if fn is not None:
        try:
            return fn()
        except Exception:
            pass
    return default


def _sample():
    global _last_write
    pawn, _world = _player_pawn()
    row = {"t": round(time.time() - _started, 3)}

    if pawn is None:
        row["pawn"] = None
    else:
        row["pawn"] = pawn.get_name()
        row["pawn_class"] = pawn.get_class().get_name()
        try:
            loc = pawn.get_actor_location()
            row["z"] = round(loc.z, 2)
            row["x"] = round(loc.x, 2)
            row["y"] = round(loc.y, 2)
        except Exception:
            pass
        try:
            row["vz"] = round(pawn.get_velocity().z, 2)
            row["speed"] = round(pawn.get_velocity().size(), 2)
        except Exception:
            pass

        movement = pawn.get_component_by_class(unreal.CharacterMovementComponent) if hasattr(
            pawn, "get_component_by_class") else None
        if movement is not None:
            try:
                row["max_fly_speed"] = round(float(movement.get_editor_property("max_fly_speed")), 1)
            except Exception:
                pass

        row["ascending"] = bool(_read(pawn, "b_is_ascending", False))
        row["descending"] = bool(_read(pawn, "b_is_descending", False))
        row["perched"] = bool(_call(pawn, "is_perched", _read(pawn, "b_is_perched", False)))
        row["perch_approaching"] = bool(_read(pawn, "b_is_perch_approaching", False))
        row["crest_raise"] = round(float(_call(pawn, "get_crest_raise", 0.0) or 0.0), 4)
        row["vertical_cap"] = round(float(_call(pawn, "get_vertical_speed_cap", 0.0) or 0.0), 1)

    _samples.append(row)
    now = time.time()
    if now - _last_write > 0.75 or len(_samples) == 1:
        _last_write = now
        _flush()


def _flush():
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT_FILE, "w", encoding="utf-8") as fh:
            json.dump({
                "run_id": _run_id,
                "started": _started,
                "sample_interval_s": SAMPLE_INTERVAL,
                "sample_count": len(_samples),
                "samples": _samples,
            }, fh, indent=1)
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning("[sir_flight_probe] write failed: %s" % exc)


def _tick(delta_seconds):
    try:
        _sample()
    except Exception as exc:  # noqa: BLE001
        unreal.log_error("[sir_flight_probe] sample failed: %s" % exc)


def _begin():
    global _samples, _started, _run_id
    _samples = []
    _started = time.time()
    _run_id = "sir-flight-probe-%d" % int(_started)
    unreal.register_slate_post_tick_callback(_tick)
    unreal.log("[sir_flight_probe] started run_id=%s -> %s" % (_run_id, OUT_FILE))
    _sample()


def _end():
    try:
        unreal.unregister_slate_post_tick_callback(_tick)
    except Exception:
        pass
    _flush()
    unreal.log("[sir_flight_probe] stopped; %d samples" % len(_samples))


if __name__ == "__main__":
    _begin()
