"""Structured logging for melodia_gn ΓÇö replaces silent error swallowing.

Levels:
  debug   ΓÇö only printed when melodia_gn_debug is enabled in addon prefs
  info    ΓÇö normal operational messages
  warning ΓÇö non-fatal issues (always printed)
  error   ΓÇö failures (always printed + raises optional exception)

Usage:
  from .logging import log
  log.debug("Building %s", tree_name)
  log.warning("Node %s not found, skipping", bl_idname)
  log.error("Failed to create tree: %s", e)
"""

from __future__ import annotations

import traceback
from typing import Callable

LOG_TAG = "[Melodia GN]"


class Logger:
    """Module-scoped singleton logger with deferred preference lookup."""

    def __init__(self, tag: str = LOG_TAG):
        self.tag = tag
        self._pref_getter: Callable[[], bool] | None = None

    def set_pref_getter(self, fn: Callable[[], bool]):
        """Attach a lazy function that returns the debug toggle from prefs."""
        self._pref_getter = fn

    def _is_debug(self) -> bool:
        if self._pref_getter is None:
            return False
        try:
            return self._pref_getter()
        except Exception:
            return False

    def debug(self, fmt: str, *args):
        if self._is_debug():
            print(f"{self.tag} [DEBUG] {fmt % args if args else fmt}")

    def info(self, fmt: str, *args):
        print(f"{self.tag} [INFO] {fmt % args if args else fmt}")

    def warning(self, fmt: str, *args):
        print(f"{self.tag} [WARN] {fmt % args if args else fmt}")

    def error(self, fmt: str, *args, exc: Exception | None = None):
        msg = f"{self.tag} [ERROR] {fmt % args if args else fmt}"
        if exc is not None:
            msg += f"  ({type(exc).__name__}: {exc})"
        print(msg)
        if self._is_debug() and exc is not None:
            traceback.print_exc()

    def exception(self, fmt: str, *args):
        """Log an error with full traceback (always prints traceback)."""
        msg = f"{self.tag} [ERROR] {fmt % args if args else fmt}"
        print(msg)
        print(traceback.format_exc())


log = Logger()


# ΓöÇΓöÇ Preference bridge ΓöÇΓöÇ

def _resolve_debug_pref():
    """Try to read melodia_gn_debug from SurrealArch preferences.

    Returns False if preferences are unavailable (headless / during bake).
    """
    try:
        import bpy
        prefs = bpy.context.preferences.addons.get("surreal_architecture_gen")
        if prefs is None:
            return False
        return bool(getattr(prefs.preferences, "melodia_gn_debug", False))
    except Exception:
        return False


def install_pref_bridge():
    """Wire the logger to read the debug toggle from addon preferences.

    Call once from register_overhaul() after preferences are registered.
    Safe to call multiple times.
    """
    log.set_pref_getter(_resolve_debug_pref)
    if log._is_debug():
        log.info("Debug logging ENABLED")
