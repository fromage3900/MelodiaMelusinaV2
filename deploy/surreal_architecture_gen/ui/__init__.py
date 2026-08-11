"""UI registration wrapper."""
from __future__ import annotations

import sys
from pathlib import Path

_deploy_parent = str(Path(__file__).resolve().parent.parent.parent)
if _deploy_parent not in sys.path:
    sys.path.insert(0, _deploy_parent)

import importlib

_monolith = None

def _load():
    global _monolith
    if _monolith is None:
        _monolith = importlib.import_module("surreal_architecture_gen")
    return _monolith

class _UI:
    def register_ui(self):
        m = _load()
        if hasattr(m, "register_ui"):
            m.register_ui()

    def unregister_ui(self):
        m = _load()
        if hasattr(m, "unregister_ui"):
            m.unregister_ui()

ui = _UI()