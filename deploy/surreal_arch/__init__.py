"""Surreal Architecture overhaul package (v2.68.0 — Melodia Studio).

Product name: Melodia Studio
Addon module id: melodia_studio
Operators: surreal_arch.*
"""

from .integration import register_overhaul, unregister_overhaul
from .bootstrap import register_preferences, unregister_preferences

__all__ = ["register_overhaul", "unregister_overhaul", "register_preferences", "unregister_preferences"]
