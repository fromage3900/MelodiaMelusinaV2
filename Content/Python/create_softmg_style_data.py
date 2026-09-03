import unreal

print("=== Creating DA_MelodiaSoftMG_UIStyle Data Asset ===\n")

# Create the Data Asset
asset_path = "/Game/Melodia/UI/DA_MelodiaSoftMG_UIStyle"
factory = unreal.DataAssetFactory()

# Check if it already exists
if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
    print(f"Data Asset already exists at {asset_path}")
    da = unreal.EditorAssetLibrary.load_asset(asset_path)
else:
    print(f"Creating Data Asset at {asset_path}")
    da = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name="DA_MelodiaSoftMG_UIStyle",
        package_path="/Game/Melodia/UI",
        asset_class=unreal.DataAsset,
        factory=factory
    )

if da:
    print("Data Asset created successfully")
    
    # Define color palette (SoftMG theme)
    # Lilac: RGB(200, 162, 200) = LinearColor(0.784, 0.635, 0.784)
    # Blush: RGB(255, 182, 193) = LinearColor(1.0, 0.714, 0.757)
    # Gold: RGB(255, 215, 0) = LinearColor(1.0, 0.843, 0.0)
    # Ivory: RGB(255, 255, 240) = LinearColor(1.0, 1.0, 0.941)
    
    print("\nColor Palette (SoftMG Theme):")
    print("  Lilac: (0.784, 0.635, 0.784)")
    print("  Blush: (1.0, 0.714, 0.757)")
    print("  Gold: (1.0, 0.843, 0.0)")
    print("  Ivory: (1.0, 1.0, 0.941)")
    
    print("\nTexture References:")
    print("  Parchment: /Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment")
    print("  Filigree Corner: /Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CornerBaroque")
    print("  Filigree Crest: /Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CrestBaroque")
    print("  Magic Heart: /Game/Melodia/Magical/T_Magic_Heart")
    print("  Magic Star: /Game/Melodia/Magical/T_Magic_Star")
    
    print("\nFont References:")
    print("  Title: /Game/Melodia/UI/Fonts/F_Syne")
    print("  Body: /Game/Melodia/UI/Fonts/F_InstrumentSerif")
    print("  Decorative: /Game/Melodia/UI/Fonts/F_TwinkleStar")
    
    print("\nData Asset created. Next steps:")
    print("1. Open DA_MelodiaSoftMG_UIStyle in editor")
    print("2. Add properties for colors, textures, and fonts")
    print("3. Reference this Data Asset in all UI widgets")
else:
    print("Failed to create Data Asset")

print("\nDONE")