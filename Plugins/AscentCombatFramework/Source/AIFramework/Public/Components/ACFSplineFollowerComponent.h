// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <AITypes.h>
#include <Navigation/PathFollowingComponent.h>

#include "ACFSplineFollowerComponent.generated.h"

class USplineComponent;
class AAIController;

/** Delegate signatures */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnSplineFollowerEvent);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSplineSegmentReached, int32, SegmentIndex);

/**
 * Component that handles AI movement along a spline path while maintaining distance from a target pawn.
 * The AI will follow the spline but pause if the target pawn gets too far away.
 *
 * Usage:
 * 1. Add this component to an AIController
 * 2. Call StartFollowing() with a spline and target pawn
 * 3. The AI will move along the spline, waiting if the target falls behind
 * 4. Listen to events for state changes
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFSplineFollowerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	UACFSplineFollowerComponent();

	/**
	 * Start following the spline path while monitoring target pawn distance
	 * @param InSpline - The spline component to follow
	 * @param InTargetPawn - The pawn to wait for if it falls behind
	 */
	UFUNCTION(BlueprintCallable, Category= "ACF")
	void StartFollowing(USplineComponent* InSpline, APawn* InTargetPawn);

	/**
	 * Initialize the path to follow without starting movement
	 * @param InSpline - The spline component to assign as path
	 * @param InTargetPawn - The pawn to keep track of while following
	 */
	UFUNCTION(BlueprintCallable, Category= "ACF")
	void InitPath(USplineComponent* InSpline, APawn* InTargetPawn);

	/**
	 * Start following the currently initialized spline if valid
	 */
	UFUNCTION(BlueprintCallable, Category= "ACF")
	void StartFollowingCurrentSpline();

	/** Stop following and cleanup all references */
	UFUNCTION(BlueprintCallable, Category= "ACF")
	void StopFollowing();

	/** Returns true if currently following a spline */
	UFUNCTION(BlueprintPure, Category= "ACF")
	bool IsFollowing() const { return bIsActive; }

	/** Returns true if currently waiting for the target pawn to catch up */
	UFUNCTION(BlueprintPure, Category= "ACF")
	bool IsWaitingForTarget() const { return bIsWaitingForTarget; }

	/** Get current progress as percentage (0-100) along the spline */
	UFUNCTION(BlueprintPure, Category= "ACF")
	float GetProgressPercentage() const;

	/** Get the index of the current segment being targeted */
	UFUNCTION(BlueprintPure, Category= "ACF")
	int32 GetCurrentSegmentIndex() const;

	UFUNCTION(BlueprintPure, Category= "ACF")
	bool IsTargetPawnTooFar() const;
	// ========================================
	// Events / Delegates
	// ========================================

	/** Called when the AI starts following the spline */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineFollowerEvent OnFollowingStarted;

	/** Called when the AI stops following (either completed or manually stopped) */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineFollowerEvent OnFollowingStopped;

	/** Called when the AI stops to wait for the target pawn */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineFollowerEvent OnStartedWaitingForTarget;

	/** Called when the target pawn gets close enough to resume movement */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineFollowerEvent OnTargetRejoined;

	/** Called when the AI reaches the end of the spline */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineFollowerEvent OnSplineCompleted;

	/** Called each time the AI reaches a new segment point along the spline */
	UPROPERTY(BlueprintAssignable, Category = "Spline Follower|Events")
	FOnSplineSegmentReached OnSegmentReached;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	// Maximum distance at which the AI will follow the target before stopping or switching behavior
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	float MaxFollowDistance = 1000.0f;

	// Minimum distance the AI maintains from the target while following
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	float MinFollowDistance = 500.0f;

	// Threshold distance to consider a navigation point as reached
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	float PointReachedThreshold = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	float NavMeshProjectionExtent = 500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	bool bRequireValidNavMeshProjection = false;

	/** Draw debug spheres at final goal locations (after NavMesh projection). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Debug")
	bool bDrawDebugProjectedGoals = false;

	/** Radius used by debug spheres for projected goals. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Debug", meta = (EditCondition = "bDrawDebugProjectedGoals", ClampMin = "1.0"))
	float DebugProjectedGoalSphereRadius = 40.0f;

	/** Duration in seconds for projected goal debug spheres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Debug", meta = (EditCondition = "bDrawDebugProjectedGoals", ClampMin = "0.0"))
	float DebugProjectedGoalSphereDuration = 2.0f;

	/** Color used by projected goal debug spheres. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Debug", meta = (EditCondition = "bDrawDebugProjectedGoals"))
	FColor DebugProjectedGoalSphereColor = FColor::Green;

private:
	/** Delegate handle for move completed callback */
	FDelegateHandle MoveCompletedDelegateHandle;

	/** Called when AI reaches a spline point */
	void OnMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result);

	/** Helper functions */
	float GetDistanceToTargetPawn() const;
	bool IsTargetPawnCloseEnough() const;
	FVector GetNextSplineLocation() const;
	bool HasReachedSplineEnd() const;
	void MoveToNextSplinePoint();
	void NotifySplinePathPointReached(int32 PointIndex) const;
	void StopAndWaitForTargetPawn();
	void ResumeFollowingSpline();
	void UpdateMovement(float DeltaTime);

	/** State */
	UPROPERTY()
	TObjectPtr<USplineComponent> SplinePath;

	UPROPERTY()
	TObjectPtr<APawn> TargetPawn;

	UPROPERTY()
	TObjectPtr<AAIController> OwnerAIController;

	/** Whether we're actively following a spline */
	bool bIsActive;
	/** Whether we're currently waiting for target to catch up */
	bool bIsWaitingForTarget;
	/** Current distance along the spline in world units */
	float CurrentSplineDistance;
	/** Target distance we're moving towards along the spline */
	float TargetSplineDistance;
	/** Current segment index for tracking progress */
	int32 CurrentSplinePointIndex;
};
