// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFAIPatrolComponent.h"
#include "ACFAIController.h"
#include "ACFSplinePath.h"
#include <Components/SplineComponent.h>
#include <Navigation/PathFollowingComponent.h>
#include <NavigationSystem.h>
#include <NavFilters/NavigationQueryFilter.h>
#include <GameplayTagsManager.h>

UACFAIPatrolComponent::UACFAIPatrolComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetPatrolType(EPatrolType::EFollowSpline);
    RandomPatrolRadius = 5000;
    WaitTimeAtPoint = 2.f;
}

void UACFAIPatrolComponent::BeginPlay()
{
    Super::BeginPlay();
}

bool UACFAIPatrolComponent::TryGetNextWaypoint(FVector& outLocation)
{
    if (GetPatrolType() == EPatrolType::EFollowSpline && PathToFollow) {
        const USplineComponent* path = PathToFollow->GetSplineComponent();
        if (!path) {
            return false;
        }

        const int32 NumSplinePoints = path->GetNumberOfSplinePoints();
        if (NumSplinePoints <= 0) {
            return false;
        }

        // Wrap the index back to the start when we have visited all points.
        if (patrolIndex > NumSplinePoints - 1) {
            patrolIndex = 0;
        }

        CurrentPatrolPointIndex = patrolIndex;
        const FTransform waypoint = path->GetTransformAtSplinePoint(CurrentPatrolPointIndex, ESplineCoordinateSpace::World);
        patrolIndex++;

        // Prefer a NavMesh-projected location; fall back to the raw spline position if projection fails.
        FVector outLoc;
        if (UNavigationSystemV1::K2_ProjectPointToNavigation(this, waypoint.GetLocation(), outLoc, nullptr, UNavigationQueryFilter::StaticClass())) {
            outLocation = outLoc;
        } else if (waypoint.GetLocation() != FVector::ZeroVector) {
            outLocation = waypoint.GetLocation();
        }
        return true;
    } else if (GetPatrolType() == EPatrolType::ERandomPoint) {
        TObjectPtr<APawn> pawnOwner = Cast<APawn>(GetOwner());
        if (pawnOwner) {
            TObjectPtr<AACFAIController> controller = Cast<AACFAIController>(pawnOwner->GetController());
            if (controller && UNavigationSystemV1::K2_GetRandomReachablePointInRadius(controller, controller->GetHomeLocation(), outLocation, RandomPatrolRadius)) {
                return true;
            }
        }
    }

    return false;
}

float UACFAIPatrolComponent::GetWaitTime() const
{
    return WaitTimeAtPoint;
}

void UACFAIPatrolComponent::StartPatrolLoop(bool bStartImmediately)
{
    TObjectPtr<APawn> PawnOwner = Cast<APawn>(GetOwner());
    if (!PawnOwner) {
        return;
    }

    CachedAIController = Cast<AACFAIController>(PawnOwner->GetController());
    if (!CachedAIController) {
        return;
    }

    bPatrolLoopActive = true;
    BindControllerMoveCompleted();

    if (bStartImmediately) {
        CachedAIController->TryGoToNextWaypoint();
    }
}

void UACFAIPatrolComponent::StopPatrolLoop()
{
    bPatrolLoopActive = false;
    UnbindControllerMoveCompleted();
    CachedAIController = nullptr;
}

void UACFAIPatrolComponent::HandleMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result)
{
    (void)RequestID;

    // Ignore if the loop was stopped, the controller is gone, or the move failed.
    if (!bPatrolLoopActive || !CachedAIController || !Result.IsSuccess()) {
        return;
    }

    // Only advance when the AI is in a patrol/routine state; ignore move completions
    // that happen while combat or other states are active.
    const FGameplayTag CurrentState = CachedAIController->GetAIState();
    const FGameplayTag PatrolTag = UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIPatrol);
    const FGameplayTag RoutineTag = UGameplayTagsManager::Get().RequestGameplayTag(ACF::AIRoutine);
    if (CurrentState != PatrolTag && CurrentState != RoutineTag) {
        return;
    }

    // Don't interrupt an externally issued command (e.g., investigate, chase).
    if (CachedAIController->IsExecutingCommand()) {
        return;
    }

    NotifyPathPointReached(CurrentPatrolPointIndex);
    CachedAIController->TryGoToNextWaypoint();
}

void UACFAIPatrolComponent::BindControllerMoveCompleted()
{
    if (!CachedAIController || !CachedAIController->GetPathFollowingComponent()) {
        return;
    }

    // Unbind first to avoid duplicate bindings if StartPatrolLoop is called multiple times.
    UnbindControllerMoveCompleted();
    MoveCompletedHandle = CachedAIController->GetPathFollowingComponent()->OnRequestFinished.AddUObject(
        this,
        &UACFAIPatrolComponent::HandleMoveCompleted);
}

void UACFAIPatrolComponent::UnbindControllerMoveCompleted()
{
    if (!CachedAIController || !CachedAIController->GetPathFollowingComponent() || !MoveCompletedHandle.IsValid()) {
        return;
    }

    CachedAIController->GetPathFollowingComponent()->OnRequestFinished.Remove(MoveCompletedHandle);
    MoveCompletedHandle.Reset();
}

void UACFAIPatrolComponent::OnComponentSaved()
{
    if (APawn* Pawn = Cast<APawn>(GetOwner()))
    {
        if (AACFAIController* Ctrl = Cast<AACFAIController>(Pawn->GetController()))
        {
            SavedHomeLocation = Ctrl->GetHomeLocation();
            bHasSavedHomeLocation = true;
        }
    }
}

void UACFAIPatrolComponent::OnComponentLoaded()
{
    if (!bHasSavedHomeLocation)
    {
        return;
    }

    if (APawn* Pawn = Cast<APawn>(GetOwner()))
    {
        if (AACFAIController* Ctrl = Cast<AACFAIController>(Pawn->GetController()))
        {
            Ctrl->SetHomeLocation(SavedHomeLocation);
        }
    }
}

void UACFAIPatrolComponent::NotifyPathPointReached(int32 PointIndex) const
{
    if (!PathToFollow || !CachedAIController || PointIndex == INDEX_NONE) {
        return;
    }

    PathToFollow->NotifyPointReached(PointIndex, CachedAIController->GetPawn());
}
