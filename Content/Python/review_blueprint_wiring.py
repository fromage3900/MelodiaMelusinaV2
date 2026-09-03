import unreal

# ============================================================
# Core Game Mechanics Blueprint Wiring Review Script
# Run in Unreal Editor: -ExecutePythonScript=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/review_blueprint_wiring.py
# ============================================================

def review_core_blueprints():
    """Review key blueprints for core game mechanics wiring"""
    
    key_blueprints = [
        # Game Instance / Config
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance_Config",
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGController_Config",
        
        # Battle System
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaBattleBridge",
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode",
        "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController",
        
        # Character
        "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
        
        # Intro/Opening
        "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro",
        
        # Template Battle Blueprints
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OneTimeBattle",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_PermanentBattle",
    ]
    
    print(f"\n{'='*70}")
    print(f"CORE GAME MECHANICS BLUEPRINT WIRING REVIEW")
    print(f"{'='*70}")
    
    for bp_path in key_blueprints:
        print(f"\n--- {bp_path} ---")
        if not unreal.EditorAssetLibrary.does_asset_exist(bp_path):
            print(f"  NOT FOUND")
            continue
        
        bp_asset = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp_asset:
            print(f"  FAILED TO LOAD")
            continue
        
        # Get the generated class
        bp_class = bp_asset.generated_class()
        if not bp_class:
            print(f"  NO GENERATED CLASS (may need to compile)")
            continue
        
        print(f"  Class: {bp_class.get_name()}")
        print(f"  Parent: {bp_class.get_super_class().get_name() if bp_class.get_super_class() else 'None'}")
        
        # Get all component blueprints
        components = bp_class.get_components()
        if components:
            print(f"  Components ({len(components)}):")
            for comp in components:
                comp_class = comp.get_class()
                print(f"    - {comp.get_name()} ({comp_class.get_name()})")
        
        # Check for key properties/variables
        # This is limited in Python - mainly shows structure

def review_melodia_skills():
    """Review Melodia skill blueprints"""
    skill_paths = [
        "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaTrueStrike",
        "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence",
        "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaFocusAttack",
        "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaDoubleHit",
    ]
    
    print(f"\n{'='*70}")
    print(f"MELODIA SKILL BLUEPRINTS")
    print(f"{'='*70}")
    
    for skill_path in skill_paths:
        print(f"\n--- {skill_path} ---")
        if not unreal.EditorAssetLibrary.does_asset_exist(skill_path):
            print(f"  NOT FOUND")
            continue
        
        skill_asset = unreal.EditorAssetLibrary.load_asset(skill_path)
        if not skill_asset:
            print(f"  FAILED TO LOAD")
            continue
        
        skill_class = skill_asset.generated_class()
        if not skill_class:
            print(f"  NO GENERATED CLASS")
            continue
        
        print(f"  Class: {skill_class.get_name()}")
        print(f"  Parent: {skill_class.get_super_class().get_name() if skill_class.get_super_class() else 'None'}")

def review_melodia_animation_blueprints():
    """Review Animation Blueprints"""
    abp_paths = [
        "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current",
        "/Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation",
    ]
    
    print(f"\n{'='*70}")
    print(f"ANIMATION BLUEPRINTS")
    print(f"{'='*70}")
    
    for abp_path in abp_paths:
        print(f"\n--- {abp_path} ---")
        if not unreal.EditorAssetLibrary.does_asset_exist(abp_path):
            print(f"  NOT FOUND")
            continue
        
        abp_asset = unreal.EditorAssetLibrary.load_asset(abp_path)
        if not abp_asset:
            print(f"  FAILED TO LOAD")
            continue
        
        abp_class = abp_asset.generated_class()
        if not abp_class:
            print(f"  NO GENERATED CLASS")
            continue
        
        print(f"  Class: {abp_class.get_name()}")
        print(f"  Parent: {abp_class.get_super_class().get_name() if abp_class.get_super_class() else 'None'}")

