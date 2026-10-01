// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFSplineFollowerComponent.h"
#include "AIController.h"
#include "ACFSplinePath.h"
#include "Components/SplineComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "DrawDebugHelpers.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"

UACFSplineFollowerComponent::UACFSplineFollowerComponent()
{
    // Tick is enabled only while actively following; disabled otherwise to avoid overhead.
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;

    bIsActive = false;
    bIsWaitingForTarget = false;
    CurrentSplinePointIndex = 0;

    PointReachedThreshold = 100.0f;
    MaxFollowDistance = 2000.0f;
    MinFollowDistance = 500.0f;
    NavMeshProjectionExtent = 500.0f;
}

void UACFSplineFollowerComponent::BeginPlay()
{
    Super::BeginPlay();

    // This component must be owned by an AIController; cache the reference once here.
    OwnerAIController = Cast<AAIController>(GetOwner());
    if (!OwnerAIController) {
        UE_LOG(LogTemp, Warning, TEXT("ACFSplineFollowerComponent: Owner is not an AIController"));
    }
}

void UACFSplineFollowerComponent::StartFollowing(USplineComponent* InSpline, APawn* InTargetPawn)
{
    if (!OwnerAIController) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: No AIController found"));
        return;
    }

    InitPath(InSpline, InTargetPawn);
    StartFollowingCurrentSpline();
}

void UACFSplineFollowerComponent::InitPath(USplineComponent* InSpline, APawn* InTargetPawn)
{
    if (!InSpline || !InTargetPawn) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: Invalid spline or target pawn"));
        return;
    }

    SplinePath = InSpline;
    TargetPawn = InTargetPawn;
}

void UACFSplineFollowerComponent::StartFollowingCurrentSpline()
{
    bIsActive = true;
    bIsWaitingForTarget = false;

    if (!SplinePath || SplinePath->GetNumberOfSplinePoints() < 2) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: Invalid spline or not enough points"));
        StopFollowing();
        return;
    }

    // Find the next spline point ahead of the AI's current world position so that
    // resuming mid-path doesn't backtrack to already-visited points.
    if (OwnerAIController) {
        APawn* AIPawn = OwnerAIController->GetPawn();
        if (AIPawn) {
            const FVector CurrentLocation = AIPawn->GetActorLocation();
            const int32 NumPoints = SplinePath->GetNumberOfSplinePoints();

            // FindInputKeyClosestToWorldLocation returns a fractional key; ceiling gives
            // the first point that is strictly ahead of the current position.
            const float InputKey = SplinePath->FindInputKeyClosestToWorldLocation(CurrentLocation);
            const int32 NextPointIndex = FMath::CeilToInt(InputKey);
            CurrentSplinePointIndex = FMath::Clamp(NextPointIndex, 0, NumPoints - 1);

            UE_LOG(LogTemp, Log, TEXT("SplineFollower: Resuming from NEXT point %d (InputKey: %f)"),
                CurrentSplinePointIndex, InputKey);
        } else {
            CurrentSplinePointIndex = 0;
        }
    } else {
        CurrentSplinePointIndex = 0;
    }

    UE_LOG(LogTemp, Log, TEXT("SplineFollower: Starting to follow spline with %d points from point %d"),
        SplinePath->GetNumberOfSplinePoints(), CurrentSplinePointIndex);

    SetComponentTickEnabled(true);
    MoveToNextSplinePoint();
    OnFollowingStarted.Broadcast();
}

void UACFSplineFollowerComponent::StopFollowing()
{
    if (!bIsActive) {
        return;
    }

    bIsActive = false;
    SetComponentTickEnabled(false);

    // Remove the move-completed delegate before clearing the controller reference.
    if (OwnerAIController && MoveCompletedDelegateHandle.IsValid()) {
        OwnerAIController->GetPathFollowingComponent()->OnRequestFinished.Remove(MoveCompletedDelegateHandle);
        MoveCompletedDelegateHandle.Reset();
    }

    SplinePath = nullptr;
    TargetPawn = nullptr;

    OnFollowingStopped.Broadcast();
}

void UACFSplineFollowerComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!bIsActive || !SplinePath || !TargetPawn || !OwnerAIController) {
        return;
    }

    UpdateMovement(DeltaTime);
}

void UACFSplineFollowerComponent::UpdateMovement(float DeltaTime)
{
    // End the follow session once all spline points have been visited.
    if (HasReachedSplineEnd()) {
        UE_LOG(LogTemp, Warning, TEXT("SplineFollower: Spline completed!"));
        OnSplineCompleted.Broadcast();
        StopFollowing();
        return;
    }

    // If the target moved too far away, pause the AI and wait for them to catch up.
    if (IsTargetPawnTooFar()) {
        if (!bIsWaitingForTarget) {
            StopAndWaitForTargetPawn();
        }
        return;
    }

    // Once the target is close enough again, resume forward movement along the spline.
    if (bIsWaitingForTarget && IsTargetPawnCloseEnough()) {
        ResumeFollowingSpline();
        return;
    }
}

