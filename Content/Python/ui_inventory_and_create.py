import unreal

print("=" * 60)
print("DEEP UI ASSET INVENTORY + ARTIST-FRIENDLY CREATION")
print("=" * 60)

ar = unreal.AssetRegistryHelpers.get_asset_registry()
eal = unreal.EditorAssetLibrary

# =============================================
# PART 1: Inventory all T_Melodia_* textures
# =============================================
print("\n--- T_Melodia_* Texture Assets ---")
melodia_textures = []
for prefix in ["/Game/EnvSandbox/Textures/Melodia", "/Game/Melodia/Magical", "/Game/Melodia/Characters"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        cls = str(a.asset_class_path.asset_name)
        if "Melodia" in name or "Magic" in name or "GameUI" in name or "Filigree" in name or "Parchment" in name:
            melodia_textures.append(f"  {name} ({cls})")

print(f"  Total: {len(melodia_textures)} Melodia-themed assets")
for t in melodia_textures[:40]:
    print(t)

# =============================================
# PART 2: BatchO Filigree details
# =============================================
print("\n--- BatchO Filigree Detail ---")
filigree_path = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO"
for a in (ar.get_assets_by_path(filigree_path, recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    if "Filigree" in name or filigree_path in name:
        print(f"  {name} ({cls})")

# =============================================
# PART 3: Kenney UI assets  
# =============================================
print("\n--- Kenney Fantasy UI Assets ---")
kenney_path = "/Game/kenney_fantasy-ui-borders"
for a in (ar.get_assets_by_path(kenney_path, recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    print(f"  {name} ({cls})")

# =============================================
# PART 4: Existing Widget Blueprints
# =============================================
print("\n--- Existing Widget Blueprints ---")
for prefix in ["/Game/Melodia/UI", "/Game/MelodiaIntegration", "/Game/TurnBasedJRPGTemplate/Blueprints/UI"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        cls = str(a.asset_class_path.asset_name)
        if "WidgetBlueprint" in cls or "WBP" in name:
            print(f"  {name} ({cls})")

# =============================================
# PART 5: Fonts
# =============================================
print("\n--- Font Assets ---")
for a in (ar.get_assets_by_path("/Game", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    if "Font" in cls and ("Melodia" in name or "Syne" in name or "Noto" in name):
        print(f"  {name} ({cls})")

# =============================================
# PART 6: Magic/Sparkle Motif Assets
# =============================================
print("\n--- Magic/Sparkle Motifs ---")
for a in (ar.get_assets_by_path("/Game/Melodia/Magical", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    print(f"  {name} ({cls})")

# =============================================
# PART 7: MIDI Check
# =============================================
print("\n--- MIDI Assets ---")
for a in (ar.get_assets_by_path("/Game/MelodiaIntegration/MIDI", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    print(f"  {name} ({cls})")

# Also check /Game/Melodia/Audio/MIDI
for a in (ar.get_assets_by_path("/Game/Melodia/Audio/MIDI", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    print(f"  {name} ({cls})")

# =============================================
# PART 8: Existing Data Assets
# =============================================
print("\n--- Existing Melodia Data Assets ---")
for a in (ar.get_assets_by_path("/Game/MelodiaIntegration/Config", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    print(f"  {name} ({cls})")

print("\nDONE")