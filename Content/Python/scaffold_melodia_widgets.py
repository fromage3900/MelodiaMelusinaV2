"""
Scaffold Melodia UI Widgets from Figma specifications
Auto-generates UMG widget blueprints with pre-configured structure
"""

import json
import os
from pathlib import Path

# Paths
TOKENS_JSON = r"c:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melodia_design_tokens_ue.json"
OUTPUT_DIR = r"c:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\UI"
SPEC_FILE = r"c:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_CUTE_UI_ELEMENTS_SPEC_2026-07-31.md"

def load_tokens():
    """Load design tokens from JSON"""
    with open(TOKENS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_widget_scaffold(widget_name, widget_type, structure, properties):
    """Generate a widget scaffold JSON structure"""
    scaffold = {
        "widget_name": widget_name,
        "widget_type": widget_type,  # "UserWidget", "Border", "Canvas", etc.
        "structure": structure,
        "properties": properties,
        "design_tokens": {}
    }
    return scaffold

def generate_menu_button_scaffold():
    """Generate WBP_MenuButton scaffold"""
    structure = {
        "root": {
            "type": "SizeBox",
            "children": [
                {
                    "name": "Background",
                    "type": "Border",
                    "properties": {
                        "BrushColor": "{GameColors.ParchmentField}",
                        "BorderThickness": 1.0,
                        "BorderColor": "{GameColors.GoldBorder}"
                    },
                    "children": [
                        {"name": "CornerStar_TL", "type": "Image", "properties": {"Opacity": 0.6}},
                        {"name": "CornerStar_TR", "type": "Image", "properties": {"Opacity": 0.6}},
                        {"name": "CornerStar_BL", "type": "Image", "properties": {"Opacity": 0.6}},
                        {"name": "CornerStar_BR", "type": "Image", "properties": {"Opacity": 0.6}}
                    ]
                },
                {
                    "name": "Content",
                    "type": "Overlay",
                    "children": [
                        {"name": "ButtonText", "type": "TextBlock"},
                        {"name": "ButtonIcon", "type": "Image", "optional": True}
                    ]
                },
                {
                    "name": "SparkleOverlay",
                    "type": "CanvasPanel",
                    "properties": {"Opacity": 0.0}
                }
            ]
        }
    }
    
    properties = {
        "ButtonText": {"type": "FText", "default": "Button"},
        "ButtonStyle": {"type": "TEnum", "values": ["Primary", "Secondary", "Tertiary"], "default": "Primary"},
        "ShowCorners": {"type": "bool", "default": True},
        "SparkleOnHover": {"type": "bool", "default": True},
        "IsDisabled": {"type": "bool", "default": False},
        "OnClicked": {"type": "FScriptDelegate", "description": "Delegate fired when button is clicked"}
    }
    
    # Gameplay integration notes
    gameplay_integration = {
        "purpose": "Reusable button for all menu panels (MainMenu, SaveLoad, Settings, etc.)",
        "events": {
            "OnClicked": "Bind to menu actions (NewGame, LoadGame, SaveGame, OpenSettings, etc.)"
        },
        "subsystem_bindings": {
            "MainMenu": "UMelodiaOpeningFlowSubsystem::ResetOpening() for New Game",
            "SaveLoad": "UMelodiaSaveGameSubsystem::SaveGame() / LoadGame()",
            "Settings": "UMelodiaGameUserSettings for persistence"
        },
        "sparkle_integration": {
            "trigger": "Call WBP_SparkleFX::PlaySparkle() on OnClicked",
            "density_tier": "Read from UMelodiaGameUserSettings motion tier"
        }
    }
    
    scaffold = generate_widget_scaffold("WBP_MenuButton", "UserWidget", structure, properties)
    scaffold["gameplay_integration"] = gameplay_integration
    return scaffold

def generate_parchment_panel_scaffold():
    """Generate WBP_ParchmentPanel scaffold"""
    structure = {
        "root": {
            "type": "SizeBox",
            "children": [
                {
                    "name": "ParchmentBackground",
                    "type": "Border",
                    "properties": {
                        "BrushColor": "{GameColors.ParchmentField}",
                        "CornerRadius": 8.0
                    },
                    "children": [
                        {"name": "GrainOverlay", "type": "Image", "properties": {"Opacity": 0.03, "BlendMode": "Multiply"}},
                        {"name": "ScrollEdge_Left", "type": "Image", "optional": True},
                        {"name": "ScrollEdge_Right", "type": "Image", "optional": True}
                    ]
                },
                {
                    "name": "ClefWatermark",
                    "type": "Image",
                    "properties": {"Opacity": 0.08, "Visibility": "HitTestInvisible"}
                },
                {
                    "name": "ContentSlot",
                    "type": "CanvasPanel"
                }
            ]
        }
    }
    
    properties = {
        "ParchmentTint": {"type": "FLinearColor", "default": "{GameColors.ParchmentField}"},
        "ShowClef": {"type": "bool", "default": True},
        "ShowScrollEdges": {"type": "bool", "default": True},
        "CornerRadius": {"type": "float", "default": 8.0}
    }
    
    # Gameplay integration notes
    gameplay_integration = {
        "purpose": "Base panel for all meta UI (SaveLoad, Settings, QuestJournal, NPCInfo, etc.)",
        "usage": "Helper atom - compose into larger panels, no direct gameplay bindings",
        "subsystem_usage": {
            "SaveLoad": "Background for WBP_SaveLoad, contains slot cards",
            "Settings": "Background for WBP_Settings, contains tabbed controls",
            "QuestJournal": "Background for WBP_QuestJournal, contains quest list",
            "NPCInfo": "Background for WBP_NPCInfo, contains NPC details"
        },
        "theming": {
            "parchment_tint": "Read from DA_MelodiaDesignTokens GameColors.ParchmentField",
            "clef_watermark": "Musical theme element, no gameplay function"
        }
    }
    
    scaffold = generate_widget_scaffold("WBP_ParchmentPanel", "UserWidget", structure, properties)
    scaffold["gameplay_integration"] = gameplay_integration
    return scaffold

def generate_keybind_badge_scaffold():
    """Generate WBP_KeybindBadge scaffold"""
    structure = {
        "root": {
            "type": "SizeBox",
            "properties": {"WidthOverride": 48.0, "HeightOverride": 48.0},
            "children": [
                {
                    "name": "KeycapBackground",
                    "type": "Border",
                    "properties": {
                        "CornerRadius": 4.0,
                        "BorderThickness": 1.0,
                        "BorderColor": "{GameColors.GoldBorder}"
                    },
                    "children": [
                        {"name": "KeyLetter", "type": "TextBlock", "properties": {"Font": "Bold", "Size": 24}},
                        {"name": "ActionIcon", "type": "Image", "properties": {"Size": 16, "Visibility": "HitTestInvisible"}},
                        {"name": "GlowOverlay", "type": "Border", "properties": {"Opacity": 0.0}}
                    ]
                }
            ]
        }
    }
    
    properties = {
        "KeyLetter": {"type": "FText", "default": "F"},
        "ActionType": {"type": "TEnum", "values": ["Interact", "Attack", "Skill", "Ultimate", "Menu", "Back"], "default": "Interact"},
        "IsActive": {"type": "bool", "default": False},
        "ShowIcon": {"type": "bool", "default": True}
    }
    
    # Gameplay integration notes
    gameplay_integration = {
        "purpose": "JRPG keybind visualizer (F=Interact, J=Attack, K=Skill, L=Ultimate, E=Menu, ESC=Back)",
        "input_context": "UMelodiaInputContextSubsystem for keybind mappings",
        "keybind_mapping": {
            "F": "Interact - UMelodiaNPCInteractionComponent::BeginInteraction",
            "J": "Attack - UMelodiaBattleSession::SubmitBasicCommand",
            "K": "Skill - UMelodiaBattleSession::SubmitSkillCommand",
            "L": "Ultimate - UMelodiaBattleSession::SubmitUltimateCommand",
            "E": "Menu - Open menu overlay",
            "ESC": "Back - Close current panel / cancel action"
        },
        "color_mapping": {
            "Interact": "KeybindColors.Interact (rose)",
            "Attack": "KeybindColors.Attack (amber)",
            "Skill": "KeybindColors.Skill (lavender)",
            "Ultimate": "KeybindColors.Ultimate (seafoam)",
            "Menu": "KeybindColors.Menu (parchment)",
            "Back": "KeybindColors.Back (ink)"
        },
        "events": {
            "OnKeyPressed": "Set IsActive=true, show glow",
            "OnKeyReleased": "Set IsActive=false, hide glow",
            "OnCooldown": "Desaturate color during cooldown"
        }
    }
    
    scaffold = generate_widget_scaffold("WBP_KeybindBadge", "UserWidget", structure, properties)
    scaffold["gameplay_integration"] = gameplay_integration
    return scaffold

def generate_sparkle_fx_scaffold():
    """Generate WBP_SparkleFX scaffold"""
    structure = {
        "root": {
            "type": "CanvasPanel",
            "children": [
                {
                    "name": "ParticleSystem",
                    "type": "NiagaraWidget",
                    "properties": {
                        "NiagaraSystem": "/Game/Melodia/VFX/NS_SparkleBurst"
                    }
                },
                {
                    "name": "DensityController",
                    "type": "FloatParameter",
                    "properties": {"DefaultValue": 1.0}
                }
            ]
        }
    }
    
    properties = {
        "SparkleType": {"type": "TEnum", "values": ["Burst", "Drift", "Orbit"], "default": "Burst"},
        "DensityTier": {"type": "TEnum", "values": ["Full", "Soft", "Chrome", "Off"], "default": "Full"},
        "ColorOverride": {"type": "FLinearColor", "default": "White"},
        "AutoPlay": {"type": "bool", "default": False},
        "Loop": {"type": "bool", "default": False}
    }
    
    # Gameplay integration notes
    gameplay_integration = {
        "purpose": "Shared sparkle effects for UI feedback (success, hover, burst)",
        "cpp_hook": "UMelodiaRhythmHUDWidget::TriggerSparkleBurst() / DoPulse()",
        "events": {
            "PlaySparkle": "Blueprint-callable function to trigger sparkle animation",
            "SetDensityTier": "Update density based on UMelodiaGameUserSettings motion tier"
        },
        "subsystem_bindings": {
            "Battle": "UMelodiaRhythmHUDWidget::TriggerSparkleBurst() on Perfect/Break/ULT",
            "Menu": "Call PlaySparkle() on button hover/click",
            "Settings": "Read motion tier from UMelodiaGameUserSettings (full/soft/chrome/off)"
        },
        "density_mapping": {
            "Full": "1.0 density, motion enabled",
            "Soft": "0.5 density, motion enabled",
            "Chrome": "0.25 density, motion enabled",
            "Off": "0.0 density, motion disabled"
        }
    }
    
    scaffold = generate_widget_scaffold("WBP_SparkleFX", "UserWidget", structure, properties)
    scaffold["gameplay_integration"] = gameplay_integration
    return scaffold

def generate_filigree_border_scaffold():
    """Generate WBP_FiligreeBorder scaffold"""
    structure = {
        "root": {
            "type": "SizeBox",
            "children": [
                {"name": "Corner_TL", "type": "Image", "optional": True},
                {"name": "Corner_TR", "type": "Image", "optional": True},
                {"name": "Corner_BL", "type": "Image", "optional": True},
                {"name": "Corner_BR", "type": "Image", "optional": True},
                {"name": "TopEdge", "type": "Image", "optional": True},
                {"name": "BottomEdge", "type": "Image", "optional": True},
                {"name": "LeftEdge", "type": "Image", "optional": True},
                {"name": "RightEdge", "type": "Image", "optional": True},
                {"name": "Crest", "type": "Image", "optional": True}
            ]
        }
    }
    
    properties = {
        "BorderThickness": {"type": "float", "default": 16.0},
        "ShowCorners": {"type": "bool", "default": True},
        "ShowCrest": {"type": "bool", "default": False},
        "ColorOverride": {"type": "FLinearColor", "default": "{GameColors.GoldBorder}"}
    }
    
    # Gameplay integration notes
    gameplay_integration = {
        "purpose": "Decorative Baroque borders for panel polish",
        "usage": "Helper atom - compose into panels for visual polish, no direct gameplay bindings",
        "theming": {
            "color": "Read from DA_MelodiaDesignTokens GameColors.GoldBorder",
            "crest": "Optional header accent for important panels (MainMenu, Title)"
        },
        "usage_context": {
            "MainMenu": "ShowCrest=true for main menu header",
            "SaveLoad": "ShowCorners=true for slot cards",
            "Settings": "ShowCorners=true for section dividers"
        }
    }
    
    scaffold = generate_widget_scaffold("WBP_FiligreeBorder", "UserWidget", structure, properties)
    scaffold["gameplay_integration"] = gameplay_integration
    return scaffold

def save_scaffold(scaffold, output_path):
    """Save scaffold to JSON file"""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scaffold, f, indent=2)
    
    print(f"✓ Generated scaffold: {output_path}")

def main():
    print("=== Melodia UI Widget Scaffolding ===\n")
    
    # Generate all widget scaffolds
    scaffolds = [
        ("WBP_MenuButton", generate_menu_button_scaffold()),
        ("WBP_ParchmentPanel", generate_parchment_panel_scaffold()),
        ("WBP_KeybindBadge", generate_keybind_badge_scaffold()),
        ("WBP_SparkleFX", generate_sparkle_fx_scaffold()),
        ("WBP_FiligreeBorder", generate_filigree_border_scaffold())
    ]
    
    output_base = Path(OUTPUT_DIR) / "WidgetScaffolds"
    
    for widget_name, scaffold in scaffolds:
        output_path = output_base / f"{widget_name}_scaffold.json"
        save_scaffold(scaffold, str(output_path))
    
    print(f"\n✓ Generated {len(scaffolds)} widget scaffolds")
    print(f"  Output directory: {output_base}")
    print("\nNext steps:")
    print("  1. Review scaffold JSON files")
    print("  2. Use UE5 Python API to create actual widget blueprints")
    print("  3. Or manually author widgets based on scaffold structure")

if __name__ == "__main__":
    main()
