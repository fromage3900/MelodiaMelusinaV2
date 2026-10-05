#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaPCGResonanceSensorComponent.generated.h"

class UMelodiaHarmonicStateSubsystem;

/**
 * PCG awareness sensor: measures how much resonant PCG content sits near the listener
 * and feeds that back into the harmonic state spine, so the ambience/field picture
 * thickens near dense cymatic PCG and thins in the open.
 *
 * Direction of data flow (presentation only, no audio or gameplay authority):
 *   this component (counts tagged ISM instances near the player/owner)
 *     -> UMelodiaHarmonicStateSubsystem::SetPCGResonanceDensity (sole MPC writer)
 *     -> MPC_Melodia_HarmonicState.PCG_ResonanceDensity
 *   this component ALSO registers the owner as a spatial UWorldFieldBus field source,
 *   so UWorldFieldBus::SampleAt() returns a local PCG-aware register for materials,
 *   PCG and water within ReactRadius.
 *
 * Counting is a slow rescan (RescanIntervalSec), not a per-frame scan, so a dense
 * PCG scatter costs almost nothing at runtime.
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaPCGResonanceSensorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaPCGResonanceSensorComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Local PCG resonance density (0..1), eased. */
	UFUNCTION(BlueprintPure, Category = "Melodia|PCG Resonance")
	float GetPCGResonanceDensity() const { return Density; }

	/** ISM components (or their actors) carrying this tag count toward the local density. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|PCG Resonance|Targets")
	FName ResonantTag = TEXT("MelodiaCymatic");

	/** Count instances within this radius (cm) of the sample point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|PCG Resonance|Targets", meta = (ClampMin = "100"))
	float DensityRadiusCm = 8000.0f;

	/** Instance count that maps to density 1.0 (anything more clamps). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|PCG Resonance|Targets", meta = (ClampMin = "1"))
	int32 DensityFullCount = 400;

	/** How often the instance scan re-runs (seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|PCG Resonance|Performance", meta = (ClampMin = "0.5"))
	float RescanIntervalSec = 3.0f;

	/** Sample point: the player pawn when present, otherwise the owning actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|PCG Resonance|Targets")
	bool bSamplePlayer = true;

private:
	void Rescan();
	void UpdateFieldSource();

	float Density = 0.0f;
	float RescanTimer = 0.0f;
	int32 FieldSourceId = 0;
	FVector LastSamplePoint = FVector::ZeroVector;

	TWeakObjectPtr<UMelodiaHarmonicStateSubsystem> HarmonicState;
};
