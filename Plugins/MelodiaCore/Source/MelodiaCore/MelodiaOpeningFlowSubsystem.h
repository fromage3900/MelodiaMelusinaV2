#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaOpeningFlowSubsystem.generated.h"

UENUM(BlueprintType)
enum class EMelodiaOpeningPhase : uint8
{
	NotStarted UMETA(DisplayName="Not Started"),
	Morning UMETA(DisplayName="Melusina's Morning"),
	SirDeparted UMETA(DisplayName="Sir Melodious Departed"),
	Dreamstate UMETA(DisplayName="Dreamstate"),
	ZenExploration UMETA(DisplayName="Zen Forest Exploration"),
	FirstDungeonUnlocked UMETA(DisplayName="First Dungeon Unlocked"),
	SirRescued UMETA(DisplayName="Sir Melodious Rescued"),
	ReturnedHome UMETA(DisplayName="Returned Home")
};

UENUM(BlueprintType)
enum class EMelodiaOpeningTravelEvent : uint8
{
	None UMETA(DisplayName="None"),
	EnterDreamstate UMETA(DisplayName="Enter Dreamstate"),
	CompleteDreamstate UMETA(DisplayName="Complete Dreamstate")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaOpeningPhaseChanged, EMelodiaOpeningPhase, NewPhase, EMelodiaOpeningPhase, PreviousPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FMelodiaFirstDungeonUnlocked);

/** Persistent authority for the authored bedroom -> Dreamstate -> Zen opening. */
UCLASS()
class MELODIACORE_API UMelodiaOpeningFlowSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Opening", meta=(WorldContext="WorldContextObject"))
	static UMelodiaOpeningFlowSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool BeginMorning();

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifySirDeparted();

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifyDreamstateEntered();

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifyDreamstateCompleted();

	/** Unlocks once, and only for the authored Zen tutorial encounter. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifyZenEncounterVictory(FName EnemyId);

	/** Sir Melodious rescued at the end of the first dungeon run. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifySirRescued();

	/** Player has traveled back to the bedroom/hub after the rescue, closing the opening loop. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool NotifyReturnedHome();

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	bool ApplyTravelEvent(EMelodiaOpeningTravelEvent TravelEvent);

	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	void ResetOpening();

	/** Restores state from a loaded save, bypassing the gated TransitionTo sequence
	 * since a load can jump directly to any phase. Broadcasts OnPhaseChanged only
	 * if the phase actually changed. Call after the destination level's BeginPlay
	 * pass has already run (e.g. via a short deferred call after OpenLevel), not
	 * synchronously from another actor's BeginPlay, so BeginMorning()'s own
	 * NotStarted->Morning no-op guard cannot race the restored phase. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Opening")
	void RestoreFromSave(EMelodiaOpeningPhase InPhase, bool bInHeartMelodyTokenGranted);

	UFUNCTION(BlueprintPure, Category="Melodia|Opening")
	bool IsFirstDungeonUnlocked() const { return Phase == EMelodiaOpeningPhase::FirstDungeonUnlocked; }

	/**
	 * Records one bedroom exploration point as visited. Only meaningful during
	 * Morning; a no-op (and returns false) at any other phase so a stray overlap
	 * during Dreamstate or later cannot inflate the count. Idempotent per PointId
	 * so re-overlapping an already-visited point does not count twice.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Opening|Exploration")
	bool NotifyExplorationPointVisited(FName PointId);

	UFUNCTION(BlueprintPure, Category="Melodia|Opening|Exploration")
	int32 GetExplorationPointsVisited() const { return VisitedExplorationPointIds.Num(); }

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Opening")
	EMelodiaOpeningPhase Phase = EMelodiaOpeningPhase::NotStarted;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Opening")
	bool bHeartMelodyTokenGranted = false;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Opening")
	FMelodiaOpeningPhaseChanged OnPhaseChanged;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Opening")
	FMelodiaFirstDungeonUnlocked OnFirstDungeonUnlocked;

private:
	bool TransitionTo(EMelodiaOpeningPhase ExpectedPhase, EMelodiaOpeningPhase NewPhase);

	/** Bedroom exploration points visited this Morning, keyed by their authored
	 * PointId. Cleared on ResetOpening(); deliberately not cleared on ordinary
	 * phase transitions since Morning only occurs once per playthrough. */
	UPROPERTY()
	TSet<FName> VisitedExplorationPointIds;
};
