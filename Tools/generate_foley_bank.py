"""generate_foley_bank.py -- deterministic offline foley bank (created-first, 2026-10-05).

Generates the 65 source WAVs specified in Docs/Production/FOLEY_BANK_SPEC_2026-10-05.md:
  Content/Melodia/Audio/Foley/Footsteps/{Grass,Dirt,Stone,Wood,Splash}/SW_FS_*
  Content/Melodia/Audio/Foley/Interaction/SW_INT_*
  Content/Melodia/Audio/Foley/Combat/SW_CMB_*

Created-deterministic (spec source decision): seeded synthesis, no neural source, no
network. Reruns are byte-stable per seed. Import the .wav files to .uasset in one pass
(editor open), all SCL_SFX-routed per the spec.

Run:  python Tools/generate_foley_bank.py
Evidence: Saved/Audit/Status/foley_bank_manifest.json
"""

import json
import os
import struct
import wave

import numpy as np

OUT_ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Audio\Foley"
EVIDENCE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\Status"
SR = 44100
PEAK_DB = -3.0
GLOBAL_SEED = 20261005


def rng(seed: int):
    return np.random.default_rng(seed)


def normalize(x: np.ndarray, peak_db: float = PEAK_DB) -> np.ndarray:
    peak = np.max(np.abs(x))
    if peak <= 1e-9:
        return x
    target = 10.0 ** (peak_db / 20.0)
    return x * (target / peak)


