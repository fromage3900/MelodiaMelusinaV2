r"""build_faraway_lullaby.py -- W12: the Faraway lullaby motif (MIDI + driven curves + piano-roll sheet). spike: true

No source audio exists in the repo, so the motif is composed deterministically here (D Lydian, 96 bpm, 4/4, 8 bars = 20 s):
  phrase A (bars 1-4) asks and ends on E (unresolved); phrase B (bars 5-8) answers and resolves to D.
  Lullaby gate phrase = the first three notes of A (D5 F#5 A5).
Outputs (<out>): lullaby.mid (format 0, 480 ppq), lullaby_curves.json (24 Hz glow / breath / bloom-note / hum-window),
lullaby_notes.json, lullaby_pianoroll.png, manifest.json. Curves are the one timing source for lantern glow, La Berceuse
breath and sing-to-bloom note index (read-only consumers; the audio chain keeps its single writers).
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayLullaby_20261026"
BPM, PPQ, BEATS_PER_BAR, BARS = 96, 480, 4, 8
N = {"D5": 74, "E5": 76, "F#5": 78, "G#5": 80, "A5": 81, "B5": 83, "C#5": 73, "D3": 50, "E3": 52, "G3": 55, "B2": 47, "A2": 45}
# (note, start_beat, dur_beats)
MEL = [("D5", 0, 1), ("F#5", 1, 1), ("A5", 2, 2),
       ("G#5", 4, 1), ("F#5", 5, 1), ("E5", 6, 2),
       ("F#5", 8, 1), ("A5", 9, 1), ("B5", 10, 1), ("A5", 11, 1),
       ("F#5", 12, 2), ("E5", 14, 2),
       ("B5", 16, 1), ("A5", 17, 1), ("F#5", 18, 2),
       ("E5", 20, 1), ("F#5", 21, 1), ("G#5", 22, 2),
       ("A5", 24, 1), ("F#5", 25, 1), ("E5", 26, 1), ("C#5", 27, 1),
       ("D5", 28, 4)]
BASS = [("D3", 0, 4), ("D3", 4, 4), ("B2", 8, 4), ("E3", 12, 4), ("G3", 16, 4), ("E3", 20, 4), ("A2", 24, 4), ("D3", 28, 4)]


def vlq(v):
    b = [v & 0x7F]
    v >>= 7
    while v:
        b.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(b))


def write_midi(path):
    ev = []
    for name, st, du in MEL:
        ev += [(int(st * PPQ), 0x90, N[name], 84), (int((st + du) * PPQ) - 8, 0x80, N[name], 0)]
    for name, st, du in BASS:
        ev += [(int(st * PPQ), 0x91, N[name], 56), (int((st + du) * PPQ) - 8, 0x81, N[name], 0)]
    ev.sort(key=lambda e: (e[0], e[1]))
    trk = b"\x00\xff\x51\x03" + (60_000_000 // BPM).to_bytes(3, "big") + b"\x00\xff\x58\x04\x04\x02\x18\x08"
    t = 0
    for tick, s, n, v in ev:
        trk += vlq(tick - t) + bytes((s, n, v))
        t = tick
    trk += b"\x00\xff\x2f\x00"
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ) + b"MTrk" + struct.pack(">I", len(trk)) + trk)


def read_midi_notes(path):
    d = path.read_bytes()
    assert d[:4] == b"MThd"
    i = 14 + 8
    n_on, t, run = 0, 0, 0
    end = len(d)
    while i < end:
        v = 0
        while True:
            b = d[i]; i += 1; v = (v << 7) | (b & 0x7F)
            if not b & 0x80: break
        t += v
        s = d[i]
        if s == 0xFF:
            i += 3 + d[i + 2]; continue
        run = s; i += 1
        if (run & 0xF0) == 0x90 and d[i + 1] > 0: n_on += 1
        i += 2
    return n_on


def png(path, a):
    h, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_midi(OUT / "lullaby.mid")
    total_beats = BARS * BEATS_PER_BAR
    hz = 24
    spb = 60.0 / BPM
    T = np.arange(0, total_beats * spb, 1.0 / hz)
    glow = np.zeros_like(T)
    note_idx = np.zeros_like(T)
    pcs = {"D": 0, "E": 1, "F#": 2, "G#": 3, "A": 4, "B": 5, "C#": 6}
    for name, st, du in MEL:
        t0 = st * spb
        m = T >= t0
        glow[m] = np.maximum(glow[m], np.exp(-(T[m] - t0) / (0.55 * du * spb + 0.25)))
        note_idx[(T >= t0) & (T < t0 + du * spb)] = pcs[name[:-1]]
    beat = T / spb
    breath = 0.5 + 0.5 * np.sin(2 * math.pi * (beat / BEATS_PER_BAR) - math.pi / 2)
    hum_window = ((beat % 4) < 0.5).astype(int)       # downbeat window: on-beat hum accepted
    gate_notes = [n for n, *_ in MEL[:3]]
    curves = {"hz": hz, "bpm": BPM, "duration_s": round(float(T[-1]), 3), "loop": True,
              "glow": [round(float(x), 4) for x in glow], "breath": [round(float(x), 4) for x in breath],
              "bloom_note_index": [int(x) for x in note_idx], "hum_window": [int(x) for x in hum_window]}
    (OUT / "lullaby_curves.json").write_text(json.dumps(curves))
    (OUT / "lullaby_notes.json").write_text(json.dumps({"key": "D Lydian", "bpm": BPM, "time": "4/4", "bars": BARS,
        "melody": [{"note": n, "midi": N[n], "start_beat": s, "dur_beats": d} for n, s, d in MEL],
        "bass": [{"note": n, "midi": N[n], "start_beat": s, "dur_beats": d} for n, s, d in BASS],
        "phrases": {"A": {"bars": [1, 4], "ends_on": "E5", "function": "question"}, "B": {"bars": [5, 8], "ends_on": "D5", "function": "answer, resolves"}},
        "lullaby_gate_phrase": gate_notes, "scale_degree_for_bloom_index": list(pcs)}, indent=1))

    # piano roll sheet: 8 bars x 960 px wide, pitches 45..84, plus glow/breath strips
    W, H = 1024, 420
    a = np.zeros((H, W, 3), np.uint8) + 16
    px_beat = (W - 32) / total_beats
    for b in range(total_beats + 1):
        a[:300, 16 + int(b * px_beat):17 + int(b * px_beat)] = (50, 50, 70) if b % 4 else (110, 110, 150)
    def y(p): return 300 - int((p - 44) / 40 * 290) - 6
    for n, s, d in BASS:
        a[y(N[n]):y(N[n]) + 6, 16 + int(s * px_beat):16 + int((s + d) * px_beat) - 2] = (90, 120, 255)
    for k, (n, s, d) in enumerate(MEL):
        col = (255, 90, 170) if k < 3 else ((255, 190, 90) if s < 16 else (150, 255, 170))
        a[y(N[n]):y(N[n]) + 8, 16 + int(s * px_beat):16 + int((s + d) * px_beat) - 2] = col
    for i, g in enumerate(glow):
        x = 16 + int(i / len(glow) * (W - 32)); a[310:310 + int(g * 50), x] = (255, 220, 120)
    for i, g in enumerate(breath):
        x = 16 + int(i / len(breath) * (W - 32)); a[370:370 + int(g * 40), x] = (120, 200, 255)
    png(OUT / "lullaby_pianoroll.png", a)

    notes_back = read_midi_notes(OUT / "lullaby.mid")
    gate = {"midi_roundtrip_notes": notes_back, "expected_notes": len(MEL) + len(BASS),
            "ends_on_tonic": MEL[-1][0] == "D5", "phrase_A_ends_unresolved": MEL[-3 + 1][0] != "D5" and MEL[11][0] == "E5",
            "bars": max(s + d for _, s, d in MEL) / BEATS_PER_BAR, "curve_samples": len(glow),
            "curves_in_unit_range": bool(glow.min() >= 0 and glow.max() <= 1 and breath.min() >= 0 and breath.max() <= 1)}
    gate["pass"] = bool(gate["midi_roundtrip_notes"] == gate["expected_notes"] and gate["ends_on_tonic"] and gate["phrase_A_ends_unresolved"]
                        and gate["bars"] == BARS and gate["curves_in_unit_range"])
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_lullaby.spike.v1", "spike": True, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
