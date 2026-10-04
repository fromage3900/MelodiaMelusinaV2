"""Persistent cross-agent continuity primitives for Melodia.

This package is intentionally standard-library only and does not mutate Unreal,
DCC assets, Git refs, or canonical gameplay state.
"""

from .handoff import compile_handoff
from .store import ContinuityStore

__all__ = ["ContinuityStore", "compile_handoff"]
