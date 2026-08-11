#pragma once

#include "CoreMinimal.h"
#include "MelodiaAfflictionTypes.h"
#include "MelodiaRoguelikeAuthorityTypes.generated.h"

UENUM(BlueprintType)
enum class EMelodiaRunLifecyclePhase : uint8
{
    Inactive,
    Generating,
    Exploring,
    Encounter,
    RewardChoice,
    TransitionReady,
    Defeated,
    StructuredComplete,
    EndlessOffer,
    RunSummary,
    RecoverableFailure
};

UENUM(BlueprintType)
enum class EMelodiaCompanionRequirement : uint8
{
    None,
    Present,
    Resonance,
    Playable
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRunBuildModifier
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName SourceRewardId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaModifierStat Stat = EMelodiaModifierStat::Attack;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaModifierOp Operation = EMelodiaModifierOp::Mul;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") float Value = 1.0f;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 MaxStacks = 1;
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaAuthoritativeStageRecipe
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 SchemaVersion = 1;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 ActIndex = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StageIndex = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 EndlessDepth = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName StageId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName RoomDefinitionId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName RoomDataId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName EncounterId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName EnemyId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 DifficultyTier = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<FName> MutatorIds;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName RewardPoolId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FName DissonanceProfileId = NAME_None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaCompanionRequirement CompanionRequirement = EMelodiaCompanionRequirement::None;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StageSeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 TopologySeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 RoomSeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 EnemySeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 RewardSeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 MutatorSeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 CosmeticSeed = 0;
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRunSnapshot
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 SchemaVersion = 1;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 RunSeed = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 CurrentStageIndex = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 EndlessDepth = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaRunLifecyclePhase Phase = EMelodiaRunLifecyclePhase::Inactive;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") FMelodiaAuthoritativeStageRecipe CurrentStage;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<FName> AcquiredRewardIds;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<FMelodiaRunBuildModifier> AcquiredBuildModifiers;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<FName> PendingRewardIds;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<uint8> PendingRewardTypes;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<float> PendingRewardMagnitudes;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") TArray<float> PendingRewardDissonanceCosts;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bEncounterResultRecorded = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bRewardCommitted = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bFallbackRecipeActive = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") float SongPowerMultiplier = 1.0f;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") float RecoveryMultiplier = 1.0f;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") float Dissonance = 0.0f;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 HeartMelodyTokens = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 SwirlMelodyTokens = 0;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bStructuredMode = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bEndlessMode = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StructuredActCount = 1;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StructuredStagesPerAct = 3;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StagesPerDungeon = 3;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bCompanionPresent = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bResonanceAvailable = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bCompanionPlayable = false;
    UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 CompanionBond = 0;
};
