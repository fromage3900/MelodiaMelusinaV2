"""Wise mesh placement -- trace-grounded snapping for level dressing.

Idiom reused from morning_resnap / level_arrangement_tools (Visibility
trace, preserve XY/rotation/scale, rest bounds-bottom on ground +
clearance). No new authority: it moves actors the designer selected.

Menu: Melodia > Placement (init_unreal._register_melodia_menu).
Offline-safe: HOLD without the editor.
"""
from __future__ import annotations

from typing import Any


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _trace_ground(unreal, world, x: float, y: float, z: float) -> tuple[float | None, str]:
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(x, y, z + 4000.0), unreal.Vector(x, y, z - 8000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], 0, 0.0)
        if hit and hit[0]:
            blocking = hit[4] if len(hit) > 4 else None
            actor = blocking.get_actor() if blocking else None
            if actor is not None:
                return float(blocking.location.z), actor.get_actor_label()
    except Exception as exc:
        return None, f"trace failed: {exc}"
    return None, "no hit"


def snap_selected(clearance_cm: float = 0.0) -> dict[str, Any]:
    """Rest every selected StaticMeshActor's bounds-bottom on traced ground."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    world = unreal.EditorLevelLibrary.get_editor_world()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    moved, skipped = [], []
    for a in eas.get_selected_level_actors():
        try:
            is_mesh = "StaticMesh" in a.get_class().get_name()
            lbl = a.get_actor_label()
        except Exception:
            continue
        if not is_mesh:
            skipped.append(f"{lbl} (not a static mesh)")
            continue
        v = a.get_actor_location()
        gz, src = _trace_ground(unreal, world, v.x, v.y, v.z)
        if gz is None:
            skipped.append(f"{lbl} ({src})")
            continue
        try:
            bounds = a.get_actor_bounds(False) if hasattr(a, "get_actor_bounds") else (None, 0)
            half_z = bounds[1].z if bounds and bounds[0] else 0.0
        except Exception:
            half_z = 0.0
        a.set_actor_location(unreal.Vector(v.x, v.y, gz + half_z + clearance_cm), False, False)
        moved.append({"label": lbl, "z": gz + half_z + clearance_cm, "ground": src})
    return {"ok": True, "moved": moved, "skipped": skipped}


def place_asset(asset_path: str, x: float, y: float, clearance_cm: float = 0.0) -> dict[str, Any]:
    """Spawn a static mesh at XY, resting on traced ground. Returns label."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    world = unreal.EditorLevelLibrary.get_editor_world()
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if mesh is None:
        return {"ok": False, "error": f"asset not found: {asset_path}"}
    gz, src = _trace_ground(unreal, world, x, y, 2000.0)
    if gz is None:
        return {"ok": False, "error": f"no ground at ({x}, {y}): {src}"}
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, y, gz + clearance_cm), unreal.Rotator(0, 0, 0))
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_editor_property("static_mesh", mesh)
    return {"ok": True, "label": actor.get_actor_label(), "z": gz + clearance_cm, "ground": src}


def save_level() -> dict[str, Any]:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    unreal.EditorLevelLibrary.save_current_level()
    return {"ok": True, "saved": True}


def menu_snap_summary(clearance_cm: float = 0.0) -> str:
    result = snap_selected(clearance_cm)
    if not result.get("ok"):
        return f"[Placement] HOLD ({result.get('error')})"
    lines = [f"[Placement] moved={len(result['moved'])} skipped={len(result['skipped'])}"]
    for m in result["moved"]:
        lines.append(f"  ok {m['label']} z={round(m['z'], 1)} on {m['ground']}")
    for s in result["skipped"]:
        lines.append(f"  -- {s}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(menu_snap_summary())
