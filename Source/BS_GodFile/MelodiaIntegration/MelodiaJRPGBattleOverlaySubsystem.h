#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaJRPGBattleOverlaySubsystem.generated.h"

class UMelodiaNarrativeSubsystem;

/**
 * Retired presentation observer for the standalone Melodia rhythm prompt.
 *
 * UMelodiaUIBridgeSubsystem is the sole owner of battle-time Melodia widgets.
 * This subsystem remains as a compatibility observer for existing subsystem
 * construction and event wiring, but it must not create viewport widgets.
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

};
