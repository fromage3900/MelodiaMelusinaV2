#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaPartySubsystem.generated.h"

class APawn;
class APlayerController;

/**
 * Owns the explore-mode party roster and Ctrl-cycling between members
 * (Melusina ground/glide <-> Sir Melodious flight). Pawns are spawned
 * lazily and parked (hidden, no collision, anims paused) while inactive
 * so their state survives swaps.
 */
UCLASS()
class MELODIACORE_API UMelodiaPartySubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static UMelodiaPartySubsystem* Get(const UObject* WorldContext);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Ordered roster; index 0 is the default (Melusina). Set once at startup or from BP. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Party")
	TArray<TSoftClassPtr<APawn>> PartyPawnClasses;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Party")
	int32 ActiveIndex = 0;

	/** A pawn announces itself as roster member Index (e.g. the level-placed Melusina). */
	UFUNCTION(BlueprintCallable, Category="Melodia|Party")
	void RegisterPawn(APawn* Pawn, int32 Index);

	UFUNCTION(BlueprintCallable, Category="Melodia|Party")
	void SwitchToNext(APlayerController* PC);

	/**
	 * Presentation-side acknowledgement that the stock JRPG party has recruited
	 * Sir Melodious. This never changes the combat roster itself; it only opens
	 * the already-authored exploration possession handoff.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Party")
	void SetSirMelodiousExplorationUnlocked(bool bUnlocked);

	UFUNCTION(BlueprintPure, Category="Melodia|Party")
	bool IsSirMelodiousExplorationUnlocked() const { return bSirMelodiousExplorationUnlocked; }

	UFUNCTION(BlueprintPure, Category="Melodia|Party")
	APawn* GetActivePawn() const;

	/** Restore hook for the save subsystem. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Party")
	void SetActiveIndex(int32 NewIndex, APlayerController* PC);

private:
	UPROPERTY()
	TArray<TObjectPtr<APawn>> SpawnedPawns;

	/** False until the stock JRPG controller accepts Sir into its party. */
	bool bSirMelodiousExplorationUnlocked = false;

	APawn* EnsurePawn(int32 Index, const FTransform& SpawnAt);
	static void ParkPawn(APawn* Pawn, bool bParked);
};
