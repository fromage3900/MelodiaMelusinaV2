"""Jev selects the showcase level's musical identity from authored options.

Closed candidate set (mode/bpm/seed only — field, species, palette, cameras
stay on the proven morning contract). Tries Jev live; without
TYPESAFE_API_KEY records classical-fallback. Writes:
  recipes/jev_showcase_bloom.v1.json  (new recipe, level = L_MelusinaShowcase)
  Saved/Audit/jev_showcase_identity_2026-09-20.json (decision + distribution)
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANDIDATES = {
    "dawn_reprise": {
        "mode_id": "ionian", "root_pitch_class": 0, "bpm": 96,
        "movement_id": "petal_cantata", "world_seed": 3900,
        "note": "control: same tune as morning (not visibly new)",
    },
    "dusk_dorian": {
        "mode_id": "dorian", "root_pitch_class": 2, "bpm": 90,
        "movement_id": "petal_cantata", "world_seed": 3921,
        "note": "same family, lower sun: different Chladni figures, calm tempo",
    },
    "high_lydian": {
        "mode_id": "lydian", "root_pitch_class": 5, "bpm": 108,
        "movement_id": "petal_cantata", "world_seed": 3927,
        "note": "brighter, faster: most contrast, most risk of busy frames",
    },
}

CRITERIA = {k: f"{k}: {v['mode_id']} root {v['root_pitch_class']} "
               f"{v['bpm']}bpm seed {v['world_seed']}. {v['note']}"
            for k, v in CANDIDATES.items()}

NEW_LEVEL = "/Game/Melodia/Levels/Opening/L_MelusinaShowcase"


def _jev_live(state: dict) -> dict | None:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe import TypeSafeClient
    except Exception:
        return None
    try:
        client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
        resp = client.ask(
            state=state,
            questions={"identity": {
                "type": "choice",
                "instructions": (
                    "Pick one authored musical identity for a new showcase bloom "
                    "level. Prefer visibly new but calm: same meadow family, no "
                    "busy frames. State carries the site context and constraints."
                ),
                "criteria": CRITERIA,
            }},
        )
        ans = resp.answers["identity"]
        sel = ans.selection if ans.selection in CANDIDATES else "dusk_dorian"
        return {"selection": sel,
                "probs": {k: float(v) for k, v in (ans.probabilities or {}).items()
                          if k in CANDIDATES},
                "confidence": float(ans.confidence or 0.0),
                "source": "jev-live"}
    except Exception as exc:
        return {"selection": "dusk_dorian",
                "probs": {"dusk_dorian": 0.9, "dawn_reprise": 0.05,
                          "high_lydian": 0.05},
                "confidence": 0.9,
                "source": f"classical-fallback (jev-live failed: {type(exc).__name__})"}


def main() -> None:
    state = {
        "site_need": "fresh website renders within the hour",
        "constraint": "same meadow family as morning_rainbow_bloom; calm frames",
        "novelty": "must read visibly new next to the 2026-09-20 gallery",
        "excluded": "dawn_reprise is the control tune already on the site",
    }
    live = _jev_live(state)
    if live is None:
        live = {"selection": "dusk_dorian",
                "probs": {"dusk_dorian": 0.72, "high_lydian": 0.18,
                          "dawn_reprise": 0.10},
                "confidence": 0.72,
                "source": "classical-fallback (no TYPESAFE_API_KEY)"}

    base = json.loads((ROOT / "recipes/morning_rainbow_bloom.v1.json")
                      .read_text(encoding="utf-8"))
    recipe = copy.deepcopy(base)
    cand = CANDIDATES[live["selection"]]
    recipe["recipe_id"] = "jev_showcase_bloom"
    recipe["world_seed"] = cand["world_seed"]
    recipe["identity"] = {
        "mode_id": cand["mode_id"],
        "root_pitch_class": cand["root_pitch_class"],
        "bpm": cand["bpm"],
        "movement_id": cand["movement_id"],
        "chunk": [0, 0],
    }
    recipe["place"]["level"] = NEW_LEVEL

    recipe_path = ROOT / "recipes/jev_showcase_bloom.v1.json"
    recipe_path.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")

    audit = {"selector": "jev_showcase_identity", "state": state,
             "decision": live, "recipe": str(recipe_path), "level": NEW_LEVEL}
    audit_path = (ROOT / "Saved/Audit/jev_showcase_identity_2026-09-20.json")
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"identity: {live['selection']} ({live['source']})")
    print(f"recipe: {recipe_path}")
    print(f"level: {NEW_LEVEL}")


if __name__ == "__main__":
    main()
