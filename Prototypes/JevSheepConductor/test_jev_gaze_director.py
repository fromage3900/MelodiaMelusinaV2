"""Mock-harness tests for the gaze director. No editor, no network.

Run: python test_jev_gaze_director.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jev_gaze_director import (  # noqa: E402
    RELEASE_RADIUS_M,
    SheepGazeDirector,
    SheepHandle,
)
from jev_sheep_conductor import (  # noqa: E402
    ChannelResult,
    Decision,
    FLOCK_OPTIONS,
    WORLD_OPTIONS,
)

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool) -> None:
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name)


def synth_dec(flock: str, fprob: float, source: str) -> Decision:
    n_f, n_w = len(FLOCK_OPTIONS), len(WORLD_OPTIONS)
    fdist = {o: (fprob if o == flock else (1 - fprob) / (n_f - 1))
             for o in FLOCK_OPTIONS}
    wdist = {o: (0.6 if o == "SOFT_WIND" else 0.4 / (n_w - 1))
             for o in WORLD_OPTIONS}
    fch = ChannelResult(flock, fdist, fprob,
                        sorted(((o, p) for o, p in fdist.items() if o != flock),
                               key=lambda kv: kv[1], reverse=True))
    wch = ChannelResult("SOFT_WIND", wdist, 0.6, [])
    return Decision(fch, wch, source, "synthetic", True, False,
                    cand_flock=flock, cand_world="SOFT_WIND")


def flock(n: int = 3) -> list[SheepHandle]:
    return [SheepHandle(f"s{i}", x=float(i * 2), y=0.0) for i in range(n)]


TURN = lambda s: synth_dec("TURN_TO_PLAYER", 1.0, "jev-live")  # noqa: E731
GRAZE = lambda s: synth_dec("GRAZE", 0.8, "classical-fallback")  # noqa: E731


# 1. enter -> gaze on
d = SheepGazeDirector(flock(), decide=TURN)
r = d.tick(25.0, 0.0, 1.2, 0.2, 2.0)  # far, walking
check("far: no gaze", r["gaze_on"] is False)
r = d.tick(5.0, 0.0, 0.1, 0.2, 2.0)  # close, still
check("enter still: gaze on", r["gaze_on"] is True)
check("director jev", r["director"] == "JEV")

# 2. wind rises -> gaze holds (the point-of-view moment)
r = d.tick(5.0, 0.0, 0.1, 0.9, 2.0)
check("wind 0.9: gaze holds", r["gaze_on"] is True)

# 3. authored release: leaving wins over Jev
r = d.tick(RELEASE_RADIUS_M + 2.0, 0.0, 0.1, 0.2, 2.0)
check("leaves radius: released", r["gaze_on"] is False)
check("resolution authored", "AUTHORED" in r["hud"])

# 4. authored release: sustained running
d2 = SheepGazeDirector(flock(), decide=TURN)
d2.tick(5.0, 0.0, 0.1, 0.2, 2.0)
check("gaze on", d2.gaze_on is True)
d2.tick(5.0, 0.0, 2.5, 0.2, 2.0)
r = d2.tick(5.0, 0.0, 2.5, 0.2, 2.0)  # 4s fast -> release
check("running 4s: released despite Jev TURN", r["gaze_on"] is False)

# 5. failsafe: Jev throws -> deterministic, never blocks
def boom(s):
    raise ConnectionError("no backend")
d3 = SheepGazeDirector(flock(), decide=boom)
r = d3.tick(5.0, 0.0, 0.1, 0.2, 2.0)
check("jev throws: no gaze, no crash", r["gaze_on"] is False)
check("failsafe director label", r["director"] == "FALLBACK")

# 6. Jev says GRAZE -> no gaze (Jev decides the middle)
d4 = SheepGazeDirector(flock(), decide=GRAZE)
r = d4.tick(5.0, 0.0, 0.1, 0.2, 2.0)
check("jev graze: no gaze", r["gaze_on"] is False)

# 7. no snap: per-sheep onset + slew cap
d5 = SheepGazeDirector(flock(), decide=TURN)
r = d5.tick(0.0, 5.0, 0.0, 0.2, 0.1)  # tiny dt right after onset
yaws = [a["yaw_deg"] for a in r["acts"]]
check("slew capped (no snap)", all(abs(y) <= 9.0 + 1e-9 for y in yaws))
d6 = SheepGazeDirector(flock(), decide=TURN)
d6.tick(0.0, 5.0, 0.0, 0.2, 2.0)
check("onset delays differ per sheep",
      len({s.onset_delay_s for s in d6.sheep}) > 1)
check("yaw variance differs per sheep",
      len({s.yaw_var_deg for s in d6.sheep}) > 1)

# 8. HUD format
hud = r["hud"]
for needle in ("JEV SHEEP CONDUCTOR", "Behavior:", "Alt:", "Wind:",
               "PlayerDist:", "PlayerStill:", "Director:", "Resolution:"):
    check(f"hud has {needle}", needle in hud)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
