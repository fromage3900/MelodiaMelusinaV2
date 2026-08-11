"""Pure deterministic layout helpers for the walkable Xylophone Trail."""
from __future__ import annotations

import math
from dataclasses import dataclass


PENTATONIC_C_MAJOR = (60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84)


@dataclass(frozen=True)
class XylophoneBarSpec:
    step: int
    lane: int
    midi_note: int
    x: float
    y: float
    z: float
    yaw: float
    bar_length: float
    seed: int


def build_xylophone_path_specs(
    note_count: int = 24,
    step_spacing: float = 360.0,
    path_amplitude: float = 620.0,
    path_rise: float = 420.0,
    bar_length: float = 520.0,
    bar_depth: float = 250.0,
) -> tuple[XylophoneBarSpec, ...]:
    """Return a finite, foot-readable S-curve of crosswise xylophone bars."""
    note_count = max(1, int(note_count))
    step_spacing = max(1.0, float(step_spacing))
    path_amplitude = max(0.0, float(path_amplitude))
    path_rise = float(path_rise)
    bar_length = max(1.0, float(bar_length))
    bar_depth = max(1.0, float(bar_depth))

    specs: list[XylophoneBarSpec] = []
    for step in range(note_count):
        t = 0.0 if note_count <= 1 else step / float(note_count - 1)
        phase = t * math.pi * 1.35
        x = (step - (note_count - 1) * 0.5) * step_spacing
        y = math.sin(phase) * path_amplitude
        z = 0.5 * bar_depth + t * path_rise

        previous_t = max(0.0, t - (1.0 / max(1, note_count - 1)))
        next_t = min(1.0, t + (1.0 / max(1, note_count - 1)))
        previous_x = (previous_t * (note_count - 1) - (note_count - 1) * 0.5) * step_spacing
        next_x = (next_t * (note_count - 1) - (note_count - 1) * 0.5) * step_spacing
        previous_y = math.sin(previous_t * math.pi * 1.35) * path_amplitude
        next_y = math.sin(next_t * math.pi * 1.35) * path_amplitude
        yaw = math.degrees(math.atan2(next_y - previous_y, next_x - previous_x)) + 90.0

        midi_note = PENTATONIC_C_MAJOR[step % len(PENTATONIC_C_MAJOR)] + 12 * (step // len(PENTATONIC_C_MAJOR))
        # Longer bars carry the lower register, while every seed remains a
        # stable (step, lane, MIDI) identity understood by APCGHeroMusicNode.
        length = bar_length * (1.18 - 0.16 * (midi_note % 12) / 11.0)
        seed = ((step & 0xFFFF) << 16) | (0 << 8) | (midi_note & 0xFF)
        specs.append(XylophoneBarSpec(step, 0, midi_note, x, y, z, yaw, length, seed))
    return tuple(specs)


def validate_xylophone_layout(specs: tuple[XylophoneBarSpec, ...]) -> list[str]:
    errors: list[str] = []
    seeds = [spec.seed for spec in specs]
    if len(seeds) != len(set(seeds)):
        errors.append("xylophone bar seeds are not unique")
    for spec in specs:
        if not all(math.isfinite(float(value)) for value in (spec.x, spec.y, spec.z, spec.yaw, spec.bar_length)):
            errors.append(f"xylophone bar {spec.step} contains a non-finite transform")
        if spec.bar_length <= 0.0:
            errors.append(f"xylophone bar {spec.step} has no playable length")
    return errors
