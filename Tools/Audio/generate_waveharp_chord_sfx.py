#!/usr/bin/env python3
"""Generate compact, pitch-clean WaveHarp chord SFX with NumPy.

Run from the project root:
    python Tools/Audio/generate_waveharp_chord_sfx.py

The neutral C4 sample is suitable for per-shot UE pitch modulation. The phrase
and completion files are audition references and can be imported as authored
SoundWaves by the existing WaveHarp combat owner.
"""

from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np


SAMPLE_RATE = 48_000
TARGET_PEAK = 10.0 ** (-9.0 / 20.0)
C4_HZ = 261.625565
FAMILIES = {
    "Cmaj7": {"name": "C major 7", "intervals": (0, 4, 7, 11, 12)},
    "Cmaj6": {"name": "C major 6", "intervals": (0, 4, 7, 9, 12)},
    "Cm7": {"name": "C minor 7", "intervals": (0, 3, 7, 10, 12)},
}


def tone(freq: float, duration: float, *, brightness: float = 1.0,
         velocity: float = 1.0, pan: float = 0.0) -> np.ndarray:
    """A small, clean plucked-string voice with a soft attack and no hard edge."""
    count = max(1, round(duration * SAMPLE_RATE))
    t = np.arange(count, dtype=np.float64) / SAMPLE_RATE
    # Inharmonicity is avoided so the note remains useful under pitch shifting.
    partials = ((1, 1.0), (2, 0.34 * brightness), (3, 0.13 * brightness),
                (4, 0.045 * brightness), (5, 0.018 * brightness))
    voice = np.zeros(count, dtype=np.float64)
    for partial, level in partials:
        # A tiny, deterministic detune between two string layers gives a soft
        # ensemble shimmer without chorus wobble or pitch ambiguity.
        voice += level * np.sin(2 * np.pi * freq * partial * t)
        if partial <= 3:
            voice += 0.17 * level * np.sin(2 * np.pi * freq * partial * 1.0011 * t + 0.22)

    attack = np.minimum(1.0, t / 0.009)
    decay = 0.76 * np.exp(-t / 0.23) + 0.24 * np.exp(-t / 0.72)
    # Last 45 ms fades to zero, avoiding both a click and an unnecessarily long tail.
    release = np.ones(count, dtype=np.float64)
    fade_samples = min(count, round(0.045 * SAMPLE_RATE))
    if fade_samples > 1:
        release[-fade_samples:] = np.linspace(1.0, 0.0, fade_samples)
    env = attack * decay * release
    voice *= env * velocity
    # Equal-power panning; inputs are clamped to keep channels in a sane range.
    pan = max(-1.0, min(1.0, pan))
    left = math.sqrt((1.0 - pan) * 0.5)
    right = math.sqrt((1.0 + pan) * 0.5)
    return np.column_stack((voice * left, voice * right))


