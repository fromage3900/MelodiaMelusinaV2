"""melodia.phrase/v1 — shared musical state contract.

FL Studio exposes this; Jev interprets it; UE consumes it. Single source of
truth for the schema lives here and nowhere else. Spec:
Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md §1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum

SCHEMA_VERSION = "melodia.phrase/v1"


class SectionTag(str, Enum):
    SPARSE = "SPARSE"
    VOICE = "VOICE"
    BUILD = "BUILD"
    CLIMAX = "CLIMAX"
    RELEASE = "RELEASE"


class EnergyTrend(str, Enum):
    FALLING = "FALLING"
    FLAT = "FLAT"
    RISING = "RISING"


class PhraseSchemaError(ValueError):
    """Raised when a payload fails melodia.phrase/v1 validation."""


@dataclass(frozen=True)
class PhraseState:
    schema_version: str = SCHEMA_VERSION
    phrase_index: int = 0
    section: SectionTag = SectionTag.SPARSE
    bar: int = 0
    beat_in_bar: float = 0.0          # 0.0 .. beats_per_bar
    energy: float = 0.0               # 0..1, authored automation, not DSP
    energy_trend: EnergyTrend = EnergyTrend.FLAT
    confidence: float = 1.0           # 0..1, decays through rests/gaps
    boundary_pulse: bool = False      # held exactly one bar

    def to_dict(self) -> dict:
        d = asdict(self)
        d["section"] = self.section.value
        d["energy_trend"] = self.energy_trend.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


def _err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def validate_payload(d: dict, beats_per_bar: float = 4.0) -> list[str]:
    """Return a list of validation errors (empty == valid)."""
    errors: list[str] = []
    if not isinstance(d, dict):
        return ["payload is not a JSON object"]

    allowed = set(PhraseState.__dataclass_fields__.keys())
    unknown = set(d.keys()) - allowed
    if unknown:
        _err(errors, f"unknown fields: {sorted(unknown)}")

    if d.get("schema_version") != SCHEMA_VERSION:
        _err(errors, f"schema_version must be {SCHEMA_VERSION!r}, got {d.get('schema_version')!r}")

    for k in ("phrase_index", "bar"):
        if k in d and (not isinstance(d[k], int) or isinstance(d[k], bool) or d[k] < 0):
            _err(errors, f"{k} must be a non-negative int")

    if "beat_in_bar" in d:
        v = d["beat_in_bar"]
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= float(v) < beats_per_bar + 1e-6):
            _err(errors, f"beat_in_bar must be in [0, {beats_per_bar}], got {v!r}")

    for k in ("energy", "confidence"):
        if k in d:
            v = d[k]
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= float(v) <= 1.0):
                _err(errors, f"{k} must be in [0, 1], got {v!r}")

    if "section" in d:
        try:
            SectionTag(d["section"])
        except ValueError:
            _err(errors, f"section must be one of {[s.value for s in SectionTag]}, got {d['section']!r}")

    if "energy_trend" in d:
        try:
            EnergyTrend(d["energy_trend"])
        except ValueError:
            _err(errors, f"energy_trend must be one of {[t.value for t in EnergyTrend]}, got {d['energy_trend']!r}")

    if "boundary_pulse" in d and not isinstance(d["boundary_pulse"], bool):
        _err(errors, "boundary_pulse must be a bool")

    return errors


def from_payload(d: dict) -> PhraseState:
    errors = validate_payload(d)
    if errors:
        raise PhraseSchemaError("; ".join(errors))
    return PhraseState(
        schema_version=d["schema_version"],
        phrase_index=d["phrase_index"],
        section=SectionTag(d["section"]),
        bar=d["bar"],
        beat_in_bar=float(d["beat_in_bar"]),
        energy=float(d["energy"]),
        energy_trend=EnergyTrend(d["energy_trend"]),
        confidence=float(d["confidence"]),
        boundary_pulse=d["boundary_pulse"],
    )


def from_json(s: str) -> PhraseState:
    try:
        d = json.loads(s)
    except json.JSONDecodeError as e:
        raise PhraseSchemaError(f"invalid JSON: {e}") from e
    return from_payload(d)
