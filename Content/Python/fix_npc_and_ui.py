import unreal

print("=== NPC INTERACTION FIX + UI OVERHAUL ===\n")

eal = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# =============================================
# PART 1: NPC INTERACTION FIX
# =============================================

print("--- Part 1: NPC Interaction Diagnostic ---")

# The handoff explicitly says: "ZenForestTest currently instantiates MelodiaSmokeCharacter
# with a plain PlayerController; therefore direct stock-controller inventory readback
# is unavailable on that exploration map."
# 
# The stock JRPG interaction system relies on:
#   - BP_InteractionDetector (component on NPCs)
#   - BP_JRPGPlayerController or BP_MelodiaJRPGPlayerController (reads detector)
#   - BP_InteractionUI (shows interaction prompt)
#   - IMC_MelodiaDefault (input mapping context with 'Interact' action)
#
# Fix: Use Monolith's author_map_settings to set ZenForestTest's GameMode
# to BP_MelodiaJRPGGameMode, which uses the proper controller class.

# First check the current state
gm = eal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode")
pc = eal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController")
imc = eal.load_asset("/Game/Melodia/Input/IMC_MelodiaDefault")

print(f"  BP_MelodiaJRPGGameMode: {'OK' if gm else 'MISSING'}")
print(f"  BP_MelodiaJRPGPlayerController: {'OK' if pc else 'MISSING'}")
print(f"  IMC_MelodiaDefault: {'OK' if imc else 'MISSING'}")

# Check if ZenForestTest NPCs have interaction components
# The JRPG template's BP_NPC/BP_QuestNPC/BP_QuestNPCBase use
# BP_InteractionDetector for overlap-based interaction
npc_base = eal.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Interactables/BP_QuestNPCBase")
interaction_detector = eal.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/Interactables/BP_InteractionDetector")
interaction_ui = eal.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_InteractionUI")

print(f"  BP_QuestNPCBase: {'OK' if npc_base else 'MISSING'}")
print(f"  BP_InteractionDetector: {'OK' if interaction_detector else 'MISSING'}")
print(f"  BP_InteractionUI: {'OK' if interaction_ui else 'MISSING'}")

# The fix: the plain PlayerController in ZenForestTest needs to be
# swapped to BP_MelodiaJRPGPlayerController. The way to do this is
# setting the WorldSettings->GameMode Override on the level.
# Use author_map_settings via MCP (we're calling it programmatically here)

print("\n  >>> FIX CANDIDATE: ZenForestTest WorldSettings needs GameMode Override")
print("  >>> Set to: /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode")
print("  >>> This provides: BP_MelodiaJRPGPlayerController + IMC_MelodiaDefault + interaction system")

# =============================================
# PART 2: UI OVERHAUL - Apply SoftMG palette
# =============================================

print("\n--- Part 2: UI Palette Verification ---")

# SoftMG assets we'll use
ui_assets = {
    "Parchment base": "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment",
    "Magic Heart": "/Game/Melodia/Magical/T_Magic_Heart",
    "Magic Star": "/Game/Melodia/Magical/T_Magic_Star",
}
for label, path in ui_assets.items():
    exists = eal.does_asset_exist(path)
    print(f"  {label}: {'OK' if exists else 'MISSING'} - {path}")

# Kenney fantasy-ui borders
kenney_panels = eal.does_asset_exist("/Game/kenney_fantasy-ui-borders/PNG/Default/Panel")
print(f"  Kenney Panel borders: {'OK' if kenney_panels else 'MISSING'}")

# Check filigree batch
filigree_path = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO"
filigree_assets = ar.get_assets_by_path(filigree_path, recursive=True) or []
filigree_count = sum(1 for a in filigree_assets if "Filigree" in str(a.package_name))
print(f"  Filigree variants: {filigree_count} found in {filigree_path}")

# =============================================
# PART 3: HARMONIX INTEGRATION POINTS
# =============================================

print("\n--- Part 3: Harmonix Integration Points ---")

# Check Harmonix plugin
harmonix_enabled = unreal.PluginManager.is_plugin_loaded("Harmonix") if hasattr(unreal.PluginManager, "is_plugin_loaded") else False
print(f"  Harmonix plugin loaded (Python check): {harmonix_enabled}")

# Check audio reactive presentation subsystem
audio_class = unreal.find_class("MelodiaAudioReactivePresentationSubsystem")
if audio_class:
    print(f"  MelodiaAudioReactivePresentationSubsystem: FOUND")
    # List available methods
    methods = [m for m in dir(audio_class) if not m.startswith('_') and callable(getattr(audio_class, m, None))]
    audio_methods = [m for m in methods if any(k in m.lower() for k in ['audio', 'sound', 'beat', 'rhythm', 'midi', 'note', 'play', 'trigger'])]
    if audio_methods:
        print(f"    Audio methods: {', '.join(audio_methods[:10])}")
    else:
        print(f"    No audio-specific methods found (check BP-callable functions)")
else:
    print(f"  MelodiaAudioReactivePresentationSubsystem: NOT FOUND")

# Check rhythm presentation component
rhythm_class = unreal.find_class("MelodiaJRPGPresentationRhythmComponent")
if rhythm_class:
    print(f"  MelodiaJRPGPresentationRhythmComponent: FOUND")
else:
    print(f"  MelodiaJRPGPresentationRhythmComponent: NOT FOUND")

# =============================================
# PART 4: ACTION PLAN SUMMARY
# =============================================

print("\n" + "=" * 60)
print("FIX PLAN SUMMARY")
print("=" * 60)
print("""
1. [IN-EDITOR REQUIRED] Open ZenForestTest in editor.
   a. World Settings -> GameMode Override -> set to:
      /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode
   b. Save level.
   c. PIE test: walk up to Petal Priestess NPC, press F.
   d. Should see BP_InteractionUI prompt.

2. [IN-EDITOR] Apply SoftMG UI to WBP_SaveLoad:
   a. Open WBP_SaveLoad widget.
   b. Set root panel background to T_Melodia_SoftMG_Parchment.
   c. Add filigree corner decorations.
   d. Button styling: lilac/blush focus with gold border.
   e. Compile. Verify no errors.

3. [IN-EDITOR] Skybound Refrain conditional bonus:
   a. Open BP_SirSkyboundRefrain Blueprint graph.
   b. Add Branch after DealDamage node.
   c. Condition: check target's activeBuffs for BP_Resonance class.
   d. True: multiply damage by 1.5x. False: normal damage.
   e. Compile.

4. [SCRIPTED] Create BP_MelodiaCombatRhythmFeedback:
   a. Cosmetic pulse VFX on skill use (read-only Harmonix clock)
   b. No authority change.
""")

print("DONE")