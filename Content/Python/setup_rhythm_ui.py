"""Setup Melodia Rhythm Battle UI Widgets.

Creates Persona 5-style UI themes with beat-synced animations.
- WBP_RhythmHUD (note highway, judgment popups)
- WBP_BattleHUD (turn order bar, SP pips, crescendo meter)
- WBP_DamageText (pastel bubble floats)

RUN IN UNREAL EDITOR PYTHON CONSOLE:
import setup_rhythm_ui; print(setup_rhythm_ui.build_rhythm_ui_setup())
"""
from __future__ import annotations

import json
import unreal


# UI Asset Paths
WBP_RHYTHM_HUD = "/Game/UI/Rhythm/WBP_RhythmHUD"
WBP_BATTLE_HUD = "/Game/UI/Battle/WBP_BattleHUD"
WBP_DAMAGE_TEXT = "/Game/UI/Battle/WBP_DamageText"


def get_palette() -> dict:
    """Melusina/P5-inspired color palette."""
    return {
        "deep_ink_navy": "#0A0A14",
        "melusina_aqua": "#7DD3C0",
        "gilded_accent": "#D4AF37",
        "pastel_lavender": "#C8B6DB",
        "pastel_seafoam": "#7DD3C0",
        "pastel_cream": "#F5F5DC"
    }


def create_rhythm_hud_spec() -> dict:
    """WBP_RhythmHUD specification for manual BP creation."""
    return {
        "widget_name": "WBP_RhythmHUD",
        "location": "/Game/UI/Rhythm/",
        "components": [
            {
                "name": "NoteHighway",
                "type": "CanvasPanel",
                "description": "Angled note highway with 8 note gems in row"
            },
            {
                "name": "JudgmentPopup",
                "type": "TextBlock",
                "description": "Center display: Perfect ✨, Good 🎵, Miss 💧",
                "font": "Orbitron 24pt",
                "colors": {
                    "Perfect": "#66FF99",  # Mint green
                    "Great": "#33CCFF",    # Cyan
                    "Good": "#FFCC33",    # Gold
                    "Miss": "#FF4D70"     # Rose
                }
            },
            {
                "name": "CrescendoMeter",
                "type": "ProgressBar",
                "description": "Bottom fill bar, 0→1 per Perfect (5 pts)"
            },
            {
                "name": "BeatPulseRing",
                "type": "Image",
                "description": "Scales on MPC BeatPulse"
            }
        ],
        "bindings": {
            "OnBeat": "PulseBeat animation (scale 1.0→1.2→1.0 over 0.2s)",
            "OnJudgment": "ShowJudgmentPopup with fade out 0.3s",
            "OnCrescendoGain": "FillCrescendoMeter"
        },
        "animations": [
            "BeatPulse: scale on MPC_MusicClock.BeatPulse",
            "JudgmentFade: timeline-based fade for popups",
            "NoteGlow: material parameter pulse on beat"
        ]
    }


def create_battle_hud_spec() -> dict:
    """WBP_BattleHUD specification."""
    return {
        "widget_name": "WBP_BattleHUD",
        "location": "/Game/UI/Battle/",
        "components": [
            {
                "name": "TurnOrderBar",
                "type": "VerticalBox",
                "description": "P5-style vertical portrait strip with beat-pulsed NOW slot"
            },
            {
                "name": "SP_Pips",
                "type": "HorizontalBox",
                "description": "5 pips showing skill point pool"
            },
            {
                "name": "UltimateRing",
                "type": "Image",
                "description": "Circular meter for ultimate energy"
            },
            {
                "name": "CommandMenu",
                "type": "StackPanel",
                "description": "Skill selection (Basic, Skills, Ultimate)"
            }
        ],
        "diagonal_entries": "12-18° angle entry animations",
        "beat_sync": "All animations driven by MPC_MusicClock.BeatPulse"
    }


def create_damage_text_spec() -> dict:
    """WBP_DamageText bubble float specification."""
    return {
        "widget_name": "WBP_DamageText",
        "location": "/Game/UI/Battle/",
        "properties": {
            "text_color": "#0066CC",
            "font": "Orbitron 14pt",
            "initial_scale": 0.5,
            "final_scale": 1.2,
            "float_height": 100,
            "fade_start_time": 1.0,
            "total_lifetime": 1.5
        },
        "animations": [
            "FloatUp: move Y+ over 1.5s",
            "ExpandScale: scale 0.5→1.2",
            "FadeOut: alpha 1→0 in last 0.5s"
        ]
    }


def assess_existing_ui_assets() -> dict:
    """Check what UI assets already exist."""
    report = {"existing_widgets": [], "existing_animations": []}
    
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    
    # Check UI folder
