"""Contract tests for the Jev Sheep Conductor prototype.

Run: python test_jev_sheep_conductor.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jev_sheep_conductor import (
    FLOCK_OPTIONS,
    WORLD_OPTIONS,
    ConductorState,
    SheepConductor,
    format_hud,
)

os.environ.pop("TYPESAFE_API_KEY", None)  # tests pin the fallback path

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool) -> None:
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name)


def calm_state(**kw) -> ConductorState:
    base = dict(bpm_intensity=0.2, beat_energy=0.2, player_distance_m=25.0,
                player_movement="still", resonance=0.1, wind_strength=0.2,
                seconds_since_last_response=2.0)
    base.update(kw)
    return ConductorState(**base)


# 1. authored options only
c = SheepConductor()
d = c.evaluate(calm_state(), now=100.0)
check("flock choice is authored", d.flock.choice in FLOCK_OPTIONS)
check("world choice is authored", d.world.choice in WORLD_OPTIONS)
check("flock dist covers all 9", set(d.flock.probabilities) == set(FLOCK_OPTIONS))
check("world dist covers all 6", set(d.world.probabilities) == set(WORLD_OPTIONS))

# 2. distributions sum to 1, top matches choice
check("flock dist sums to 1",
      abs(sum(d.flock.probabilities.values()) - 1.0) < 1e-6)
check("world dist sums to 1",
      abs(sum(d.world.probabilities.values()) - 1.0) < 1e-6)
check("flock top == choice",
      max(d.flock.probabilities, key=d.flock.probabilities.get) == d.flock.choice)

# 3. sanity beats resolve as expected (fallback heuristic)
c2 = SheepConductor()
d2 = c2.evaluate(calm_state(), now=200.0)
check("quiet exploration holds calm", d2.flock.choice in ("GRAZE", "TURN_TO_PLAYER"))

c3 = SheepConductor()
d3 = c3.evaluate(calm_state(player_distance_m=4.0), now=300.0)
check("approach greets player", d3.flock.choice == "TURN_TO_PLAYER")

c4 = SheepConductor()
d4 = c4.evaluate(calm_state(wind_strength=0.8), now=400.0)
check("strong wind turns flock", d4.flock.choice == "FOLLOW_WIND")

c5 = SheepConductor()
d5 = c5.evaluate(calm_state(resonance=0.95, beat_energy=0.9,
                            bpm_intensity=0.9, seconds_since_last_response=1.0),
                 now=500.0)
check("peak bursts", d5.flock.choice == "CRESCENDO_BURST")
check("peak ripples world", d5.world.choice == "RESONANCE_RIPPLE")

# 4. cooldown: no twitch on flip-flop evaluations
c6 = SheepConductor()
s_calm = calm_state()
s_wind = calm_state(wind_strength=0.9)
c6.evaluate(s_calm, now=600.0)
first = c6.current_flock
c6.evaluate(s_wind, now=600.5)  # 0.5s later: must hold, not twitch
check("cooldown holds under MIN_HOLD", c6.current_flock == first)
c6.evaluate(s_wind, now=600.5 + 10.0)  # after hold: may switch
check("releases after hold", c6.current_flock == "FOLLOW_WIND")

# 5. fallback is deterministic
c7, c8 = SheepConductor(), SheepConductor()
a = c7.evaluate(calm_state(wind_strength=0.7), now=700.0)
b = c8.evaluate(calm_state(wind_strength=0.7), now=700.0)
check("fallback deterministic",
      a.flock.probabilities == b.flock.probabilities)

# 6. provenance is honest
check("fallback labeled", a.source == "classical-fallback")

# 7. HUD format
hud = format_hud(a)
check("hud header", hud.startswith("JEV SHEEP CONDUCTOR"))
check("hud behavior line", "Behavior: " in hud)
check("hud world line", "World: " in hud)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
