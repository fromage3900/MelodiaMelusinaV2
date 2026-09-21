# Resonance Loom - naming conventions + collision pre-checks.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# All Loom-authored Blender names in one module so the UE handoff contract is
# checkable from either side. Short-name collisions are a shipped defect class
# in this project (AGENTS.md rule 9 family); the exporter refuses to write when
# the outgoing name set collides.

from __future__ import annotations

import re

# Vertex-group conventions (what the artist paints).
ACCENT_GROUP = "LOOM_Accent"   # flourish intensity on accent beats
HIT_GROUP = "LOOM_Hit"         # impulse on downbeats
HEM_GROUP = "LOOM_Hem"         # hem/secondary sway driven by the baked action

# Authored result names (what the bake produces).
ACCENT_SHAPE_KEY = "SK_LOOM_Accent"
HIT_SHAPE_KEY = "SK_LOOM_Hit"
SECONDARY_ACTION = "ACT_LoomSecondary"

# Vertex groups this addon owns. Anything outside the LOOM_ namespace is
# never touched -- parallel-authority defense on the mesh itself.
LOOM_VGROUPS: tuple[str, ...] = (ACCENT_GROUP, HIT_GROUP, HEM_GROUP)

_COSMETIC_ID_RE = re.compile(r"^Cos_[A-Za-z0-9_]+$")


def is_valid_cosmetic_id(cosmetic_id: str) -> bool:
    """Cosmetic ids are FName-shaped and prefixed Cos_ (draft contract)."""
    return bool(_COSMETIC_ID_RE.match(cosmetic_id))


def short_name_collisions(names: list[str]) -> list[str]:
    """Return the subset of names that collide case-insensitively.

    Blender asset names and UE import names are case-insensitive at the seam;
    'sk_melusina_dress' vs 'SK_Melusina_Dress' is a collision that substring
    assertions cannot distinguish (AGENTS.md duplicate-short-name class).
    """
    seen: dict[str, str] = {}
    collisions: list[str] = []
    for name in names:
        key = name.lower()
        if key in seen and name not in collisions:
            collisions.append(name)
        seen.setdefault(key, name)
    return collisions


def garment_asset_names(cosmetic_id: str) -> list[str]:
    """Names the export will emit for one garment (FBX object + sidecar stem)."""
    if not is_valid_cosmetic_id(cosmetic_id):
        raise ValueError(f"cosmetic id {cosmetic_id!r} must match Cos_<Name>")
    return [
        cosmetic_id,
        ACCENT_SHAPE_KEY,
        HIT_SHAPE_KEY,
        SECONDARY_ACTION,
    ]
