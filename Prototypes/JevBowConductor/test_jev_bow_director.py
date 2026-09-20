"""Contract tests for the Jev Bow Conductor prototype.

Run: python test_jev_bow_director.py
Pins the fallback path (drops the key) so tests are deterministic and free.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.pop("TYPESAFE_API_KEY", None)

from jev_bow_director import (  # noqa: E402
    ASSET_MAP,
    BOW_MESH,
    BOW_OPTIONS,
    BowConductor,
    BowState,
    format_hud,
)

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool) -> None:
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name)


def calm(**kw) -> BowState:
    base = dict(bpm_intensity=0.2, beat_energy=0.2, target_distance_m=None,
                movement="still", resonance=0.1, wind_strength=0.2,
                seconds_since_last_loose=99.0)
    base.update(kw)
    return BowState(**base)


# 1. every option maps to a real authored asset on disk (presence only)
for opt in BOW_OPTIONS:
    check(f"asset present: {opt}", os.path.isfile(ASSET_MAP[opt]))
check("bow mesh present", os.path.isfile(BOW_MESH))

# 2. choices stay authored, distributions sum to 1
c = BowConductor()
d = c.evaluate(calm(), now=100.0)
check("choice is authored", d.bow.choice in BOW_OPTIONS)
check("dist covers all 7", set(d.bow.probabilities) == set(BOW_OPTIONS))
check("dist sums to 1", abs(sum(d.bow.probabilities.values()) - 1.0) < 1e-6)
check("top == choice",
      max(d.bow.probabilities, key=d.bow.probabilities.get) == d.bow.choice)

# 3. sanity beats
c2 = BowConductor()
check("quiet rests ready",
      c2.evaluate(calm(), now=200.0).bow.choice == "IDLE_READY")

c3 = BowConductor()
d3 = c3.evaluate(calm(target_distance_m=12.0), now=300.0)
check("engagement draws V1", d3.bow.choice == "BOW_V1")

c4 = BowConductor()
d4 = c4.evaluate(calm(target_distance_m=10.0, beat_energy=0.85,
                      bpm_intensity=0.8), now=400.0)
check("heavy beat draws V2", d4.bow.choice == "BOW_V2")

c5 = BowConductor()
d5 = c5.evaluate(calm(target_distance_m=10.0, beat_energy=0.9,
                      bpm_intensity=0.9, resonance=0.95,
                      seconds_since_last_loose=30.0), now=500.0)
check("peak showcases polished", d5.bow.choice == "BOW_POLISHED")
check("peak earns loose", d5.loose is True)

c6 = BowConductor()
d6 = c6.evaluate(calm(seconds_since_last_loose=2.0), now=600.0)
check("after loose lowers", d6.bow.choice == "LOWER_BOW")
check("rest never looses", d6.loose is False or d6.bow.choice != "IDLE_READY")

# 4. cooldown: no twitch on flip-flop
c7 = BowConductor()
s_calm, s_hot = calm(), calm(target_distance_m=8.0, beat_energy=0.9,
                             bpm_intensity=0.9, resonance=0.9)
c7.evaluate(s_calm, now=700.0)
first = c7.current
c7.evaluate(s_hot, now=700.5)
check("cooldown holds under MIN_HOLD", c7.current == first)
c7.evaluate(s_hot, now=710.5)
check("releases after hold", c7.current == "BOW_POLISHED")

# 5. determinism + provenance
a = BowConductor().evaluate(calm(target_distance_m=9.0), now=800.0)
b = BowConductor().evaluate(calm(target_distance_m=9.0), now=800.0)
check("fallback deterministic", a.bow.probabilities == b.bow.probabilities)
check("fallback labeled", a.source == "classical-fallback")

# 6. HUD format
hud = format_hud(a)
check("hud header", hud.startswith("JEV BOW CONDUCTOR"))
check("hud bow line", "Bow: " in hud)
check("hud loose line", "Loose: " in hud)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
