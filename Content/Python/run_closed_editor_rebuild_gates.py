"""Execute non-PIE UI and Melusina asset integrity gates in UE 5.8 commandlet."""
from __future__ import annotations

import importlib


def run() -> None:
    import compile_playtest_ui_and_owners as ui
    importlib.reload(ui)
    ui.main()
    # This module performs its own report write during import.
    import audit_melusina_gameplay_animation_chain as animation
    importlib.reload(animation)
    print("CLOSED_EDITOR_REBUILD_GATES_OK")


run()
