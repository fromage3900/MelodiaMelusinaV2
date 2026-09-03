#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaCymaticsSubsystem.generated.h"

/**
 * Cymatics — audio → geometric standing-wave patterns (READ-ONLY driver).
 *
 * Implements the "audio-driven geometry" concept (Trench Sweep III Test E) and
 * the cymatics/synesthesia thread of MELODIA_AUDIO_VISUAL_SYNESTHESIA_LAYER.
 *
 * This is NOT an audio writer. It READS the MPC_Melodia_Palette values already
 * published by UMelodiaAudioReactivePresentationSubsystem (BeatPulse, BeatIntensity,
 * BassIntensity, MidIntensity) and converts them into a Chladni standing-wave pattern
 * on a virtual plate — audio → shape. Consumers (materials via WPO, Niagara particle
 * placement, static-mesh vertex offset) sample this read-only contract.
 *
 * Guardrails: presentation-only, read-only, no second writer, no new audio authority,
 * no Content/_PROJECT/ writes. Chladni: amp = cos(n·π·x/L)·cos(m·π·y/L) − cos(m·π·x/L)·cos(n·π·y/L)
 * where the mode indices (n,m) are driven by the audio bands.
 */
UCLASS()
class BS_GODFILE_API UMelodiaCymaticsSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Sample the Chladni standing-wave amplitude at normalized plate coords (u,v in [0,1]). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	float SampleCymaticAmplitude(float U, float V) const;

	/** Current Chladni mode indices driven by the audio bands (n,m). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	void GetCymaticMode(int32& OutN, int32& OutM) const;

	/** Beat pulse 0..1 (mirror of MPC BeatPulse) for pattern intensity. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	float GetBeatPulse() const;

	/** Bass band 0..1 (drives radial mode growth) — the "BassIntensity" read. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	float GetBassIntensity() const;

	/** Assert read-only contract: never writes MPC, never owns audio. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	bool IsReadOnlyByContract() const { return true; }

private:
	bool TickCymatics(float DeltaTime);
	void RefreshFromMPC();

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> AudioParameterCollection;

	int32 ModeN = 2;   // Chladni mode along X
	int32 ModeM = 3;   // Chladni mode along Y
	float BeatPulse = 0.f;
	float BassIntensity = 0.f;
	FTSTicker::FDelegateHandle TickerHandle;
};
