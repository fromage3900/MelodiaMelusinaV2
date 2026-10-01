// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "ACFAITypes.h"

#include "ACFAIPatrolComponent.generated.h"

struct FAIRequestID;
struct FPathFollowingResult;

/**
 * Manages AI patrol behaviour for a pawn.
 *
 * Supports two modes, chosen via EPatrolType:
 *   - EFollowSpline : the AI walks through the points of an AACFSplinePath in order,
 *                     wrapping back to the first point when it reaches the end.
 *   - ERandomPoint  : the AI picks a random reachable point within RandomPatrolRadius
 *                     of its home location each time it needs a new destination.
 *
 * Call StartPatrolLoop() once the owning pawn has a valid AACFAIController.
 * The component listens to the controller's path-following delegate and automatically
 * requests the next waypoint after each move completes.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFAIPatrolComponent : public UActorComponent {
    GENERATED_BODY()

public:
    UACFAIPatrolComponent();

protected:
    virtual void BeginPlay() override;

    /** Determines which patrol strategy is used (spline or random). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    EPatrolType PatrolType;

    /** Spline actor to follow when PatrolType == EFollowSpline. */
    UPROPERTY(EditAnywhere, meta = (EditCondition = "PatrolType == EPatrolType::EFollowSpline"), BlueprintReadWrite, Category = ACF)
    TObjectPtr<AACFSplinePath> PathToFollow;

    /** Search radius for random waypoints when PatrolType == ERandomPoint. */
    UPROPERTY(EditAnywhere, meta = (EditCondition = "PatrolType == EPatrolType::ERandomPoint"), BlueprintReadWrite, Category = ACF)
    float RandomPatrolRadius;

    /** How long (seconds) the AI waits at each waypoint before moving to the next. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float WaitTimeAtPoint;

    /** Home location snapshot taken at save time, used to restore the controller's home after load. */
    UPROPERTY(SaveGame)
    FVector SavedHomeLocation = FVector::ZeroVector;

    /** True once a home location has been explicitly snapshotted. False on new games or before the first save. */
    UPROPERTY(SaveGame)
    bool bHasSavedHomeLocation = false;

public:
    /** Returns the spline path currently assigned for EFollowSpline patrol. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    AACFSplinePath* GetPathToFollow() const { return PathToFollow; }

    /** Assigns a new spline path. Safe to call at runtime; takes effect on the next waypoint request. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetPathToFollow(AACFSplinePath* val) { PathToFollow = val; }

    /**
     * Fills outLocation with the next patrol destination.
     * For EFollowSpline: returns the next spline point (projected onto NavMesh when possible).
     * For ERandomPoint: returns a random reachable point within RandomPatrolRadius of home.
     * @return false if no valid location could be determined.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool TryGetNextWaypoint(FVector& outLocation);

    /** Returns the active patrol type. */
    UFUNCTION(BlueprintPure, Category = ACF)
    EPatrolType GetPatrolType() const { return PatrolType; }

    /** Switches the patrol strategy at runtime. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetPatrolType(EPatrolType val) { PatrolType = val; }

    /** Returns the random patrol search radius. */
    UFUNCTION(BlueprintPure, Category = ACF)
    float GetRandomPatrolRadius() const { return RandomPatrolRadius; }

    /** Sets the random patrol search radius. Values below 0 are clamped to 0. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetRandomPatrolRadius(float InRadius) { RandomPatrolRadius = FMath::Max(0.f, InRadius); }

    /** Returns the wait time at each waypoint in seconds. */
    UFUNCTION(BlueprintPure, Category = ACF)
    float GetWaitTime() const;

    /** Overrides the wait time at each waypoint at runtime. Values below 0 are clamped to 0. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetWaitTimeAtPoint(float InWaitTime) { WaitTimeAtPoint = FMath::Max(0.f, InWaitTime); }

    /**
     * Activates the patrol loop. The component binds to the controller's move-completed
     * delegate and will keep requesting waypoints until StopPatrolLoop() is called.
     * @param bStartImmediately - if true, kicks off the first move request right away.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StartPatrolLoop(bool bStartImmediately = true);

    /** Deactivates the patrol loop and unbinds the move-completed delegate. */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StopPatrolLoop();

    /** Returns true while the patrol loop is running. */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsPatrolLoopActive() const { return bPatrolLoopActive; }

    /** Called by the ALS save system before the component is serialized. Snapshots the controller's current home location. */
    UFUNCTION()
    void OnComponentSaved();

    /** Called by the ALS save system after the owning actor has been deserialized and its controller respawned. */
    UFUNCTION()
    void OnComponentLoaded();

private:
    /** Invoked by the controller's PathFollowingComponent when a move request finishes. */
    void HandleMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result);

    /** Binds HandleMoveCompleted to CachedAIController's OnRequestFinished delegate. */
    void BindControllerMoveCompleted();

    /** Removes the HandleMoveCompleted binding and resets the delegate handle. */
    void UnbindControllerMoveCompleted();

    /** Notifies the spline path actor that a specific point was reached by the pawn. */
    void NotifyPathPointReached(int32 PointIndex) const;

    /** Index of the next spline point to visit (wraps around at the end of the path). */
    int32 patrolIndex = 0;

    /** Index of the spline point the AI is currently moving towards (INDEX_NONE if none). */
    int32 CurrentPatrolPointIndex = INDEX_NONE;

    /** True while the patrol loop delegate is active. */
    bool bPatrolLoopActive = false;

    /** Handle used to remove the move-completed binding when the loop stops. */
    FDelegateHandle MoveCompletedHandle;

    /** Cached controller reference, valid only while the patrol loop is active. */
    UPROPERTY(Transient)
    TObjectPtr<class AACFAIController> CachedAIController = nullptr;
};
