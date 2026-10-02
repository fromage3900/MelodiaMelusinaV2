// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ATSTargetingComponent.h"
#include "ATSTargetPointComponent.h"
#include "ATSTargetableInterface.h"
#include "CCMCameraFunctionLibrary.h"
#include "Interfaces/ACFEntityInterface.h"
#include <Camera/PlayerCameraManager.h>
#include <Components/ActorComponent.h>
#include <Engine/World.h>
#include <GameFramework/Actor.h>
#include <GameFramework/Character.h>
#include <GameFramework/Controller.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>

// Sets default values for this component's properties
UATSTargetingComponent::UATSTargetingComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = true;

    SetTargetingType(ETargetingType::EMagneticLockYawOnly);
    SetMaxTargetingDistance(1500.f);
    SetComponentTickEnabled(false);
}

// Called when the game starts
void UATSTargetingComponent::BeginPlay()
{
    Super::BeginPlay();
    SetComponentTickEnabled(false);
    SetOwnerReferences();
}

void UATSTargetingComponent::ToggleTargeting()
{
    TriggerTargeting(!bIsTargeting);
}

// Called every frame
void UATSTargetingComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!bCanTarget && Xvalue < deadband && YValue < deadband) {
        bCanTarget = true;
    }

    UpdateTargeting(DeltaTime);
}

void UATSTargetingComponent::TriggerTargeting(bool bActivate)
{
    bIsTargeting = bActivate;
    if (bIsTargeting) {
        ActivateTargeting();
    } else {
        SetCurrentTarget(nullptr);
    }
    bIsTargeting = CurrentTarget != nullptr;
    OnTargetingStateChanged.Broadcast(bIsTargeting);
}

void UATSTargetingComponent::AddFilter(TSubclassOf<UATSTargetingFilter> filterClass)
{
    UATSTargetingFilter* newFilter = NewObject<UATSTargetingFilter>(filterClass);
    TargetFilters.AddUnique(newFilter);
}

void UATSTargetingComponent::AddObjectType(TEnumAsByte<EObjectTypeQuery> objectTypeToTrace)
{
    if (!ObjectsToQuery.Contains(objectTypeToTrace)) {
        ObjectsToQuery.Add(objectTypeToTrace);
    }
}

void UATSTargetingComponent::RemoveObjectType(TEnumAsByte<EObjectTypeQuery> objectTypeToTrace)
{
    if (ObjectsToQuery.Contains(objectTypeToTrace)) {
        ObjectsToQuery.Remove(objectTypeToTrace);
    }
}

bool UATSTargetingComponent::RemoveFilter(TSubclassOf<UATSTargetingFilter> filterClass)
{
    int32 index = -1;
    for (UATSTargetingFilter* filter : TargetFilters) {
        if (filter->IsA(filterClass)) {
            index = TargetFilters.IndexOfByKey(filter);
            break;
        }
    }
    if (TargetFilters.IsValidIndex(index)) {
        TargetFilters.RemoveAt(index);
        return true;
    }
    return false;
}

void UATSTargetingComponent::ActivateTargeting()
{
    AActor* currentTarget = nullptr;

    if (ControlledPawn && cameraManger) {
        PopulatePotentialTargetsArray();
        FVector cameraForwardVector = UKismetMathLibrary::GetForwardVector(cameraManger->GetCameraRotation());

        cameraForwardVector.Z = 0;
        cameraForwardVector = cameraForwardVector.GetSafeNormal();
        float maxDistance = BIG_NUMBER;
        float maxDirection = -1.0f;
        for (AActor* target : availableTargets) {

            if (target && target->WasRecentlyRendered() && IsValidTarget(target)) {

                float distance = target->GetDistanceTo(ControlledPawn);

                switch (GetTargetSelectionType()) {
                case ETargetSelectionType::ENearestTarget:

                    if (distance < maxDistance) {
                        currentTarget = target;
                        maxDistance = distance;
                    }
                    break;
                case ETargetSelectionType::EForwardTarget:
                    FVector vdistance = target->GetActorLocation() - ControlledPawn->GetActorLocation();
                    vdistance = vdistance.GetUnsafeNormal();
                    float direction = FVector::DotProduct(cameraForwardVector, vdistance);
                    if (direction > maxDirection) {
                        currentTarget = target;
                        maxDirection = direction;
                    }
                    break;
                }
            }

            if (currentTarget) {
                SetCurrentTarget(currentTarget);
            } else {
                UE_LOG(LogTemp, Warning, TEXT("No Availble Target"));
            }
        }
    }
}

