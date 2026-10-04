"""Melodia PIE tools -- small, growing tooling menu for Play-In-Editor work.

Extension point for later tooling: add a function here + one menu entry in
init_unreal.py (_register_melodia_menu, "PIE Tools" section). No framework.

Entry points delegate to existing owners only:
  - PIE simulate/end: unreal.EditorLevelLibrary (same calls as
    Content/Python/pie_zenforest_roguelike_smoke.py)
  - per-tool scripts stay where they are; this module only lists/launches.

Offline-safe: HOLD without the editor instead of raising.
"""
from __future__ import annotations


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _les():
    unreal = _unreal()
    try:
        return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    except Exception:
        return None


def pie_status() -> dict:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    probes: dict = {}
    les = _les()
    if les is not None:
        try:
            probes["simulating"] = bool(les.is_in_play_in_editor())
        except Exception as exc:
            probes["simulating_probe"] = f"unavailable: {exc}"
    if "simulating" not in probes:
        try:
            probes["simulating"] = len(unreal.EditorLevelLibrary.get_pie_worlds(False)) > 0
        except Exception as exc:
            probes["simulating_probe"] = f"unavailable: {exc}"
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        probes["editor_world"] = world.get_name() if world else None
    except Exception as exc:
        probes["editor_world_probe"] = f"unavailable: {exc}"
    return {"ok": True, **probes}


def pie_play() -> dict:
    """Start Simulate in the CURRENT level. Never loads another level."""
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    try:
        les = _les()
        if les is not None and hasattr(les, "editor_play_simulate"):
            les.editor_play_simulate()
        else:
            unreal.EditorLevelLibrary.editor_play_simulate()
        return {"ok": True, "simulating": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def pie_stop() -> dict:
    unreal = _unreal()
    if unreal is None:
        return {"ok": False, "status": "HOLD", "error": "Unreal not running"}
    try:
        les = _les()
        if les is not None and hasattr(les, "editor_request_end_play"):
            les.editor_request_end_play()
        else:
            unreal.EditorLevelLibrary.editor_end_play()
        return {"ok": True, "simulating": False}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def menu_status_summary() -> str:
    state = pie_status()
    if not state.get("ok"):
        return f"[PIE] HOLD ({state.get('error')})"
    return f"[PIE] simulating={state.get('simulating', '?')} world={state.get('editor_world', '?')}"


if __name__ == "__main__":
    print(menu_status_summary())
