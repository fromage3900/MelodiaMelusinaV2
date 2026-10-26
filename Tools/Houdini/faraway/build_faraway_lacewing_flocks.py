r"""build_faraway_lacewing_flocks.py -- W11 (analytic; crowdsolver unavailable): beat-locked Lace Wing flight paths. spike: true

8 closed flight templates (Lissajous orbits that START and END on a settle pose), period = 4 bars at 96 bpm = 10 s,
sampled at 12 Hz in LOCAL metres around a settle point (z up). Each of the 231 settle points from FarawayWonder gets
template id, yaw, phase offset (in beats, multiples of 0.25) and flock size. Wing phase: one wingbeat per beat.
Contract (gate): every template is C0-closed, touches the settle pose (r<0.05 m, z=0) exactly on the bar downbeat,
speed <= 1.6 m/s, altitude 0..3.2 m; assignments deterministic.
Outputs: flock_templates.json, flock_assignments.json, flight_paths_sheet.png, manifest.json. No UE, no materials.
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
S = ROOT / "Saved" / "Staging" / "HoudiniForge"
OUT = S / "FarawayFlocks_20261026"
BPM, BARS, HZ = 96, 4, 12
PERIOD = BARS * 4 * 60.0 / BPM      # 10 s
VMAX = 1.6


def h(*a):
    x = 2166136261
    for v in a:
        x = ((x ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 4294967295.0


def template(k):
    """closed orbit; settle pose at t=0 and t=PERIOD (smooth ease in/out of the orbit amplitude)."""
    n = int(PERIOD * HZ)
    t = np.arange(n + 1) / n                       # 0..1
    amp = np.sin(math.pi * t) ** 2                 # 0 at both ends -> settled
    a, b = [(1, 1), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2), (1, 1)][k]
    R = 1.5 / max(a, b) * (1.0 + 0.12 * (k % 3))      # peak speed ~ 2*pi*f*R/T, kept under the 1.6 m/s drift limit
    ph = 2 * math.pi * k / 8
    x = R * amp * np.sin(2 * math.pi * a * t + ph)
    y = R * amp * np.sin(2 * math.pi * b * t + 0.5 * ph + (math.pi / 2 if a == b else 0.0))
    z = 0.5 + 1.3 * amp * (0.5 + 0.5 * np.sin(2 * math.pi * 2 * t + ph)) - 0.5 * (1 - amp)   # 0 at ends
    z = np.maximum(z, 0.0) * (amp > 1e-6) + 0.0
    z = 1.1 * amp * (1 + 0.4 * np.sin(2 * math.pi * 2 * t + ph))
    return np.c_[x, y, z]


def png(path, a):
    hh, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(hh))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, hh, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw, 6)) + ch(b"IEND", b""))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    T = [template(k) for k in range(8)]
    speeds = [float(np.max(np.linalg.norm(np.diff(p, axis=0), axis=1) * HZ)) for p in T]
    tpl = [{"id": k, "hz": HZ, "period_s": PERIOD, "bars": BARS, "loop": True,
            "points_m": [[round(float(v), 3) for v in q] for q in p[::1]], "max_speed_m_s": round(speeds[k], 3),
            "wingbeat": {"per_beat": 1, "phase_beats": round(0.25 * k, 2)}} for k, p in enumerate(T)]
    (OUT / "flock_templates.json").write_text(json.dumps({"bpm": BPM, "templates": tpl}))
    lw = json.load(open(S / "FarawayWonder_20261026" / "lace_wings.json"))
    assign = []
    for i, sp in enumerate(lw["settle_points"]):
        assign.append({"x": sp["x"], "y": sp["y"], "template": int(h(i, 1) * 8) % 8, "yaw_deg": round(h(i, 2) * 360, 1),
                       "phase_beats": round(int(h(i, 3) * 16) * 0.25, 2), "flock": sp["flock"]})
    (OUT / "flock_assignments.json").write_text(json.dumps({"count": len(assign), "assignments": assign}))
    # sheet: top-down overlay + altitude strips
    N = 960
    img = np.zeros((N, N // 2 + 200, 3), np.uint8) + 14
    pal = [(255, 160, 200), (150, 180, 255), (255, 230, 140), (160, 255, 190), (255, 140, 120), (200, 160, 255), (140, 230, 255), (255, 200, 110)]
    for k, p in enumerate(T):
        for q in p:
            i = int(240 + q[0] * 110); j = int(240 + q[1] * 110)
            if 0 <= i < 480 and 0 <= j < 480: img[j, i] = pal[k]
        for n_, q in enumerate(p):
            i = int(480 + n_ / len(p) * 190); j = int(520 + k * 50 - q[2] / 3.2 * 40)
            if 0 <= j < N and i < img.shape[1]: img[j, i] = pal[k]
    png(OUT / "flight_paths_sheet.png", img)
    ends = [float(np.linalg.norm(p[0] - p[-1])) for p in T]
    gate = {"templates": 8, "max_speed_m_s": round(max(speeds), 3), "closure_error_max_m": round(max(ends), 5),
            "settle_pose_max_m": round(max(max(np.linalg.norm(p[0]), np.linalg.norm(p[-1])) for p in T), 5),
            "max_altitude_m": round(max(float(p[:, 2].max()) for p in T), 3), "min_altitude_m": round(min(float(p[:, 2].min()) for p in T), 5),
            "assignments": len(assign), "period_beats": BARS * 4}
    gate["pass"] = bool(gate["max_speed_m_s"] <= VMAX and gate["closure_error_max_m"] < 1e-6 and gate["settle_pose_max_m"] < 0.05
                        and 0 <= gate["min_altitude_m"] and gate["max_altitude_m"] <= 3.2 and gate["assignments"] == len(lw["settle_points"]))
    (OUT / "manifest.json").write_text(json.dumps({"schema": "melodia.faraway_flocks.spike.v1", "spike": True, "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(OUT.glob("*")) if p.is_file() and p.name != "manifest.json"}}, indent=1))
    print("GATE", json.dumps(gate))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
