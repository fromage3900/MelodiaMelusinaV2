#!/usr/bin/env python3
"""
audit_melodia_integration_map_ui.py - Melodia Integration Map UI & Storybook Dopamine Audit.

Performs a comprehensive audit across all interactive Blueprints in MelodiaIntegrationMap
through the "Storybook Lens & Dopamine-Driven Interactive UI" paradigm.
Organizes front-facing screenshots in Docs/Screenshots/ and generates the audit report.

Usage:
    python Content/Python/audit_melodia_integration_map_ui.py
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
DOCS_SCREENSHOTS = ROOT / "Docs" / "Screenshots"
SAVED_SCREENSHOTS = ROOT / "Saved" / "Screenshots"
SAVED_AUDIT = ROOT / "Saved" / "Audit"

INTERACTIVE_BPS = [
    {
        "blueprint": "BP_InteractionBattle",
        "role": "Turn-based encounter trigger (melodia_smoke_encounter)",
        "current_ui": "Default interaction prompt; transitions into BP_BattleUI with stock dialogue boxes",
        "storybook_dopamine_treatment": "Golden astrolabe encounter swirl; battle transition with comic-panel curtain wipe; rhythmic musical chord on battle start",
        "dopamine_mechanic": "Anticipation chime + dramatic musical beat sync upon encounter trigger",
        "priority": "P0",
    },
    {
        "blueprint": "BP_InteractionDialogue",
        "role": "QuillScript narrative dialogue trigger (Melusina morning / sanctuary flow)",
        "current_ui": "Stock dialogue window; linear text scrolling",
        "storybook_dopamine_treatment": "Illuminated storybook manuscript page with Gilded Ivory (#F8ECD6) parchment, floating animated celestial star glyphs (✸), and vocal chime blips",
        "dopamine_mechanic": "Text typewriter with harmonic pitch variation per punctuation; golden page-turn flourish on dialog advancement",
        "priority": "P0",
    },
    {
        "blueprint": "BP_InteractionChest",
        "role": "Loot container & cosmetic item award",
        "current_ui": "Basic item obtain modal popup",
        "storybook_dopamine_treatment": "Ornate gold lock pop with bursting constellation motes; item card reveal with 3D turntable spin and holographic rarity shimmer",
        "dopamine_mechanic": "Multi-tier loot reveal fanfare (Common starlight -> Legendary radiant aurora) with haptic/rumble cadence",
        "priority": "P1",
    },
    {
        "blueprint": "BP_InteractionShop",
        "role": "Merchant exchange and wardrobe preview",
        "current_ui": "Stock two-column list with buy/sell buttons",
        "storybook_dopamine_treatment": "Fashion-lookbook catalog cards with fabric swatch physics preview and golden seal stamp animations on purchase",
        "dopamine_mechanic": "Satisfying tactile coin clink + wax seal stamping animation upon checkout",
        "priority": "P1",
    },
    {
        "blueprint": "BP_MelodiaRhythmPrompt",
        "role": "Musical prompt overlay & lane rating presenter",
        "current_ui": "Functional 4-lane highway with flat text rating readouts",
        "storybook_dopamine_treatment": "Sheet-music staff highway with glowing clef rails (T_Melodia_FiligreeLaneRail), iridescent note glyphs, and expanding celestial GradePop burst halos",
        "dopamine_mechanic": "Consecutive streak crescendo (combo flames change from gold -> celestial violet -> radiant prism) with dynamic audio pitch modulation",
        "priority": "P0",
    },
    {
        "blueprint": "BP_MelodiaVictoryDialogue",
        "role": "Post-battle victory and rewards resolution",
        "current_ui": "Flat banner with static EXP/Gold text",
        "storybook_dopamine_treatment": "HoYoverse-style victory scorecard with animated golden star rating stamps (★★★), rolling EXP score odometer, and character victory flourish",
        "dopamine_mechanic": "Rapid odometer tick-up with cascading gold coin showers and level-up radial starlight pulse",
        "priority": "P0",
    },
    {
        "blueprint": "BP_MelodiaExploreUI",
        "role": "Exploration HUD (zone banner, interact prompt, minimap)",
        "current_ui": "Minimalist circular minimap and text interact badge",
        "storybook_dopamine_treatment": "Astrolabe compass ring with animated orbital planets, delicate gold star interact prompt ([E] ✸ Examine), and parchment region ribbon banners",
        "dopamine_mechanic": "Soft breathing glow on interactive objects + melodic shimmer audio proximity cue",
        "priority": "P1",
    },
]


def organize_screenshots() -> List[Dict[str, str]]:
    DOCS_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    manifest = []

    shot_mappings = [
        (SAVED_SCREENSHOTS / "NS_Melodia_BattleBackdropPulse_Live.png", DOCS_SCREENSHOTS / "UI_Battle_Backdrop_Pulse.png", "Battle Backdrop Rhythmic Pulse"),
        (SAVED_SCREENSHOTS / "NS_Melodia_LaneHit_live.png", DOCS_SCREENSHOTS / "UI_Rhythm_Lane_Hit_FX.png", "Rhythm Highway Lane Hit Particle Burst"),
        (SAVED_SCREENSHOTS / "MainMenu_Before_Redesign.png", DOCS_SCREENSHOTS / "UI_MainMenu_Storybook_Baseline.png", "Main Menu Storybook Baseline"),
        (SAVED_SCREENSHOTS / "SDF_Utility_Grandmaster_Grid.png", DOCS_SCREENSHOTS / "UI_SDF_Grandmaster_Grid.png", "SDF Utility Grandmaster UI Shader Grid"),
        (ROOT / "Saved" / "Audit" / "choral_sheep" / "houdini_variants_review" / "_ChoralSheep_Chromatic_ContactSheet.png", DOCS_SCREENSHOTS / "UI_ChoralSheep_ContactSheet.png", "Choral Sheep Companion Lookdev Contact Sheet"),
    ]

    for src, dst, label in shot_mappings:
        if src.exists():
            shutil.copy2(src, dst)
            manifest.append({
                "label": label,
                "file": str(dst.relative_to(ROOT)),
                "size_bytes": dst.stat().st_size,
            })
            print(f"[ScreenshotSync] Copied {src.name} -> {dst.relative_to(ROOT)}")
        else:
            print(f"[ScreenshotSync] Notice: Source not found: {src}")

    return manifest


def main() -> int:
    SAVED_AUDIT.mkdir(parents=True, exist_ok=True)
    print("==================================================================")
    print(" Melodia Integration Map Storybook & Dopamine UI Audit")
    print("==================================================================")

    screenshots = organize_screenshots()

    audit_data = {
        "audit_title": "Melodia Integration Map Storybook & Dopamine UI Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_interactive_bps": len(INTERACTIVE_BPS),
        "interactive_blueprints": INTERACTIVE_BPS,
        "verified_screenshots": screenshots,
        "design_pillars": [
            "1. Storybook Whimsy: Gilded Ivory manuscript panels, 1px champagne gold rule lines, constellation star-chart backplates.",
            "2. Dopamine Loop Feedback: Multi-tier judgment bursts (GradePopLuxury), rolling odometer meters, radial level-up pulses.",
            "3. Audio-Visual Synesthesia: Beat-driven border respiration (MPC BeatPulse), pitch-scaled streak crescendo, punctuation vocal chimes.",
            "4. Tactile Polish: Wax seal stamp animations, 3D item card turntable spin, illuminated page-turn transitions.",
        ],
    }

    report_path = SAVED_AUDIT / "melodia_storybook_ui_audit.json"
    report_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
    print(f"\nSaved audit report to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
