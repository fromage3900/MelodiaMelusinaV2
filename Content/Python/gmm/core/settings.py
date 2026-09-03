"""GMM Settings Manager — Configures environment, styling, and gameplay settings.

Saves config to Saved/Config/gmm_settings.json.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# Local project root path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SETTINGS_PATH = PROJECT_ROOT / "Saved" / "Config" / "gmm_settings.json"

DEFAULT_SETTINGS = {
    "active_genome": "NikkiFlorawish",
    "metronome_latency_offset_ms": 0.0,
    "perfect_accuracy_window_s": 0.09,
    "great_accuracy_window_s": 0.12,
    "good_accuracy_window_s": 0.16,
    "auto_save_on_compile": True,
    "stage_approval_required": True,
    "mcp_server_port": 9316,
}


class GmmSettings:
    """Settings controller for all Grandmaster Melodia Melusina subsystems."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {}
            cls._instance.load()
        return cls._instance

    def load(self) -> dict:
        """Load settings from disk or initialize with defaults."""
        try:
            if SETTINGS_PATH.exists():
                content = SETTINGS_PATH.read_text(encoding="utf-8")
                self.data = json.loads(content)
                # Fill in any missing default keys
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in self.data:
                        self.data[k] = v
            else:
                self.data = DEFAULT_SETTINGS.copy()
                self.save()
        except Exception:
            self.data = DEFAULT_SETTINGS.copy()
        return self.data

    def save(self) -> bool:
        """Save settings to Saved/Config/gmm_settings.json."""
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting by key."""
        return self.data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any) -> bool:
        """Set a setting value and persist it."""
        if key in DEFAULT_SETTINGS:
            # Validate types against default value
            expected_type = type(DEFAULT_SETTINGS[key])
            try:
                if expected_type == float and isinstance(value, int):
                    value = float(value)
                elif not isinstance(value, expected_type):
                    # Try to convert type
                    value = expected_type(value)
            except (ValueError, TypeError):
                return False
            
            self.data[key] = value
            return self.save()
        return False

    def reset_defaults(self) -> bool:
        """Reset all settings back to default values."""
        self.data = DEFAULT_SETTINGS.copy()
        return self.save()
