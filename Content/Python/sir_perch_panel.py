"""Sir Melodious perch panel -- authored landing spots, wisely placed.

Converges on the native owner: ASirPerchPoint (MelodiaCore), which
AMelodiousFlightCharacter.FindNearestPerch already iterates. Position data
is reused from setup_sir_melodious_perches.PERCHES (no second list).

Wise placement: each spawn traces down (Visibility) and rests on the first
Landscape / static-mesh hit + 30 cm; sky perches with no hit keep authored Z
and are reported, not dropped.

Menu: Melodia > Sir Perches (init_unreal._register_melodia_menu).
Offline-safe: HOLD without the editor.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import setup_sir_melodious_perches as perch_data

LABEL_PREFIX = "SirMelodiousPerch_"
REST_ABOVE_CM = 30.0


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _current_level_path(unreal) -> str | None:
    for getter in (
        lambda: unreal.EditorLevelLibrary.get_editor_world(),
        lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(),
    ):
        try:
            world = getter()
            if world is not None:
                return world.get_path_name().split(".")[0]
        except Exception:
            continue
    return None


def authored_for_level(level_path: str | None) -> list[tuple[float, float, float, str]]:
    if not level_path:
        return []
    for key, perches in perch_data.PERCHES.items():
        if level_path == key or level_path.endswith(key.split("/")[-1]):
            return list(perches)
    return []


def _trace_ground(unreal, world, x: float, y: float, z: float) -> float | None:
    """Visibility trace down; return hit Z on landscape/mesh, else None."""
    try:
        start = unreal.Vector(x, y, z + 2000.0)
        end = unreal.Vector(x, y, z - 5000.0)
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], 0, 0.0)
        if hit and hit[0]:
            blocking = hit[4] if len(hit) > 4 else None
            actor = blocking.get_actor() if blocking else None
            if actor is not None:
                return float(blocking.location.z)
    except Exception:
        pass
    return None


def list_perches() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    level = _current_level_path(unreal)
    authored = authored_for_level(level)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    placed = []
    for a in eas.get_all_level_actors():
        try:
            lbl = a.get_actor_label()
        except Exception:
            continue
        if lbl.startswith(LABEL_PREFIX):
            v = a.get_actor_location()
            placed.append({"label": lbl, "location": [v.x, v.y, v.z]})
    placed_names = {p["label"] for p in placed}
    missing = [f"{LABEL_PREFIX}{label}" for (_, _, _, label) in authored
               if f"{LABEL_PREFIX}{label}" not in placed_names]
    return {"ok": True, "level": level, "authored": len(authored),
            "placed": placed, "missing": missing}


def spawn_missing() -> dict[str, Any]:
    """Spawn authored-but-missing perches in the current level (wise Z)."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    perch_cls = getattr(unreal, "SirPerchPoint", None)
    if perch_cls is None:
        return {"ok": False, "error": "ASirPerchPoint not visible to Python (build mismatch?)"}
    state = list_perches()
    if not state.get("ok"):
        return state
    world = unreal.EditorLevelLibrary.get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    _ = eas  # listing only; spawn goes through EditorLevelLibrary
    spawned, kept_z, errors = [], [], []
    want = {f"{LABEL_PREFIX}{label}": (x, y, z)
            for (x, y, z, label) in authored_for_level(state["level"])}
    for label in state["missing"]:
        x, y, z = want[label]
        try:
            ground = _trace_ground(unreal, world, x, y, z)
            final_z = (ground + REST_ABOVE_CM) if ground is not None else z
            if ground is None:
                kept_z.append(label)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                perch_cls, unreal.Vector(x, y, final_z), unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            spawned.append({"label": label, "location": [x, y, final_z],
                            "snapped": ground is not None})
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    return {"ok": not errors, "level": state["level"], "spawned": spawned,
            "kept_authored_z": kept_z, "errors": errors}


def snap_selected() -> dict[str, Any]:
    """Drop selected perches onto traced ground (+30 cm)."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    world = unreal.EditorLevelLibrary.get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    moved, skipped = [], []
    for a in eas.get_selected_level_actors():
        try:
            lbl = a.get_actor_label()
        except Exception:
            continue
        if not lbl.startswith(LABEL_PREFIX):
            skipped.append(f"{lbl} (not a perch)")
            continue
        v = a.get_actor_location()
        ground = _trace_ground(unreal, world, v.x, v.y, v.z)
        if ground is None:
            skipped.append(f"{lbl} (no ground)")
            continue
        a.set_actor_location(unreal.Vector(v.x, v.y, ground + REST_ABOVE_CM), False, False)
        moved.append({"label": lbl, "z": ground + REST_ABOVE_CM})
    return {"ok": True, "moved": moved, "skipped": skipped}


def save_level() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    unreal.EditorLevelLibrary.save_current_level()
    return {"ok": True, "saved": True}


def menu_list_summary() -> str:
    state = list_perches()
    if not state.get("ok"):
        return f"[Perches] HOLD ({state.get('error')})"
    lines = [f"[Perches] {state['level']} authored={state['authored']} "
             f"placed={len(state['placed'])} missing={len(state['missing'])}"]
    for p in state["placed"]:
        loc = [round(c) for c in p["location"]]
        lines.append(f"  ok {p['label']} @ {loc}")
    for m in state["missing"]:
        lines.append(f"  -- {m} (not placed)")
    return "\n".join(lines)


if __name__ == "__main__":
    print(menu_list_summary())
