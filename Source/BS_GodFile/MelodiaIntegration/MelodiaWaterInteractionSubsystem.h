#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterInteractionSubsystem.generated.h"

class AActor;
class UWaterBodyComponent;
class FSubsystemCollectionBase;
class FWaterBodyManager;

/**
 * Game-wide water interaction bus. Water Body queries, traversal, Niagara,
 * fluid adapters, post-process, and audio can evolve independently while
 * sharing one authoritative packet format.
 */
UCLASS()
class BS_GODFILE_API UMelodiaWaterInteractionSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaWaterInteractionSubsystem* Get(const UObject* WorldContextObject);

	/** Submit the latest query result for an actor or other gameplay source. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water")
	void SubmitSample(AActor* SourceActor, const FMelodiaWaterSample& Sample);

	/** Publish a normalized event for all presentation/simulation consumers. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water")
	void PublishContact(const FMelodiaWaterContactEvent& Event);

	/** Publish a bounded impulse for a future Shallow Water/FLIP adapter. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Fluid")
	void PublishFluidImpulse(const FMelodiaWaterFluidImpulse& Impulse);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Fluid")
	void GetRecentFluidImpulses(TArray<FMelodiaWaterFluidImpulse>& OutImpulses) const;

	/** Query the closest registered Water Body at a world position. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water")
	bool QueryWaterAtLocation(const FVector& WorldLocation, FMelodiaWaterSample& OutSample);

	/** Query using the actor-aware fast path, caching its last Water Body. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Water")
	bool QueryWaterAtLocationForActor(AActor* SourceActor, const FVector& WorldLocation, FMelodiaWaterSample& OutSample);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Native")
	bool TryGetWaterBodyComponent(FName WaterBodyId, UWaterBodyComponent*& OutWaterBodyComponent) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Native")
	bool GetNativeWaterLimits(FMelodiaWaterNativeLimits& OutLimits) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Water")
	bool GetLatestSample(AActor* SourceActor, FMelodiaWaterSample& OutSample) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water")
	void ClearActor(AActor* SourceActor);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water")
	int32 GetActiveSampleCount() const { return LatestSamples.Num(); }

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water")
	FMelodiaWaterSampleUpdated OnSampleUpdated;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water")
	FMelodiaWaterContactEventSignature OnContactEvent;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|Fluid")
	FMelodiaWaterFluidImpulseSignature OnFluidImpulse;

private:
	bool QueryWaterInternal(AActor* SourceActor, const FVector& WorldLocation, FMelodiaWaterSample& OutSample);
	bool QueryWaterBodyComponent(UWaterBodyComponent* WaterBodyComponent, const FVector& WorldLocation, float& OutScore, FMelodiaWaterSample& OutSample) const;
	void CacheWaterBody(UWaterBodyComponent* WaterBodyComponent);
	void HandleWaterBodyAdded(UWaterBodyComponent* WaterBodyComponent);
	void HandleWaterBodyRemoved(UWaterBodyComponent* WaterBodyComponent);
	void ApplyProjectWaterDefaults(UWaterBodyComponent* WaterBodyComponent);
	void EnsureSurfaceBridge(AActor* WaterBodyActor);
	void RemoveInvalidSamples();

	TMap<TWeakObjectPtr<AActor>, FMelodiaWaterSample> LatestSamples;
	TMap<TWeakObjectPtr<AActor>, TWeakObjectPtr<UWaterBodyComponent>> ActorWaterBodies;
	TMap<FName, TWeakObjectPtr<UWaterBodyComponent>> WaterBodiesById;
	FWaterBodyManager* RegisteredWaterBodyManager = nullptr;

	UPROPERTY(Transient)
	TArray<FMelodiaWaterFluidImpulse> RecentFluidImpulses;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Water|Fluid")
	int32 MaxRecentFluidImpulses = 64;
};
