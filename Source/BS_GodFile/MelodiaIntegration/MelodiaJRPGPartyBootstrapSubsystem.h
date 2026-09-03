#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaJRPGPartyBootstrapSubsystem.generated.h"

/**
 * One-way integration adapter: seeds Melusina through the stock JRPG controller's
 * AddPlayerUnit API.  It deliberately owns neither turn flow nor party state.
 */
UCLASS()
class BS_GODFILE_API UMelodiaJRPGPartyBootstrapSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * Adds the authored Sir unit through the stock controller's AddPlayerUnit
	 * contract. The call is idempotent and unlocks exploration flight only after
	 * the stock party accepts the unit.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|Party")
	bool RecruitSirMelodiousThroughStockParty();

private:
	void HandlePostLoadMap(UWorld* LoadedWorld);
	void SeedOnNextTick();
	bool TrySeedPresentationUnit();
	void TryRecruitSirMelodious();

	UFUNCTION()
	void HandleOpeningPhaseChanged(EMelodiaOpeningPhase NewPhase, EMelodiaOpeningPhase PreviousPhase);

	/**
	 * Lane A4. The slice has no dungeon run, so the MorningIntro completion flag is
	 * what stands in for "first dungeon cleared" and triggers Sir's rescue.
	 *
	 * The only other caller of NotifySirRescued() is MelodiaDungeonRunCoordinator,
	 * and no map places that actor -- so without this hook Sir is never recruited,
	 * bSirMelodiousExplorationUnlocked stays false, and Ctrl-switching to him can
	 * never work however correct the party code is.
	 *
	 * NotifySirRescued() is STRICT: it returns false unless Phase is already
	 * FirstDungeonUnlocked, cannot repeat, and fails after ReturnedHome
	 * (MelodiaCoreRulesTests.cpp:415-426). This handler therefore reports the
	 * refusal and the phase it saw rather than calling and discarding the result --
	 * a silent no-op here is exactly the failure this project keeps paying for.
	 */
	UFUNCTION()
	void HandleNarrativeFlagChanged(FName FlagId, bool bValue);

	bool bSeededForCurrentWorld = false;
	FDelegateHandle PostLoadMapHandle;
};
