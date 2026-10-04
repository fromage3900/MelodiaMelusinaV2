"""Melodia platform speed panel -- clickable UI backend for moving platforms.

Owns nothing new. Reads/writes the existing authored properties:
  - AMelodiaMovingPlatform: TravelDuration (>= 0.1), bAutoStart, bPingPong,
    StartMotion()/StopMotion()/ResetPlatform()
  - AMelodiaWaterPlatform: MotionComponent.Speed, DockPauseSeconds

Menu entries live in init_unreal.py (Melodia > Platforms). Every function is
offline-safe: without the editor it returns HOLD instead of raising.

Usage in-editor (or via menu):
  import platform_speed_panel as psp
  unreal.log(psp.menu_list_summary())
  unreal.log(psp.menu_set_summary("0", 4.0))
"""
from __future__ import annotations

from typing import Any


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _iter_platforms(unreal) -> list[dict[str, Any]]:
    """All platform actors in the current level, moving + water."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out: list[dict[str, Any]] = []
    for actor in eas.get_all_level_actors():
        try:
            cls_name = actor.get_class().get_name()
        except Exception:
            continue
        entry: dict[str, Any] | None = None
        if cls_name == "AMelodiaMovingPlatform" or "MelodiaMovingPlatform" in cls_name:
            try:
                entry = {
                    "label": actor.get_actor_label(),
                    "class": cls_name,
                    "kind": "moving",
                    "travel_duration": float(actor.get_editor_property("TravelDuration")),
                    "auto_start": bool(actor.get_editor_property("bAutoStart")),
                    "ping_pong": bool(actor.get_editor_property("bPingPong")),
                }
            except Exception as exc:
                entry = {"label": actor.get_actor_label(), "class": cls_name,
                         "kind": "moving", "error": str(exc)}
        elif cls_name == "AMelodiaWaterPlatform" or "MelodiaWaterPlatform" in cls_name:
            try:
                motion = actor.get_editor_property("MotionComponent")
                entry = {
                    "label": actor.get_actor_label(),
                    "class": cls_name,
                    "kind": "water",
                    "speed": float(motion.get_editor_property("Speed")) if motion else None,
                    "dock_pause": float(motion.get_editor_property("DockPauseSeconds")) if motion else None,
                    "active": bool(motion.get_editor_property("bActive")) if motion else None,
                }
            except Exception as exc:
                entry = {"label": actor.get_actor_label(), "class": cls_name,
                         "kind": "water", "error": str(exc)}
        if entry is not None:
            entry["actor"] = actor
            out.append(entry)
    return out


def _resolve(unreal, ref: str):
    """Ref is a level-actor label (exact, case-insensitive) or a list index."""
    plats = _iter_platforms(unreal)
    if ref.isdigit():
        idx = int(ref)
        if 0 <= idx < len(plats):
            return plats[idx], None
        return None, f"index {idx} out of range (0..{len(plats) - 1})"
    lowered = ref.lower()
    for p in plats:
        if p["label"].lower() == lowered:
            return p, None
    near = [p["label"] for p in plats if lowered in p["label"].lower()][:5]
    hint = f" similar: {', '.join(near)}" if near else ""
    return None, f"no platform labelled '{ref}' ({len(plats)} in level).{hint}"


def list_platforms() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    plats = _iter_platforms(unreal)
    rows = []
    for i, p in enumerate(plats):
        row = {k: v for k, v in p.items() if k != "actor"}
        row["index"] = i
        rows.append(row)
    return {"ok": True, "count": len(rows), "platforms": rows}


def set_travel_duration(ref: str, seconds: float) -> dict[str, Any]:
    """Set AMelodiaMovingPlatform.TravelDuration (clamped >= 0.1)."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    plat, err = _resolve(unreal, ref)
    if err:
        return {"ok": False, "error": err}
    if plat.get("kind") != "moving":
        return {"ok": False, "error": f"'{plat['label']}' is a water platform; use set_water_speed"}
    clamped = max(0.1, float(seconds))
    plat["actor"].set_editor_property("TravelDuration", clamped)
    return {"ok": True, "label": plat["label"], "travel_duration": clamped}


