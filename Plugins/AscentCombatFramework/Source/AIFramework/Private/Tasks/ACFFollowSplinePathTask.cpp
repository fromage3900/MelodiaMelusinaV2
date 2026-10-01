// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Tasks/ACFFollowSplinePathTask.h"

#include "ACFAIController.h"
#include "ACFAITypes.h"
#include "ACFSplinePath.h"
#include "Components/ACFAIPatrolComponent.h"
#include "GameplayTagsManager.h"

void UACFFollowSplinePathTask::OnTaskStarted_Implementation(const APawn* ControlledPawn)
{
    Super::OnTaskStarted_Implementation(ControlledPawn);

    if (!ControlledPawn || !SplinePath)
    {
        return;
    }

    AACFAIController* AIController = Cast<AACFAIController>(ControlledPawn->GetController());
    if (!AIController)
    {
        return;
    }

    CachedPatrolComponent = ControlledPawn->FindComponentByClass<UACFAIPatrolComponent>();
    if (!CachedPatrolComponent)
    {
        return;
    }

    CachedSplinePath = SplinePath;

    // Override wait time at each waypoint if requested.
    if (bOverrideWaitTimeAtPoint)
    {
        CachedPatrolComponent->SetWaitTimeAtPoint(WaitTimeAtPoint);
    }

    // Store the previous locomotion state for the AIRoutine tag so we can restore it on end.
    const FGameplayTag RoutineTag = UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIRoutine);
    const TMap<FGameplayTag, ELocomotionState>& CurrentMap = AIController->GetLocomotionStateByAIState();
    const ELocomotionState* PrevPtr = CurrentMap.Find(RoutineTag);
    bHadPreviousLocomotionState = (PrevPtr != nullptr);
    PreviousLocomotionState = bHadPreviousLocomotionState ? *PrevPtr : ELocomotionState::EWalk;

    // Write the desired locomotion state for the AIRoutine tag.
    // SetCurrentAIState (below) will call UpdateLocomotionState(), which reads this map entry.
    AIController->SetLocomotionStateForAIState(RoutineTag, LocomotionState);

    // Assign the spline path and force EFollowSpline patrol type.
    AIController->SetPatrolPath(SplinePath, /*forcePathFollowing=*/true);

    // Listen for individual waypoint arrivals so Blueprint subclasses can react.
    CachedSplinePath->OnPointReached.AddDynamic(this, &UACFFollowSplinePathTask::HandlePointReached);

    // Set AI state to Routine — internally calls UpdateLocomotionState() using the map entry above.
    AIController->SetCurrentAIState(RoutineTag);
    CachedPatrolComponent->StartPatrolLoop(bStartMovementOnTaskStart);
}

void UACFFollowSplinePathTask::OnTaskEnded_Implementation()
{
    if (CachedPatrolComponent)
    {
        CachedPatrolComponent->StopPatrolLoop();
        CachedPatrolComponent = nullptr;
    }

    if (CachedSplinePath)
    {
        CachedSplinePath->OnPointReached.RemoveDynamic(this, &UACFFollowSplinePathTask::HandlePointReached);
        CachedSplinePath = nullptr;
    }

    // Restore the previous locomotion state for the AIRoutine tag.
    if (AACFAIController* AIController = Cast<AACFAIController>(Controller))
    {
        const FGameplayTag RoutineTag = UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIRoutine);
        if (bHadPreviousLocomotionState)
        {
            AIController->SetLocomotionStateForAIState(RoutineTag, PreviousLocomotionState);
        }
        else
        {
            // Remove the entry we added so we leave the map clean.
            TMap<FGameplayTag, ELocomotionState> CurrentMap = AIController->GetLocomotionStateByAIState();
            CurrentMap.Remove(RoutineTag);
            AIController->SetLocomotionStateByAIState(CurrentMap);
        }
    }

    Super::OnTaskEnded_Implementation();
}

void UACFFollowSplinePathTask::HandlePointReached(int32 PointIndex, APawn* TraversingPawn)
{
    // Forward the event only for the pawn this task is controlling.
    if (TraversingPawn && Controller && TraversingPawn->GetController() == Controller)
    {
        OnSplinePointReached(PointIndex);
    }
}
