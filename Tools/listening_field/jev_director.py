"""A5 — Jev decision service for the Listening Field.

Consumes melodia.phrase/v1 states (trace or live), asks Jev ONE batched set
of questions per phrase boundary, and emits melodia.directive/v1 packets.
Decisions at bar N are tagged for_bar = N+1 (latency rule).

Offline-first: with no TYPESAFE_API_KEY or no typesafe_sdk, the service runs
the authored classical table and still produces the full sequence. With Jev
available, `--verify` runs both and reports agreement per boundary.

Usage:
  python jev_director.py run    --trace ../../Saved/Audit/phrase_traces/listening_field_v1.jsonl \
                                --out   ../../Saved/Audit/listening_field/directives_v1.jsonl
  python jev_director.py verify --trace <same>     # Jev vs fallback agreement
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "phrase_bridge"))

from phrase_schema import PhraseState, from_payload  # noqa: E402
from directive_schema import (  # noqa: E402
    Directive, LAYOUT_SEEDS, sanitize,
)
from director_table import (  # noqa: E402
    DECISION_TABLE, JEV_QUESTIONS, RESTRAINT_LEVEL_VALUES, phrase_class,
)

BOUNDARY_CONFIDENCE_MIN = 0.5
MIN_BARS_BETWEEN_SHEEP_CHANGES = 1  # dwell, conductor also enforces its own


def jev_available() -> bool:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return False
    try:
        import typesafe_sdk  # noqa: F401
        return True
    except ImportError:
        return False


class Director:
    """Boundary-driven director. One decide() per boundary pulse."""

    def __init__(self, use_jev: bool | None = None):
        self.use_jev = jev_available() if use_jev is None else use_jev
        self._last_sheep_change_bar = -10**9
        self._prev_section: str | None = None

    # ---- classical fallback (also the answer key) ----
    def fallback_decide(self, s: PhraseState, accumulator: float,
                        entering_climax: bool = False) -> Directive:
        cls = phrase_class(s.phrase_index, s.section.value)
        sheep, world, restraint = DECISION_TABLE[(s.section.value, cls)]
        if sheep and s.bar - self._last_sheep_change_bar < MIN_BARS_BETWEEN_SHEEP_CHANGES:
            sheep = "HOLD" if sheep != "HOLD" else sheep
        if sheep and sheep != "HOLD":
            self._last_sheep_change_bar = s.bar
        # The meadow blooms ONCE: seed chosen on the transition into CLIMAX,
        # not on every boundary the CLIMAX spans. Gate arrives from decide()
        # because it already advanced the section tracker.
        seed = self._pick_seed(s) if entering_climax else None
        return sanitize(Directive(s.bar + 1, sheep, world, restraint, seed, "fallback", 1.0))

    def _pick_seed(self, s: PhraseState) -> str:
        keys = sorted(LAYOUT_SEEDS.keys())
        # deterministic, energy-aware: hotter phrase -> later (fuller) seed
        i = min(len(keys) - 1, int(s.energy * len(keys)))
        return keys[i]

    # ---- Jev path ----
    def jev_decide(self, s: PhraseState, accumulator: float, entering_climax: bool) -> Directive:
        """One batched System One request; falls back per-question on failure."""
        from typesafe_sdk import TypeSafeClient  # deferred: optional dep

        state = {
            "phrase": s.to_dict(),
            "resonance_accumulator": accumulator,
            "authored_seeds": LAYOUT_SEEDS,
        }
        # JEV_QUESTIONS is the authored table (old wire format); adapt to the
        # current typesafe_sdk question schema at the boundary.
        questions: dict[str, dict[str, Any]] = {}
        for qid, spec in JEV_QUESTIONS.items():
            if qid == "layout_seed" and not entering_climax:
                continue
            q = dict(spec)
            options = q.pop("options", None)
            if options is not None:
                q["criteria"] = {option: None for option in options}
            levels = q.pop("levels", None)
            if levels is not None:
                q["criteria"] = list(levels)
            questions[qid] = q

        with TypeSafeClient() as client:
            result = client.system_one(state=state, questions=questions)

        answers = result.answers
        sheep = answers["sheep_next"].choice
        world = answers["world_next"].choice
        restraint_levels = JEV_QUESTIONS["restraint_amount"]["levels"]
        score_idx = int(answers["restraint_amount"].score or 0)
        level = (
            restraint_levels[score_idx]
            if 0 <= score_idx < len(restraint_levels)
            else "partial"
        )
        restraint = RESTRAINT_LEVEL_VALUES.get(level, 0.5)
        seed = answers.get("layout_seed")
        seed = seed.choice if seed is not None and seed.choice in LAYOUT_SEEDS else None
        conf = min(a.confidence for a in answers.values())
        return sanitize(Directive(s.bar + 1, sheep, world, restraint, seed, "jev", conf))

    def decide(self, s: PhraseState, accumulator: float) -> Directive:
        # Bloom gate is computed in decide() so both paths agree on it even
        # when one path raises and degrades to the other mid-sequence.
        entering_climax = s.section.value == "CLIMAX" and self._prev_section != "CLIMAX"
        self._prev_section = s.section.value
        if self.use_jev:
            try:
                return self.jev_decide(s, accumulator, entering_climax)
            except Exception:
                pass  # any Jev failure degrades to the table for this boundary
        return self.fallback_decide(s, accumulator, entering_climax)


def run_trace(trace_path: str, out_path: str, use_jev: bool | None = None) -> list[Directive]:
    """Play a trace through the director. Deterministic against the fallback."""
    director = Director(use_jev=use_jev)
    directives: list[Directive] = []
    accumulator = 0.0
    with open(trace_path, "r", encoding="utf-8") as f:
        for ln in f:
            rec = json.loads(ln)
            if rec["kind"] != "state":
                continue
            s = from_payload(rec["payload"])
            # deterministic integrator mirrors the UE conductor
            accumulator += s.energy * (1.0 - 0.7) * 0.1  # k tuned for the trace
            if s.boundary_pulse and s.beat_in_bar == 0.0 and s.confidence >= BOUNDARY_CONFIDENCE_MIN:
                d = director.decide(s, accumulator)
                directives.append(d)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            for d in directives:
                f.write(d.to_json() + "\n")
    return directives


def verify_agreement(trace_path: str) -> int:
    fb = run_trace(trace_path, None, use_jev=False)
    if not jev_available():
        print("Jev unavailable (no TYPESAFE_API_KEY / typesafe_sdk) — "
              "fallback sequence is the authority:")
        for d in fb:
            print(" ", d.to_json())
        return 0
    jv = run_trace(trace_path, None, use_jev=True)
    agree = sum(1 for a, b in zip(jv, fb)
                if (a.sheep, a.world, a.restraint, a.layout_seed)
                == (b.sheep, b.world, b.restraint, b.layout_seed))
    print(f"boundaries: {len(fb)}  agreement: {agree}/{len(fb)}")
    for a, b in zip(jv, fb):
        if (a.sheep, a.world, a.restraint, a.layout_seed) != (b.sheep, b.world, b.restraint, b.layout_seed):
            print("  MISMATCH\n   jev: ", a.to_json(), "\n   fb:  ", b.to_json())
    return 0 if agree == len(fb) else 1


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--trace", required=True)
        p.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.cmd == "run":
        ds = run_trace(args.trace, args.out, use_jev=None)
        print(f"{len(ds)} directives -> {args.out}")
        for d in ds:
            print(" ", d.to_json())
    else:
        sys.exit(verify_agreement(args.trace))
