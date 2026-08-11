"""Extend roguelike blessings with generated room modifiers.

This script adds the Ollama-generated room modifiers as blessings
to the roguelike.py BLESSINGS registry without removing existing ones.
"""
from __future__ import annotations

import json
from pathlib import Path

# Load the generated room mods
ROOM_MODS_PATH = Path("Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json")
OUTPUT_SNIPPET_PATH = Path("Content/Melodia/DataStuctures/blessing_extensions_snippet.py")

def load_room_mods() -> list[dict]:
    """Load the generated room modifiers."""
    if not ROOM_MODS_PATH.exists():
        return []
    data = json.loads(ROOM_MODS_PATH.read_text(encoding="utf-8"))
    return [{"id": mod_id, **mod_data} for mod_id, mod_data in data.get("Rows", {}).items()]

def generate_blessing_extensions(mods: list[dict]) -> dict:
    """Create blessing entries from room modifiers for roguelike.py."""
    extensions = {}
    for m in mods:
        extensions[f"RoomMod_{m['id']}"] = {
            "blessing_id": f"RoomMod_{m['id']}",
            "display_name": m.get("display_name", "Unknown"),
            "description": m.get("description", ""),
            "token_cost": m.get("token_cost", 50),
            "effect_type": m.get("effect_type", "passive"),
            "effect_value": m.get("effect_value", 0.0),
            "effect_str": m.get("effect_str", ""),
        }
    return extensions

def generate_python_snippet(extensions: dict) -> str:
    """Generate Python code snippet for roguelike.py."""
    lines = [
        "# Generated Room Modifier Blessings (Ollama/Qwen)",
        "# DO NOT DELETE - extends existing BLESSINGS registry",
        "# Source: Imports/Data/RoomMods/ (48 enemies, 24 charts, 20 mods generated)",
        "",
    ]
    
    for key, data in extensions.items():
        lines.append(f'ROOGMOD_{key.upper().replace("-", "_")} = Blessing(')
        lines.append(f'    blessing_id="{data["blessing_id"]}",')
        lines.append(f'    display_name="{data["display_name"]}",')
        lines.append(f'    description="{data["description"]}",')
        lines.append(f'    token_cost={data["token_cost"]},')
        lines.append(f'    effect_type="{data["effect_type"]}",')
        lines.append(f'    effect_value={data["effect_value"]},')
        lines.append(f'    effect_str="{data["effect_str"]}",')
        lines.append(')')
        lines.append("")
    
    return "\n".join(lines)

def main() -> dict:
    """Run the extension process."""
    mods = load_room_mods()
    extensions = generate_blessing_extensions(mods)
    
    # Save as Python snippet
    snippet = generate_python_snippet(extensions)
    OUTPUT_SNIPPET_PATH.write_text(snippet, encoding="utf-8")
    
    return {
        "room_mods_loaded": len(mods),
        "blessing_extensions_generated": len(extensions),
        "output_path": str(OUTPUT_SNIPPET_PATH),
    }

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))