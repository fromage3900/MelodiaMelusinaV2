#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterAudioBridgeComponent.generated.h"

class UAudioComponent;
class UMelodiaWaterInteractionSubsystem;
class UMelodiaWaterProfile;
class UMetaSoundSource;
class USoundAttenuation;
class USoundConcurrency;

/**
 * Project-owned water audio consumer. Gameplay publishes one normalized water
 * contact; this component resolves the profile's MetaSound, applies bounded
 * intensity/immersion parameters, and enforces a local voice budget.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterAudioBridgeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterAudioBridgeComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Audio")
	bool IsAudioReady() const { return bAudioReady; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Audio")
	int32 GetAudioEventsThisWindow() const { return AudioEventsThisWindow; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Audio")
	int32 GetActiveAudioVoices() const { return ActiveAudioVoices; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Audio")
	int32 GetRejectedAudioEvents() const { return RejectedAudioEvents; }

protected:
	UFUNCTION()
	void HandleWaterContact(FMelodiaWaterContactEvent Event);

	UMetaSoundSource* ResolveSound(const FMelodiaWaterContactEvent& Event) const;
	UAudioComponent* PlayWaterMetaSound(const FMelodiaWaterContactEvent& Event, UMetaSoundSource* Sound);
	void CleanupActiveVoices();
	bool CanPlayEvent(const FMelodiaWaterContactEvent& Event);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio")
	TObjectPtr<UMelodiaWaterProfile> Profile = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio")
	bool bOnlySpawnForOwner = true;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MinimumIntensity = 0.05f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio", meta=(ClampMin="1", ClampMax="32"))
	int32 MaxConcurrentVoices = 4;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Audio", meta=(ClampMin="1", ClampMax="60"))
	int32 MaxAudioEventsPerSecond = 8;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Audio|MetaSound")
	FName IntensityParameter = TEXT("WaterIntensity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Audio|MetaSound")
	FName ImmersionParameter = TEXT("WaterImmersion");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Audio|MetaSound")
	FName VelocityParameter = TEXT("WaterVelocity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Audio|MetaSound")
	FName DepthParameter = TEXT("WaterDepth");

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Audio|Runtime")
	bool bAudioReady = false;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Audio|Runtime")
	int32 AudioEventsThisWindow = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Audio|Runtime")
	int32 ActiveAudioVoices = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Audio|Runtime")
	int32 RejectedAudioEvents = 0;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

	UPROPERTY(Transient)
	TArray<TWeakObjectPtr<UAudioComponent>> ActiveAudioComponents;

	UPROPERTY(Transient)
	TObjectPtr<UMetaSoundSource> DefaultSurfaceMovementMetaSound = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMetaSoundSource> DefaultSurfaceEntryMetaSound = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMetaSoundSource> DefaultUnderwaterBubbleMetaSound = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMetaSoundSource> DefaultWaterImpactMetaSound = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UMetaSoundSource> DefaultReemergenceMetaSound = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<USoundConcurrency> DefaultAudioConcurrency = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<USoundAttenuation> DefaultAudioAttenuation = nullptr;

	float AudioWindowStart = 0.0f;
	float LastReemergenceTime = -BIG_NUMBER;
};
