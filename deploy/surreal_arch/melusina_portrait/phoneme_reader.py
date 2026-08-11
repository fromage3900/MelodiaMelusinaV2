"""Phoneme reader ΓÇö parse USTX / UST voice-synth files into timed PhonemeEvent lists.

USTX (OpenUTAU JSON):
  {"notes": [{"position": 0, "duration": 240, "tone": 60, "lyric": "a"}, ...]}

UST (UTAU INI):
  [#0000] Length=240 Lyric=a NoteNum=60 ...

Tempo-dependent: 480 ticks = 1 beat at 120 BPM (configurable resolution).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


# UTAU default: 480 ticks per quarter note
DEFAULT_TICKS_PER_BEAT = 480


@dataclass
class PhonemeEvent:
    """One vocal event: phoneme + timing + pitch info."""
    start_sec: float
    end_sec: float
    phoneme: str
    tone: int = 60          # MIDI note number
    duration_ticks: int = 0
    position_ticks: int = 0

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class VoiceTrack:
    """Parsed voice data from a USTX/UST file."""
    name: str = ""
    tempo: float = 120.0
    events: list[PhonemeEvent] = field(default_factory=list)
    total_duration_sec: float = 0.0
    source_file: str = ""
    format: str = ""

    @property
    def phoneme_sequence(self) -> list[str]:
        return [e.phoneme for e in self.events]


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# USTX parser (OpenUTAU JSON)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def parse_ustx(path: str | Path, tempo_override: float | None = None) -> VoiceTrack:
    """Parse an OpenUTAU .ustx JSON file into a VoiceTrack."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tempo = tempo_override or data.get("tempo", 120.0)
    name = data.get("name", path.stem)
    events: list[PhonemeEvent] = []

    # Seconds per tick at this tempo
    spb = 60.0 / tempo                           # seconds per beat
    spt = spb / DEFAULT_TICKS_PER_BEAT           # seconds per tick

    for track in data.get("tracks", []):
        for part in track.get("parts", []):
            for note in part.get("notes", []):
                pos_ticks = note.get("position", 0)
                dur_ticks = note.get("duration", 240)
                start = pos_ticks * spt
                end = (pos_ticks + dur_ticks) * spt
                events.append(PhonemeEvent(
                    start_sec=start,
                    end_sec=end,
                    phoneme=note.get("lyric", "a"),
                    tone=note.get("tone", 60),
                    duration_ticks=dur_ticks,
                    position_ticks=pos_ticks,
                ))

    total = max((e.end_sec for e in events), default=0.0)

    return VoiceTrack(
        name=name,
        tempo=tempo,
        events=sorted(events, key=lambda e: e.start_sec),
        total_duration_sec=total,
        source_file=str(path),
        format="ustx",
    )


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# UST parser (classic UTAU INI)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

_RE_UST_NOTE_HEADER = re.compile(r"^\[#?(\d{4,})\]$")
_RE_UST_KV = re.compile(r"^(\w+)=(.+)$")


def parse_ust(path: str | Path, tempo_override: float | None = None) -> VoiceTrack:
    """Parse a classic UTAU .ust file into a VoiceTrack."""
    path = Path(path)
    raw = Path(path).read_text(encoding="utf-8", errors="replace")

    tempo = 120.0
    notes_raw: list[dict] = []
    current_note: dict | None = None
    current_position: int | None = None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        mh = _RE_UST_NOTE_HEADER.match(line)
        if mh:
            if current_note is not None:
                notes_raw.append(current_note)
            current_position = int(mh.group(1))
            current_note = {"_position": current_position}
            continue

        if line.startswith("[") and line.endswith("]"):
            # Section header like [#VERSION], [#SETTING], [#TRACK]
            if current_note is not None:
                notes_raw.append(current_note)
                current_note = None
                current_position = None
            continue

        mkv = _RE_UST_KV.match(line)
        if mkv and current_note is not None:
            key = mkv.group(1)
            val = mkv.group(2)
            current_note[key] = val
        elif "=" in line and current_note is not None:
            parts = line.split("=", 1)
            current_note[parts[0].strip()] = parts[1].strip()
        elif line.startswith("Tempo="):
            try:
                tempo = float(line.split("=", 1)[1].strip())
            except ValueError:
                pass

    if current_note is not None and current_note.get("Lyric"):
        notes_raw.append(current_note)

    if tempo_override is not None:
        tempo = tempo_override

    spb = 60.0 / tempo
    spt = spb / DEFAULT_TICKS_PER_BEAT

    events: list[PhonemeEvent] = []
    for note in notes_raw:
        pos = int(note.get("_position", 0))
        length = int(note.get("Length", 240))
        tone = int(note.get("NoteNum", 60))
        lyric = note.get("Lyric", "a").strip()

        start = pos * spt
        end = (pos + length) * spt
        events.append(PhonemeEvent(
            start_sec=start,
            end_sec=end,
            phoneme=lyric,
            tone=tone,
            duration_ticks=length,
            position_ticks=pos,
        ))

    total = max((e.end_sec for e in events), default=0.0)

    name = f"{path.stem}"
    for note in notes_raw:
        pn = note.get("ProjectName", "")
        if pn:
            name = pn
            break

    return VoiceTrack(
        name=name,
        tempo=tempo,
        events=sorted(events, key=lambda e: e.start_sec),
        total_duration_sec=total,
        source_file=str(path),
        format="ust",
    )


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Unified loader
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def parse_voice_file(path: str | Path, tempo: float | None = None) -> VoiceTrack:
    """Auto-detect format and parse a voice file (USTX or UST)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".ustx":
        return parse_ustx(path, tempo_override=tempo)
    elif suffix == ".ust":
        return parse_ust(path, tempo_override=tempo)
    else:
        # Try USTX first (JSON), fallback to UST
        try:
            return parse_ustx(path, tempo_override=tempo)
        except (json.JSONDecodeError, KeyError):
            return parse_ust(path, tempo_override=tempo)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Simplified JSON timing track (for hand-authoring)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def parse_timing_json(path: str | Path) -> VoiceTrack:
    """Parse a simplified timing JSON.

    Format:
      {"tempo": 120, "events": [
        {"p": "ah", "start": 0.0, "end": 0.3},
        {"p": "ee", "start": 0.3, "end": 0.6}
      ]}
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tempo = data.get("tempo", 120.0)
    events: list[PhonemeEvent] = []
    for ev in data.get("events", []):
        events.append(PhonemeEvent(
            start_sec=ev.get("start", 0.0),
            end_sec=ev.get("end", 0.0),
            phoneme=ev.get("p", ev.get("phoneme", "a")),
            tone=ev.get("tone", ev.get("t", 60)),
        ))

    total = max((e.end_sec for e in events), default=0.0)
    return VoiceTrack(
        name=data.get("name", path.stem),
        tempo=tempo,
        events=sorted(events, key=lambda e: e.start_sec),
        total_duration_sec=total,
        source_file=str(path),
        format="json",
    )


def timing_json_example() -> dict:
    """Return an example timing JSON for hand-authoring new dialogue."""
    return {
        "name": "melusina_hello",
        "tempo": 120.0,
        "events": [
            {"p": "hh", "start": 0.0, "end": 0.15},
            {"p": "eh", "start": 0.15, "end": 0.30},
            {"p": "ll", "start": 0.30, "end": 0.45},
            {"p": "ow", "start": 0.45, "end": 0.70},
            {"p": "rest", "start": 0.70, "end": 1.0},
        ],
    }
