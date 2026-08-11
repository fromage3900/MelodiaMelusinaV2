"""
Unreal Editor Python utility to add a "Quantum: Request Ranking" command.

Safe to import (no side-effects). Exposes `register()` and `unregister()` to
bind/unbind a menu entry or button in the Editor UI. Best-effort: works when
`unreal` and `unreal.ToolMenus` are available; otherwise falls back to a
no-op with helpful logging.

When invoked the command will prompt for a JSON payload (best-effort using
Editor dialogs) and call `start_request_and_watch(payload, target_actor_name=...)`.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


DEFAULT_PAYLOAD = json.dumps(
    {
        "request_id": "sample-001",
        "layouts": [
            {"id": "A", "score_hint": 0.5},
            {"id": "B", "score_hint": 0.6},
            {"id": "C", "score_hint": 0.4},
        ],
    },
    indent=2,
)


def _safe_import_unreal():
    try:
        import unreal

        return unreal
    except Exception:
        return None


def request_ranking(payload_str: Optional[str] = None, target_actor_name: str = "QuantumReceiver"):
    """Prompt for a payload (or use the provided/default) and invoke the request.

    This function is safe to call from the Editor UI. It will attempt several
    editor dialog approaches; if none are available it falls back to `input()`.
    """
    unreal = _safe_import_unreal()

    if not payload_str:
        # Best-effort try editor dialog APIs
        prompt_msg = f"Enter JSON payload for Quantum ranking (default shown):\n{DEFAULT_PAYLOAD}"
        tried = False
        if unreal is not None:
            try:
                # Try a few possible editor dialog helper names used across versions
                dialog = getattr(unreal, "EditorDialog", None)
                if dialog is not None:
                    # Some builds expose show_text_entry / show_message / show_input_box
                    for fn in ("show_text_entry", "show_input_box", "show_message"):
                        func = getattr(dialog, fn, None)
                        if callable(func):
                            try:
                                # API shapes differ; try common signatures
                                result = func(prompt_msg, "Quantum Request")
                                if isinstance(result, tuple):
                                    # many EditorDialog APIs return (ok, text)
                                    payload_str = result[1] if len(result) > 1 else None
                                else:
                                    payload_str = result
                                tried = True
                                break
                            except Exception:
                                continue
            except Exception:
                tried = False

        if not tried:
            try:
                # As a last resort use simple terminal input (may not work in editor)
                payload_str = input(f"{prompt_msg}\nPayload (empty for default): ")
            except Exception:
                payload_str = None

    if not payload_str:
        payload_str = DEFAULT_PAYLOAD

    # Parse JSON
    try:
        payload = json.loads(payload_str)
    except Exception as exc:
        logger.exception("Failed to parse provided JSON payload; using default. %s", exc)
        payload = json.loads(DEFAULT_PAYLOAD)

    # Import and call the handler (best-effort)
    try:
        from BS_GodFile.Content.Python.quantum.ue_editor_example import start_request_and_watch

        logger.info("Calling start_request_and_watch with target_actor_name=%s", target_actor_name)
        start_request_and_watch(payload, target_actor_name=target_actor_name)
    except Exception:
        logger.exception("Failed to call start_request_and_watch; ensure the module exists and is importable.")


_REGISTERED_MENU_OWNER = "BS_GodFile.QuantumPlugin"


def register():
    """Register the Editor command/menu entry. Best-effort; safe to call multiple times.

    It will attempt to place an entry under the Window menu in the Level Editor
    called "Quantum: Request Ranking" which triggers `request_ranking()`.
    """
    unreal = _safe_import_unreal()
    if unreal is None:
        logger.warning("Unreal Python API not available; register() is a no-op in this environment.")
        return

    try:
        menus = unreal.ToolMenus.get()
        # Ensure owner exists (harmless if already added)
        if not menus.is_menu_registered(_REGISTERED_MENU_OWNER):
            menus.register_owner(_REGISTERED_MENU_OWNER)

        # Try to extend the main Level Editor Window menu
        menu_name = "LevelEditor.MainMenu.Window"
        entry_name = "BS_GodFile.Quantum.RequestRanking"

        menu = menus.extend_menu(menu_name)

        entry = unreal.ToolMenuEntry(
            name=entry_name, type=unreal.MultiBlockType.MENU_ENTRY
        )
        entry.set_label("Quantum: Request Ranking")
        entry.set_tool_tip("Prompt for a job payload and send a quantum ranking request.")

        # Use a PYTHON string command that imports and calls our function
        python_command = (
            "from BS_GodFile.Content.Python.quantum.ue_editor_widget "
            "import request_ranking; request_ranking()"
        )
        entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "", python_command)

        menu.add_menu_entry("Window", entry)
        menus.refresh_all_widgets()
        logger.info("Registered 'Quantum: Request Ranking' menu entry under %s", menu_name)
    except Exception:
        logger.exception("Failed to register Editor menu entry; attempting fallback registration.")
        # Fallback: try to add a level blueprint utility button if available
        try:
            utl = getattr(unreal, "EditorLevelLibrary", None)
            if utl is not None:
                logger.info("EditorLevelLibrary present but no safe public API to attach a global button; registration ended.")
        except Exception:
            logger.exception("Fallback registration also failed.")


def unregister():
    """Attempt to remove the menu entry we added. Best-effort cleanup.

    Safe to call even if not previously registered.
    """
    unreal = _safe_import_unreal()
    if unreal is None:
        return

    try:
        menus = unreal.ToolMenus.get()
        menu_name = "LevelEditor.MainMenu.Window"
        entry_name = "BS_GodFile.Quantum.RequestRanking"

        if menus.is_menu_registered(menu_name):
            menu = menus.find_menu(menu_name)
            if menu is not None:
                try:
                    menu.remove_menu_entry("Window", entry_name)
                    menus.refresh_all_widgets()
                    logger.info("Unregistered Quantum menu entry from %s", menu_name)
                except Exception:
                    # best-effort: ignore
                    logger.debug("Could not remove menu entry cleanly.")
    except Exception:
        logger.exception("Error while unregistering Quantum menu entry.")


__all__ = ["register", "unregister", "request_ranking"]
