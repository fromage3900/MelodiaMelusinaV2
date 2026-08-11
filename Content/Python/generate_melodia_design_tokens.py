"""
Generate Melodia Design Tokens Data Asset from Figma tokens.json
Reads melodia-design-system/tokens.json and outputs UE-compatible data structure
"""

import json
import os
from pathlib import Path

# Paths
TOKENS_PATH = r"c:\EnvironmentPortfolio\BS_GodFile\melodia-design-system\tokens.json"
OUTPUT_PATH = r"c:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melodia_design_tokens_ue.json"

def resolve_reference(value, tokens):
    """Resolve token references like {primitives.ivory.100}"""
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        # Extract path: primitives.ivory.100
        ref_path = value[1:-1]
        parts = ref_path.split(".")
        
        # Navigate through tokens dict
        current = tokens
        for part in parts:
            if part in current:
                current = current[part]
            else:
                return value  # Return original if not found
        
        # Extract the actual value
        if isinstance(current, dict) and "value" in current:
            return resolve_reference(current["value"], tokens)
        return current
    return value

def flatten_tokens(tokens, prefix=""):
    """Flatten nested token structure to dot-notation keys"""
    flat = {}
    
    for key, value in tokens.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Check if this is a token with value/type
            if "value" in value and "type" in value:
                flat[full_key] = {
                    "value": resolve_reference(value["value"], tokens),
                    "type": value["type"],
                    "description": value.get("description", "")
                }
            else:
                # Recurse into nested structure
                flat.update(flatten_tokens(value, full_key))
    
    return flat

def generate_ue_structure(flat_tokens):
    """Convert flattened tokens to UE-friendly structure"""
    ue_tokens = {
        "Colors": {},
        "Spacing": {},
        "Radius": {},
        "Typography": {},
        "Effects": {}
    }
    
    for key, token in flat_tokens.items():
        token_type = token["type"]
        value = token["value"]
        description = token["description"]
        
        if token_type == "color":
            ue_tokens["Colors"][key] = {
                "Hex": value,
                "Description": description
            }
        elif token_type == "spacing":
            ue_tokens["Spacing"][key] = {
                "Value": int(value),
                "Description": description
            }
        elif token_type == "borderRadius":
            ue_tokens["Radius"][key] = {
                "Value": int(value),
                "Description": description
            }
        elif token_type == "typography":
            ue_tokens["Typography"][key] = {
                "FontFamily": value.get("fontFamily", ""),
                "FontSize": int(value.get("fontSize", 16)),
                "FontWeight": value.get("fontWeight", "Regular"),
                "LineHeight": int(value.get("lineHeight", 24)),
                "LetterSpacing": value.get("letterSpacing", "0"),
                "TextCase": value.get("textCase", "none"),
                "Description": description
            }
        elif token_type in ["boxShadow", "dropShadow"]:
            ue_tokens["Effects"][key] = {
                "X": float(value.get("x", 0)),
                "Y": float(value.get("y", 0)),
                "Blur": float(value.get("blur", 0)),
                "Spread": float(value.get("spread", 0)),
                "Color": value.get("color", "rgba(0,0,0,0)"),
                "Type": token_type,
                "Description": description
            }
    
    return ue_tokens

def main():
    # Load tokens
    with open(TOKENS_PATH, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    # Flatten tokens
    flat_tokens = flatten_tokens(tokens)
    
    # Generate UE structure
    ue_tokens = generate_ue_structure(flat_tokens)
    
    # Add game-specific color mappings (from Figma wiring plan)
    ue_tokens["GameColors"] = {
        "VoidPlate": "#0b0a13",
        "ParchmentField": "rgba(56,41,59,0.92)",
        "ParchmentFill_Start": "#F2E6CF",
        "ParchmentFill_End": "#E3D3AD",
        "GoldBorder": "rgba(235,184,87,0.8)",
        "GoldText": "#F2D69E",
        "IriCyan": "#78EBFF",
        "PlumButton": "rgba(77,46,61,0.95)",
        "Ink": "#291A21",
        "CardGold": "rgba(232,199,140,0.95)"
    }
    
    # Add JRPG keybind colors
    ue_tokens["KeybindColors"] = {
        "Interact": "#E8A9A1",  # Rose for F
        "Attack": "#D9A566",   # Amber for J
        "Skill": "#B6A6D9",    # Lavender for K
        "Ultimate": "#8FC9BD", # Seafoam for L
        "Menu": "#F2E6CF",     # Parchment for E
        "Back": "#3B2A22"      # Ink for ESC
    }
    
    # Add sparkle density tiers (from Figma wiring plan)
    ue_tokens["SparkleTiers"] = {
        "Full": {"Density": 1.0, "Motion": "enabled"},
        "Soft": {"Density": 0.5, "Motion": "enabled"},
        "Chrome": {"Density": 0.25, "Motion": "enabled"},
        "Off": {"Density": 0.0, "Motion": "disabled"}
    }
    
    # Save output
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(ue_tokens, f, indent=2)
    
    print(f"✓ Generated UE design tokens: {OUTPUT_PATH}")
    print(f"  - Colors: {len(ue_tokens['Colors'])}")
    print(f"  - Spacing: {len(ue_tokens['Spacing'])}")
    print(f"  - Radius: {len(ue_tokens['Radius'])}")
    print(f"  - Typography: {len(ue_tokens['Typography'])}")
    print(f"  - Effects: {len(ue_tokens['Effects'])}")
    print(f"  - Game Colors: {len(ue_tokens['GameColors'])}")
    print(f"  - Keybind Colors: {len(ue_tokens['KeybindColors'])}")
    print(f"  - Sparkle Tiers: {len(ue_tokens['SparkleTiers'])}")

if __name__ == "__main__":
    main()