TArray<AActor*> UATSTargetingComponent::GetAllTargetsByDirection(ETargetingDirection direction)
{
    TArray<AActor*> actorFilter;
    for (AActor* target : availableTargets) {
        if (target != CurrentTarget && IsValidTarget(target)) {
            FVector PotentialTargetLocation = target->GetActorLocation();

            if (!IsInFrontOfOwner(target)) {
                continue;
            }
            switch (direction) {
            case ETargetingDirection::ERight:
                if (IsRightOfCurrentTarget(PotentialTargetLocation)) {
                    actorFilter.AddUnique(target);
                }
                break;
            case ETargetingDirection::ELeft:
                if (!IsRightOfCurrentTarget(PotentialTargetLocation)) {
                    actorFilter.AddUnique(target);
                }
                break;
            case ETargetingDirection::EDown:
                if (!IsUpOfCurrentTarget(PotentialTargetLocation)) {
                    actorFilter.AddUnique(target);
                }
                break;
            case ETargetingDirection::EUp:
                if (IsUpOfCurrentTarget(PotentialTargetLocation)) {
                    actorFilter.AddUnique(target);
                }
                break;
            default:
                break;
            }
        }
    }

    return actorFilter;
}

bool UATSTargetingComponent::TrySwitchPointOnCurrentTarget(ETargetingDirection direction)
{
    UATSTargetPointComponent* bestpoint = nullptr;
    TArray<UATSTargetPointComponent*> potentialTargets;
    if (CurrentTarget && CurrentTargetPoint) {
        TArray<UActorComponent*> points;
        CurrentTarget->GetComponents(UATSTargetPointComponent::StaticClass(), points, true);
        if (points.Num() > 1) {
            for (auto point : points) {
                UATSTargetPointComponent* targetpoint = Cast<UATSTargetPointComponent>(point);
                if (targetpoint && targetpoint != CurrentTargetPoint) {
                    FVector PotentialTargetLocation = targetpoint->GetComponentLocation();

                    switch (direction) {
                    case ETargetingDirection::ERight:
                        if (IsRightOfCurrentTarget(PotentialTargetLocation)) {
                            potentialTargets.Add(targetpoint);
                        }
                        break;
                    case ETargetingDirection::ELeft:
                        if (!IsRightOfCurrentTarget(PotentialTargetLocation)) {
                            potentialTargets.Add(targetpoint);
                        }
                        break;
                    case ETargetingDirection::EDown:
                        if (!IsUpOfCurrentTarget(PotentialTargetLocation)) {
                            potentialTargets.Add(targetpoint);
                        }
                        break;
                    case ETargetingDirection::EUp:
                        if (IsUpOfCurrentTarget(PotentialTargetLocation)) {
                            potentialTargets.Add(targetpoint);
                        }
                        break;
                    default:
                        break;
                    }
                }
            }
        }
    }

    if (potentialTargets.Num() == 0) {
        return false;
    } else {
        UATSTargetPointComponent* finaltarget = GetNearestTargetPoint(potentialTargets);
        UpdateCurrentTargetPoint(finaltarget);
    }

    return false;
}

