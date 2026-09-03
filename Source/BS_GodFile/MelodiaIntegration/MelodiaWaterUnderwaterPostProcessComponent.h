#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterUnderwaterPostProcessComponent.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class UMelodiaWaterInteractionSubsystem;
class UMelodiaWaterProfile;
class UWaterBodyComponent;

/**
 * Camera-manager blendable bridge for the rollback underwater post material.
 * A Water v10 profile can provide the native Water Body material; the
 * camera-manager blend remains a fallback for custom/non-Water surfaces. The
 * component is owned by the interacting pawn, but the blend is applied to the
 * local player camera so third-person and first-person views share one state.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterUnderwaterPostProcessComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterUnderwaterPostProcessComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater")
	TObjectPtr<UMaterialInterface> UnderwaterMaterial = nullptr;

	/** Optional v10 profile. Its UnderwaterMaterial is used for native Water
	 * Bodies when assigned; the legacy material above remains fallback-only. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater")
	TObjectPtr<UMelodiaWaterProfile> Profile = nullptr;

	/** Native Water Bodies own activation and blending when enabled. The
	 * camera-manager blend remains available for custom/non-Water surfaces. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater")
	bool bUseNativeWaterPostProcess = true;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater")
	FName BlendParameter = TEXT("UnderwaterBlend");

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater")
	FName DepthParameter = TEXT("UnderwaterDepth");

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater", meta=(ClampMin="0.1"))
	float BlendInSpeed = 8.0f;

	UPROPERTY(EditDefaultsOnly, Category="Melodia|Water|Underwater", meta=(ClampMin="0.1"))
	float BlendOutSpeed = 5.0f;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> UnderwaterMID = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> NativeUnderwaterMID = nullptr;

	TWeakObjectPtr<UWaterBodyComponent> ActiveNativeWaterBody;

	float CurrentBlend = 0.0f;
};
