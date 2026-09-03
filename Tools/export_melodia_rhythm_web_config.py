"""Export rhythm windows from melodia_rules.json for the Melusina web demo.

Source of truth: Plugins/MelodiaCore/Rules/melodia_rules.json
Output: my-site-clean/generated/melodia_rhythm_web_config.json

Consumed by my-site-clean/wix/melodia-game-ui.js (loadRhythmConfig).
Also invoked from Tools/generate_melodia_rules.py after C++/gmm emit.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Plugins" / "MelodiaCore" / "Rules" / "melodia_rules.json"
OUT = ROOT / "my-site-clean" / "generated" / "melodia_rhythm_web_config.json"

PHASES = ["command", "rhythm", "enemy", "results"]


def export_web_config(rules: dict | None = None) -> Path:
    if rules is None:
        rules = json.loads(SRC.read_text(encoding="utf-8"))
    rhythm = rules["rhythm"]

    payload = {
        "source": "Plugins/MelodiaCore/Rules/melodia_rules.json",
        "exported": date.today().isoformat(),
        "rhythm": {
            "windows_ms": {
                "perfect": int(rhythm["windows_ms"]["perfect"]),
                "great": int(rhythm["windows_ms"]["great"]),
                "good": int(rhythm["windows_ms"]["good"]),
            },
            "grade_multipliers": dict(rhythm["grade_multipliers"]),
            "default_bpm": int(rhythm["default_bpm"]),
        },
        "phases": list(PHASES),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return OUT


def main() -> int:
    out = export_web_config()
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
