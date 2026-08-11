#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaPacingSubsystem.generated.h"

class UMelodiaPacingProfile;

/**
 * The project's pacing authority -- resolves an authored duration/delay by a
 * stable FName ID against an optional UMelodiaPacingProfile.
 *
 * Native to MelodiaCore, not behind the authority-locator interface layer:
 * every current consumer (MelodiaSirMelodiousIntroActor, MelodiaBattleSession,
 * MelodiaBattleArena, MelodiaExplorationActors) already lives in this module,
 * so there is no cross-module problem to solve here.
 *
 * DEGRADE GRACEFULLY, NEVER INVENT A VALUE: if no profile is set, or the ID
 * isn't in it, ResolveDuration returns false and leaves OutValue untouched --
 * same contract as UMelodiaMusicClockSubsystem::HasMusicalTime(). Callers
 * must keep their own EditAnywhere default and use it on a false return; this
 * subsystem is additive polish, never a hard dependency for a value to exist.
 *
 * Scope note (2026-07-31): migrated consumers -- MelodiaSirMelodiousIntroActor
 * (departure delay/duration), MelodiaBattleSession (staged enemy-turn windows),
 * MelodiaBattleArena (break-dolly / hitstop), MelodiaExplorationActors
 * (platform travel duration). Each keeps its authored EditAnywhere default and
 * resolves the same FName ID; a false return leaves the default untouched.
 */
UCLASS()
class MELODIACORE_API UMelodiaPacingSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Loads the project's DA_MelodiaPacingProfile (if present) and sets it active.
	 * Mirrors UMelodiaPartySubsystem::Initialize: a hard-coded project asset path,
	 * degrade-gracefully when the asset is missing. */
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Pacing", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaPacingSubsystem* Get(const UObject* WorldContextObject);

	/** Sets the active profile. Callers fall back to their own EditAnywhere default
	 * whenever no profile is set or the ID is absent (false return), so this is
	 * additive polish, never a hard dependency. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Pacing")
	void SetActiveProfile(UMelodiaPacingProfile* InProfile);

	/** @return false (OutValue untouched) if no profile is set or DurationId isn't in it. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Pacing")
	bool ResolveDuration(FName DurationId, float& OutValue) const;

private:
	UPROPERTY()
	TObjectPtr<UMelodiaPacingProfile> ActiveProfile;
};
