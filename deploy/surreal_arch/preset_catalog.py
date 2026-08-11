"""Preset catalog bridge — research presets as canonical LD source (v2.72.2)."""

from __future__ import annotations

from .research_presets import RESEARCH_PRESETS

# Playable arch grid keys that map to research preset ids (single source for props)
PLAYABLE_RESEARCH_LINKS = {
    "GREYBOX_TOWER": "greybox_tower_4f",
}

# Scale-tier duplicates allowed (same arch_type, different metre params)
ALLOWED_DUPLICATE_ARCH_TYPES = {
    "MONASTERY": frozenset({
        "preset_monastery_cloister",
        "preset_gothic_cloister_walk",
        "preset_moorish_courtyard",
        "preset_covered_bazaar",
    }),
}


def research_entries_by_group(group: str):
    """Filter RESEARCH_PRESETS by optional group tag."""
    out = {}
    for key, spec in RESEARCH_PRESETS.items():
        if spec.get("group", "RESEARCH") == group:
            out[key] = spec
    return out


def research_props_for(key: str):
    spec = RESEARCH_PRESETS.get(key)
    if not spec:
        return None
    return dict(spec.get("props", {}))
