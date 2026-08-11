#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DungeonGeneratorBase.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaDungeonRunCoordinator.generated.h"

class AMelodiaRoomEntrance;
class AMelodiaRoomExit;
class UMelodiaBattleSession;
class UMelodiaRoguelikeRewardWidget;
class UMelodiaRoguelikePersistenceSubsystem;
struct FTimerHandle;

/** World bridge between streamed dungeon generation and persistent run state. */
// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (deferred roguelike). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API AMelodiaDungeonRunCoordinator : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaDungeonRunCoordinator();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike")
	TObjectPtr<ADungeonGeneratorBase> DungeonGenerator;

	/** The one doorway authorized to advance this run. Assign explicitly in authored maps. */
	UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Melodia|Roguelike")
	TObjectPtr<AMelodiaRoomExit> ActiveRoomExit;

	/** Optional authored fallback. Generated rooms should expose exactly one entrance after generation. */
	UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Melodia|Roguelike")
	TObjectPtr<AMelodiaRoomEntrance> ActiveRoomEntrance;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike")
	bool bStartRunOnBeginPlay = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike")
	int32 InitialRunSeed = 1337;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike")
	FVector SirMelodiousReunionOffset = FVector(650.0f, 0.0f, 120.0f);

	/** Fails a stage transition cleanly if ProceduralDungeon never reports completion. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety", meta=(ClampMin="5.0"))
	float GenerationTimeoutSeconds = 30.0f;

	/** Move the local player to the generated-room entrance after post-generation succeeds. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety")
	bool bRelocatePlayerAfterGeneration = true;

	/** Production generators must implement UMelodiaDungeonRecipeConsumer. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety")
	bool bRequireRecipeConsumer = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety", meta=(ClampMin="100.0"))
	float SafeGroundTraceDepth = 3000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety", meta=(ClampMin="0.0"))
	float SafeGroundClearance = 5.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Safety", meta=(ClampMin="0", ClampMax="1"))
	int32 MaxDeterministicFallbackAttempts = 1;

	/** GMM manifest pipeline target — populated by Content/Python/import_melodia_manifest.py. When unset, hardcoded pools are used. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Archetype")
	TSoftObjectPtr<class UMelodiaRunArchetypeDefinition> RunArchetype;

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool CommitReward(int32 CandidateIndex);

	/** Compatibility only. Reward commitment never advances the stage. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike", meta=(DeprecatedFunction, DeprecationMessage="Use CommitReward. Stage advancement belongs to the room exit."))
	bool CommitRewardAndAdvance(int32 CandidateIndex) { return CommitReward(CandidateIndex); }

	/** Called by the unlocked room exit after the player crosses it. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RequestNextStage();

	/** Starts the first generated stage after the authored opening unlocks it. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool StartFirstDungeonRun(int32 Seed = 1337);

	/** Accepts the existing endless offer and starts its first generated room. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool ContinueEndlessRun();

	/** Restarts the current seed after defeat and regenerates stage zero. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	bool RestartDungeonRun();

	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Roguelike")
	void PresentRewardChoices(const TArray<FMelodiaRunRewardCandidate>& Candidates);

	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Roguelike")
	void PresentDefeatSummary();

	UFUNCTION(BlueprintNativeEvent, Category="Melodia|Roguelike")
	void SetRoomExitLocked(bool bLocked);

	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Roguelike")
	void BeginStageTransition();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandleBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase);

	UFUNCTION()
	void HandleEncounterEnded(EMelodiaEncounterResult Result);

	UFUNCTION()
	void HandleRewardsReady(const TArray<FMelodiaRunRewardCandidate>& Candidates);

	UFUNCTION()
	void HandleGenerationComplete();

	UFUNCTION()
	void HandleGenerationFailed();

	void HandleGenerationTimeout();

	UFUNCTION()
	void HandleRunCompleted();

	UFUNCTION()
	void HandleRunDefeated();

	bool ResolveActiveRoomExit();
	bool ResolveActiveRoomEntrance(bool bLogFailure = true);
	bool BeginGenerationRequest();
	bool ApplyRecipeToGenerator();
	bool RelocatePlayerToSafeEntrance();
	bool IsAnyStreamedRoomPCGGenerating() const;
	bool IsActorInAuthoritativeRoom(const AActor* Actor) const;
	void SetPlayerTransitionLocked(bool bLocked);
	void CheckpointCurrentStage();
	UFUNCTION()
	void OnPersistenceOperation(FName Operation, bool bSuccess);
	bool ResolveArchetype();

	UPROPERTY()
	TObjectPtr<UMelodiaRoguelikeRunSubsystem> RunSubsystem;

	UPROPERTY()
	TObjectPtr<class UMelodiaRoguelikePersistenceSubsystem> Persistence;

	UPROPERTY()
	TObjectPtr<UMelodiaBattleSession> BattleSession;

	UPROPERTY()
	TObjectPtr<UMelodiaRoguelikeRewardWidget> RewardWidget;

	FTimerHandle GenerationTimeoutHandle;
	bool bGenerationRequestPending = false;
	bool bGenerationFailedThisAttempt = false;
	int32 GenerationAttemptId = 0;
	int32 FallbackStageIndex = INDEX_NONE;
	int32 FallbackAttemptsThisStage = 0;

	/** PCG-authored rooms generate their floor/environment asynchronously (PCGComponent has no
	 * synchronous blocking Generate()) -- these gate the post-streaming entrance/exit validation
	 * with a few short retries instead of failing on the first check while PCG is still running. */
	FTimerHandle EntranceValidationRetryHandle;
	int32 EntranceValidationRetryCount = 0;
	static constexpr int32 MaxEntranceValidationRetries = 8;
	static constexpr float EntranceValidationRetryDelaySeconds = 0.25f;
};
