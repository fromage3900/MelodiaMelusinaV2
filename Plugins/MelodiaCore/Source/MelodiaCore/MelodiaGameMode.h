// Melodia game mode ΓÇö bootstraps HUD, input binding, and battle session for rhythm combat.
// Simplified from MelodiaMelusina_PROD's 363-line MelodiaRhythmGameModeBase.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaGameMode.generated.h"

class UMelodiaRhythmHUDWidget;
class UMelodiaBattleResultsWidget;
class UMelodiaBattleInputComponent;

UENUM(BlueprintType)
enum class EMelodiaLoopPhase : uint8
{
	Bootstrapping UMETA(DisplayName="Bootstrapping"),
	Exploration UMETA(DisplayName="Exploration"),
	Battle UMETA(DisplayName="Battle"),
	VictoryReward UMETA(DisplayName="Victory Reward")
};

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (competing game mode). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API AMelodiaGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMelodiaGameMode();

	/** Default BPM for battle music. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Game Mode")
	float DefaultBattleBPM = 128.0f;

	/** HUD widget class to spawn. Must be a UMelodiaRhythmHUDWidget subclass. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Game Mode")
	TSubclassOf<UMelodiaRhythmHUDWidget> HUDWidgetClass;

	/** Results presentation class; gameplay results remain owned by MelodiaBattleSession. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Game Mode")
	TSubclassOf<UMelodiaBattleResultsWidget> BattleResultsWidgetClass;

	/** When true, battles use instant skill resolution (HSR-style). When false, uses rhythm highway. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Game Mode")
	bool bHSRStyleBattle = false;

	/** When true, battle can also use the rhythm note highway for skill execution. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Game Mode")
	bool bUseRhythmHighway = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Game Mode")
	EMelodiaLoopPhase CurrentLoopPhase = EMelodiaLoopPhase::Bootstrapping;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Game Mode")
	TObjectPtr<UMelodiaRhythmHUDWidget> ActiveHUDWidget = nullptr;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Game Mode")
	TObjectPtr<UMelodiaBattleResultsWidget> ActiveBattleResultsWidget = nullptr;

	UFUNCTION(BlueprintCallable, Category="Melodia|Game Mode")
	void SetLoopPhase(EMelodiaLoopPhase NewPhase);

	UFUNCTION(BlueprintCallable, Category="Melodia|Game Mode")
	void SpawnBattleHUD();

	UFUNCTION(BlueprintCallable, Category="Melodia|Game Mode")
	void RemoveBattleHUD();

protected:
	virtual void BeginPlay() override;
	virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;

private:
	void Bootstrap();
	void BindBattleSession();
	UFUNCTION()
	void OnBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase);
	UFUNCTION()
	void OnEncounterEnded(EMelodiaEncounterResult Result);

	UPROPERTY()
	TObjectPtr<UMelodiaBattleInputComponent> InputComponentRef = nullptr;
};
