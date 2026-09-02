#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaCymaticsWriterSubsystem.generated.h"

/**
 * Single writer for MPC_Cymatics_Driver.
 *
 * Contract:
 * - UMelodiaCymaticsSubsystem is READ-ONLY (IsReadOnlyByContract=true). It READS
 *   MPC_Melodia_Palette and exposes Chladni sampling. It NEVER writes.
 * - This subsystem is the SOLE writer of MPC_Cymatics_Driver. It reads the
 *   canonical audio beat/bands from MPC_Melodia_Palette (published by
 *   UMelodiaAudioReactivePresentationSubsystem) and from the music clock, maps
 *   them to cymatic material params, and publishes to MPC_Cymatics_Driver.
 * - Materials (MI_Copernicus_* and MI_FarawayMother_*) sample MPC_Cymatics_Driver
 *   for IridescenceTint / EmissiveScale / UV distortion. No second writer exists.
 *
 * Parameter contract on MPC_Cymatics_Driver (all scalars):
 *   Cymatic_BeatPulse          0..1  BeatPulse driven by music clock (cos^2)
 *   Cymatic_BassIntensity      0..1  Bass band from MPC_Melodia_Palette
 *   Cymatic_MidIntensity       0..1  Mid band (derived / placeholder from palette)
 *   Cymatic_EmissiveScale      scalar for emissive pulse (BeatPulse -> emissive)
 *   Cymatic_IridescenceShift   scalar hue-shift for iridescence tint (Bass-driven)
 *   Cymatic_UVDistortion       0..0.1 UV warble strength (BeatPulse * 0.08)
 *   Cymatic_ModeN              1..8  Chladni N (Bass-driven)
 *   Cymatic_ModeM              1..8  Chladni M (BeatPulse-driven)
 */
UCLASS()
class BS_GODFILE_API UMelodiaCymaticsWriterSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Returns true if this is the single writer (always). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Cymatics")
	bool IsSingleWriter() const { return true; }

private:
	bool TickWriter(float DeltaTime);
	void RefreshAndPublish();

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> SourcePalette; // MPC_Melodia_Palette (read)

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> DriverCollection; // MPC_Cymatics_Driver (write)

	FTSTicker::FDelegateHandle TickerHandle;
};
