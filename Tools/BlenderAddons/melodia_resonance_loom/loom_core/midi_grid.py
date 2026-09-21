# Resonance Loom - stdlib MIDI parser (no dependencies, no bpy).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# A project rule says: never hand-build a song map; parse the imported MIDI.
# `MelodiaMusicClockSubsystem` validated tempo+bar+beat maps from these same
# files, and `128BPMarpeggiomelody_beatgrid.mid` is the beat authority. This
# parser reads the same source of truth so a garment baked in Blender lands on
# the beats the game clock actually plays.
#
# Scope: SMF format 0/1, metrical division (ticks-per-quarter). Running status,
# varlen deltas, meta events, sysex skipping. Deliberately minimal -- it exists
# to read the project's beatgrid files, not to be a general MIDI toolkit.

from __future__ import annotations

from dataclasses import dataclass, field


class MidiParseError(ValueError):
    """Raised on malformed or unsupported MIDI input."""


@dataclass
class NoteEvent:
    """One note with times in seconds (converted from ticks via the tempo map)."""
    start_sec: float
    end_sec: float
    pitch: int
    velocity: int
    channel: int


@dataclass
class MidiGrid:
    """Parsed, tempo-resolved view of one MIDI file."""
    bpm: float
    ticks_per_quarter: int
    seconds_per_beat: float
    notes: list[NoteEvent] = field(default_factory=list)
    beats_per_bar: int = 4
    duration_sec: float = 0.0

    def beat_times(self) -> list[float]:
        """Grid beat onset times (seconds), spanning the file duration."""
        if self.seconds_per_beat <= 0.0:
            return []
        count = int(self.duration_sec / self.seconds_per_beat) + 1
        return [i * self.seconds_per_beat for i in range(count)]

    def downbeat_indices(self) -> list[int]:
        """Indices into beat_times() that start a bar."""
        return [i for i in range(len(self.beat_times())) if i % self.beats_per_bar == 0]

    def lane_of_pitch(self, pitch: int) -> int:
        """Deterministic pitch -> lane (0..3). Q=lowest quartile, P=highest."""
        from . import lanes  # local import: avoids cycles in pure module
        return min(3, max(0, (pitch - 21) * len(lanes.LANES) // 88))


def _read_varlen(data: bytes, pos: int) -> tuple[int, int]:
    """MIDI variable-length quantity. Returns (value, next_pos)."""
    value = 0
    for _ in range(4):
        if pos >= len(data):
            raise MidiParseError("truncated varlen quantity")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos
    raise MidiParseError("varlen quantity longer than 4 bytes")


def _tempo_to_bpm(micros_per_quarter: int) -> float:
    if micros_per_quarter <= 0:
        raise MidiParseError("non-positive tempo microseconds")
    return 60_000_000.0 / micros_per_quarter


def parse_midi(data: bytes) -> MidiGrid:
    """Parse SMF bytes into a tempo-resolved MidiGrid."""
    if len(data) < 14 or data[:4] != b"MThd":
        raise MidiParseError("not a MIDI file (missing MThd)")
    header_len = int.from_bytes(data[4:8], "big")
    fmt = int.from_bytes(data[8:10], "big")
    ntrks = int.from_bytes(data[10:12], "big")
    division = int.from_bytes(data[12:14], "big")
    if fmt not in (0, 1):
        raise MidiParseError(f"unsupported MIDI format {fmt} (want 0 or 1)")
    if division & 0x8000:
        raise MidiParseError("SMPTE division unsupported (project uses metrical)")

    tpb = division if division else 480
    pos = 8 + header_len

    micros_per_quarter = 500_000  # default 120 bpm per SMF spec
    beats_per_bar = 4
    notes: list[tuple[int, int, int, int, int]] = []
    end_tick = 0

    track_no = 0
    while pos < len(data) and track_no < max(ntrks, 1):
        if data[pos:pos + 4] != b"MTrk":
            raise MidiParseError(f"expected MTrk at byte {pos}")
        track_len = int.from_bytes(data[pos + 4:pos + 8], "big")
        track = data[pos + 8:pos + 8 + track_len]
        pos += 8 + track_len
        track_no += 1

        tick = 0
        i = 0
        running_status = None
        open_notes: dict[tuple[int, int], tuple[int, int]] = {}

        while i < len(track):
            delta, i = _read_varlen(track, i)
            tick += delta
            if i >= len(track):
                break
            status = track[i]
            if status & 0x80:
                i += 1
                if status != 0xFF:
                    running_status = status
            else:
                if running_status is None:
                    raise MidiParseError("running status without prior status byte")
                status = running_status

            if status == 0xFF:  # meta: type + varlen body
                if i >= len(track):
                    break
                meta_type = track[i]
                i += 1
                length, i = _read_varlen(track, i)
                body = track[i:i + length]
                i += length
                if meta_type == 0x51 and len(body) == 3:
                    micros_per_quarter = int.from_bytes(body, "big")
                elif meta_type == 0x58 and len(body) >= 2 and body[1]:
                    beats_per_bar = body[0]
                continue

            if status in (0xF0, 0xF7):  # sysex: skip by varlen length
                length, i = _read_varlen(track, i)
                i += length
                continue

            kind = status & 0xF0
            data_bytes = 2 if kind in (0x80, 0x90, 0xA0, 0xB0, 0xE0) else 1
            if i + data_bytes > len(track):
                break
            b1 = track[i]
            b2 = track[i + 1] if data_bytes > 1 else 0
            i += data_bytes

            if kind == 0x90 and b2 > 0:
                open_notes[(status & 0x0F, b1)] = (tick, b2)
            elif kind == 0x80 or (kind == 0x90 and b2 == 0):
                key = (status & 0x0F, b1)
                if key in open_notes:
                    start_tick, vel = open_notes.pop(key)
                    notes.append((start_tick, tick, b1, vel, key[0]))
                    end_tick = max(end_tick, tick)

    if not notes and ntrks == 0:
        raise MidiParseError("no tracks parsed")

    spb = micros_per_quarter / 1_000_000.0
    notes.sort()
    note_events = [
        NoteEvent(
            start_sec=nt[0] * spb / tpb,
            end_sec=nt[1] * spb / tpb,
            pitch=nt[2],
            velocity=nt[3],
            channel=nt[4],
        )
        for nt in notes
    ]
    longest_note = max((n.end_sec for n in note_events), default=0.0)
    duration = max(end_tick * spb / tpb, longest_note)
    return MidiGrid(
        bpm=_tempo_to_bpm(micros_per_quarter),
        ticks_per_quarter=tpb,
        seconds_per_beat=spb,
        notes=note_events,
        beats_per_bar=beats_per_bar,
        duration_sec=duration,
    )


def load_beatgrid(path) -> MidiGrid:
    """Load a .mid/.midi file from disk into a MidiGrid."""
    from pathlib import Path
    return parse_midi(Path(path).read_bytes())


def accent_notes(grid: MidiGrid, threshold: int = 96) -> list[NoteEvent]:
    """Notes that read as accents: high velocity OR onset on a bar line.

    On-beat notes are accents regardless of velocity so a soft-quantized
    beatgrid still produces downbeat flourishes.
    """
    out: list[NoteEvent] = []
    bar_len = grid.seconds_per_beat * grid.beats_per_bar
    eps = 1e-6
    for note in grid.notes:
        if bar_len > 0:
            bars = note.start_sec / bar_len
            on_bar = abs(bars - round(bars)) < eps
        else:
            on_bar = False
        if note.velocity >= threshold or on_bar:
            out.append(note)
    return out

