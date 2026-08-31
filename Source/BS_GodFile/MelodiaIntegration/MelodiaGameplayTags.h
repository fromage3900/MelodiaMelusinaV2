#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "MelodiaGameplayTags.generated.h"

/**
 * Melodia Gameplay Tags — hierarchical, compile-time validated identifiers.
 *
 * Replaces raw FName strings for network IDs, node IDs, route IDs, puzzle IDs,
 * encounter IDs, quest IDs, flag IDs, level IDs, reward IDs, stat IDs, and all
 * other Melodia identifier channels.
 *
 * Migration status (2026-08-28):
 *   [x] Infrastructure (this file)
 *   [x] MelodiaWaterGameplaySubsystem (proof of concept)
 *   [ ] MelodiaNarrativeSubsystem
 *   [ ] MelodiaExternalJRPGBridgeSubsystem
 *   [ ] MelodiaExplorationActors
 *   [ ] MelodiaPCGWaterGameplayBridgeComponent
 *   [ ] MelodiaPCGNarrativeChallengeBridgeComponent
 *   [ ] MelodiaBattleMapConfig
 *   [ ] All Blueprints (manual update required)
 *   [ ] All Data Assets (manual update required)
 *
 * Hierarchy:
 *   Melodia.Water.Network.*
 *   Melodia.Water.Node.*
 *   Melodia.Water.Route.*
 *   Melodia.Water.Body.*
 *   Melodia.Water.Puzzle.*
 *   Melodia.Water.Platform.*
 *   Melodia.Water.Channel.*
 *   Melodia.Battle.Encounter.*
 *   Melodia.Quest.*
 *   Melodia.Flag.*
 *   Melodia.Travel.*
 *   Melodia.Reward.*
 *   Melodia.Stat.*
 *   Melodia.Bond.*
 *   Melodia.Intent.*
 *   Melodia.StateAnchor.*
 *   Melodia.Checkpoint.*
 *   Melodia.Spawn.*
 */

