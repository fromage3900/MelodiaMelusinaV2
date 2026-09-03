#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterFluidZoneComponent.generated.h"

class UMelodiaWaterInteractionSubsystem;

/**
 * Opt-in local height-field prototype for an authored water zone.
 *
 * This is deliberately a bounded CPU reference path: it makes the impulse
 * contract observable and deterministic before a Niagara Shallow Water or
 * 2D FLIP asset is promoted. The visual material bridge remains the cheap
 * fallback; this component is only for active hero/interaction zones.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterFluidZoneComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterFluidZoneComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category="Melodia|Water|Fluid")
	void ResetSimulation();

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Fluid")
	float GetNormalizedEnergy() const { return NormalizedEnergy; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Fluid")
	float GetPeakHeight() const { return PeakHeight; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Fluid")
	float GetHeightAtWorldLocation(const FVector& WorldLocation) const;

protected:
	UFUNCTION()
	void HandleFluidImpulse(FMelodiaWaterFluidImpulse Impulse);

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	bool bEnabled = true;

	/** The zone accepts requests up to this tier and can downgrade higher asks. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	EMelodiaWaterSimulationTier SimulationTier = EMelodiaWaterSimulationTier::ShallowWater2D;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	bool bAllowTierDowngrade = true;

	/** None accepts impulses from any water body; otherwise use the Water Body actor name. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	FName WaterBodyId = NAME_None;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="4", ClampMax="128"))
	FIntPoint GridResolution = FIntPoint(32, 32);

	/** Half extent of the local simulation tile in centimeters. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="50.0"))
	FVector2D LocalHalfExtent = FVector2D(1000.0f, 1000.0f);

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="0.001", ClampMax="0.1"))
	float FixedStepSeconds = 1.0f / 30.0f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="1", ClampMax="4"))
	int32 MaxSubstepsPerFrame = 2;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="0.1", ClampMax="50.0"))
	float WaveSpeed = 7.0f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="0.0", ClampMax="10.0"))
	float HeightDamping = 1.5f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="0.0", ClampMax="100.0"))
	float MaxHeight = 30.0f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid", meta=(ClampMin="0.0", ClampMax="10.0"))
	float ImpulseGain = 1.0f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	bool bWriteMaterialTelemetry = true;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	FName FluidEnergyParameter = TEXT("FluidEnergy");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	FName FluidPeakParameter = TEXT("FluidPeak");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Fluid")
	FName FluidCenterParameter = TEXT("FluidCenter");

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

private:
	int32 GetCellIndex(int32 X, int32 Y) const;
	bool WorldToCell(const FVector& WorldLocation, int32& OutX, int32& OutY) const;
	FVector CellToWorld(int32 X, int32 Y) const;
	void StepSimulation(float StepSeconds);
	void UpdateTelemetry();
	void WriteMaterialTelemetry();
	bool AcceptsTier(EMelodiaWaterSimulationTier RequestedTier) const;

	TArray<float> Heights;
	TArray<float> Velocities;
	float Accumulator = 0.0f;
	float NormalizedEnergy = 0.0f;
	float PeakHeight = 0.0f;
	FVector StrongestWorldLocation = FVector::ZeroVector;
};
