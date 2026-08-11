#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaQuantumDrawSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaRhythmSkillDefinition;
class IHttpRequest;

/** One weighted-draw candidate, mirroring the service contract. */
USTRUCT(BlueprintType)
struct FMelodiaDrawCandidate
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Quantum Draw")
	FName Id = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Quantum Draw", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Difficulty = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Quantum Draw", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Spacing = 0.5f;
};

DECLARE_DYNAMIC_DELEGATE_ThreeParams(FMelodiaDrawCompleted, FName, WinnerId, FString, Backend, bool, bSuccess);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FMelodiaDrawBroadcast, FName, WinnerId, FString, Backend, bool, bSuccess);

/**
 * "The library chooses your song."
 *
 * GameInstance-scoped async client for the Melodia draw service
 * (http://127.0.0.1:8008/rank_layouts, python service.py). At battle start it
 * draws which chart from each skill's song asset plays this battle, and latches
 * the result into UMelodiaRhythmCombatSubsystem before any session starts.
 *
	 * The draw is strictly asynchronous: FHttpModule completes on the game thread,
	 * a timer covers the dead-service case, and song draws are serialized through
	 * an explicit queue so each skill keeps its own seed and identity. Generation
	 * tokens reject late HTTP callbacks after timeout, cancellation, or teardown.
 */
UCLASS()
class BS_GODFILE_API UMelodiaQuantumDrawSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * POST one draw request to the service and report the winner.
	 * Never blocks; OnCompleted fires on the game thread (or after the
	 * configured timeout with bSuccess=false when the service is unreachable).
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Quantum Draw")
	void RequestDraw(int32 Seed, const TArray<FMelodiaDrawCandidate>& Candidates, const FString& Provider, FMelodiaDrawCompleted OnCompleted);

	/**
	 * Draw one song chart per skill song asset (deduped by asset) and latch the
	 * winners into the rhythm subsystem. Called from OnBattleRequested; exposed
	 * so Blueprint/QuillScript can re-draw mid-battle.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Quantum Draw")
	void DrawSongsForBattle(FName EncounterId);

	UFUNCTION(BlueprintPure, Category = "Melodia|Quantum Draw")
	bool IsDrawInFlight() const { return bDrawInFlight; }

	/** Fired for every completed draw (success or fallback), for UI/QuillScript. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Quantum Draw")
	FMelodiaDrawBroadcast OnDrawCompleted;

private:
	/**
	 * Publish the finished draw into MPC_Melodia_Palette.
	 *
	 * MelodiaWaterNiagaraBridgeComponent reads QuantumChoice, QuantumSeed,
	 * QuantumBackend, QuantumPulse and QuantumReactionColor off that collection,
	 * and early-outs when QuantumPulse is below its threshold. This subsystem is
	 * the sole runtime MPC writer; editor Python tooling is preview-only and the
	 * Water bridge only consumes the resulting values.
	 *
	 * Every value published here is derived from the draw, never invented:
	 *   QuantumChoice  normalized winner index (the bridge computes 1 - Choice,
	 *                  so this must be 0..1, NOT a raw chart index)
	 *   QuantumSeed    the seed actually sent to the service, normalized
	 *   QuantumBackend 1 when a real quantum backend answered, 0 for the
	 *                  classical baseline or a timeout
	 *   QuantumPulse   1 on a successful draw, then decayed
	 *   QuantumReactionColor  the winning skill's authored LaneColor
	 */
	void PublishQuantumPresentation(FName WinnerId, const FString& Backend, bool bSuccess);

	/** Writes the currently latched values. Safe to call every tick. */
	void WriteQuantumParameters();

	/**
	 * Decays QuantumPulse at the same 3.5/sec used by RhythmPulse, so a draw
	 * reads as a moment rather than latching the exotic layer on permanently --
	 * which is the whole point of reserving it for meaningful draws.
	 */
	bool TickQuantumPulse(float DeltaTime);

	UFUNCTION()
	void HandleBattleRequested(FName EncounterId);

	UFUNCTION()
	void HandleSongDrawCompleted(FName WinnerId, FString Backend, bool bSuccess);

	/** Build chart-derived candidates for one skill and POST the draw. */
	void RequestSongDraw(const UMelodiaRhythmSkillDefinition* Skill);

	/** Shared completion path: cancels the timeout, broadcasts, clears in-flight. */
	void FinalizeDraw(uint64 RequestGeneration, FName WinnerId, const FString& Backend, bool bSuccess);

	/** Starts the next queued song draw after the active request completes. */
	void StartNextSongDraw();

	/** Cancels the active request and invalidates late callbacks. */
	void CancelActiveDraw();

	struct FQueuedSongDraw
	{
		FName SkillId = NAME_None;
		int32 Seed = 0;
		TArray<FMelodiaDrawCandidate> Candidates;
		FString Provider;
	};

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaNarrativeSubsystem> NarrativeSubsystem;

	/** Skill IDs a draw is currently in flight for (one per skill, one per asset per battle). */
	TSet<FName> DrawnAssetsThisBattle;

	FTimerHandle TimeoutHandle;
	TSharedPtr<IHttpRequest> ActiveRequest;
	FMelodiaDrawCompleted PendingCallback;
	FName PendingSkillId = NAME_None;
	bool bDrawInFlight = false;
	bool bProcessingSongDrawQueue = false;
	uint64 NextRequestGeneration = 0;
	uint64 ActiveRequestGeneration = 0;
	TArray<FQueuedSongDraw> PendingSongDraws;

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> QuantumParameterCollection;

	FTSTicker::FDelegateHandle QuantumTickerHandle;

	/** Seed and candidate count of the in-flight draw, kept so the published
	 *  QuantumSeed/QuantumChoice describe the draw that actually happened. */
	int32 LastDrawSeed = 0;
	int32 LastCandidateCount = 0;

	float QuantumPulse = 0.0f;
	float LastQuantumChoice = 0.0f;
	float LastQuantumSeedNormalized = 0.0f;
	float LastQuantumBackend = 0.0f;
	FLinearColor LastQuantumReactionColor = FLinearColor::White;
};
