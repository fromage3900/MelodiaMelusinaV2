#!/usr/bin/env python3
"""Generate the deterministic Harmonix beat-grid MIDI used by Melodia combat."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


TICKS_PER_QUARTER = 960
BPM = 128
BARS = 16
BEATS_PER_BAR = 4
STRONG_BEAT_PITCH = 12
NORMAL_BEAT_PITCH = 13
NOTE_LENGTH_TICKS = 60


def variable_length(value: int) -> bytes:
    if value < 0:
        raise ValueError("MIDI delta times cannot be negative")

    encoded = [value & 0x7F]
    value >>= 7
    while value:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(encoded))


def build_track() -> bytes:
    track = bytearray()
    track += variable_length(0) + b"\xff\x03\x04BEAT"

    microseconds_per_quarter = round(60_000_000 / BPM)
    track += variable_length(0) + b"\xff\x51\x03" + microseconds_per_quarter.to_bytes(3, "big")
    track += variable_length(0) + b"\xff\x58\x04\x04\x02\x18\x08"

    total_beats = BARS * BEATS_PER_BAR
    for beat_index in range(total_beats):
        delta_to_note = 0 if beat_index == 0 else TICKS_PER_QUARTER - NOTE_LENGTH_TICKS
        pitch = STRONG_BEAT_PITCH if beat_index % BEATS_PER_BAR == 0 else NORMAL_BEAT_PITCH
        track += variable_length(delta_to_note) + bytes((0x90, pitch, 100))
        track += variable_length(NOTE_LENGTH_TICKS) + bytes((0x80, pitch, 0))

    final_delta = TICKS_PER_QUARTER - NOTE_LENGTH_TICKS
    track += variable_length(final_delta) + b"\xff\x2f\x00"
    return bytes(track)


def build_midi() -> bytes:
    track = build_track()
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_QUARTER)
    return header + b"MTrk" + struct.pack(">I", len(track)) + track


def validate_midi(data: bytes) -> None:
    expected_tempo = round(60_000_000 / BPM).to_bytes(3, "big")
    if not data.startswith(b"MThd\x00\x00\x00\x06"):
        raise RuntimeError("generated data is not a standard MIDI file")
    if b"\xff\x03\x04BEAT" not in data:
        raise RuntimeError("generated MIDI is missing the BEAT track name")
    if b"\xff\x51\x03" + expected_tempo not in data:
        raise RuntimeError("generated MIDI is missing the 128 BPM tempo event")
    if b"\xff\x58\x04\x04\x02\x18\x08" not in data:
        raise RuntimeError("generated MIDI is missing the 4/4 time signature")
    if data.count(bytes((0x90, STRONG_BEAT_PITCH, 100))) != BARS:
        raise RuntimeError("generated MIDI has the wrong strong-beat count")
    if data.count(bytes((0x90, NORMAL_BEAT_PITCH, 100))) != BARS * (BEATS_PER_BAR - 1):
        raise RuntimeError("generated MIDI has the wrong normal-beat count")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.mid"),
    )
    args = parser.parse_args()

    data = build_midi()
    validate_midi(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(
        f"wrote {args.output} ({len(data)} bytes, {BARS} bars, "
        f"{TICKS_PER_QUARTER} TPQ, {BPM} BPM, {BEATS_PER_BAR}/4)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
