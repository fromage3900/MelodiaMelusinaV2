"""Room shell builders — re-exports from shells + combat room delegate (v2.72.2)."""

from __future__ import annotations

from . import shells

_M = None


def bind(monolith):
    global _M
    _M = monolith
    shells.bind(monolith)


def attach_to_monolith(monolith):
    """Room/corridor shells live in shells.py; combat room stays on monolith until extracted."""
    bind(monolith)
    shells.attach_to_monolith(monolith)
