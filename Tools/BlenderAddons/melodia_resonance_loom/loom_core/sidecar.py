# Resonance Loom - rhythm garment sidecar (the UE handoff contract).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# The sidecar is the ONLY thing this addon ships to the game. It travels next
# to the garment FBX and is consumed by the Melusina asset-import flow, which
# hands the flourish metadata to the presentation lane (UMelodiaRhythmHUD /
# reactivity). This addon never writes .uasset and never opens an editor --
# sidecar-file handoff keeps the laptop lock-free (no port 9316 writer here).
#
# Schema version is additive-only: new fields are optional with defaults, so
# an older consumer never breaks on a newer sidecar.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import lanes
from .lanes import assign_lanes
from .midi_grid import MidiGrid

SCHEMA_ID = "MelodiaRhythmGarment-v1"

# Amplitude defaults for the two authored shape keys. Flourish amounts, not
# gameplay multipliers -- the presentation lane may scale them further.
ACCENT_AMPLITUDE_DEFAULT = 0.35
HIT_AMPLITUDE_DEFAULT = 0.6


@dataclass
class RhythmGarmentSidecar:
    """What one Loom-baked garment promises the game."""
    schema: str = SCHEMA_ID
    cosmetic_id: str = ""
    source_draft: str = ""
    skill_id: str = ""
    midi_file: str = ""
    bpm: float = 0.0
    tempo_band: str = "mid"
    pattern_density: float = 0.0  # authored flourish density, 0..1
    cloth_tier: str = lanes.CLOTH_TIER
    accent_amplitude: float = ACCENT_AMPLITUDE_DEFAULT
    hit_amplitude: float = HIT_AMPLITUDE_DEFAULT
    lane_hits: dict[str, int] = field(default_factory=dict)  # lane -> hit count
    lane_strategy: str = "pitch_quartile"  # which arrangement produced lane_hits
    expressiveness_only: bool = True  # Decision 016 marker: never a gate


def pattern_density(grid: MidiGrid, window_sec: float = 8.0) -> float:
    """Authored flourish density: notes-per-beat normalized against 4/beat.

    A pattern that averages four note onsets per beat saturates at 1.0. This
    number is presentation metadata (pre-play pattern ranking), never hit
    detection -- timing stays classical in UE.
    """
    if grid.seconds_per_beat <= 0 or not grid.notes:
        return 0.0
    span = min(grid.duration_sec, window_sec) or grid.duration_sec
    if span <= 0:
        return 0.0
    onsets = sum(1 for n in grid.notes if n.start_sec <= span)
    per_beat = onsets / max(span / grid.seconds_per_beat, 1.0)
    return round(min(per_beat / 4.0, 1.0), 3)


def build_sidecar(
    grid: MidiGrid,
    cosmetic_id: str,
    skill_id: str,
    midi_file: str = "",
    source_draft: str = "",
    lane_strategy: str = "pitch_quartile",
) -> RhythmGarmentSidecar:
    """Assemble the sidecar for one garment from a parsed beatgrid."""
    if skill_id not in lanes.SKILL_IDS:
        raise ValueError(
            f"skill_id {skill_id!r} is not one of the authored rhythm ids "
            f"(an unknown id is a silent no-op in StartSession)"
        )
    lane_of = assign_lanes(grid, lane_strategy)
    lane_hits: dict[str, int] = {lane: 0 for lane in lanes.LANES}
    for note, lane_idx in zip(grid.notes, lane_of):
        lane_hits[lanes.LANES[lane_idx]] += 1
    return RhythmGarmentSidecar(
        cosmetic_id=cosmetic_id,
        source_draft=source_draft,
        skill_id=skill_id,
        midi_file=midi_file,
        bpm=round(grid.bpm, 2),
        tempo_band=lanes.tempo_band(grid.bpm),
        pattern_density=pattern_density(grid),
        lane_hits=lane_hits,
        lane_strategy=lane_strategy,
    )


def validate_sidecar(data: dict) -> list[str]:
    """Structural checks before the sidecar leaves the addon. Empty = healthy."""
    errors: list[str] = []
    if data.get("schema") != SCHEMA_ID:
        errors.append(f"schema must be {SCHEMA_ID!r}, got {data.get('schema')!r}")
    cosmetic_id = data.get("cosmetic_id", "")
    if not cosmetic_id.startswith("Cos_"):
        errors.append(f"cosmetic_id {cosmetic_id!r} must be a Cos_ id")
    if data.get("skill_id") not in lanes.SKILL_IDS:
        errors.append(
            f"skill_id {data.get('skill_id')!r} is not an authored rhythm id "
            f"(silent no-op in StartSession)"
        )
    bpm = data.get("bpm", 0.0)
    if not isinstance(bpm, (int, float)) or bpm <= 0:
        errors.append(f"bpm {bpm!r} must be positive")
    band = data.get("tempo_band", "")
    if band not in ("slow", "mid", "fast"):
        errors.append(f"tempo_band {band!r} invalid")
    density = data.get("pattern_density", -1.0)
    if not isinstance(density, (int, float)) or not 0.0 <= density <= 1.0:
        errors.append(f"pattern_density {density!r} must be within 0..1")
    lane_hits = data.get("lane_hits", {})
    if set(lane_hits) != set(lanes.LANES):
        errors.append(
            f"lane_hits keys {sorted(lane_hits)} != lane vocabulary {list(lanes.LANES)}"
        )
    if data.get("lane_strategy") not in lanes.LANE_STRATEGIES:
        errors.append(
            f"lane_strategy {data.get('lane_strategy')!r} invalid; "
            f"one of {list(lanes.LANE_STRATEGIES)}"
        )
    if data.get("expressiveness_only") is not True:
        errors.append("expressiveness_only must be true (Decision 016: never a gate)")
    return errors


def write_sidecar(sidecar: RhythmGarmentSidecar, out_path: Path) -> Path:
    """Serialize to JSON next to the garment FBX. Returns the written path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(asdict(sidecar), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path


def read_sidecar(path: Path) -> RhythmGarmentSidecar:
    """Load a sidecar written by this addon (lossy-but-safe consumer path)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    known = {f for f in RhythmGarmentSidecar.__dataclass_fields__}
    return RhythmGarmentSidecar(**{k: v for k, v in data.items() if k in known})
