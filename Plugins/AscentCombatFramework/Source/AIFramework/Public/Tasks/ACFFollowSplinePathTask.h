// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFTask.h"
#include "ACFCCTypes.h"
#include "ACFFollowSplinePathTask.generated.h"

class AACFSplinePath;
class UACFAIPatrolComponent;

/**
 * Routine task that makes the AI loop around an ACFSplinePath in order.
 *
 * On start:
 *   - Assigns the chosen SplinePath to the pawn's ACFAIPatrolComponent.
 *   - Forces the patrol type to EFollowSpline.
 *   - Optionally overrides the wait time the AI spends at each waypoint.
 *   - Sets the AI state to ACF::AIRoutine and starts the patrol loop.
 *
 * On end:
 *   - Stops the patrol loop and releases all internal references.
 *   - Unbinds the waypoint-reached delegate.
 *
 * Usage: assign this task inside an ACFAIRoutineComponent. The pawn must
 * have an ACFAIPatrolComponent and be controlled by an AACFAIController.
 */
UCLASS(BlueprintType, Blueprintable, EditInlineNew)
class AIFRAMEWORK_API UACFFollowSplinePathTask : public UACFTask
{
    GENERATED_BODY()

public:
    /** The spline path the AI will loop around. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|SplineFollow")
    TObjectPtr<AACFSplinePath> SplinePath = nullptr;

    /**
     * When true, immediately requests the first waypoint move at task start.
     * Set to false if you want to trigger the first movement manually.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|SplineFollow")
    bool bStartMovementOnTaskStart = true;

    /**
     * When true, overrides the WaitTimeAtPoint on the ACFAIPatrolComponent
     * with the value below every time the task starts.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|SplineFollow")
    bool bOverrideWaitTimeAtPoint = false;

    /**
     * Seconds the AI will pause at each waypoint before moving to the next one.
     * Only used when bOverrideWaitTimeAtPoint is true.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|SplineFollow",
        meta = (EditCondition = "bOverrideWaitTimeAtPoint", ClampMin = "0.0"))
    float WaitTimeAtPoint = 1.0f;

    /**
     * Locomotion state the AI will use while following the spline.
     * This entry is written into the controller's LocomotionStateByAIState map
     * for the ACF::AIRoutine tag, so it takes effect as soon as the task starts
     * and is automatically restored to its previous value when the task ends.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|SplineFollow")
    ELocomotionState LocomotionState = ELocomotionState::EWalk;

    /**
     * Called each time the AI reaches a waypoint on the spline.
     * Override in Blueprint to react to individual waypoint arrivals.
     * @param PointIndex  Zero-based index of the reached spline point.
     */
    UFUNCTION(BlueprintNativeEvent, Category = "ACF|SplineFollow")
    void OnSplinePointReached(int32 PointIndex);
    virtual void OnSplinePointReached_Implementation(int32 PointIndex) {}

protected:
    virtual void OnTaskStarted_Implementation(const APawn* ControlledPawn) override;
    virtual void OnTaskEnded_Implementation() override;

private:
    UPROPERTY(Transient)
    TObjectPtr<UACFAIPatrolComponent> CachedPatrolComponent = nullptr;

    UPROPERTY(Transient)
    TObjectPtr<AACFSplinePath> CachedSplinePath = nullptr;

    /** Previous locomotion state stored for the AIRoutine tag, restored on task end. */
    ELocomotionState PreviousLocomotionState = ELocomotionState::EWalk;

    /** Whether the AIRoutine tag had an entry in the map before this task started. */
    bool bHadPreviousLocomotionState = false;

    /** Bound to AACFSplinePath::OnPointReached while the task is active. */
    UFUNCTION()
    void HandlePointReached(int32 PointIndex, APawn* TraversingPawn);
};
