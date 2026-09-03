"""Addon registration smoke test."""
from __future__ import annotations

def test_addon_import():
    import deploy.surreal_architecture_gen as addon
    assert hasattr(addon, "register")
    assert hasattr(addon, "unregister")
    assert hasattr(addon, "bl_info")
    assert addon.bl_info["name"]
    assert addon.bl_info["version"]
    print("[test_register] import OK")