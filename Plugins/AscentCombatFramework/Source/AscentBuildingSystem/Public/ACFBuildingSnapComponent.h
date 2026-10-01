// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ACFBuildingSnapComponent.generated.h"

class UACFBuildingSnapPointComponent;

/**
 * Component responsible for handling snapping logic for buildable actors.
 * Provides functions to detect nearby snap points and align the actor accordingly.
 * Used during building placement to assist with modular construction.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTBUILDINGSYSTEM_API UACFBuildingSnapComponent : public UActorComponent {
	GENERATED_BODY()

public:
	/**
	 * Constructor that sets default values for this component's properties.
	 */
	UACFBuildingSnapComponent();

	/**
	 * Finds the nearest available snap target component.
	 * @return Pointer to the nearest UACFBuildingSnapComponent, or nullptr if none found.
	 */
	UFUNCTION(BlueprintCallable, Category = "Snapping")
	UACFBuildingSnapComponent* FindNearestSnapTarget();

	/**
	 * Attempts to snap this component to the specified target.
	 * @param Target The target snap component.
	 * @return True if successfully snapped.
	 */
	UFUNCTION(BlueprintCallable, Category = "Snapping")
	bool SnapToTarget(const UACFBuildingSnapComponent* const Target);

	/**
	 * Gets the list of world space snap points for this component.
	 * @return An array of world space positions.
	 */
	UFUNCTION(BlueprintCallable, Category = "Snapping")
	TArray<FVector> GetWorldSnapPoints() const;

	/**
	 * Tries to find and snap to a valid nearby snap target.
	 * @return True if snapping was successful.
	 */
	UFUNCTION(BlueprintCallable, Category = "Snapping")
	bool TrySnap();

	TObjectPtr<AActor> GetCurrentSnapActor() const { return CurrentSnapActor; }

protected:
	void BeginPlay() override;

	/**
	* Ticks the component every frame.
	* @param DeltaTime Time elapsed since last tick.
	* @param TickType Type of tick.
	* @param ThisTickFunction Tick function data.
	*/
	void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	// Internal function to calculate snap position
	FVector CalculateSnapPosition(const FVector& MyPoint, const FVector& TargetPoint) const;

	// Internal function to check if two points are within snap distance
	bool IsWithinSnapDistance(const FVector& Point1, const FVector& Point2) const;

	// Function to update the cached snap targets
	void UpdateSnapTargetsCache();

	// Snap distance threshold
	UPROPERTY(EditAnywhere, Category = "Snapping")
	float SnapDistance = 100.0f;

	// Whether snapping is enabled
	UPROPERTY(EditAnywhere, Category = "Snapping")
	bool bSnapEnabled = true;

	// Snap tolerance for fine-tuning
	UPROPERTY(EditAnywhere, Category = "Snapping")
	float SnapTolerance = 10.0f;

	// Whether to snap on all axes or just X and Y
	UPROPERTY(EditAnywhere, Category = "Snapping")
	bool bSnapVertically = true;

	// Snap points relative to the actor's origin
	UPROPERTY()
	TArray<UACFBuildingSnapPointComponent*> SnapPoints;


	UPROPERTY()
	TObjectPtr<AActor> CurrentSnapActor;
	void SetCurrentSnapActor(TObjectPtr<AActor> val) { CurrentSnapActor = val; }
	// Cache for performance
	TArray<UACFBuildingSnapComponent*> CachedSnapTargets;
	float LastCacheUpdate = 0.0f;
	float CacheUpdateInterval = 0.1f; // Update cache every 0.1 seconds
};