// ── Water Gameplay Tags ──────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterNetworkTag
{
	GENERATED_BODY()

	static FGameplayTag TagAlpha;
	static FGameplayTag TagBeta;
	static FGameplayTag TagGamma;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterNodeTag
{
	GENERATED_BODY()

	// Reservoirs
	static FGameplayTag ReservoirMain;
	static FGameplayTag ReservoirEast;
	static FGameplayTag ReservoirWest;

	// Channels
	static FGameplayTag ChannelNorth;
	static FGameplayTag ChannelSouth;
	static FGameplayTag ChannelCentral;

	// Valves
	static FGameplayTag ValveMain;
	static FGameplayTag ValveBypass;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterRouteTag
{
	GENERATED_BODY()

	static FGameplayTag MainFlow;
	static FGameplayTag Bypass;
	static FGameplayTag Overflow;
	static FGameplayTag Return;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterBodyTag
{
	GENERATED_BODY()

	static FGameplayTag LakeKaleido;
	static FGameplayTag RiverNave;
	static FGameplayTag FallsMelusina;
	static FGameplayTag PoolReflection;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterPuzzleTag
{
	GENERATED_BODY()

	static FGameplayTag Resonance01;
	static FGameplayTag Resonance02;
	static FGameplayTag Resonance03;
	static FGameplayTag FlowControl;
	static FGameplayTag PressureBalance;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterPlatformTag
{
	GENERATED_BODY()

	static FGameplayTag FerryKaleido;
	static FGameplayTag RaftNave;
	static FGameplayTag LiftFalls;

	static void RegisterTags();
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaWaterChannelTag
{
	GENERATED_BODY()

	static FGameplayTag Harmonic;
	static FGameplayTag Dissonant;
	static FGameplayTag Crescendo;
	static FGameplayTag Diminuendo;

	static void RegisterTags();
};

// ── Battle Tags ──────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaBattleEncounterTag
{
	GENERATED_BODY()

	static FGameplayTag KaleidoNaveMelodySlime;
	static FGameplayTag CrystalShard;
	static FGameplayTag CosmicReaver;
	static FGameplayTag ChoralSheep;

	static void RegisterTags();
};

// ── Quest Tags ───────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaQuestTag
{
	GENERATED_BODY()

	static FGameplayTag FirstDream;
	static FGameplayTag WardrobeEquip;
	static FGameplayTag ChoralSheepRecruit;
	static FGameplayTag SeaAboveCutscene;
	static FGameplayTag Echo01;
	static FGameplayTag Echo02;
	static FGameplayTag Echo03;
	static FGameplayTag SmokeQuest;

	static void RegisterTags();
};

// ── Flag Tags ────────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaFlagTag
{
	GENERATED_BODY()

	static FGameplayTag BattleWon;
	static FGameplayTag SmokeComplete;
	static FGameplayTag FirstDreamCompleted;
	static FGameplayTag FirstDreamAttempted;
	static FGameplayTag FirstDreamFled;
	static FGameplayTag P0PlaythroughCompleted;
	static FGameplayTag P0PlaythroughAttempted;
	static FGameplayTag P0PlaythroughFled;
	static FGameplayTag WardrobeOutfitEquipped;
	static FGameplayTag WardrobeEquipCompleted;
	static FGameplayTag MelusinaSorrowSeamRestored;
	static FGameplayTag ChoralSheepRecruited;
	static FGameplayTag ChoralSheepCompleted;
	static FGameplayTag SeaAboveWitnessed;
	static FGameplayTag SeaAboveMembranePulseActive;
	static FGameplayTag SeaAboveCompleted;

	static void RegisterTags();
};

// ── Travel Tags ──────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaTravelTag
{
	GENERATED_BODY()

	static FGameplayTag KaleidoNave;
	static FGameplayTag MelusinaMorning;
	static FGameplayTag SeaAbovePrototype;

	static void RegisterTags();
};

// ── Reward Tags ──────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaRewardTag
{
	GENERATED_BODY()

	static FGameplayTag DawnVeil;
	static FGameplayTag DreamweaveShawl;
	static FGameplayTag SolsticeDrum;
	static FGameplayTag StarCharm;
	static FGameplayTag TuningFork;
	static FGameplayTag SmokeReward;
	static FGameplayTag FirstResonanceEcho;
	static FGameplayTag WardrobeFirstOutfit;
	static FGameplayTag CompanionChoralSheep;
	static FGameplayTag SeaAboveMemory;

	static void RegisterTags();
};

// ── Stat Tags ────────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaStatTag
{
	GENERATED_BODY()

	static FGameplayTag Harmony;
	static FGameplayTag Elegance;
	static FGameplayTag Resonance;

	static void RegisterTags();
};

// ── Bond Tags ────────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaBondTag
{
	GENERATED_BODY()

	static FGameplayTag SirMelodious;
	static FGameplayTag TheOrrery;

	static void RegisterTags();
};

// ── Intent Tags ──────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaIntentTag
{
	GENERATED_BODY()

	// Quest completion intents
	static FGameplayTag FirstDreamComplete;
	static FGameplayTag WardrobeEquipComplete;
	static FGameplayTag ChoralSheepComplete;
	static FGameplayTag SeaAboveComplete;

	// World challenge intents
	static FGameplayTag Resonance01Complete;
	static FGameplayTag Resonance02Complete;
	static FGameplayTag Resonance03Complete;

	// State anchor intents
	static FGameplayTag AnchorFirstDream;
	static FGameplayTag AnchorWardrobe;

	static void RegisterTags();
};

// ── State Anchor Tags ────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaStateAnchorTag
{
	GENERATED_BODY()

	static FGameplayTag FirstDream;
	static FGameplayTag Wardrobe;
	static FGameplayTag ChoralSheep;
	static FGameplayTag SeaAbove;

	static void RegisterTags();
};

// ── Checkpoint Tags ──────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaCheckpointTag
{
	GENERATED_BODY()

	static FGameplayTag AfterBattle;
	static FGameplayTag AfterDialogue;
	static FGameplayTag AfterTravel;
	static FGameplayTag AfterWardrobe;

	static void RegisterTags();
};

// ── Spawn Tags ───────────────────────────────────────────────────────────────

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMeliaSpawnTag
{
	GENERATED_BODY()

	static FGameplayTag Default;
	static FGameplayTag AfterBattle;
	static FGameplayTag AfterTravel;
	static FGameplayTag Checkpoint;

	static void RegisterTags();
};

// ── Registration ─────────────────────────────────────────────────────────────

/**
 * Registers all Melodia Gameplay Tags with UGameplayTagsManager.
 * Call once at module startup (e.g., from FMelodiaCoreModule::StartupModule).
 */
void BS_GODFILE_API RegisterMelodiaGameplayTags();