float UACFSplineFollowerComponent::GetProgressPercentage() const
{
    if (!SplinePath) {
        return 0.0f;
    }

    const int32 NumPoints = SplinePath->GetNumberOfSplinePoints();
    if (NumPoints <= 1) {
        return 0.0f;
    }

    return FMath::Clamp(
        (float)CurrentSplinePointIndex / (float)(NumPoints - 1) * 100.0f,
        0.0f,
        100.0f
    );
}

int32 UACFSplineFollowerComponent::GetCurrentSegmentIndex() const
{
    return CurrentSplinePointIndex;
}

float UACFSplineFollowerComponent::GetDistanceToTargetPawn() const
{
    if (!OwnerAIController || !TargetPawn) {
        return 0.0f;
    }

    const APawn* const AIPawn = OwnerAIController->GetPawn();
    if (!AIPawn) {
        return 0.0f;
    }

    return FVector::Dist(AIPawn->GetActorLocation(), TargetPawn->GetActorLocation());
}

bool UACFSplineFollowerComponent::IsTargetPawnTooFar() const
{
    return GetDistanceToTargetPawn() > MaxFollowDistance;
}

bool UACFSplineFollowerComponent::IsTargetPawnCloseEnough() const
{
    return GetDistanceToTargetPawn() < MinFollowDistance;
}

FVector UACFSplineFollowerComponent::GetNextSplineLocation() const
{
    if (!SplinePath) {
        return FVector::ZeroVector;
    }

    const int32 NumPoints = SplinePath->GetNumberOfSplinePoints();
    if (CurrentSplinePointIndex >= NumPoints) {
        return SplinePath->GetLocationAtSplinePoint(NumPoints - 1, ESplineCoordinateSpace::World);
    }

    return SplinePath->GetLocationAtSplinePoint(CurrentSplinePointIndex, ESplineCoordinateSpace::World);
}

bool UACFSplineFollowerComponent::HasReachedSplineEnd() const
{
    if (!SplinePath) {
        return true;
    }

    return CurrentSplinePointIndex >= SplinePath->GetNumberOfSplinePoints();
}

void UACFSplineFollowerComponent::MoveToNextSplinePoint()
{
    if (!OwnerAIController || !SplinePath) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: Cannot move, invalid AIController or SplinePath"));
        return;
    }

    if (!OwnerAIController->GetPathFollowingComponent()) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: PathFollowingComponent is missing on controller %s"),
            *GetNameSafe(OwnerAIController));
        StopFollowing();
        return;
    }

    if (!OwnerAIController->GetPawn()) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: Controller %s has no possessed pawn"),
            *GetNameSafe(OwnerAIController));
        StopFollowing();
        return;
    }

    const int32 NumSplinePoints = SplinePath->GetNumberOfSplinePoints();
    if (CurrentSplinePointIndex >= NumSplinePoints) {
        UE_LOG(LogTemp, Log, TEXT("SplineFollower: No more points to move to"));
        return;
    }

    const FVector SplinePointLocation = SplinePath->GetLocationAtSplinePoint(
        CurrentSplinePointIndex, ESplineCoordinateSpace::World);

    UE_LOG(LogTemp, Log, TEXT("SplineFollower: Moving to spline point %d/%d"),
        CurrentSplinePointIndex, NumSplinePoints - 1);

    // Project the spline point onto the NavMesh so the pathfinder has a valid destination.
    // If projection fails, fall back to the raw spline location unless strict mode is enabled.
    FVector TargetLocation = SplinePointLocation;
    UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld());
    if (NavSys) {
        FNavLocation NavLocation;
        const FVector SearchExtent(NavMeshProjectionExtent, NavMeshProjectionExtent, NavMeshProjectionExtent);
        const bool bProjected = NavSys->ProjectPointToNavigation(SplinePointLocation, NavLocation, SearchExtent);

        if (bProjected) {
            TargetLocation = NavLocation.Location;
        } else {
            UE_LOG(LogTemp, Warning, TEXT("SplineFollower: Failed to project point %d to NavMesh"),
                CurrentSplinePointIndex);

            if (bRequireValidNavMeshProjection) {
                UE_LOG(LogTemp, Error, TEXT("SplineFollower: Point %d requires valid NavMesh projection. Stopping follow."),
                    CurrentSplinePointIndex);
                StopFollowing();
                return;
            }
        }
    } else {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: NavigationSystem is null, cannot project spline point %d"),
            CurrentSplinePointIndex);
    }

    if (bDrawDebugProjectedGoals) {
        DrawDebugSphere(
            GetWorld(),
            TargetLocation,
            DebugProjectedGoalSphereRadius,
            12,
            DebugProjectedGoalSphereColor,
            false,
            DebugProjectedGoalSphereDuration
        );
    }

    FAIMoveRequest MoveRequest;
    MoveRequest.SetGoalLocation(TargetLocation);
    MoveRequest.SetAcceptanceRadius(PointReachedThreshold);
    MoveRequest.SetUsePathfinding(true);
    MoveRequest.SetReachTestIncludesAgentRadius(false);
    MoveRequest.SetCanStrafe(false);

    // Always remove the previous binding before adding a new one to avoid double-firing.
    if (MoveCompletedDelegateHandle.IsValid()) {
        OwnerAIController->GetPathFollowingComponent()->OnRequestFinished.Remove(MoveCompletedDelegateHandle);
    }
    MoveCompletedDelegateHandle = OwnerAIController->GetPathFollowingComponent()->OnRequestFinished.AddUObject(
        this, &UACFSplineFollowerComponent::OnMoveCompleted);

    FPathFollowingRequestResult MoveResult = OwnerAIController->MoveTo(MoveRequest);

    if (MoveResult.Code == EPathFollowingRequestResult::Failed) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: MoveTo FAILED for point %d. SplinePoint=%s Target=%s"),
            CurrentSplinePointIndex,
            *SplinePointLocation.ToString(),
            *TargetLocation.ToString());
        StopFollowing();
    } else if (MoveResult.Code == EPathFollowingRequestResult::AlreadyAtGoal) {
        // The AI is already standing on this point; immediately advance to the next one.
        UE_LOG(LogTemp, Warning, TEXT("SplineFollower: Already at point %d, moving to next"),
            CurrentSplinePointIndex);
        const int32 ReachedPointIndex = CurrentSplinePointIndex;
        CurrentSplinePointIndex++;
        OnSegmentReached.Broadcast(ReachedPointIndex);
        NotifySplinePathPointReached(ReachedPointIndex);
        MoveToNextSplinePoint();
    }
}

