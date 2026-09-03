#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaSharedAuthorityInterfaces.h"
#include "MelodiaTravelSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaTravelStarted, FName, LevelId, FName, SpawnTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaTravelArrived, FName, LevelId, bool, bPlacedAtSpawn);

/**
 * The project's single travel authority.
 *
 * Before this existed, travel happened four different ways: RequestTravel (validated
 * but with no consumer), UMelodiaMapTransitionComponent (unvalidated, and calling
 * LoadStreamLevel on a standalone map, which cannot work), UMelodiaSaveSlotLibrary
 * (hardcoded OpenLevel), and literal map strings in Blueprint travel nodes. None of
 * them placed the player deliberately on arrival, so the destination PlayerStart was
 * whatever the engine happened to pick first -- a coin flip on any map with more than
 * one, which KaleidoNave has four of.
 *
 * Everything now routes through TravelTo(). It validates against the narrative
 * allowlist, records where to arrive, performs the travel, and places the pawn on the
 * far side.
 *
 * This is a GameInstance subsystem deliberately: it must outlive the level transition
 * it is performing.
 *
 * AUTHORITY: travel only. It does not own save, battle, quest, or party state. The
 * spawn tag is persisted through FMelodiaNarrativeRecord::SpawnContext, the project's
 * single persistence seam -- not in a member of this class.
 *
 * Implements IMelodiaTravelProvider and registers with UMelodiaAuthorityLocator
 * (MelodiaCore) on Initialize() so MelodiaCore's native C++ -- which cannot depend
 * on this module directly -- can reach TravelTo without a circular module dependency.
 */
UCLASS()
class BS_GODFILE_API UMelodiaTravelSubsystem final : public UGameInstanceSubsystem, public IMelodiaTravelProvider
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Travel", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaTravelSubsystem* Get(const UObject* WorldContextObject);

	/**
	 * The one way to travel. Every teleport source -- overlap volume, Quill intent,
	 * Orrery UI, dialogue choice, menu -- should call this and nothing else.
	 *
	 * @param LevelId   Must be present in UMelodiaIntegrationConfig::TravelLevelIds.
	 *                  Accepts a full /Game/ path or a short map name.
	 * @param SpawnTag  PlayerStart to arrive at. Matched against the actor's
	 *                  PlayerStartTag first, then its Tags array. NAME_None leaves
	 *                  placement to the engine, which is the old behaviour.
	 *
	 * @return false when the ID is not allowlisted or no world is available. A false
	 *         return means no travel happened -- callers must not assume success.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Travel")
	virtual bool TravelTo(FName LevelId, FName SpawnTag) override;

	/** Where the player will be placed on arrival at MapId, or None. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Travel")
	virtual FName GetPendingSpawnTag(FName MapId) const override;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Travel")
	FMelodiaTravelStarted OnTravelStarted;

	/** bPlacedAtSpawn is false when no tag was set or no matching PlayerStart existed. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Travel")
	FMelodiaTravelArrived OnTravelArrived;

private:
	/** Narrative broadcasts this after allowlist validation; we are its only consumer. */
	UFUNCTION()
	void HandleTravelRequested(FName LevelId);

	void HandlePostLoadMap(UWorld* LoadedWorld);

	/** Returns true only if a matching PlayerStart was found and the pawn moved. */
	bool PlacePawnAtSpawn(UWorld* World, FName SpawnTag) const;

	UMelodiaNarrativeSubsystem* GetNarrative() const;

	FDelegateHandle PostLoadMapHandle;

	/** The destination currently in flight, used to look up its spawn tag on arrival. */
	FName TravellingToLevelId;
};
