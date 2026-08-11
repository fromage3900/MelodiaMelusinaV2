"""Pure-Python layout math for the full-size PCG piano.

This module intentionally has no Unreal imports so it can be unit-tested outside
the editor and reused by graph/build scripts.
"""

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


BLACK_PITCH_CLASSES = frozenset({1, 3, 6, 8, 10})
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True)
class PianoDimensions:
    white_width: float = 23.5
    white_depth: float = 150.0
    white_height: float = 20.0
    black_width: float = 13.5
    black_depth: float = 95.0
    black_height: float = 32.0
    inter_key_gap: float = 0.5
    keybed_top: float = 0.0


@dataclass(frozen=True)
class PianoKeySpec:
    key_index: int
    midi_note: int
    note_name: str
    is_black: bool
    x: float
    y: float
    z: float
    width: float
    depth: float
    height: float
    seed: int


def is_black_midi(midi_note: int) -> bool:
    return midi_note % 12 in BLACK_PITCH_CLASSES


def note_name(midi_note: int) -> str:
    octave = (midi_note // 12) - 1
    return f"{NOTE_NAMES[midi_note % 12]}{octave}"


def pack_seed(key_index: int, midi_note: int) -> int:
    if not 0 <= key_index <= 0xFF:
        raise ValueError(f"key_index must fit in one byte: {key_index}")
    if not 0 <= midi_note <= 0xFF:
        raise ValueError(f"midi_note must fit in one byte: {midi_note}")
    return (midi_note << 8) | key_index


def unpack_seed(seed: int) -> tuple[int, int]:
    return seed & 0xFF, (seed >> 8) & 0xFF


def _white_centers(first_midi: int, last_midi: int, dimensions: PianoDimensions) -> Mapping[int, float]:
    white_notes = [midi for midi in range(first_midi, last_midi + 1) if not is_black_midi(midi)]
    pitch_step = dimensions.white_width + dimensions.inter_key_gap
    center_offset = (len(white_notes) - 1) * 0.5
    return {
        midi: (white_index - center_offset) * pitch_step
        for white_index, midi in enumerate(white_notes)
    }


def build_layout(
    first_midi: int = 21,
    last_midi: int = 108,
    dimensions: PianoDimensions | None = None,
) -> tuple[PianoKeySpec, ...]:
    """Build centered A0-C8 key centers in Unreal centimeter units."""

    if first_midi > last_midi:
        raise ValueError("first_midi must be <= last_midi")
    dimensions = dimensions or PianoDimensions()
    white_centers = _white_centers(first_midi, last_midi, dimensions)
    white_notes = [midi for midi in range(first_midi, last_midi + 1) if not is_black_midi(midi)]
    white_index_by_midi = {midi: index for index, midi in enumerate(white_notes)}
    specs: list[PianoKeySpec] = []

    for key_index, midi in enumerate(range(first_midi, last_midi + 1)):
        black = is_black_midi(midi)
        if black:
            lower_white = midi - 1
            upper_white = midi + 1
            if lower_white not in white_centers or upper_white not in white_centers:
                raise ValueError(f"black note {midi} needs adjacent white notes in the requested range")
            x = (white_centers[lower_white] + white_centers[upper_white]) * 0.5
            y = (dimensions.white_depth - dimensions.black_depth) * 0.5
            z = dimensions.keybed_top + dimensions.white_height + dimensions.black_height * 0.5
            width = dimensions.black_width
            depth = dimensions.black_depth
            height = dimensions.black_height
        else:
            x = white_centers[midi]
            y = 0.0
            z = dimensions.keybed_top + dimensions.white_height * 0.5
            width = dimensions.white_width
            depth = dimensions.white_depth
            height = dimensions.white_height

        specs.append(
            PianoKeySpec(
                key_index=key_index,
                midi_note=midi,
                note_name=note_name(midi),
                is_black=black,
                x=x,
                y=y,
                z=z,
                width=width,
                depth=depth,
                height=height,
                seed=pack_seed(key_index, midi),
            )
        )

    return tuple(specs)


def split_layout(specs: Iterable[PianoKeySpec]) -> tuple[tuple[PianoKeySpec, ...], tuple[PianoKeySpec, ...]]:
    white: list[PianoKeySpec] = []
    black: list[PianoKeySpec] = []
    for spec in specs:
        (black if spec.is_black else white).append(spec)
    return tuple(white), tuple(black)


def expected_counts(first_midi: int = 21, last_midi: int = 108) -> tuple[int, int, int]:
    specs = build_layout(first_midi, last_midi)
    white, black = split_layout(specs)
    return len(specs), len(white), len(black)
