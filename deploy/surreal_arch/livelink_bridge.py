"""Minimal LiveLink stubs so Live Bridge panel operators degrade gracefully.

Real TCP LiveLink lives outside this package; these helpers keep the N-panel
importable and report clear not-connected status when the bridge is absent.
"""

from __future__ import annotations

_STATUS = {"connected": False, "detail": "livelink_bridge stub — start LiveLink separately"}


def is_connected() -> bool:
    return bool(_STATUS.get("connected"))


def get_status() -> dict:
    return dict(_STATUS)


def ensure_livelink() -> bool:
    return is_connected()


def start_server(*_a, **_k) -> bool:
    _STATUS["detail"] = "start_server: no live TCP server wired in this install"
    return False


def stop_server(*_a, **_k) -> None:
    _STATUS["connected"] = False


def send_scene_to_unreal(*_a, **_k) -> bool:
    return False


def send_selected_to_unreal(*_a, **_k) -> bool:
    return False


def send_melusina_outfit(*_a, **_k) -> bool:
    return False
