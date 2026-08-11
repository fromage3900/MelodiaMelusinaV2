#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterBuoyancyComponent.generated.h"

UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterBuoyancyComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterBuoyancyComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Buoyancy")
	void InitializePlatformState();

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Buoyancy")
	bool HasAuthoritativeWaterSample() const { return bHasAuthoritativeSample; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy")
	FName WaterBodyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy")
	FName WaterNetworkId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy")
	TArray<FVector> ProbeOffsets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.1"))
	float ProbeRadius = 50.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float BuoyancyScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float LinearDrag = 0.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float AngularDrag = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float FlowForceScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float TorqueScale = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float MaximumForce = 250000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0"))
	float SleepThreshold = 3.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MinimumImmersionThreshold = 0.05f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Buoyancy")
	bool bPublishImpactEvents = true;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Melodia|Water|Buoyancy")
	float LastImmersion = 0.0f;

private:
	bool bHasAuthoritativeSample = false;
	bool bWasImmersed = false;
};