def review_melodia_core_cpp():
    """Review MelodiaCore C++ classes (via reflection)"""
    print(f"\n{'='*70}")
    print(f"MELODIA CORE C++ CLASSES (Reflection)")
    print(f"{'='*70}")
    
    # These are C++ classes, we can find them via reflection
    core_classes = [
        "MelodiaRhythmExecutionComponent",
        "MelodiaBattleSession",
        "MelodiaSongSkillLibrary",
        "MelodiaSongDataAsset",
        "MelodiaCoreRulesLibrary",
        "MelodiaMidiParser",
        "MelodiaBattleAdapter",
    ]
    
    for class_name in core_classes:
        print(f"\n--- {class_name} ---")
        # Find via UClass reflection
        # This is limited in Python but we can try
        uclass = unreal.find_class(class_name)
        if uclass:
            print(f"  FOUND: {uclass.get_name()}")
            print(f"  Parent: {uclass.get_super_class().get_name() if uclass.get_super_class() else 'None'}")
            
            # Get functions
            functions = uclass.get_functions()
            if functions:
                print(f"  Functions ({len(functions)}):")
                for func in functions[:10]:  # Limit to first 10
                    print(f"    - {func.get_name()}")
                if len(functions) > 10:
                    print(f"    ... and {len(functions) - 10} more")
        else:
            print(f"  NOT FOUND via reflection (C++ class)")

def check_t3d_systems():
    """Check for T3D (Turn-Based 3D) systems"""
    print(f"\n{'='*70}")
    print(f"T3D SYSTEM CHECK")
    print(f"{'='*70}")
    
    # Search for T3D related assets
    search_terms = ["T3D", "TurnBased", "BattleController", "BattleSession", "RhythmExecution"]
    
    for term in search_terms:
        print(f"\nSearching for '{term}'...")
        # This would require asset registry search which is complex in Python
        # Just note what to look for
        print(f"  Look for: Classes, Blueprints, Components with '{term}' in name")

def print_summary():
    print(f"\n{'='*70}")
    print(f"SUMMARY: KEY AREAS TO VERIFY IN EDITOR")
    print(f"{'='*70}")
    print("""
1. BP_MelodiaJRPGGameInstance
   - Does it initialize MelodiaCore systems?
   - Does it load MIDI charts via MelodiaMidiParser?
   - Is SetSongDataAsset called at boot?

2. BP_MelodiaBattleBridge
   - Connects TurnBasedJRPGTemplate battle system to MelodiaCore rhythm
   - Verify FMelodiaRhythmEffectRequest flow

3. BP_MelusinaJRPGCharacter
   - Mesh assigned: SK_Melusina (check slots 24, 26, 28)
   - Animation Blueprint: ABP_Melusina_Current
   - MelodiaRhythmExecutionComponent attached?

4. BP_BattleController (Template)
   - Authority: TurnBasedJRPGTemplate owns combat (Decision 016)
   - MelodiaCore is presentation-only

5. MelodiaRhythmExecutionComponent (C++)
   - BuildNotesFromChart() consumes FMelodiaSongChart.BasicChartNotes
   - Latency fix: signed error fed to grader (line 203, 205, 280-281)
   - Quartz fallback: FinishExecution() if battle clock drops (line 55-70)

6. MelodiaMidiParser (C++)
   - Parses SMF type 0/1/PPQ
   - Outputs FMelodiaSongChart with BasicChartNotes array
   - Lane policy: EMelodiaLaneMode (PitchClassMod default)

7. MelodiaSongSkillLibrary (C++)
   - Hardcoded 30-row fallback (DO NOT DELETE until real DA_* exists)
   - BuildBasicNotes() demo path -> replace with chart consumption

8. SK_Melusina Material Slots
   - Slots 24, 26, 28: Check for _SkeletonFixSpike materials
   - Reassign to clean MI_Melusina_* instances

9. New Assets to Create/Verify:
   - MPC_TP_Melusina (Material Parameter Collection)
   - NS_Uni_WaterMist (Niagara System with ProximitySpawnRateModule)
   - MF_WaterBioluminescence_v7 (Material Function)
""")

if __name__ == "__main__":
    review_core_blueprints()
    review_melodia_skills()
    review_melodia_animation_blueprints()
    review_melodia_core_cpp()
    check_t3d_systems()
    print_summary()