bool UATSTargetingComponent::IsRightOfCurrentTarget(FVector LocationToCheck)
{
    FVector CurrentTargetLocation = GetCurrentTargetPointLocation();
    FVector2D currentTargetLocationOnScreen;
    FVector2D potentialTargetLocationOnScreen;

    APlayerController* playerController = UGameplayStatics::GetPlayerController(this, 0);

    if (playerController) {
        playerController->ProjectWorldLocationToScreen(CurrentTargetLocation, currentTargetLocationOnScreen);
        playerController->ProjectWorldLocationToScreen(LocationToCheck, potentialTargetLocationOnScreen);

        return (potentialTargetLocationOnScreen.X - currentTargetLocationOnScreen.X) >= 0;
    }
    return false;
}

bool UATSTargetingComponent::IsUpOfCurrentTarget(FVector LocationToCheck)
{
    FVector CurrentTargetLocation = GetCurrentTargetPointLocation();
    FVector2D currentTargetLocationOnScreen;
    FVector2D potentialTargetLocationOnScreen;

    APlayerController* playerController = UGameplayStatics::GetPlayerController(this, 0);

    if (playerController) {
        playerController->ProjectWorldLocationToScreen(CurrentTargetLocation, currentTargetLocationOnScreen);
        playerController->ProjectWorldLocationToScreen(LocationToCheck, potentialTargetLocationOnScreen);

        return (potentialTargetLocationOnScreen.Y - currentTargetLocationOnScreen.Y) >= 0;
    }
    return false;
}

AActor* UATSTargetingComponent::GetNearestTarget(TArray<AActor*>& actorFilter)
{
    AActor* localTarget = nullptr;
    if (actorFilter.Num() > 0) {
        float distanceFromCurrentTarget = 999999.f;

        for (int32 i = 0; i < actorFilter.Num(); ++i) {
            if (!actorFilter[i]) {
                continue;
            }
            float distance = actorFilter[i]->GetDistanceTo(ControlledPawn);
            if (distance < distanceFromCurrentTarget) {
                distanceFromCurrentTarget = distance;
                localTarget = actorFilter[i];
            }
        }
    }
    return localTarget;
}

UATSTargetPointComponent* UATSTargetingComponent::GetNearestTargetPoint(TArray<UATSTargetPointComponent*> points)
{
    UATSTargetPointComponent* localTarget = nullptr;
    if (points.Num() > 0) {
        float distanceFromCurrentTarget = 999999.f;

        for (int32 i = 0; i < points.Num(); ++i) {
            if (!points.IsValidIndex(i)) {
                continue;
            }

            float distance = FVector::Distance(points[i]->GetComponentLocation(), CurrentTargetPoint->GetComponentLocation());
            if (distance < distanceFromCurrentTarget) {
                distanceFromCurrentTarget = distance;
                localTarget = points[i];
            }
        }
    }
    return localTarget;
}

void UATSTargetingComponent::HandlePawnChanged(class APawn* newPawn)
{
    ControlledPawn = newPawn;
}

bool UATSTargetingComponent::IsValidTarget(AActor* target)
{
    if (target && ControlledPawn && target != ControlledPawn) {
        bool bImplements = target->GetClass()->ImplementsInterface(UATSTargetableInterface::StaticClass());
        if (bImplements) {
            for (UATSTargetingFilter* filter : TargetFilters) {
                if (filter && !filter->IsActorTargetable(GetOwner(), target)) {
                    return false;
                }
            }
            return true;
        }
    }
    return false;
}

bool UATSTargetingComponent::IsInFrontOfOwner(AActor* target)
{

    FVector forward = cameraManger->GetCameraRotation().Vector();
    FVector distance = target->GetActorLocation() - ControlledPawn->GetActorLocation();
    distance.Normalize();
    float AimAtAngle = FMath::RadiansToDegrees(acosf(FVector::DotProduct(forward, distance)));
    if (AimAtAngle < GetMaxAngularDistanceDegree()) {
        return true;
    }
    return false;
}

