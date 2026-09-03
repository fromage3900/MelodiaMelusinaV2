"""Update melodia_material_maker_addon.py presets to v2 parameter names."""
import re
from pathlib import Path

ADDON = Path(__file__).parent.parent / "melodia_material_maker_addon.py"
text = ADDON.read_text(encoding="utf-8")

# 1. Rename v1 params to v2
renames = {
    "DreamSaturation": "NikkiSaturation",
    "PastelLift": "NikkiPastelLift",
    "WitchBarrierEmissiveVeins": "MadokaVeinEmissive",
}
for old, new in renames.items():
    text = text.replace(old, new)

# 2. v2-only params (same defaults as JSON presets)
V2_ONLY = {
    "GlobalSeed": 0.5,
    "NikkiSparkleAmount": 0.35,
    "NikkiFabricDetail": 0.15,
    "NikkiFlowStrength": 0.25,
    "MadokaGlowAmount": 0.3,
    "MadokaEmissiveBrightness": 2.0,
    "MadokaCuteBias": 0.5,
    "IttoWearAmount": 0.4,
    "IttoBreakupAmount": 0.25,
    "IttoErosionStrength": 0.2,
    "CelestialScale": 1.0,
    "CelestialDrift": 0.1,
    "CelestialOrbitSpeed": 0.05,
    "CelestialOrbitPeriod": 60,
    "CelestialCMBAmount": 0.15,
    "CelestialEmissiveBoost": 1.5,
    "HeightScale": 0.25,
    "NormalStrength": 0.8,
    "NormalDetail": 0.3,
    "RoughnessBias": 0.55,
    "RoughnessContrast": 0.3,
    "MetallicAmount": 0.05,
    "AOStrength": 0.7,
    "SSSAmount": 0.12,
    "EmissiveIntensity": 1.0,
    "ExportResolution": 11,
}

# Style-specific overrides (key = preset name, value = dict of overrides)
STYLE_OVERRIDES = {
    "nikki": {
        "NikkiSparkleAmount": 0.5,
        "NikkiFabricDetail": 0.2,
        "NikkiFlowStrength": 0.3,
        "NikkiSaturation": 0.6,
    },
    "madoka": {
        "MadokaGlowAmount": 0.4,
        "MadokaEmissiveBrightness": 2.5,
        "MadokaCuteBias": 0.5,
        "MadokaVeinEmissive": 0.4,
    },
    "itto": {
        "IttoWearAmount": 0.4,
        "IttoBreakupAmount": 0.25,
        "IttoErosionStrength": 0.2,
    },
    "celestial": {
        "CelestialScale": 1.5,
        "CelestialNebulaScale": 0.5,
        "CelestialTwinkle": 0.6,
        "CelestialDrift": 0.15,
        "CelestialOrbitSpeed": 0.08,
        "CelestialCMBAmount": 0.2,
        "CelestialEmissiveBoost": 2.0,
    },
    "sakura": {
        "NikkiSparkleAmount": 0.4,
        "NikkiFabricDetail": 0.15,
        "NikkiFlowStrength": 0.25,
        "NikkiSaturation": 0.6,
        "NikkiPastelLift": 0.3,
    },
}

# Find each preset block and inject v2-only params
def make_v2_block(name):
    """Generate the params lines for a preset, inserting v2-only params with style overrides."""
    lines = []
    overrides = STYLE_OVERRIDES.get(name, {})
    for key, val in V2_ONLY.items():
        val = overrides.get(key, val)
        lines.append(f'                "{key}": {val},\n')
    # Remove trailing comma from last line
    if lines:
        lines[-1] = lines[-1].rstrip(",\n") + "\n"
    return lines

def escape_regex(s):
    return re.escape(s)

# For each preset, inject v2-only params before the closing `}` of its params dict
# Pattern: we know each preset has "CelestialTwinkle": X.X before the closing `}`
# We'll find the block by matching the pattern around CelestialTwinkle

preset_names = ["neutral", "nikki", "madoka", "itto", "celestial", "sakura"]

# Use a different strategy: find each preset by its description line, then locate the 
# closing "            }" that follows the params block

