#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterNiagaraBridgeComponent.generated.h"

class UNiagaraSystem;
class UMelodiaWaterInteractionSubsystem;
class UMelodiaWaterProfile;
class UNiagaraDataChannelAsset;
class UMaterialParameterCollection;

/**
 * Reusable Niagara consumer for one water-interacting actor. It listens to
 * the shared event bus, filters state-only notifications, and writes the same
 * normalized parameters to a pooled contact system for Melusina or any future
 * creature/prop.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterNiagaraBridgeComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterNiagaraBridgeComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Niagara")
	int32 GetQuantumReactionsThisWindow() const { return QuantumReactionsThisWindow; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Niagara")
	float GetLastQuantumPulse() const { return LastQuantumPulse; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Niagara")
	FLinearColor GetLastQuantumReactionColor() const { return LastQuantumReactionColor; }

	UFUNCTION(BlueprintPure, Category="Melodia|Water|Niagara|Data Channel")
	int32 GetDataChannelContactsConsumedThisFrame() const { return DataChannelContactsConsumedThisFrame; }

	protected:
	UFUNCTION()
	void HandleWaterContact(FMelodiaWaterContactEvent Event);
	bool WriteContactToDataChannel(const FMelodiaWaterContactEvent& Event);
	void ConsumeContactDataChannel();
	void SpawnDirectContactVFX(const FMelodiaWaterContactEvent& Event);
	void SpawnQuantumReactionVFX(const FMelodiaWaterContactEvent& Event);
	bool CanWriteContactToDataChannel(const FMelodiaWaterContactEvent& Event);
	bool CanSpawnQuantumReaction(const FMelodiaWaterContactEvent& Event);
	void ReadQuantumPresentation(float& OutChoice, float& OutSeed, float& OutBackend, float& OutPulse, FLinearColor& OutColor) const;

	bool ShouldSpawnForEvent(EMelodiaWaterContactType EventType) const;
	UNiagaraSystem* ResolveSystemForEvent(EMelodiaWaterContactType EventType) const;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	TObjectPtr<UNiagaraSystem> ContactSystem = nullptr;

	/** Existing authored defaults; ContactSystem overrides them when assigned. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	TObjectPtr<UNiagaraSystem> RippleSystem = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	TObjectPtr<UNiagaraSystem> SplashSystem = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	TObjectPtr<UNiagaraSystem> UnderwaterSystem = nullptr;

	/** Project-owned NDC payload. The asset is authored by text injection or
	 * the editor; the runtime only writes the bounded typed fields below. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara|Data Channel")
	TObjectPtr<UNiagaraDataChannelAsset> ContactDataChannel = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Water|Niagara|Data Channel")
	TObjectPtr<UMelodiaWaterProfile> Profile = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	bool bWriteContactDataChannel = true;

	/** Use direct pooled contact systems only when explicitly selected. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Routing")
	bool bSpawnDirectContactEffects = false;

	/** Safe compatibility fallback for maps without a valid Data Channel. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Routing")
	bool bFallbackToDirectWhenDataChannelUnavailable = true;

	/** Read the channel once per frame and make the Data Channel the sole
	 * high-frequency presentation route when it is available. */
	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Routing")
	bool bConsumeContactDataChannel = true;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel", meta=(ClampMin="1", ClampMax="240"))
	int32 MaxDataChannelWritesPerSecond = 60;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel", meta=(ClampMin="1", ClampMax="64"))
	int32 MaxDataChannelReadsPerTick = 16;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelPosition = TEXT("Position");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelVelocity = TEXT("Velocity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelRadius = TEXT("Radius");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelIntensity = TEXT("Intensity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelImmersion = TEXT("Immersion");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelWaterBodyIndex = TEXT("WaterBodyIndex");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelEventType = TEXT("EventType");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Data Channel")
	FName DataChannelRandomSeed = TEXT("RandomSeed");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	bool bOnlySpawnForOwner = true;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MinimumIntensity = 0.05f;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	FName RadiusParameter = TEXT("User.Radius");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	FName IntensityParameter = TEXT("User.Intensity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	FName ImmersionParameter = TEXT("User.Immersion");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara")
	FName VelocityParameter = TEXT("User.ImpactVelocity");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	TObjectPtr<UNiagaraSystem> QuantumReactionSystem = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	TObjectPtr<UNiagaraSystem> QuantumEntropySystem = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	bool bUseQuantumReactionVFX = true;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	TObjectPtr<UMaterialParameterCollection> QuantumPaletteMPC = nullptr;

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	FName QuantumReactionColorParameter = TEXT("User.ReactionColor");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	FName QuantumPulseParameter = TEXT("User.QuantumPulse");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	FName QuantumChoiceParameter = TEXT("User.QuantumChoice");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	FName QuantumSeedParameter = TEXT("User.QuantumSeed");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum")
	FName QuantumBackendParameter = TEXT("User.QuantumBackend");

	UPROPERTY(EditAnywhere, Category="Melodia|Water|Niagara|Quantum", meta=(ClampMin="0.0", ClampMax="1.0"))
	float QuantumPulseThreshold = 0.05f;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWaterInteractionSubsystem> WaterSubsystem = nullptr;

	UPROPERTY(Transient)
	float DataChannelWindowStart = 0.0f;

	UPROPERTY(Transient)
	int32 DataChannelWritesThisWindow = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Niagara|Data Channel|Runtime")
	int32 DataChannelContactsConsumedThisFrame = 0;

	uint64 LastConsumedDataChannelFrame = MAX_uint64;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Niagara|Runtime")
	int32 QuantumReactionsThisWindow = 0;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Niagara|Runtime")
	float LastQuantumPulse = 0.0f;

	UPROPERTY(Transient, BlueprintReadOnly, Category="Melodia|Water|Niagara|Runtime")
	FLinearColor LastQuantumReactionColor = FLinearColor::White;

	UPROPERTY(Transient)
	float QuantumWindowStart = 0.0f;

	UPROPERTY(Transient)
	int32 MaxQuantumReactionEventsPerSecond = 2;
};
