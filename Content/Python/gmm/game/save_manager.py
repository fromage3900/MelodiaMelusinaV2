"""Save Manager — manages save/load directory and auto-save on battle events.

Provides a simple file-based persistence layer for MelodiaPlayerState.
Saves are stored as JSON in a platform-appropriate directory.

Usage:
    from gmm.game.save_manager import SaveManager
    sm = SaveManager()
    sm.save(player_state)
    sm.load(player_state)
    path = sm.latest_save_path()
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from gmm.game.config import GAME_CFG
from gmm.game.player_state import MelodiaPlayerState, SaveSlot


def default_save_dir() -> str:
    """Platform-appropriate save directory."""
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    return os.path.join(base, "gmm", GAME_CFG.save_dir_name)


class SaveManager:
    """Manages save slots with directory creation, auto-save, and slot listing."""

    def __init__(self, save_dir: Optional[str] = None):
        self.save_dir = save_dir or default_save_dir()
        self.slot_name = GAME_CFG.save_slot_name
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(self.save_dir, exist_ok=True)

    def save(self, player_state: MelodiaPlayerState, slot: Optional[str] = None) -> str:
        """Save player state to disk. Returns path to save file."""
        slot_name = slot or self.slot_name
        path = os.path.join(self.save_dir, slot_name)
        data = player_state.to_save_data()
        data.save_date = time.strftime("%Y-%m-%d %H:%M:%S")
        data.play_time_seconds = time.time() - player_state._start_time
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, indent=2)
        return path

    def load(self, player_state: MelodiaPlayerState, slot: Optional[str] = None) -> bool:
        """Load player state from disk. Returns True on success."""
        slot_name = slot or self.slot_name
        path = os.path.join(self.save_dir, slot_name)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False
        save = SaveSlot(**data)
        player_state.load_from_save(save)
        player_state._start_time = time.time()
        return True

    def latest_save_path(self) -> Optional[str]:
        """Return the path to the most recent save file."""
        path = os.path.join(self.save_dir, self.slot_name)
        if os.path.exists(path):
            return path
        return None

    def list_slots(self) -> list[dict]:
        """List all save files with metadata."""
        slots = []
        if not os.path.isdir(self.save_dir):
            return slots
        for fname in sorted(os.listdir(self.save_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(self.save_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    slots.append({
                        "slot": fname,
                        "path": fpath,
                        "date": data.get("save_date", ""),
                        "level": data.get("level", 0),
                        "player_hp": data.get("player_hp", 0),
                        "play_time": data.get("play_time_seconds", 0),
                    })
                except Exception:
                    slots.append({"slot": fname, "path": fpath, "error": "corrupt"})
        return slots

    def delete_slot(self, slot: str) -> bool:
        """Delete a save slot. Returns True on success."""
        path = os.path.join(self.save_dir, slot)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def describe(self) -> dict:
        return {
            "save_dir": self.save_dir,
            "slot_name": self.slot_name,
            "exists": os.path.exists(os.path.join(self.save_dir, self.slot_name)),
            "slots": len(self.list_slots()),
        }
