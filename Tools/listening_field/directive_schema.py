"""melodia.directive/v1 — Jev's only vocabulary.

Jev is a DIRECTOR: it selects among authored states, never generates content.
Every field here is validated against a closed allowlist before any consumer
sees it; an unlisted value is a silent no-op, same contract as an
unallowlisted Quill id. Spec: LISTENING_FIELD_SPEC_2026-09-20.md §3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict

SCHEMA_VERSION = "melodia.directive/v1"

SHEEP_DIRECTIVES = (
    "HOLD", "TURN_TO_PLAYER", "SPIRAL_FORMATION",
    "RESONANCE_PULSE", "CRESCENDO_BURST",
)
WORLD_DIRECTIVES = ("RESTRAIN", "RELEASE")
# SETTLE / RETURN_TO_IDLE are conductor-owned and intentionally NOT here.

# Authored layout seeds: deterministic formation/flower-band arrangements,
# authored as data. Jev picks WHICH one; it never invents parameters.
# radius_m / band / density are AUTHORED constants, fixed per seed.
LAYOUT_SEEDS: dict[str, dict] = {
    "seed_spiral_north": {
        "formation": "SPIRAL", "center": "north_meadow",
        "radius_m": 14.0, "turns": 3, "band": "hue_cool", "density": 0.8,
        "note": "tight inward spiral behind the flock",
    },
    "seed_ring_pond": {
        "formation": "RING", "center": "pond_waterline",
        "radius_m": 10.0, "turns": 1, "band": "hue_warm", "density": 0.6,
        "note": "open ring at the waterline dolly framing",
    },
    "seed_arc_walk": {
        "formation": "ARC", "center": "escher_walk",
        "radius_m": 18.0, "turns": 1, "band": "hue_rainbow", "density": 1.0,
        "note": "wide arc along the walk, full rainbow band",
    },
}


class DirectiveSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class Directive:
    for_bar: int            # decision at bar N applies at bar N+1 (latency rule)
    sheep: str              # SHEEP_DIRECTIVES or ""
    world: str              # WORLD_DIRECTIVES or ""
    restraint: float        # 0..1
    layout_seed: str | None # LAYOUT_SEEDS key or None
    source: str             # "jev" | "fallback"
    confidence: float       # 0..1

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


def validate(d: dict) -> list[str]:
    errors: list[str] = []
    if d.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if d.get("sheep") not in ("", *SHEEP_DIRECTIVES):
        errors.append(f"sheep {d.get('sheep')!r} not in allowlist")
    if d.get("world") not in ("", *WORLD_DIRECTIVES):
        errors.append(f"world {d.get('world')!r} not in allowlist")
    r = d.get("restraint")
    if not isinstance(r, (int, float)) or isinstance(r, bool) or not (0.0 <= float(r) <= 1.0):
        errors.append(f"restraint must be in [0,1], got {r!r}")
    ls = d.get("layout_seed")
    if ls is not None and ls not in LAYOUT_SEEDS:
        errors.append(f"layout_seed {ls!r} not an authored seed")
    return errors


def sanitize(d: Directive) -> Directive:
    """Allowlist enforcement: unlisted values become silent no-ops (empty)."""
    sheep = d.sheep if d.sheep in SHEEP_DIRECTIVES else ""
    world = d.world if d.world in WORLD_DIRECTIVES else ""
    ls = d.layout_seed if d.layout_seed in LAYOUT_SEEDS else None
    return Directive(d.for_bar, sheep, world, float(d.restraint), ls, d.source, d.confidence)
