"""Figma Game UI design tokens — Melodia battle HUD color system.

Mirrors page 12 "Game UI" from the Melodia Figma design file.
"""
from __future__ import annotations


class GameColors:
    VOID = (0.051, 0.071, 0.141, 1.0)
    ASTRAL = (0.102, 0.122, 0.227, 1.0)
    PLUM = (0.165, 0.188, 0.333, 1.0)
    SURFACE = (0.071, 0.094, 0.165, 0.92)
    SURFACE_LIGHT = (0.102, 0.122, 0.227, 0.85)

    GOLD = (1.0, 0.902, 0.4, 1.0)
    CYAN = (0.4, 0.851, 1.0, 1.0)
    PEARL = (0.941, 0.863, 0.941, 1.0)
    MAGENTA = (1.0, 0.431, 0.698, 1.0)

    IRIS = (0.608, 0.561, 0.769, 1.0)

    TEXT_PRIMARY = (0.925, 0.918, 0.957, 1.0)
    TEXT_SECONDARY = (0.663, 0.655, 0.753, 1.0)
    TEXT_MUTED = (0.431, 0.376, 0.502, 1.0)

    BORDER = (1.0, 1.0, 1.0, 0.12)
    BORDER_GOLD = (0.788, 0.659, 0.416, 0.3)

    HP_FILL = (0.4, 0.851, 1.0, 1.0)
    SP_FILL = (1.0, 0.902, 0.4, 1.0)
    ULT_FILL = (1.0, 0.431, 0.698, 1.0)

    TOUGHNESS_FILL = (0.4, 0.851, 1.0, 1.0)
    HP_BG = (0.102, 0.122, 0.227, 0.6)
    TRACK_BG = (1.0, 1.0, 1.0, 0.08)

    JUDGE_PERFECT = (1.0, 0.902, 0.4, 1.0)
    JUDGE_GREAT = (0.4, 0.851, 1.0, 1.0)
    JUDGE_GOOD = (0.941, 0.863, 0.941, 1.0)
    JUDGE_MISS = (1.0, 0.431, 0.698, 1.0)

    LANE_A = GOLD
    LANE_B = CYAN
    LANE_C = MAGENTA
    LANE_D = PEARL

    LANE_KEYS = ("D", "F", "J", "K")
    LANE_COLORS = (LANE_A, LANE_B, LANE_C, LANE_D)

    HITLINE_GLOW = (1.0, 0.902, 0.4, 0.5)

    GRADE_WINDOWS = {"perfect": 90, "great": 120, "good": 160}

    SECTION_TEXT = "Grandmaster"


GRADE_LABELS = {
    "perfect": "PERFECT",
    "great": "GREAT",
    "good": "GOOD",
    "miss": "MISS",
}
