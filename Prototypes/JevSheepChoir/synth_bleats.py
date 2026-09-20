"""Offline sheep-choir bleat synthesizer — isolated prototype sketch.

Voices the Choral Sheep's missing choir: /b/ burst + /a/ formant stack
(F1~750, F2~1150, F3~2600 Hz) on a vibrato saw core, the same recipe a
Serum patch would use (wavetable saw -> formant-ish filter bank ->
vibrato LFO -> envelope). Serum 2 itself needs the live FL bridge, which
is currently dark; these WAVs prove the arrangement shapes now and move
into Serum presets later.

Presets map to flock behaviors:
  greeting-bleat  <- TURN_TO_PLAYER (single short bleat)
  sway-hum        <- CHORAL_SWAY (three detuned voices, 2 bars-ish)
  burst-choir     <- CRESCENDO_BURST (rising stacked bleats)

Usage: python synth_bleats.py
Writes bleats/*.wav next to this script. Prints RMS/peak per file so
silence is caught, not assumed.
"""

from __future__ import annotations

import os
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bleats")

FORMANTS = ((750.0, 90.0, 1.0), (1150.0, 110.0, 0.6), (2600.0, 160.0, 0.25))


def _saw(phase: np.ndarray) -> np.ndarray:
    return 2.0 * (phase - np.floor(phase + 0.5))


def _resonant(sig: np.ndarray, f0: float, bw: float) -> np.ndarray:
    # Two-pole resonator at f0 ( Chu-lite formant section ).
    r = np.exp(-np.pi * bw / SR)
    theta = 2.0 * np.pi * f0 / SR
    b = np.array([1.0 - r, 0.0])
    a = np.array([1.0, -2.0 * r * np.cos(theta), r * r])
    out = np.zeros_like(sig)
    for n in range(len(sig)):
        out[n] = b[0] * sig[n] - a[1] * (out[n - 1] if n > 0 else 0.0) - a[2] * (out[n - 2] if n > 1 else 0.0)
    return out


def bleat(dur: float, f0_start: float, f0_end: float, vib_hz: float = 5.5,
          vib_cents: float = 60.0, gain: float = 0.5) -> np.ndarray:
    """One /b/ + /a/ bleat. f0 glides start->end with vibrato."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    glide = np.linspace(f0_start, f0_end, n)
    vib = vib_cents / 100.0 * np.sin(2.0 * np.pi * vib_hz * t + 1.0)
    f0 = glide * 2.0 ** (vib / 12.0)
    phase = np.cumsum(f0 / SR)
    src = _saw(phase)
    # /b/ burst: 30 ms noise thump at the head.
    burst_n = min(int(0.03 * SR), n)
    src[:burst_n] += 0.8 * np.random.default_rng(7).standard_normal(burst_n) * np.hanning(burst_n)
    out = np.zeros(n)
    for f, bw, amp in FORMANTS:
        out += amp * _resonant(src, f, bw)
    out /= max(1e-6, np.abs(out).max())
    # Envelope: fast attack, gentle release tail.
    atk = int(0.04 * SR)
    rel = int(0.15 * SR)
    env = np.ones(n)
    env[:atk] = np.linspace(0.0, 1.0, atk)
    env[-rel:] = np.linspace(1.0, 0.0, rel)
    return (gain * out * env).astype(np.float64)


def write_wav(path: str, mono: np.ndarray) -> None:
    pcm = np.clip(mono, -1.0, 1.0)
    pcm16 = (pcm * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    jobs = {
        "greeting-bleat.wav": [bleat(0.7, 165.0, 220.0)],
        "sway-hum.wav": [
            bleat(2.4, 196.0, 196.0, vib_hz=4.8, gain=0.30),
            bleat(2.4, 196.0 * 2 ** (8 / 1200), 196.0 * 2 ** (8 / 1200), vib_hz=5.1, gain=0.25),
            bleat(2.4, 196.0 * 2 ** (-9 / 1200), 196.0 * 2 ** (-9 / 1200), vib_hz=4.5, gain=0.25),
        ],
        "burst-choir.wav": [
            np.concatenate([bleat(0.45, 174.0, 233.0, gain=0.35),
                            bleat(0.45, 196.0, 262.0, gain=0.35),
                            bleat(0.9, 220.0, 330.0, gain=0.4)]),
        ],
    }
    for name, layers in jobs.items():
        top = max(len(l) for l in layers)
        mix = np.zeros(top)
        for l in layers:
            mix[: len(l)] += l
        mix /= max(1e-6, np.abs(mix).max())
        mix *= 0.89
        path = os.path.join(OUT, name)
        write_wav(path, mix)
        rms = float(np.sqrt(np.mean(mix ** 2)))
        print(f"{name}: {len(mix) / SR:.2f}s rms={rms:.3f} peak={float(np.abs(mix).max()):.3f}")


if __name__ == "__main__":
    main()
