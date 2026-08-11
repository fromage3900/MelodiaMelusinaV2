#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaJRPGBattleOverlaySubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaBattleKeyboardLegendWidget;
class UUserWidget;

/**
 * Presentation-only owner for the standalone Melodia rhythm prompt.
 * Observes narrative battle lifecycle events without changing stock JRPG HUD,
 * input, focus, combat mechanics, or turn flow.
 */
UCLASS()
class BS_GODFILE_API UMelodiaJRPGBattleOverlaySubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	UFUNCTION()
	void HandleBattleRequested(FName EncounterId);

	UFUNCTION()
	void HandleBattleCompleted(FName EncounterId, EMelodiaBattleResult Result);

	UFUNCTION()
	void HandleBattleAborted(FName EncounterId, FString Reason);

	void RemoveRhythmPrompt();
	void RemoveKeyboardLegend();

	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> RhythmPrompt;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaBattleKeyboardLegendWidget> KeyboardLegend;
};
