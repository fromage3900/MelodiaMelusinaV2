"""Corridor chain builders — delegated to shells module (v2.72.2)."""

from __future__ import annotations

from . import shells


def attach_to_monolith(monolith):
    shells.bind(monolith)
    shells.attach_to_monolith(monolith)