def write_wav(path: str, x: np.ndarray):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.clip(normalize(x), -1.0, 1.0)
    pcm = (x * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def envelope(x: np.ndarray, attack_ms: float, decay_ms: float) -> np.ndarray:
    """Exponential attack to 1, exponential decay to 0 over decay_ms; total length = len(x)."""
    n = len(x)
    a = max(1, int(SR * attack_ms / 1000.0))
    d = max(1, int(SR * decay_ms / 1000.0))
    env = np.ones(n)
    env[:a] = np.linspace(0.0, 1.0, a)
    tail = np.exp(-3.0 * np.arange(d) / d)
    m = min(d, n - a)
    env[a:a + m] = tail[:m]
    if n > a + m:
        env[a + m:] = tail[-1] if m > 0 else 0.0
    return env


def bandpass(x: np.ndarray, fc: float, q: float = 1.0) -> np.ndarray:
    """First-order biquad-ish resonant bandpass (one-pole cascade, good enough for foley)."""
    dt = 1.0 / SR
    rc = 1.0 / (2.0 * np.pi * fc)
    alpha = dt / (rc + dt)
    y = np.zeros_like(x)
    x_prev, y_prev = 0.0, 0.0
    for i in range(len(x)):
        y_prev = y_prev + alpha * (x[i] - x_prev)
        x_prev = x[i]
        y[i] = y_prev
    return y


def sine_burst(freq: float, dur_ms: float, decay_ms: float, detune_hz: float = 0.0) -> np.ndarray:
    n = int(SR * dur_ms / 1000.0)
    t = np.arange(n) / SR
    env = np.exp(-3.0 * np.arange(n) / max(1, int(SR * decay_ms / 1000.0)))
    return np.sin(2.0 * np.pi * freq * t + 2.0 * np.pi * detune_hz * t * t / SR) * env


def noise_burst(dur_ms: float, decay_ms: float, fc: float, q_gain: float = 1.0, seed: int = 0) -> np.ndarray:
    n = int(SR * dur_ms / 1000.0)
    x = rng(seed).standard_normal(n)
    x = bandpass(x, fc)
    return q_gain * x * envelope(x, attack_ms=2.0, decay_ms=decay_ms)


def karplus_strong(freq: float, dur_ms: float, damping: float = 0.996, seed: int = 0) -> np.ndarray:
    n_out = int(SR * dur_ms / 1000.0)
    delay = max(2, int(round(SR / freq)))
    buf = rng(seed).standard_normal(delay).astype(float)
    buf *= 0.5
    out = np.zeros(n_out)
    for i in range(n_out):
        cur = buf[0]
        nxt = buf[1]
        buf = np.roll(buf, 1)
        buf[0] = damping * 0.5 * (cur + nxt)
        out[i] = cur
    return out


def add_to(x: np.ndarray, burst: np.ndarray, offset: int = 0) -> np.ndarray:
    """Add burst into x at offset, clipping both ends. Returns x (in place)."""
    n = min(len(burst), len(x) - offset)
    if n > 0 and 0 <= offset < len(x):
        x[offset:offset + n] += burst[:n]
    return x


def clatter(hits, seed: int) -> np.ndarray:
    """hits: list of (delay_ms, freq, dur_ms, amp)."""
    total_ms = max(h + 200 for h, _f, d, _a in hits) + 300
    n = int(SR * total_ms / 1000.0)
    out = np.zeros(n)
    r = rng(seed)
    for i, (delay_ms, freq, dur_ms, amp) in enumerate(hits):
        b = sine_burst(freq * r.uniform(0.96, 1.04), dur_ms, dur_ms)
        off = int(SR * delay_ms / 1000.0)
        out[off:off + len(b)] += amp * b
    return out


manifest = []
seed_counter = [GLOBAL_SEED]


def emit(relpath: str, audio: np.ndarray, label: str):
    seed_counter[0] += 1
    path = os.path.join(OUT_ROOT, relpath.replace("/", os.sep))
    write_wav(path, audio)
    manifest.append({
        "asset_base": os.path.splitext(os.path.basename(relpath))[0],
        "label": label,
        "seconds": round(len(audio) / SR, 3),
        "seed": seed_counter[0],
    })
    print(f"  {relpath}  ({len(audio)/SR:.3f}s, seed {seed_counter[0]})")


# ── Footsteps ─────────────────────────────────────────────────────────────
# Surface character: transient "knock" (sine burst) + filtered noise bed.
# Grass: soft, little knock, lots of low-amp fine noise. Dirt: muddy thump.
# Stone: bright knock + short hard noise. Wood: mid knock + slight ring. Splash: noise + droplets.

FOOT = {
    "Grass":  dict(kick=95.0,  kick_db=0.35, noise_db=0.55, fc=1800.0, dur=110, decay=90,  extra="grass"),
    "Dirt":   dict(kick=70.0,  kick_db=0.85, noise_db=0.60, fc=900.0,  dur=130, decay=120, extra="thud"),
    "Stone":  dict(kick=180.0, kick_db=0.95, noise_db=0.70, fc=3200.0, dur=90,  decay=70,  extra="clack"),
    "Wood":   dict(kick=140.0, kick_db=0.80, noise_db=0.55, fc=2400.0, dur=110, decay=85,  extra="ring"),
    "Splash": dict(kick=60.0,  kick_db=0.50, noise_db=0.95, fc=4500.0, dur=180, decay=160, extra="splash"),
}

for surface, p in FOOT.items():
    for i in range(1, 7):
        s = seed_counter[0] + i
        r = rng(s)
        n = int(SR * p["dur"] / 1000.0)
        kick = sine_burst(p["kick"] * r.uniform(0.94, 1.06), p["dur"], p["decay"]) * p["kick_db"]
        bed = noise_burst(p["dur"], p["decay"], p["fc"], p["noise_db"], seed=s + 1)
        x = kick + bed
        if p["extra"] == "grass":
            rustle = noise_burst(60, 50, 6000.0, 0.25, seed=s + 2)
            off = int(n * 0.25)
            x[off:off + len(rustle)] += rustle[: min(len(rustle), n - off)]
        elif p["extra"] == "thud":
            add_to(x, sine_burst(45.0 * r.uniform(0.95, 1.05), 140, 130) * 0.5)
        elif p["extra"] == "clack":
            add_to(x, sine_burst(2600.0 * r.uniform(0.9, 1.1), 24, 20) * 0.18)
        elif p["extra"] == "ring":
            add_to(x, karplus_strong(420.0 * r.uniform(0.9, 1.1), 90, 0.994, seed=s + 3) * 0.12)
        elif p["extra"] == "splash":
            for k in range(int(r.integers(3, 6))):
                drop = sine_burst(r.uniform(1800, 3600), 30, 26) * 0.3
                off = int(n * (0.35 + 0.6 * k / 5.0))
                x[off:off + len(drop)] += drop[: min(len(drop), n - off)]
        emit(f"Footsteps/{surface}/SW_FS_{surface}_{i}.wav", x, f"footstep {surface} {i}")

# ── Interaction ───────────────────────────────────────────────────────────
for i in range(1, 5):  # rock pickup: short clatter
    s = seed_counter[0] + i
    r = rng(s)
    x = clatter(
        [(0, 220 * r.uniform(0.9, 1.1), 90, 0.9),
         (40 + 30 * r.random(), 340 * r.uniform(0.9, 1.1), 70, 0.5),
         (90 + 40 * r.random(), 150 * r.uniform(0.9, 1.1), 120, 0.4)],
        seed=s)
    add_to(x, noise_burst(60, 40, 2600.0, 0.3, seed=s + 1))
    emit(f"Interaction/SW_INT_Rock_{i}.wav", x, f"rock pickup {i}")

for i in range(1, 4):  # bench sit: low thump + fabric
    s = seed_counter[0] + i
    r = rng(s)
    x = sine_burst(55 * r.uniform(0.9, 1.1), 200, 190) * 0.9
    add_to(x, noise_burst(120, 100, 700.0, 0.4, seed=s + 1))
    add_to(x, noise_burst(180, 160, 2400.0, 0.22, seed=s + 2))  # fabric settle
    emit(f"Interaction/SW_INT_BenchSit_{i}.wav", x, f"bench sit {i}")

for i in range(1, 4):  # bench stand: thump lighter + fabric lift
    s = seed_counter[0] + i
    r = rng(s)
    x = sine_burst(65 * r.uniform(0.9, 1.1), 150, 140) * 0.6
    add_to(x, noise_burst(140, 120, 1600.0, 0.3, seed=s + 1))
    emit(f"Interaction/SW_INT_BenchStand_{i}.wav", x, f"bench stand {i}")

for i in range(1, 5):  # door: creak (inharmic sweep) + latch
    s = seed_counter[0] + i
    r = rng(s)
    n = int(SR * 420 / 1000.0)
    t = np.arange(n) / SR
    f0, f1 = r.uniform(90, 140), r.uniform(300, 480)
    freq = f0 + (f1 - f0) * (t / (len(t) / SR)) ** 1.4
    creak = (np.sin(2 * np.pi * np.cumsum(freq) / SR) + 0.4 * np.sin(4.7 * 2 * np.pi * np.cumsum(freq) / SR))
    creak *= envelope(creak, 90.0, 330.0)
    latch = sine_burst(1400 * r.uniform(0.9, 1.1), 30, 26) * 0.5
    x = np.zeros(n + len(latch))
    x[:n] += 0.8 * creak
    x[-len(latch):] += latch
    emit(f"Interaction/SW_INT_Door_{i}.wav", x, f"door {i}")

for i in range(1, 5):  # prop grab: soft click + fabric
    s = seed_counter[0] + i
    r = rng(s)
    click = sine_burst(900 * r.uniform(0.9, 1.1), 22, 18) * 0.5
    x = np.zeros(max(len(click), int(SR * 70 / 1000.0)))
    add_to(x, click)
    add_to(x, noise_burst(70, 60, 3000.0, 0.25, seed=s + 1))
    emit(f"Interaction/SW_INT_Prop_{i}.wav", x, f"prop grab {i}")

# ── Combat (WaveHarp) ────────────────────────────────────────────────────
for i in range(1, 5):  # draw whoosh: rising band-passed noise
    s = seed_counter[0] + i
    r = rng(s)
    n = int(SR * 180 / 1000.0)
    x = rng(s).standard_normal(n)
    t = np.arange(n) / SR
    x *= 0.3 + 0.7 * (t / (len(t) / SR)) ** 1.6
    x = bandpass(x, 2200.0 * r.uniform(0.9, 1.1))
    x *= envelope(x, 30.0, 150.0) * 0.9
    emit(f"Combat/SW_CMB_Draw_{i}.wav", x, f"draw whoosh {i}")

for i in range(1, 5):  # release: string snap + bright transient
    s = seed_counter[0] + i
    r = rng(s)
    snap = karplus_strong(520 * r.uniform(0.95, 1.05), 220, 0.985, seed=s) * 0.5
    tick = sine_burst(3000 * r.uniform(0.9, 1.1), 14, 12) * 0.5
    n = max(len(snap), len(tick)) + 400
    x = np.zeros(n)
    x[:len(snap)] += snap
    x[80:80 + len(tick)] += tick
    emit(f"Combat/SW_CMB_Release_{i}.wav", x, f"release {i}")

for i in range(1, 4):  # arrow whoosh
    s = seed_counter[0] + i
    r = rng(s)
    n = int(SR * 130 / 1000.0)
    x = rng(s).standard_normal(n)
    x = bandpass(x, 3400 * r.uniform(0.9, 1.1))
    x *= envelope(x, 6.0, 110.0) * 0.7
    emit(f"Combat/SW_CMB_Whoosh_{i}.wav", x, f"arrow whoosh {i}")

for i in range(1, 7):  # impact thud; grades differentiate by brightness
    s = seed_counter[0] + i
    r = rng(s)
    bright = 0.4 + 0.12 * (i - 1)  # sample 6 (Perfect) brightest
    x = sine_burst(85 * r.uniform(0.9, 1.1), 160, 150) * 0.9
    add_to(x, sine_burst(240 * r.uniform(0.9, 1.1), 90, 80) * 0.4)
    add_to(x, noise_burst(70, 60, 2800.0, bright * 0.5, seed=s + 1))
    emit(f"Combat/SW_CMB_Impact_{i}.wav", x, f"impact {i} (grade {i})")

# ── Evidence ─────────────────────────────────────────────────────────────
os.makedirs(EVIDENCE_DIR, exist_ok=True)
with open(os.path.join(EVIDENCE_DIR, "foley_bank_manifest.json"), "w") as f:
    json.dump({
        "asset": "foley_bank_v1",
        "date": "2026-10-05",
        "source_decision": "created-deterministic (FOLEY_BANK_SPEC_2026-10-05.md)",
        "sr": SR,
        "peak_db": PEAK_DB,
        "out_root": OUT_ROOT,
        "count": len(manifest),
        "manifest": manifest,
    }, f, indent=2)
print(f"\nDone: {len(manifest)} WAVs in {OUT_ROOT}")
print(f"Evidence: {EVIDENCE_DIR}\\foley_bank_manifest.json")
