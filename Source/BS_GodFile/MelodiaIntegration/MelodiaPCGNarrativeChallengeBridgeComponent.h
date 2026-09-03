#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "../Piano/PCGHeroMusic.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaPCGNarrativeChallengeBridgeComponent.generated.h"

class UMelodiaNarrativeSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
	FMelodiaWorldChallengeCommitted,
	FName, ChallengeId,
	EMelodiaContentCommitResult, Result);

/**
 * Music as key: commits a completed hero-music pattern as a world challenge.
 *
 * This is the "pending world challenge adapter" named by
 * specs/blueprints/fixtures/first_resonance_world_challenge.v1.json, whose
 * runtime_authority is UMelodiaNarrativeSubsystem and which had no implementation.
 *
 * The Piano module already produces a complete music-as-key loop -- PCG-spawned
 * keys, steppable note nodes, pattern scoring and OnPatternCompleted -- but its
 * only consumer was UMelodiaPCGWaterGameplayBridgeComponent, which routes it into
 * water state. Nothing carried a completed pattern into narrative, so playing a
 * phrase could never mean anything that survived a reload.
 *
 * Attach alongside the water bridge on an APCGHeroMusicGraphHost. The two are
 * independent consumers of the same event and do not interact: water gets a
 * physical reaction, narrative gets a canonical completion.
 *
 * BOUNDARIES (these are load-bearing, not stylistic):
 *
 *  - Music opens doors; it never deals damage. This component commits a flag and
 *    an allowlisted reward. It must never call battle, damage, turn or party
 *    APIs. PCGHeroMusic.cpp keeps the same boundary on the presentation side:
 *    "the existing reactivity subsystem ... never enters the combat or damage
 *    pipeline."
 *  - It never writes a save object directly. CommitWorldChallenge is the only
 *    canonical write path, per the fixture's
 *    adapter_must_not_write_save_object_directly.
 *  - Idempotency is the narrative record's job, not this component's. The
 *    CompletionIntentId is recorded in ConsumedIntentIds, so replaying the
 *    pattern re-commits harmlessly and cannot double-grant the reward. Do not
 *    add a local "already fired" bool -- that would be a second source of truth
 *    that a reload would silently disagree with.
 */
UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaPCGNarrativeChallengeBridgeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaPCGNarrativeChallengeBridgeComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/**
	 * Allowlisted world-challenge id. Must exist in WorldChallengeIds or the
	 * commit fails closed with UnknownChallenge.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	FName ChallengeId = TEXT("challenge.first_resonance_echo");

	/** Allowlisted narrative flag set on completion. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	FName CompletionFlagId = TEXT("challenge.first_resonance_echo.completed");

	/** Allowlisted reward granted once on first completion. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	FName RewardId = TEXT("reward.first_resonance_echo");

	/**
	 * Stable per-challenge intent id. Recorded in ConsumedIntentIds, which is
	 * SaveGame-flagged, so the burn survives a reload. Keep it stable across
	 * sessions -- changing it re-opens the reward.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	FName CompletionIntentId = TEXT("challenge.first_resonance_echo.attempt_id");

	/**
	 * When true, a pattern only commits if every judged note met
	 * MinimumAcceptedGrade. Default false: pattern completion alone is the key,
	 * which is the Zelda-ocarina reading -- you played it, the door opens.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	bool bRequireCleanRun = false;

	/** Only meaningful when bRequireCleanRun is true. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Music Key")
	EMelodiaRhythmGrade MinimumAcceptedGrade = EMelodiaRhythmGrade::Good;

	/** Presentation hook. Fires for every commit attempt, including AlreadyApplied. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Music Key")
	FMelodiaWorldChallengeCommitted OnChallengeCommitted;

	/** Re-attach to the owning hero-music host. Safe to call repeatedly. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Key")
	bool RebindToHost();

	/** Canonical completion state, read through the narrative record. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Key")
	bool IsChallengeCompleted() const;

	/** Result of the most recent commit attempt, for tests and presentation. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Key")
	EMelodiaContentCommitResult GetLastCommitResult() const { return LastCommitResult; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Music Key")
	EMelodiaContentCommitFailure GetLastCommitFailure() const { return LastCommitFailure; }

private:
	UFUNCTION()
	void HandleNoteJudged(FPCGHeroMusicNoteEvent Event);

	UFUNCTION()
	void HandlePatternCompleted();

	UMelodiaNarrativeSubsystem* GetNarrative() const;

	UPROPERTY(Transient)
	TWeakObjectPtr<APCGHeroMusicGraphHost> BoundHost;

	UPROPERTY(Transient)
	EMelodiaContentCommitResult LastCommitResult = EMelodiaContentCommitResult::Rejected;

	UPROPERTY(Transient)
	EMelodiaContentCommitFailure LastCommitFailure = EMelodiaContentCommitFailure::None;

	/** Cleared on every commit attempt, so a failed run does not poison the next. */
	bool bRunHadSubStandardNote = false;

	bool bBound = false;
};
