#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterNativeSimulationComponent.generated.h"

class AWaterZone;
class UMelodiaWaterInteractionSubsystem;
class UMelodiaWaterProfile;
class UWaterBodyComponent;

/**
 * Project-owned native Water orchestration point. The engine's authored
 * ShallowWaterSim/WaveFoam/force Blueprint components are assigned on the
 * placed zone actor and are invoked through typed packets here; no engine
 * plugin asset is modified or dynamically rewritten at runtime.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterNativeSimulationComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterNativeSimulationComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Native")
	bool IsNativeWaterReady() const { return bNativeWaterReady; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Native")
	FMelodiaWaterNativeLimits GetNativeLimits() const { return NativeLimits; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Native")
	bool IsWaterBodyBound(FName WaterBodyId) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Water|Native")
	void RefreshNativeWaterBinding();

	/** Configure the project-owned references to the engine Water fluid
	 * components from the active profile. The owning Blueprint calls this from
	 * its ConfigureEngineWaterComponents event. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Water|Native")
	void ConfigureAssignedEngineWaterComponents(UMelodiaWaterProfile* ProfileAsset);

	/** Route one already-budgeted packet to the authored engine Water fluid
	 * simulation actor. The owning Blueprint calls this from its
	 * RouteImpulseToNativeWater event. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Water|Native")
	void RouteImpulseToAssignedEngineWater(const FMelodiaWaterFluidImpulse& Impulse);

	/** Implement in the project zone Blueprint to call the assigned engine
	 * FluidForceDynamic/FluidForceImpulse components. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Water|Native")
	void RouteImpulseToNativeWater(const FMelodiaWaterFluidImpulse& Impulse);

	/** Implement in the project zone Blueprint to configure the authored
	 * ShallowWaterSimComponent and WaveFoamSimComponent references. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Water|Native")
	void ConfigureEngineWaterComponents(UMelodiaWaterProfile* ProfileAsset);

protected:
	UFUNCTION()
	void HandleFluidImpulse(FMelodiaWaterFluidImpulse Impulse);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	TObjectPtr<UMelodiaWaterProfile> Profile;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	TArray<TObjectPtr<UWaterBodyComponent>> WaterBodies;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	TObjectPtr<AWaterZone> WaterZone = nullptr;

	/** Editor-authored engine components; kept as references so the project
	 * Blueprint owns their class-specific configuration. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	TArray<TObjectPtr<UActorComponent>> EngineSimulationComponents;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Native")
	bool bEnabled = true;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

	UPROPERTY(Transient)
	FMelodiaWaterNativeLimits NativeLimits;

	UPROPERTY(Transient)
	bool bNativeWaterReady = false;

	UPROPERTY(Transient)
	int32 DynamicForcesThisWindow = 0;

	UPROPERTY(Transient)
	int32 ImpulseForcesThisWindow = 0;

	UPROPERTY(Transient)
	float ForceBudgetWindowStart = 0.0f;
};