void UACFSplineFollowerComponent::OnMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result)
{
    // Discard completions that arrive while we're paused waiting for the target pawn,
    // or after the component has been deactivated.
    if (!bIsActive || bIsWaitingForTarget) {
        return;
    }
    (void)RequestID;

    if (!Result.IsSuccess()) {
        UE_LOG(LogTemp, Error, TEXT("SplineFollower: MoveTo failed"));
        StopFollowing();
        return;
    }

    UE_LOG(LogTemp, Log, TEXT("SplineFollower: Reached spline point %d"), CurrentSplinePointIndex);

    OnSegmentReached.Broadcast(CurrentSplinePointIndex);
    NotifySplinePathPointReached(CurrentSplinePointIndex);

    // At the final point, orient the pawn to match the spline's tangent direction.
    const int32 NumSplinePoints = SplinePath->GetNumberOfSplinePoints();
    if (CurrentSplinePointIndex >= NumSplinePoints - 1) {
        if (APawn* const AIPawn = OwnerAIController->GetPawn()) {
            const FRotator FinalRotation = SplinePath->GetRotationAtSplinePoint(
                CurrentSplinePointIndex, ESplineCoordinateSpace::World);
            UE_LOG(LogTemp, Log, TEXT("SplineFollower: Applying final spline rotation: %s"),
                *FinalRotation.ToString());
            AIPawn->SetActorRotation(FinalRotation);
        }
    }

    CurrentSplinePointIndex++;
    MoveToNextSplinePoint();
}

void UACFSplineFollowerComponent::NotifySplinePathPointReached(int32 PointIndex) const
{
    if (!SplinePath || !OwnerAIController) {
        return;
    }

    // The spline component's owner may be an AACFSplinePath actor that listens for point events.
    AACFSplinePath* SplinePathActor = Cast<AACFSplinePath>(SplinePath->GetOwner());
    if (!SplinePathActor) {
        return;
    }

    SplinePathActor->NotifyPointReached(PointIndex, OwnerAIController->GetPawn());
}

void UACFSplineFollowerComponent::StopAndWaitForTargetPawn()
{
    if (!OwnerAIController || !TargetPawn) {
        return;
    }

    bIsWaitingForTarget = true;
    OwnerAIController->StopMovement();

    // Face the target pawn while waiting so the idle pose looks intentional.
    if (APawn* const AIPawn = OwnerAIController->GetPawn()) {
        const FVector DirectionToTarget = (TargetPawn->GetActorLocation() - AIPawn->GetActorLocation()).GetSafeNormal();
        AIPawn->SetActorRotation(FRotator(0.0f, DirectionToTarget.Rotation().Yaw, 0.0f));
    }

    OnStartedWaitingForTarget.Broadcast();
}

void UACFSplineFollowerComponent::ResumeFollowingSpline()
{
    bIsWaitingForTarget = false;
    OnTargetRejoined.Broadcast();
    MoveToNextSplinePoint();
}
