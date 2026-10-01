// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ACFSplinePath.generated.h"

class APawn;
class USplineComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnSplinePathPointReached, int32, PointIndex, APawn*, TraversingPawn);

UCLASS()
class AIFRAMEWORK_API AACFSplinePath : public AActor
{
	GENERATED_BODY()

public:
	AACFSplinePath();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, Category = ACF)
	TObjectPtr<USplineComponent> SplineComp;

public:
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE USplineComponent* GetSplineComponent() const { return SplineComp; }

	UPROPERTY(BlueprintAssignable, Category = "ACF|Spline Path")
	FOnSplinePathPointReached OnPointReached;

	UFUNCTION(BlueprintCallable, Category = "ACF|Spline Path")
	void NotifyPointReached(int32 PointIndex, APawn* TraversingPawn);

	UFUNCTION(BlueprintNativeEvent, Category = "ACF|Spline Path")
	void HandlePointReached(int32 PointIndex, APawn* TraversingPawn);
	virtual void HandlePointReached_Implementation(int32 PointIndex, APawn* TraversingPawn);

	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddSplinePoint(const FVector& worldPos);

	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetSplinePoints(const TArray<FVector>& worldPos);
};
