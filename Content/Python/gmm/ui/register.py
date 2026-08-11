"""EnvUI menu + command registration for GMM.

Call register_gmm_menus() from init_unreal.py or envui.menu to
add the 'Grandmaster' section and all sub-commands.
"""
from __future__ import annotations

from gmm.ui.commands import GMM_COMMANDS, GMM_SECTION, CommandResult


def register_gmm_menus(owner: str = "BSGodFile_LiveLink") -> dict:
    """Register all GMM commands and EnvUI menu entries.

    Integrates with the existing envui.commands registry so that
    GMM tools appear under the LiveLink > Grandmaster section.

    Returns:
        {"registered": int} count of menu entries added.
    """
    registered = 0
    try:
        from envui import commands as envui_cmds
        from envui.menu import register_envui_menus as _ensure_envui

        _ensure_envui(owner=owner)

        # Register each GMM command into the envui command registry
        for cmd_id, (section, fn) in GMM_COMMANDS.items():
            try:
                envui_cmds.register(cmd_id, fn)
                registered += 1
            except Exception:
                pass

        return {"registered": registered}
    except ImportError:
        return {"registered": 0, "error": "envui not available"}
    except Exception as e:
        return {"registered": registered, "error": str(e)}


def register_gmm_menu_entries(owner: str = "BSGodFile_LiveLink") -> dict:
    """Register EnvUI menu entries (older-style direct menu insertion).

    This adds entries via the envui.commands registry for the
    EnvUI LiveLink menu system to pick up.
    """
    return register_gmm_menus(owner=owner)


def unregister_gmm_menus() -> dict:
    """Remove GMM commands from envui registry."""
    removed = 0
    try:
        from envui import commands as envui_cmds
        for cmd_id in GMM_COMMANDS:
            try:
                envui_cmds.unregister(cmd_id)
                removed += 1
            except Exception:
                pass
    except ImportError:
        pass
    return {"removed": removed}


def about() -> str:
    from gmm import VERSION, VERSION_NAME
    return f"{VERSION_NAME} v{VERSION}"
