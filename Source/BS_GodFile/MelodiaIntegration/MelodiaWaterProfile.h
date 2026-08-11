#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterProfile.generated.h"

class UActorComponent;
class UMaterialInterface;
class UMetaSoundSource;
class UNiagaraDataChannelAsset;
class UNiagaraSystem;
class USoundAttenuation;
class USoundConcurrency;

/**
 * Authoring contract for one water family. Profiles are the stable seam
 * between gameplay, native Water, Niagara, materials, audio, and text
 * injection. Asset references remain soft so a low-tier map does not load
 * hero simulation content accidentally.
 */
UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaWaterProfile final : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	virtual FPrimaryAssetId GetPrimaryAssetId() const override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Identity")
	FName WaterBodyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Identity")
	FName EffectProfileId = TEXT("Default");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Identity")
	FName AudioProfileId = TEXT("Default");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	EMelodiaWaterSimulationTier SimulationTier = EMelodiaWaterSimulationTier::AnalyticSurface;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	bool bUseNativeWater = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	bool bUseBakedSimulationForQueries = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	bool bRouteContactsToNativeWater = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	TSoftClassPtr<UActorComponent> NativeShallowWaterComponentClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	TSoftClassPtr<UActorComponent> NativeWaveFoamComponentClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	TSoftClassPtr<UActorComponent> NativeDynamicForceComponentClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Simulation")
	TSoftClassPtr<UActorComponent> NativeImpulseComponentClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara")
	TSoftObjectPtr<UNiagaraDataChannelAsset> ContactDataChannel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara")
	TSoftObjectPtr<UNiagaraSystem> ContactSystem;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara")
	TSoftObjectPtr<UNiagaraSystem> RippleSystem;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara")
	TSoftObjectPtr<UNiagaraSystem> SplashSystem;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara")
	TSoftObjectPtr<UNiagaraSystem> FluidSystem;

	/** Optional quantum/Nikki presentation overlay. It is never the authoritative
	 * water response and remains quiet until the shared QuantumPulse is active. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara|Quantum")
	bool bUseQuantumReactionVFX = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara|Quantum")
	TSoftObjectPtr<UNiagaraSystem> QuantumReactionSystem;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara|Quantum")
	TSoftObjectPtr<UNiagaraSystem> QuantumEntropySystem;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|MetaSound")
	TSoftObjectPtr<UMetaSoundSource> SurfaceMovementMetaSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|MetaSound")
	TSoftObjectPtr<UMetaSoundSource> SurfaceEntryMetaSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|MetaSound")
	TSoftObjectPtr<UMetaSoundSource> UnderwaterBubbleMetaSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|MetaSound")
	TSoftObjectPtr<UMetaSoundSource> WaterImpactMetaSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|MetaSound")
	TSoftObjectPtr<UMetaSoundSource> ReemergenceMetaSound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|Mix")
	TSoftObjectPtr<USoundConcurrency> AudioConcurrency;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio|Mix")
	TSoftObjectPtr<USoundAttenuation> AudioAttenuation;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials")
	TSoftObjectPtr<UMaterialInterface> SurfaceMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials")
	TSoftObjectPtr<UMaterialInterface> UnderwaterMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon")
	bool bUseSubstrateToonLayer = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon")
	FName ToonProfileId = TEXT("Water");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="1.0", ClampMax="8.0"))
	float ToonLightBands = 3.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="1.0"))
	float ToonShadowSoftness = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="4.0"))
	float ToonRimStrength = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="1.0"))
	float ToonSpecularBand = 0.65f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon")
	FLinearColor ToonShadowTint = FLinearColor(0.015f, 0.04f, 0.08f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon")
	FLinearColor ToonHighlightTint = FLinearColor(0.35f, 0.9f, 1.0f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="1.0"))
	float SurfaceRoughness = 0.08f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="1.0"))
	float SurfaceMetallic = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="1.0"))
	float SurfaceSubsurfaceWeight = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Materials|Substrate Toon", meta=(ClampMin="0.0", ClampMax="4.0"))
	float WaterBioluminescenceWeight = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="1", ClampMax="240"))
	int32 MaxContactsPerSecond = 60;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="1", ClampMax="60"))
	int32 MaxAudioEventsPerSecond = 8;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="1", ClampMax="32"))
	int32 MaxAudioVoices = 4;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="0", ClampMax="16"))
	int32 MaxQuantumReactionEventsPerSecond = 2;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="0", ClampMax="64"))
	int32 MaxNativeDynamicForces = 8;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="0", ClampMax="64"))
	int32 MaxNativeImpulseForces = 16;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Budgets", meta=(ClampMin="0.25", ClampMax="2.0"))
	float ShallowWaterRenderTargetScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Provenance")
	FName SchemaVersion = TEXT("water-v10");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Provenance", meta=(MultiLine=true))
	FString Provenance = TEXT("Project-owned profile; engine Water assets are references only.");
};