void UATSTargetingComponent::UpdateTargeting(float deltaTime)
{

    if (ControlledPawn && bIsTargeting) {
        if (GetCurrentTarget() && !GetCurrentTarget()->IsPendingKillPending()) {
            if (GetCurrentTarget()->GetDistanceTo(ControlledPawn) >= GetMaxTargetingDistance() || (bCheckLineSight && !IsTargetInSight())) {
                TriggerTargeting(false);
            } else if (GetCurrentTarget()->GetClass() && 
                GetCurrentTarget()->GetClass()->ImplementsInterface(UACFEntityInterface::StaticClass())) {
                if (!IACFEntityInterface::Execute_IsEntityAlive(GetCurrentTarget())) {
                    TriggerTargeting(false);
                }
            }   
        } else {
            TriggerTargeting(false);
        }
    }
}

void UATSTargetingComponent::SetCurrentTarget(AActor* target)
{

    if (CurrentTarget) {
        const bool bImplements = CurrentTarget->GetClass()->ImplementsInterface(UATSTargetableInterface::StaticClass());
        if (bImplements) {
            IATSTargetableInterface::Execute_OnTargetLosed(CurrentTarget);
        }
        CurrentTarget = nullptr;
        CurrentTargetPoint = nullptr;
    }
    CleanCamera();

    if (target) {
        CurrentTarget = target;
        bCanTarget = false;
        UpdateCurrentTargetPoint(GetBestTargetPointForTarget(target));
        if (!CurrentTargetPoint) {
            UCCMCameraFunctionLibrary::LockCameraOnActor(this, target, GetLockTypeByTargetingType(GetTargetingType()), GetLockMagnetism());
        }
    } else {
        UCCMCameraFunctionLibrary::StopLockingCameraOnActor(this);
    }
    SetComponentTickEnabled(CurrentTarget != nullptr);
    SetTarget(CurrentTarget);
    OnTargetChanged.Broadcast(CurrentTarget);
}

void UATSTargetingComponent::UpdateCurrentTargetPoint(UATSTargetPointComponent* inCurrentTargetPoint)
{
    const bool bImplements = CurrentTarget->GetClass()->ImplementsInterface(UATSTargetableInterface::StaticClass());
    if (bImplements) {
        SetTargetPoint(inCurrentTargetPoint);
        CurrentTargetPoint = inCurrentTargetPoint;
        CleanCamera();
        IATSTargetableInterface::Execute_OnTargetAcquired(CurrentTarget, inCurrentTargetPoint);
        if (CurrentTargetPoint) {
            currentCameraEvent = CurrentTargetPoint->GetPointCameraEvent();
            if (currentCameraEvent != NAME_None) {
                UCCMCameraFunctionLibrary::TriggerCameraEvent(this, currentCameraEvent);
            }
            if (GetTargetingType() != ETargetingType::EDontLock) {
                UCCMCameraFunctionLibrary::LockCameraOnComponent(this, CurrentTargetPoint, GetLockTypeByTargetingType(GetTargetingType()), GetLockMagnetism());
            }
        }
    }
    bCanTarget = false;
}

void UATSTargetingComponent::CleanCamera()
{
    if (currentCameraEvent != NAME_None) {
        UCCMCameraFunctionLibrary::StopCameraEvent(this, currentCameraEvent);
        currentCameraEvent = NAME_None;
    }
}

