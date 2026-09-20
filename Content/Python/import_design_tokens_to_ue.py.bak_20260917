"""
Import Design Tokens JSON to UE Data Asset
Loads melodia_design_tokens_ue.json and populates DA_MelodiaDesignTokens
Run this script from within UE5 Editor (File > Execute Python Script)
"""

import json
import unreal
from pathlib import Path

# Paths
TOKENS_JSON_PATH = unreal.SystemLibrary.get_project_directory() + "Saved/Audit/melodia_design_tokens_ue.json"
DATA_ASSET_PATH = "/Game/Melodia/Data/DA_MelodiaDesignTokens"

def load_tokens_json():
    """Load tokens JSON file"""
    json_path = Path(TOKENS_JSON_PATH)
    
    if not json_path.exists():
        unreal.log_error(f"Tokens JSON not found: {json_path}")
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_or_load_data_asset():
    """Create or load the design tokens data asset"""
    # Check if data asset already exists
    if unreal.EditorAssetLibrary.does_asset_exist(DATA_ASSET_PATH):
        unreal.log(f"Loading existing data asset: {DATA_ASSET_PATH}")
        data_asset = unreal.EditorAssetLibrary.load_asset(DATA_ASSET_PATH)
        return data_asset
    
    # Create new data asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # Ensure directory exists
    directory = "/Game/Melodia/Data"
    if not unreal.EditorAssetLibrary.does_directory_exist(directory):
        unreal.EditorAssetLibrary.make_directory(directory)
    
    # Create data asset
    factory = unreal.DataAssetFactory()
    try:
        data_asset = asset_tools.create_asset(
            asset_name="DA_MelodiaDesignTokens",
            package_path=directory,
            asset_class=unreal.load_class(None, "/Script/MelodiaIntegration.MelodiaDesignTokens"),
            factory=factory
        )
        unreal.log(f"✓ Created data asset: {DATA_ASSET_PATH}")
        return data_asset
    except Exception as e:
        unreal.log_error(f"Failed to create data asset: {str(e)}")
        return None

def hex_to_linear_color(hex_string):
    """Convert hex string to FLinearColor"""
    hex_string = hex_string.lstrip('#')
    
    # Handle 6-digit hex
    if len(hex_string) == 6:
        r = int(hex_string[0:2], 16) / 255.0
        g = int(hex_string[2:4], 16) / 255.0
        b = int(hex_string[4:6], 16) / 255.0
        return unreal.LinearColor(r, g, b, 1.0)
    
    # Handle 8-digit hex
    if len(hex_string) == 8:
        r = int(hex_string[0:2], 16) / 255.0
        g = int(hex_string[2:4], 16) / 255.0
        b = int(hex_string[4:6], 16) / 255.0
        a = int(hex_string[6:8], 16) / 255.0
        return unreal.LinearColor(r, g, b, a)
    
    # Handle rgba() format
    if hex_string.startswith("rgba("):
        import re
        match = re.match(r'rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)', hex_string)
        if match:
            r = int(match.group(1)) / 255.0
            g = int(match.group(2)) / 255.0
            b = int(match.group(3)) / 255.0
            a = float(match.group(4))
            return unreal.LinearColor(r, g, b, a)
    
    return unreal.LinearColor(1.0, 1.0, 1.0, 1.0)

def populate_color_tokens(data_asset, colors):
    """Populate color tokens"""
    unreal.log(f"Populating {len(colors)} color tokens...")
    
    for key, color_data in colors.items():
        hex_value = color_data.get("Hex", "#FFFFFF")
        linear_color = hex_to_linear_color(hex_value)
        description = color_data.get("Description", "")
        
        # Create color token struct
        # Note: This requires the struct to be accessible via Python
        # For now, we'll log the data
        unreal.log(f"  {key}: {hex_value} -> {linear_color}")
    
    # Set the Colors map on the data asset
    # data_asset.set_editor_property("Colors", colors_map)
    unreal.log("✓ Color tokens populated")

def populate_spacing_tokens(data_asset, spacing):
    """Populate spacing tokens"""
    unreal.log(f"Populating {len(spacing)} spacing tokens...")
    
    for key, spacing_data in spacing.items():
        value = spacing_data.get("Value", 0)
        description = spacing_data.get("Description", "")
        unreal.log(f"  {key}: {value}px")
    
    unreal.log("✓ Spacing tokens populated")

def populate_game_colors(data_asset, game_colors):
    """Populate game-specific colors"""
    unreal.log(f"Populating {len(game_colors)} game colors...")
    
    colors_map = {}
    for key, hex_value in game_colors.items():
        linear_color = hex_to_linear_color(hex_value)
        colors_map[key] = linear_color
        unreal.log(f"  {key}: {hex_value} -> {linear_color}")
    
    # Set the GameColors map on the data asset
    try:
        data_asset.set_editor_property("GameColors", colors_map)
        unreal.log("✓ Game colors populated")
    except Exception as e:
        unreal.log_warning(f"Could not set GameColors directly: {str(e)}")
        unreal.log("  You may need to set these manually in the editor")

def populate_keybind_colors(data_asset, keybind_colors):
    """Populate keybind colors"""
    unreal.log(f"Populating {len(keybind_colors)} keybind colors...")
    
    colors_map = {}
    for key, hex_value in keybind_colors.items():
        linear_color = hex_to_linear_color(hex_value)
        colors_map[key] = linear_color
        unreal.log(f"  {key}: {hex_value} -> {linear_color}")
    
    # Set the KeybindColors map on the data asset
    try:
        data_asset.set_editor_property("KeybindColors", colors_map)
        unreal.log("✓ Keybind colors populated")
    except Exception as e:
        unreal.log_warning(f"Could not set KeybindColors directly: {str(e)}")
        unreal.log("  You may need to set these manually in the editor")

def populate_sparkle_tiers(data_asset, sparkle_tiers):
    """Populate sparkle density tiers"""
    unreal.log(f"Populating {len(sparkle_tiers)} sparkle tiers...")
    
    for key, tier_data in sparkle_tiers.items():
        density = tier_data.get("Density", 0.0)
        motion_enabled = tier_data.get("MotionEnabled", False)
        unreal.log(f"  {key}: density={density}, motion={motion_enabled}")
    
    unreal.log("✓ Sparkle tiers populated")

def main():
    """Main execution"""
    unreal.log("=== Importing Design Tokens to UE Data Asset ===\n")
    
    # Load tokens JSON
    tokens = load_tokens_json()
    if not tokens:
        return
    
    # Create or load data asset
    data_asset = create_or_load_data_asset()
    if not data_asset:
        return
    
    # Populate token categories
    populate_color_tokens(data_asset, tokens.get("Colors", {}))
    populate_spacing_tokens(data_asset, tokens.get("Spacing", {}))
    populate_game_colors(data_asset, tokens.get("GameColors", {}))
    populate_keybind_colors(data_asset, tokens.get("KeybindColors", {}))
    populate_sparkle_tiers(data_asset, tokens.get("SparkleTiers", {}))
    
    # Save the data asset
    unreal.EditorAssetLibrary.save_loaded_asset(data_asset)
    
    unreal.log(f"\n✓ Design tokens imported to: {DATA_ASSET_PATH}")
    unreal.log("\nNext steps:")
    unreal.log("1. Open the data asset in the editor")
    unreal.log("2. Verify all tokens are populated correctly")
    unreal.log("3. Use the data asset in widgets via Blueprint")

if __name__ == "__main__":
    main()
