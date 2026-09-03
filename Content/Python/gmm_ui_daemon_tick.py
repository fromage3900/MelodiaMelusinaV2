"""GMM UI subpackage daemon — HUD tokens, menus, command manifest."""
from __future__ import annotations

from gmm.daemon.generators import UI_GENERATORS
from gmm.daemon.shared import run_tick

DAEMON = "ui"
LABEL = "GMM ui"

TASKS = [
    {"id": "combo_colors", "desc": "Combo-tier color tokens", "file": "gmm/ui/colors.py"},
    {"id": "battle_menu_wireframe", "desc": "Battle menu ASCII wireframe", "file": "gmm/ui/battle_menu.py"},
    {"id": "victory_copy", "desc": "Victory screen reward templates", "file": "gmm/ui/victory_screen.py"},
    {"id": "command_manifest", "desc": "GMM command registry JSON", "file": "gmm/ui/commands_manifest.json"},
    {"id": "rhythm_hud_stub", "desc": "WBP_Battle_Rhythm property map", "file": "gmm/ui/rhythm_hud_stub.json"},
]

SMOKE_MODULES: list[str] = []


def _smoke_extra() -> dict:
    from gmm.ui.commands import GMM_COMMANDS, run_gmm
    count = len(GMM_COMMANDS)
    r = run_gmm("gmm.game.config", {})
    return {"ok": count >= 20 and r.ok, "command_count": count, "config_ok": r.ok}


def main() -> int:
    return run_tick(
        DAEMON, TASKS, UI_GENERATORS, SMOKE_MODULES,
        smoke_extra=_smoke_extra, label=LABEL,
    )


if __name__ == "__main__":
    raise SystemExit(main())
