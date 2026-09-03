#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaRoguelikeAuthorityTypes.h"
#include "MelodiaRoguelikeRunSubsystem.generated.h"

UENUM(BlueprintType)
enum class EMelodiaRunPhase : uint8
{
	Inactive,
	Generating,
	Exploring,
	Encounter,
	RewardChoice,
	Transitioning,
	Defeated,
	Complete
};

UENUM(BlueprintType)
enum class EMelodiaRunRewardType : uint8
{
	SongPower,
	Recovery,
	SkillPointRegen,
	DissonantBargain
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRunRewardCandidate
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FName RewardId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FText DisplayName;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	EMelodiaRunRewardType Type = EMelodiaRunRewardType::SongPower;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	float Magnitude = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	float DissonanceCost = 0.0f;
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaStageRecipe
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 StageIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FName StageId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FName EnemyId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 StageSeed = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaRunPhaseChanged, EMelodiaRunPhase, NewPhase, EMelodiaRunPhase, PreviousPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaRewardCandidatesReady, const TArray<FMelodiaRunRewardCandidate>&, Candidates);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaRunRewardSelected, const FMelodiaRunRewardCandidate&, Reward);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaStageRecipeReady, const FMelodiaStageRecipe&, Recipe);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMelodiaRunCompleted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMelodiaRunDefeated);

/** Runtime authority for state that must survive streamed-room regeneration. */
// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (deferred roguelike). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaRoguelikeRunSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Roguelike", meta=(WorldContext="WorldContextObject"))
	static UMelodiaRoguelikeRunSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void StartNewRun(int32 Seed);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void StartStructuredRun(int32 Seed, int32 Acts = 1, int32 StagesPerAct = 3);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ContinueEndless();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RestartRun();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool CommitReward(int32 CandidateIndex) { return SelectReward(CandidateIndex); }

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RequestStageAdvance() { return AdvanceStage(); }

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RecordGenerationResult(bool bSucceeded);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ActivateDeterministicFallbackRecipe();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void SetCompanionState(bool bPresent, bool bHasResonance, bool bPlayable, int32 Bond);

	UFUNCTION(BlueprintPure, Category="Melodia|Roguelike")
	bool CanUseEmpoweredMusic() const { return bCompanionPresent && bResonanceAvailable; }

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RecordEncounterResult(EMelodiaEncounterResult Result);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool NotifyEncounterStarted();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool SelectReward(int32 CandidateIndex);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool AdvanceStage();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void ApplyArchetype(const class UMelodiaRunArchetypeDefinition* Archetype);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void NotifyGenerationComplete(bool bSucceeded);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void EndRun(bool bCompleted);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ConsumeHeartMelodyToken();

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	int32 GrantHeartMelodyTokens(int32 Amount = 1);

	/** Restore durable melody-token balances from the profile save. */
	void RestoreDurableTokens(int32 SavedHeartTokens, int32 SavedSwirlTokens);

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ConsumeSwirlMelodyToken();

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaRunPhaseChanged OnRunPhaseChanged;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaRewardCandidatesReady OnRewardCandidatesReady;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaRunRewardSelected OnRewardSelected;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaStageRecipeReady OnStageRecipeReady;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaRunCompleted OnRunCompleted;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Roguelike")
	FMelodiaRunDefeated OnRunDefeated;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	EMelodiaRunPhase Phase = EMelodiaRunPhase::Inactive;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 RunSeed = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 CurrentStageIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FMelodiaStageRecipe CurrentStage;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	FMelodiaAuthoritativeStageRecipe AuthoritativeStage;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	TArray<FMelodiaRunRewardCandidate> PendingRewards;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	TArray<FName> AcquiredRewardIds;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	float SongPowerMultiplier = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	float RecoveryMultiplier = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike", meta=(ClampMin="0.0", ClampMax="100.0"))
	float Dissonance = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	bool bSirMelodiousAvailable = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") EMelodiaRunLifecyclePhase LifecyclePhase = EMelodiaRunLifecyclePhase::Inactive;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bStructuredMode = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bEndlessMode = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 EndlessDepth = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StructuredActCount = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 StructuredStagesPerAct = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bCompanionPresent = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bResonanceAvailable = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") bool bCompanionPlayable = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike") int32 CompanionBond = 0;

	UFUNCTION(BlueprintPure, Category="Melodia|Roguelike")
	FMelodiaRunSnapshot ExportSnapshot() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ImportSnapshot(const FMelodiaRunSnapshot& Snapshot);

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 HeartMelodyTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 HeartMelodyTokensConsumed = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 SwirlMelodyTokens = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	int32 SwirlMelodyTokensConsumed = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike", meta=(ClampMin="2"))
	int32 StagesPerDungeon = 3;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike|Archetype")
	TObjectPtr<class UMelodiaRunArchetypeDefinition> ResolvedArchetype;

private:
	void SetPhase(EMelodiaRunPhase NewPhase);
	void BuildCurrentStage();
	void BuildRewardCandidates();
	void ResetTransientRunState(int32 Seed);
	void SetLifecyclePhase(EMelodiaRunLifecyclePhase NewPhase);
	static int32 DeriveSeed(int32 Seed, int32 StageIndex, uint32 Salt);
	FRandomStream RandomStream;
	bool bEncounterResultRecorded = false;
	bool bRewardCommitted = false;
	bool bFallbackRecipeActive = false;
};