def normalize(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    return audio * (TARGET_PEAK / peak) if peak > 0.0 else audio


def mix_notes(events: list[tuple[float, float, float, float, float]],
              duration: float) -> np.ndarray:
    """Mix (start seconds, MIDI semitones from C4, note duration, gain, pan)."""
    result = np.zeros((round(duration * SAMPLE_RATE), 2), dtype=np.float64)
    for start, semitones, length, gain, pan in events:
        sample = tone(C4_HZ * (2.0 ** (semitones / 12.0)), length,
                      brightness=0.86 if semitones < 7 else 1.0,
                      velocity=gain, pan=pan)
        offset = round(start * SAMPLE_RATE)
        end = min(result.shape[0], offset + sample.shape[0])
        if offset < result.shape[0]:
            result[offset:end] += sample[:end - offset]
    return normalize(result)


def write_wav(path: Path, audio: np.ndarray) -> dict[str, float]:
    pcm = np.clip(audio, -1.0, 1.0)
    pcm16 = np.rint(pcm * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm16.tobytes())
    peak = float(np.max(np.abs(pcm16.astype(np.float64) / 32768.0)))
    return {"seconds": audio.shape[0] / SAMPLE_RATE,
            "peak": peak,
            "peak_dbfs": 20.0 * math.log10(max(peak, 1e-12))}


def render_family(name: str, intervals: tuple[int, ...], out_dir: Path,
                  records: list[tuple[str, dict[str, float]]]) -> None:
    # This played riff follows the combat chord exactly, including the octave
    # completion on shot five; light overlap makes the SFX read as a small riff.
    step = 0.155
    events = [(index * step, semitone, 0.32, 0.78 if index < 4 else 0.72,
               (-0.12 if index % 2 == 0 else 0.12))
              for index, semitone in enumerate(intervals)]
    audio = mix_notes(events, duration=1.12)
    filename = f"WaveHarp_{name}_played_chord_riff.wav"
    records.append((filename, write_wav(out_dir / filename, audio)))

    # The completion SFX lands on the fifth-shot C5 and blooms into a compact
    # family-specific voicing drawn from that same chord's upper tones.
    upper = [12, intervals[1] + 12, intervals[2] + 12, intervals[3] + 12]
    complete_events = [(0.0, upper[0], 0.42, 0.70, 0.0),
                       (0.055, upper[1], 0.39, 0.45, -0.18),
                       (0.095, upper[2], 0.37, 0.38, 0.16),
                       (0.14, upper[3], 0.34, 0.24, 0.0)]
    completion = mix_notes(complete_events, duration=0.68)
    filename = f"WaveHarp_{name}_fifth_shot_complete.wav"
    records.append((filename, write_wav(out_dir / filename, completion)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path,
                        default=Path("Saved/Audit/HybridPlayable_20260930/ChordSFX"))
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    records: list[tuple[str, dict[str, float]]] = []

    base = mix_notes([(0.0, 0, 0.30, 1.0, 0.0)], duration=0.36)
    filename = "WaveHarp_C4_transposable_pluck.wav"
    records.append((filename, write_wav(out_dir / filename, base)))

    for family, data in FAMILIES.items():
        render_family(family, data["intervals"], out_dir, records)

    lines = [
        "# WaveHarp chord SFX receipt",
        "",
        "Generated by `Tools/Audio/generate_waveharp_chord_sfx.py` with NumPy.",
        f"Format: stereo PCM16, {SAMPLE_RATE:,} Hz. Peak target: -9 dBFS.",
        "Envelope: 9 ms soft attack, short decaying string body, 45 ms fade-out.",
        "",
        "| File | Duration | Measured peak |",
        "|---|---:|---:|",
    ]
    for filename, stats in records:
        lines.append(f"| `{filename}` | {stats['seconds']:.3f} s | "
                     f"{stats['peak']:.4f} ({stats['peak_dbfs']:.2f} dBFS) |")
    lines += [
        "",
        "Chord mapping: Cmaj7 `[0,4,7,11,12]`; Cmaj6 `[0,4,7,9,12]`; "
        "Cm7 `[0,3,7,10,12]` semitones from C4.",
        "`C4_transposable_pluck` is the neutral single-note source for the "
        "existing per-shot pitch ratio. Each `fifth_shot_complete` file is a "
        "separate authored fifth-shot flourish; each `played_chord_riff` is "
        "an audition reference following the five shot pitches.",
        "",
        "Integration seam: `UMelodiaWaveHarpCombatComponent` loads and plays "
        "`SW_WaveHarpTrial_C4` at its calculated shot pitch. Import the neutral "
        "C4 WAV as the replacement SoundWave source if desired, then select a "
        "family-matched fifth-shot flourish at `ComboStep == 5`. Keep damage "
        "and audio-reactive MPC ownership unchanged.",
        "Cymatics remains downstream: the palette is the audio writer's source; "
        "`UMelodiaCymaticsWriterSubsystem` is the sole writer of "
        "`MPC_Cymatics_Driver`.",
    ]
    (out_dir / "CHORD_SFX_RECEIPT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} WAV files and CHORD_SFX_RECEIPT.md to {out_dir}")
    for filename, stats in records:
        print(f"{filename}: {stats['seconds']:.3f}s, peak={stats['peak']:.4f} "
              f"({stats['peak_dbfs']:.2f} dBFS)")


if __name__ == "__main__":
    main()
