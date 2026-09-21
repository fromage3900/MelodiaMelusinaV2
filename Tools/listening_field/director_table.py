"""Authored decision table — the classical fallback and the Jev criteria spec.

This table IS the directorial intent for the 45 s sequence
(LISTENING_FIELD_SPEC_2026-09-20.md §5). The fallback executes it
deterministically; Jev is asked the same questions in natural language over
the same state. Both answers must agree on the trace (A5 finish line).

If you retune this table, the trace capture changes — retune deliberately.
"""

# (section, phrase_class) -> (sheep, world, restraint)
# phrase_class disambiguates the two VOICE phrases (P1 arrival vs P2 sustain).
DECISION_TABLE: dict[tuple[str, str], tuple[str, str, float]] = {
    ("SPARSE",  "opening"):   ("HOLD",            "RESTRAIN", 1.0),
    ("VOICE",   "arrival"):   ("TURN_TO_PLAYER",  "RESTRAIN", 0.7),
    ("VOICE",   "sustain"):   ("HOLD",            "RESTRAIN", 0.7),
    ("BUILD",   "layering"):  ("RESONANCE_PULSE", "RELEASE",  0.2),
    ("CLIMAX",  "major"):     ("SPIRAL_FORMATION","RELEASE",  0.0),
    ("RELEASE", "tail"):      ("CRESCENDO_BURST", "RELEASE",  0.3),
    # rest / low confidence: no Jev question at all — conductor owns SETTLE.
}

# Natural-language question Jev is asked per boundary (criteria carry the
# complete meaning; the table above is the expected answer key).
JEV_QUESTIONS = {
    "sheep_next": {
        "type": "choice",
        "options": ["HOLD", "TURN_TO_PLAYER", "SPIRAL_FORMATION",
                    "RESONANCE_PULSE", "CRESCENDO_BURST"],
        "instructions": (
            "You are the director of a living musical meadow. Given the current "
            "musical phrase, the world's accumulated resonance, and the sheep "
            "flock's current state, choose the flock's next authored behavior. "
            "Choose HOLD when the music is sparse or sustained and the world "
            "should hold its breath. Choose TURN_TO_PLAYER when a voice first "
            "enters and the flock should notice the player. Choose "
            "RESONANCE_PULSE when the music builds and the flock should send "
            "energy outward. Choose SPIRAL_FORMATION only at the major phrase "
            "when the world releases. Choose CRESCENDO_BURST as the climax "
            "resolves. Never choose anything else."
        ),
    },
    "world_next": {
        "type": "choice",
        "options": ["RESTRAIN", "RELEASE"],
        "instructions": (
            "Choose whether the world response should be held back (RESTRAIN) "
            "or allowed to bloom (RELEASE). Restrain while the music is sparse, "
            "sustained, or ambiguous; release while it builds, peaks, or resolves."
        ),
    },
    "restraint_amount": {
        "type": "score",
        "levels": ["full_hold", "held_breath", "partial", "open", "full_release"],
        "instructions": (
            "How open is the world right now? full_hold: nothing moves. "
            "held_breath: subtle drift only, response visibly capped. partial: "
            "some wind and color. open: wind and flowers move freely. "
            "full_release: everything blooms at once."
        ),
    },
    "layout_seed": {
        "type": "choice",
        "options": sorted(["seed_spiral_north", "seed_ring_pond", "seed_arc_walk"]),
        "instructions": (
            "At the major phrase, choose which authored formation/flower-band "
            "seed the meadow blooms into. seed_spiral_north: tight inward "
            "spiral behind the flock. seed_ring_pond: open ring at the "
            "waterline. seed_arc_walk: wide arc along the walk in full "
            "rainbow. Choose only at the CLIMAX; otherwise answer 'none' "
            "by choosing the seed that best fits the phrase energy."
        ),
    },
}

RESTRAINT_LEVEL_VALUES = {
    "full_hold": 1.0, "held_breath": 0.7, "partial": 0.5, "open": 0.2, "full_release": 0.0,
}


def phrase_class(phrase_index: int, section: str) -> str:
    """Map the trace's phrase index onto the table's phrase classes."""
    return {
        0: "opening", 1: "arrival", 2: "sustain", 3: "layering",
        4: "major", 5: "tail",
    }.get(phrase_index, "opening")