UATSTargetPointComponent* UATSTargetingComponent::GetBestTargetPointForTarget(AActor* target)
{
    UATSTargetPointComponent* bestpoint = nullptr;
    float maxDirection = -1.f;
    if (target) {
        TArray<UActorComponent*> points;
        target->GetComponents(UATSTargetPointComponent::StaticClass(), points, true);
        FVector cameraForwardVector = UKismetMathLibrary::GetForwardVector(cameraManger->GetCameraRotation());

        cameraForwardVector.Z = 0;
        cameraForwardVector = cameraForwardVector.GetSafeNormal();

        if (points.Num() != 0) {
            for (auto point : points) {
                UATSTargetPointComponent* targetpoint = Cast<UATSTargetPointComponent>(point);
                if (targetpoint) {
                    FVector distance = targetpoint->GetComponentLocation() - ControlledPawn->GetActorLocation();
                    distance = distance.GetUnsafeNormal();
                    const float direction = FVector::DotProduct(cameraForwardVector, distance);
                    if (direction > maxDirection) {
                        bestpoint = targetpoint;
                        maxDirection = direction;
                    }
                }
            }
        }
    }

    return bestpoint;
}

void UATSTargetingComponent::RightSearchTargetWithInput(float InputValue)
{
    Xvalue = InputValue;
    if (bIsTargeting && FMath::Abs(InputValue) > InputTrasholdForSearch && bCanTarget) {
        ETargetingDirection direction;
        if (InputValue < 0) {
            direction = ETargetingDirection::ELeft;
        } else {
            direction = ETargetingDirection::ERight;
        }

        SwitchTargetByDirection(direction);
        return;
    }
}

ELockType UATSTargetingComponent::GetLockTypeByTargetingType(ETargetingType targetType)
{
    switch (targetType) {
    case ETargetingType::EDontLock:
        break;
    case ETargetingType::EMagneticLock:
        return ELockType::EAllAxis;
        break;
    case ETargetingType::EMagneticLockYawOnly:
        return ELockType::EYawOnly;
        break;
    default:
        break;
    }
    return ELockType::EAllAxis;
}

void UATSTargetingComponent::PopulatePotentialTargetsArray()
{
    if (ControlledPawn) {

        availableTargets.Empty();
        TArray<AActor*> ignoredActors;
        ignoredActors.Add(ControlledPawn);
        TArray<AActor*> potentialTargets;
        UKismetSystemLibrary::SphereOverlapActors(this, ControlledPawn->GetActorLocation(),
            GetMaxTargetingDistance(), ObjectsToQuery, AActor::StaticClass(), ignoredActors, potentialTargets);

        if (bCheckLineSight) {
            for (int32 i = potentialTargets.Num() - 1; i >= 0; i--) {
                if (!IsPotentialTargetInSight(potentialTargets[i])) {
                    potentialTargets.RemoveAt(i);
                }
            }
        }

        availableTargets = potentialTargets;
    } else {
        SetOwnerReferences();
    }
}

void UATSTargetingComponent::SwitchTargetByDirection(ETargetingDirection direction)
{
    if (TrySwitchPointOnCurrentTarget(direction)) {
        return;
    }

    PopulatePotentialTargetsArray();
    TArray<AActor*> actorFilter = GetAllTargetsByDirection(direction);

    AActor* localCurrentTarget = GetNearestTarget(actorFilter);

    if (localCurrentTarget && localCurrentTarget != CurrentTarget) {
        SetCurrentTarget(localCurrentTarget);

        return;
    }
}

void UATSTargetingComponent::UpSearchTargetWithInput(float InputValue)
{
    YValue = InputValue;

    if (bIsTargeting && FMath::Abs(InputValue) > InputTrasholdForSearch && bCanTarget) {
        ETargetingDirection direction;
        if (InputValue < 0) {
            direction = ETargetingDirection::EDown;
        } else {
            direction = ETargetingDirection::EUp;
        }

        SwitchTargetByDirection(direction);
        return;
    }
}

void UATSTargetingComponent::SetOwnerReferences()
{
    ControlledPawn = UGameplayStatics::GetPlayerPawn(this, 0);

    APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
    auto& eventNewPawn = controller->GetOnNewPawnNotifier();
    eventNewPawn.AddLambda([this](APawn* newPawn) {
        HandlePawnChanged(newPawn);
    });

    cameraManger = UGameplayStatics::GetPlayerCameraManager(this, 0);
    CurrentTarget = nullptr;
}
