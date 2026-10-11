"""
Generate Melodia Design Tokens Data Asset from Figma tokens.json
Reads melodia-design-system/tokens.json and outputs UE-compatible data structure.

GameColors / KeybindColors are resolved from the same flatten path as Colors
(tokens.json primitives + semantics). Do not hardcode leftover Figma / Nikki hexes.
"""

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENS_PATH = REPO_ROOT / "melodia-design-system" / "tokens.json"
OUTPUT_PATH = REPO_ROOT / "Saved" / "Audit" / "melodia_design_tokens_ue.json"

# Role → SSOT flatten key (same keys as Colors). Optional alpha keeps existing
# plate/border translucency but RGB always comes from tokens.json.
GAME_COLOR_ROLES = {
    "VoidPlate": {"token": "primitives.plum.900"},
    "ParchmentField": {"token": "primitives.plum.700", "alpha": 0.92},
    "ParchmentFill_Start": {"token": "primitives.gold.100"},
    "ParchmentFill_End": {"token": "primitives.gold.300"},
    "GoldBorder": {"token": "primitives.gold.500", "alpha": 0.8},
    "GoldText": {"token": "primitives.gold.300"},
    "IriCyan": {"token": "primitives.astral.300"},
    "PlumButton": {"token": "primitives.plum.600", "alpha": 0.95},
    "Ink": {"token": "primitives.plum.800"},
    "CardGold": {"token": "primitives.gold.300", "alpha": 0.95},
}

KEYBIND_COLOR_ROLES = {
    "Interact": {"token": "primitives.sakura.500"},
    "Attack": {"token": "primitives.gold.500"},
    "Skill": {"token": "primitives.lavender.500"},
    "Ultimate": {"token": "primitives.iris.500"},
    "Menu": {"token": "primitives.gold.100"},
    "Back": {"token": "primitives.plum.800"},
}

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

def flatten_tokens(tokens, prefix="", root=None):
    """Flatten nested token structure to dot-notation keys.

    Always resolve `{primitives.*}` against the root document so semantic
    sets emit hex, not leftover reference strings.
    """
    if root is None:
        root = tokens
    flat = {}
    
    for key, value in tokens.items():
        if isinstance(key, str) and key.startswith("$"):
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Check if this is a token with value/type
            if "value" in value and "type" in value:
                flat[full_key] = {
                    "value": resolve_reference(value["value"], root),
                    "type": value["type"],
                    "description": value.get("description", "")
                }
            else:
                # Recurse into nested structure
                flat.update(flatten_tokens(value, full_key, root))
    
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


def require_color(flat_tokens, token_key):
    """Return a resolved SSOT color hex. Raises if the flatten path is missing."""
    token = flat_tokens.get(token_key)
    if not token or token.get("type") != "color":
        raise KeyError(f"SSOT color token missing from flatten path: {token_key}")
    value = token.get("value")
    if not isinstance(value, str) or not value:
        raise KeyError(f"SSOT color token has no resolved value: {token_key}")
    return value


def hex_to_rgb(hex_value):
    hex_string = hex_value.lstrip("#")
    if len(hex_string) != 6:
        raise ValueError(f"Expected 6-digit SSOT hex, got {hex_value!r}")
    return int(hex_string[0:2], 16), int(hex_string[2:4], 16), int(hex_string[4:6], 16)


def emit_role_color(flat_tokens, spec):
    """Resolve a role to an SSOT hex, optionally composing the role's existing alpha."""
    hex_value = require_color(flat_tokens, spec["token"])
    alpha = spec.get("alpha")
    if alpha is None:
        return hex_value
    r, g, b = hex_to_rgb(hex_value)
    return f"rgba({r},{g},{b},{alpha})"


def map_role_colors(flat_tokens, roles):
    return {role: emit_role_color(flat_tokens, spec) for role, spec in roles.items()}


def print_role_mappings(label, flat_tokens, roles, emitted):
    print(f"  {label}:")
    for role, spec in roles.items():
        token_key = spec["token"]
        hex_value = require_color(flat_tokens, token_key)
        extra = f"  alpha={spec['alpha']}" if "alpha" in spec else ""
        print(f"    {role}: {emitted[role]}  <- {token_key} {hex_value}{extra}")


def main():
    # Load tokens
    with open(TOKENS_PATH, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    
    # Flatten tokens
    flat_tokens = flatten_tokens(tokens)
    
    # Generate UE structure
    ue_tokens = generate_ue_structure(flat_tokens)
    
    # Game / keybind roles resolve from SSOT flatten keys (same path as Colors).
    # The old "Figma wiring plan" literals (Nikki gold/cyan/seafoam) are gone.
    ue_tokens["GameColors"] = map_role_colors(flat_tokens, GAME_COLOR_ROLES)
    ue_tokens["KeybindColors"] = map_role_colors(flat_tokens, KEYBIND_COLOR_ROLES)
    
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
    print_role_mappings("GameColors", flat_tokens, GAME_COLOR_ROLES, ue_tokens["GameColors"])
    print_role_mappings("KeybindColors", flat_tokens, KEYBIND_COLOR_ROLES, ue_tokens["KeybindColors"])

if __name__ == "__main__":
    main()
