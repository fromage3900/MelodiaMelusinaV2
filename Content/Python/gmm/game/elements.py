"""7-element wheel backed by generated Melodia rules."""
from __future__ import annotations

from gmm.game.rules_generated import RULES


_ELEMENT_RULES = RULES["elements"]

ELEMENT_CYCLE = tuple(_ELEMENT_RULES["cycle"])
ELEMENT_WEAKNESS = dict(_ELEMENT_RULES["weakness"])
ELEMENT_RESIST = dict(_ELEMENT_RULES["resist"])


def element_multiplier(attack_element: str, defense_element: str) -> float:
    """Return the generated-rule damage multiplier for an elemental matchup."""
    if ELEMENT_WEAKNESS.get(attack_element) == defense_element:
        return float(_ELEMENT_RULES["strong_multiplier"])
    if ELEMENT_RESIST.get(attack_element) == defense_element:
        return float(_ELEMENT_RULES["weak_multiplier"])
    return 1.0


def element_summary() -> dict:
    return {
        "cycle": list(ELEMENT_CYCLE),
        "weakness": dict(ELEMENT_WEAKNESS),
        "resist": dict(ELEMENT_RESIST),
        "strong_multiplier": float(_ELEMENT_RULES["strong_multiplier"]),
        "weak_multiplier": float(_ELEMENT_RULES["weak_multiplier"]),
    }
