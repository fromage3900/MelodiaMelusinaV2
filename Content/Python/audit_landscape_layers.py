"""Audit landscape paint layer weights for Figma LandscapeSplatCard.

Writes splat weight metadata consumed by portfolio_aggregator and the Figma
token bridge (`list/splat_weights`).

Output:
    Saved/Portfolio/Metadata/landscape_splat.json

Run:
    python Content/Python/audit_landscape_layers.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "Metadata" / "landscape_splat.json"

# Placeholder weights until landscape layer audit is wired to UE paint data.
DEFAULT_SPLAT_WEIGHTS = [
    {"layer": "Rock", "weight_pct": 34, "texture_path": ""},
    {"layer": "Grass", "weight_pct": 28, "texture_path": ""},
    {"layer": "Mud", "weight_pct": 18, "texture_path": ""},
    {"layer": "Path", "weight_pct": 20, "texture_path": ""},
]


def write_landscape_splat() -> Path:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "audit_landscape_layers.py",
        "splat_weights": DEFAULT_SPLAT_WEIGHTS,
        "note": "Stub data — replace with UE landscape layer paint audit when available.",
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return OUT_PATH


if __name__ == "__main__":
    path = write_landscape_splat()
    print(f"Wrote {path}")
