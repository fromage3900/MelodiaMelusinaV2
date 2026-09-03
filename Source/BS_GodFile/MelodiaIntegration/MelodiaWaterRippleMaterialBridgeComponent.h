#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterRippleMaterialBridgeComponent.generated.h"

class UMaterialInstanceDynamic;
class UMelodiaWaterInteractionSubsystem;
class UMelodiaWaterProfile;

/**
 * Runtime adapter for M_Water_Master_Grand_v9. Attach it to a water-surface
 * actor; it discovers mesh materials, shifts three ripple slots, and writes
 * the v9 parameter names without changing the authored master graph.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterRippleMaterialBridgeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterRippleMaterialBridgeComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UFUNCTION()
	void HandleWaterContact(FMelodiaWaterContactEvent Event);

	void DiscoverMaterials();
	void PushRipple(const FMelodiaWaterContactEvent& Event);
	void UpdateNativeSample(const FMelodiaWaterSample& Sample);
	void WriteParameters();
	bool AcceptsEvent(const FMelodiaWaterContactEvent& Event) const;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName WaterBodyId = NAME_None;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	bool bAcceptUnidentifiedEvents = false;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material", meta=(ClampMin="0.1"))
	float RippleDecayPerSecond = 1.6f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleCenterAParameter = TEXT("RippleCenterA");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleCenterBParameter = TEXT("RippleCenterB");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleCenterCParameter = TEXT("RippleCenterC");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleImpulseAParameter = TEXT("RippleImpulseA");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleImpulseBParameter = TEXT("RippleImpulseB");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName RippleImpulseCParameter = TEXT("RippleImpulseC");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material")
	FName BioluminescenceImpulseParameter = TEXT("WaterBioluminescenceImpulse");

	/** v10 native Water + Substrate toon parameter vocabulary. Existing v9
	 * materials safely ignore parameters they do not expose. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	bool bWriteNativeWaterParameters = true;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	TObjectPtr<UMelodiaWaterProfile> Profile = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName NativeWaterAvailabilityParameter = TEXT("NativeWaterAvailability");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName WaterBodyIndexParameter = TEXT("WaterBodyIndex");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName WaterZoneIndexParameter = TEXT("WaterZoneIndex");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName NativeShallowWaterHeightParameter = TEXT("NativeShallowWaterHeight");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName NativeShallowWaterVelocityParameter = TEXT("NativeShallowWaterVelocity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Native")
	FName NativeShallowWaterNormalParameter = TEXT("NativeShallowWaterNormal");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonLightBandsParameter = TEXT("ToonLightBands");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonShadowSoftnessParameter = TEXT("ToonShadowSoftness");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonRimStrengthParameter = TEXT("ToonRimStrength");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonSpecularBandParameter = TEXT("ToonSpecularBand");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonShadowTintParameter = TEXT("ToonShadowTint");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName ToonHighlightTintParameter = TEXT("ToonHighlightTint");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName SurfaceRoughnessParameter = TEXT("SurfaceRoughness");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName SurfaceMetallicParameter = TEXT("SurfaceMetallic");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName SurfaceSubsurfaceWeightParameter = TEXT("SurfaceSubsurfaceWeight");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Material|Substrate Toon")
	FName WaterBioluminescenceWeightParameter = TEXT("WaterBioluminescenceWeight");

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> WaterMaterials;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

	FVector RippleCenters[3] = { FVector::ZeroVector, FVector::ZeroVector, FVector::ZeroVector };
	float RippleImpulses[3] = { 0.0f, 0.0f, 0.0f };
	FMelodiaWaterSample LastNativeSample;
	bool bHasNativeSample = false;
};
