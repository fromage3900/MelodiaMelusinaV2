#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaWaterPlatformMotionComponent.generated.h"

UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterPlatformMotionComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterPlatformMotionComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Platform")
	void InitializePlatformState();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Platform")
	void ResetDeterministicProgress();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	FName RouteId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	TArray<FTransform> RoutePoints;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform", meta = (ClampMin = "0.0"))
	float Speed = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	TArray<float> DockProgressPoints;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform", meta = (ClampMin = "0.0"))
	float DockPauseSeconds = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	int32 Direction = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	FName GateActivationRequirement = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	float WaterLevelResponse = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	float PressureResponse = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	float FlowResponse = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	bool bReverseOnEnd = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	bool bStartsActive = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Platform")
	int32 DeterministicSeed = 0;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	float RouteProgress = 0.0f;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	bool bDocked = false;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Melodia|Water|Platform")
	bool bActive = false;

private:
	void ApplyRouteTransform();
	bool IsGateOpen() const;
	float GetRouteResponseScale() const;
	float DockPauseRemaining = 0.0f;
};

