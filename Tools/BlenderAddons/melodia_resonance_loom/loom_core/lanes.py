# Resonance Loom - lane vocabulary + expressive-only language guards.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# The battle lanes are Q/W/O/P (BP_BattleUI::OnKeyDown). They live here ONCE.
# Any module that needs the lane set imports it from here -- duplicating the
# tuple elsewhere is the sibling-graph-drift defect class (one surface, two
# writers), just in Python instead of Blueprint.

from __future__ import annotations

# Rhythm input lanes, exactly as authored in BP_BattleUI::OnKeyDown.
LANES: tuple[str, ...] = ("Q", "W", "O", "P")

# The eight authored rhythm ids (MelodiaIntegrationConfig.h, StockSkillRhythmIds
# value space). The sidecar must name one of these or the UE seam silently
# no-ops (StartSession returns 0).
SKILL_IDS: frozenset[str] = frozenset({
    "cadence_strike",
    "resonant_arc",
    "lullaby_mend",
    "downbeat_break",
    "dissonant_silence",
    "tempo_shift",
    "crescendo_wave",
    "harmony_shield",
})

# Decision 016: rhythm is expressive, not evaluative. No miss penalty, ever.
# Authored Loom strings (UI, reports, sidecar flavor) are scanned for these
# words so the addon cannot regress the vocabulary the owner locked.
_BANNED_WORDS: tuple[str, ...] = ("miss", "penalty", "punish", "fail")

# Presentation tiers from Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md
# Loom bakes Tier A (rigid authored motion). Anything beyond Tier A is Phase 2.
CLOTH_TIER = "A"


def assert_expressive(text: str) -> None:
    """Raise ValueError when authored Loom text uses evaluative language.

    Word-boundary match so e.g. 'dismiss' (contains 'miss') does not fire.
    """
    lowered = text.lower()
    for word in _BANNED_WORDS:
        idx = lowered.find(word)
        while idx != -1:
            before_ok = idx == 0 or not lowered[idx - 1].isalnum()
            end = idx + len(word)
            after_ok = end >= len(lowered) or not lowered[end].isalnum()
            if before_ok and after_ok:
                raise ValueError(
                    f"Decision 016 violation: authored Loom text uses the "
                    f"evaluative word {word!r}. Rhythm is expressive, never "
                    f"evaluative -- rephrase as flourish/bonus."
                )
            idx = lowered.find(word, idx + 1)


def tempo_band(bpm: float) -> str:
    """Coarse tempo band for the sidecar. Bounds are authored defaults."""
    if bpm < 100.0:
        return "slow"
    if bpm <= 140.0:
        return "mid"
    return "fast"


# Deterministic pitch/energy/position -> lane strategies. All three are pure
# functions of the parsed grid; the artist picks one per garment. A strategy
# here never gates gameplay -- it only arranges presentation (Decision 016).
LANE_STRATEGIES: tuple[str, ...] = (
    "pitch_quartile",   # Q=lowest pitches ... P=highest
    "velocity_bands",   # Q=softest ... P=loudest
    "bar_position",     # beat position within the bar, early->late
)


def assign_lanes(grid, strategy: str = "pitch_quartile") -> list[int]:
    """Return a lane index (0..3) per note, in grid.notes order.

    `grid` is a loom_core.midi_grid.MidiGrid (duck-typed here so this module
    stays import-cycle-free).
    """
    if strategy not in LANE_STRATEGIES:
        raise ValueError(f"unknown lane strategy {strategy!r}; one of {LANE_STRATEGIES}")
    out: list[int] = []
    n_lanes = len(LANES)
    for note in grid.notes:
        if strategy == "pitch_quartile":
            out.append(min(3, max(0, (note.pitch - 21) * n_lanes // 88)))
        elif strategy == "velocity_bands":
            v = note.velocity
            out.append(3 if v >= 112 else 2 if v >= 96 else 1 if v >= 80 else 0)
        else:  # bar_position
            if grid.seconds_per_beat <= 0 or grid.beats_per_bar <= 0:
                out.append(0)
                continue
            pos = (note.start_sec / grid.seconds_per_beat) % grid.beats_per_bar
            out.append(min(3, int(pos * n_lanes / grid.beats_per_bar)))
    return out

