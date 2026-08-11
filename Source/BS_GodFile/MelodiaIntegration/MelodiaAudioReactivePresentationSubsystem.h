#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaBattleSession.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaAudioReactivePresentationSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaExternalJRPGBridgeSubsystem;
class UMaterialParameterCollection;
class UMelodiaInputContextSubsystem;

/**
 * Presentation-only music-to-visual bridge. Publishes existing
 * MPC_Melodia_Palette values; it never owns combat, gameplay audio, or input.
 */
UCLASS()
class BS_GODFILE_API UMelodiaAudioReactivePresentationSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Call from an authored impact notify to create a brief visual-only pulse. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Presentation|Audio Reactive")
	void PulseImpact(float Strength = 1.0f);

	UFUNCTION(BlueprintPure, Category = "Melodia|Presentation|Audio Reactive")
	bool IsPresentationBattleActive() const { return bBattleActive; }

	void PushBattleInputContext();
	void PopBattleInputContext();

private:
	// These are dynamic multicast delegate targets.  UFUNCTION is required by
	// AddUniqueDynamic; without it UE asserts during subsystem initialization.
	UFUNCTION()
	void HandleNarrativeBattleRequested(FName EncounterId);
	UFUNCTION()
	void HandleNarrativeBattleEnded(FName EncounterId, EMelodiaBattleResult Result);
	UFUNCTION()
	void HandleNarrativeBattleAborted(FName EncounterId, FString Reason);
	UFUNCTION()
	void HandleExternalBattleStarted(FName EncounterId);
	UFUNCTION()
	void HandleExternalBattleEnded(uint8 BattleResult);
	UFUNCTION()
	void HandleMelodiaBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase);
	bool TickPresentation(float DeltaTime);
	void SetBattleActive(bool bActive, float Intensity);

	TObjectPtr<UMelodiaNarrativeSubsystem> NarrativeSubsystem;
	TObjectPtr<UMelodiaBattleSession> BattleSession;
	TObjectPtr<UMelodiaExternalJRPGBridgeSubsystem> ExternalBridge;
	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> AudioParameterCollection;
	FTSTicker::FDelegateHandle TickerHandle;
	FMelodiaInputContextHandle BattleContextHandle;
	bool bBattleActive = false;
	float BattleIntensity = 0.0f;
	float ImpactPulse = 0.0f;

	/** Previous frame's beat phase; a decrease means the beat wrapped. */
	float LastBeatPhase = 0.0f;

	/** BPM reported to the reactivity subsystem and on to TouchDesigner. Seeded at
	 *  the source music's 128, then overwritten every tick from the music clock's
	 *  real tempo once musical time is live -- so this is a starting value, not a
	 *  second authority. */
	float LastKnownBPM = 128.0f;
};