def set_water_speed(ref: str, speed: float) -> dict[str, Any]:
    """Set AMelodiaWaterPlatform MotionComponent.Speed (clamped >= 0.0)."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    plat, err = _resolve(unreal, ref)
    if err:
        return {"ok": False, "error": err}
    if plat.get("kind") != "water":
        return {"ok": False, "error": f"'{plat['label']}' is a moving platform; use set_travel_duration"}
    clamped = max(0.0, float(speed))
    plat["actor"].get_editor_property("MotionComponent").set_editor_property("Speed", clamped)
    return {"ok": True, "label": plat["label"], "speed": clamped}


def set_flags(ref: str, auto_start: bool | None = None,
              ping_pong: bool | None = None) -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    plat, err = _resolve(unreal, ref)
    if err:
        return {"ok": False, "error": err}
    if plat.get("kind") != "moving":
        return {"ok": False, "error": f"'{plat['label']}' is a water platform (no auto-start flags)"}
    applied: dict[str, Any] = {}
    if auto_start is not None:
        plat["actor"].set_editor_property("bAutoStart", bool(auto_start))
        applied["auto_start"] = bool(auto_start)
    if ping_pong is not None:
        plat["actor"].set_editor_property("bPingPong", bool(ping_pong))
        applied["ping_pong"] = bool(ping_pong)
    return {"ok": True, "label": plat["label"], **applied}


def motion(ref: str, op: str) -> dict[str, Any]:
    """Start / stop / reset a moving platform (authored BlueprintCallable)."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    plat, err = _resolve(unreal, ref)
    if err:
        return {"ok": False, "error": err}
    if plat.get("kind") != "moving":
        return {"ok": False, "error": f"'{plat['label']}' is a water platform (motion is route-driven)"}
    fn = {"start": "StartMotion", "stop": "StopMotion", "reset": "ResetPlatform"}.get(op)
    if fn is None:
        return {"ok": False, "error": f"unknown op '{op}' (start/stop/reset)"}
    actor = plat["actor"]
    try:
        getattr(actor, fn)()
    except Exception:
        actor.call_method(fn, ())
    return {"ok": True, "label": plat["label"], "op": op}


def save_level() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    unreal.EditorLevelLibrary.save_current_level()
    return {"ok": True, "saved": True}


def menu_list_summary() -> str:
    state = list_platforms()
    if not state.get("ok"):
        return f"[Platforms] HOLD ({state.get('error')})"
    lines = [f"[Platforms] {state['count']} platform(s) in current level"]
    for row in state["platforms"]:
        if row.get("kind") == "moving":
            lines.append(f"  [{row['index']}] {row['label']} travel={row.get('travel_duration')}s "
                         f"auto={row.get('auto_start')} pingpong={row.get('ping_pong')}")
        else:
            lines.append(f"  [{row['index']}] {row['label']} (water) speed={row.get('speed')} "
                         f"dock={row.get('dock_pause')}s active={row.get('active')}")
    return "\n".join(lines)


def menu_set_summary(ref: str, value: float) -> str:
    """One-click setter: moving platforms take seconds, water platforms take speed."""
    unreal = _unreal()
    if unreal is None:
        return "[Platforms] HOLD (Unreal not running)"
    plat, err = _resolve(unreal, ref)
    if err:
        return f"[Platforms] {err}"
    result = set_water_speed(ref, value) if plat.get("kind") == "water" else set_travel_duration(ref, value)
    if not result.get("ok"):
        return f"[Platforms] {result.get('error')}"
    unit = "speed" if plat.get("kind") == "water" else "travel_duration"
    return f"[Platforms] {result['label']}: {unit} -> {result.get(unit)} (level save still owed)"


def selected_platform() -> dict[str, Any]:
    """The single platform actor currently selected in the level viewport."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    try:
        selected = unreal.EditorLevelLibrary.get_selected_level_actors()
    except Exception as exc:
        return {"ok": False, "error": f"selection unreadable: {exc}"}
    plats = [p for p in _iter_platforms(unreal)
             if any(p["actor"] == s for s in selected)]
    if len(plats) != 1:
        return {"ok": False, "error": f"select exactly one platform actor ({len(plats)} match selection)"}
    row = {k: v for k, v in plats[0].items() if k != "actor"}
    return {"ok": True, **row}


def menu_nudge_summary(factor: float) -> str:
    """Scale the selected platform's timing: factor > 1 = slower."""
    unreal = _unreal()
    if unreal is None:
        return "[Platforms] HOLD (Unreal not running)"
    sel = selected_platform()
    if not sel.get("ok"):
        return f"[Platforms] {sel.get('error')}"
    label = sel["label"]
    if sel.get("kind") == "water":
        result = set_water_speed(label, (sel.get("speed") or 0.15) / factor)
        unit = "speed"
    else:
        result = set_travel_duration(label, (sel.get("travel_duration") or 2.0) * factor)
        unit = "travel_duration"
    if not result.get("ok"):
        return f"[Platforms] {result.get('error')}"
    return f"[Platforms] {label}: {unit} -> {result.get(unit)} (level save still owed)"


if __name__ == "__main__":
    print(menu_list_summary())