for name in preset_names:
    v2_lines = make_v2_block(name)
    if not v2_lines:
        continue
    
    # Find the preset block: match `"<name>": {` up to the closing `        },` or `        }`
    # We'll look for the params block end marker: a line with just `            }`
    # that follows the CelestialTwinkle line
    
    # Pattern: the params block of each preset ends with:
    #                 "CelestialTwinkle": X.X
    #             }
    # We'll replace the block between the last param and `            }`
    
    # Actually, let's find each preset by its name string and inject before the closing brace
    # Find the line with `"<name>": {` and then find the matching `            }`
    
    # Simpler approach: use regex to find each preset's params dict end
    # Match: `"CelestialTwinkle": <number>` followed by `            }`
    # Replace with: `"CelestialTwinkle": <number>\n<V2_LINES>\n            }`
    
    # Build a unique pattern for each preset based on its CelestialTwinkle value
    # But all presets except celestial have 0.0, so that won't be unique
    
    # Alternative: match the whole preset block name + description
    desc_match = {
        "neutral": r'("description": "Standard PBR without style effects")',
        "nikki": r'("description": "Rim lighting, sparkles, dream color grading")',
        "madoka": r'("description": "Witch barrier patterns, emissive veins")',
        "itto": r'("description": "Oni geometry patterns, ink crack effects")',
        "celestial": r'("description": "NASA spatial maps, nebula, twinkle effects")',
        "sakura": r'("description": "Japanese aesthetic, petal effects, warm tones")',
    }
    
    pattern = desc_match[name]
    # After matching the description, we need to find the params block end
    # The params block ends with `            }` followed by `        },` or `        }`
    # We'll use a regex that captures everything from description to the closing of params
    
    # Find the position of this preset's description
    desc_re = re.compile(pattern)
    match = desc_re.search(text)
    if not match:
        print(f"  Could not find preset '{name}'")
        continue
    
    # From the description, find the next `            }\n` that closes the params
    desc_end = match.end()
    rest = text[desc_end:]
    
    # Find the closing `            }\n` of the params block
    # The params block has "params": { ... }
    # After the description, the "params": { line is next, then all the params, then `            }`
    # We need to find the `            }` that closes `params`
    
    # Count brace depth starting from "params": {
    params_start = rest.find('"params": {')
    if params_start < 0:
        print(f"  Could not find 'params' in preset '{name}'")
        continue
    
    # Find the opening brace of params
    brace_pos = rest.find('{', params_start)
    depth = 1
    pos = brace_pos + 1
    while depth > 0 and pos < len(rest):
        if rest[pos] == '{':
            depth += 1
        elif rest[pos] == '}':
            depth -= 1
        pos += 1
    
    if depth != 0:
        print(f"  Could not find closing brace for preset '{name}'")
        continue
    
    # pos now points to the character after the closing `}`
    # The closing `}` is at pos-1, and the whitespace/newline before it is our injection point
    
    # We want to insert v2_lines before the closing `}`
    # Find the newline before the closing `}`
    
    # The `}` is at index pos-1 in rest. We need to find the start of the line containing it.
    # Actually, we can just replace the `}` with `v2_lines\n            }`
    
    # Convert back to absolute position
    abs_closing = desc_end + pos - 1
    
    # Check what's at abs_closing - should be `}`
    assert text[abs_closing] == '}', f"Expected '}}' at {abs_closing}, got {text[abs_closing]}"
    
    # The whitespace before `}` may vary. Let's capture it.
    # Go backwards from abs_closing to find the start of whitespace
    ws_start = abs_closing - 1
    while ws_start > 0 and text[ws_start] in ' \t':
        ws_start -= 1
    # Move past the newline
    if text[ws_start] == '\n':
        ws_start += 1
    
    # The indentation of the closing brace determines our v2_lines indentation
    ws_before_close = text[ws_start:abs_closing]
    
    # Inject v2_lines before the closing brace
    v2_text = ""
    for line in v2_lines:
        # line already has "                " prefix
        v2_text += line
    
    # Insert v2_text before ws + }
    old = text[ws_start:abs_closing + 1]
    new = v2_text.rstrip('\n') + '\n' + ws_before_close + '}'
    
    text = text[:ws_start] + new + text[abs_closing + 1:]
    print(f"  Updated preset '{name}'")

print("\nWriting updated addon file...")
ADDON.write_text(text, encoding="utf-8")
print("Done.")