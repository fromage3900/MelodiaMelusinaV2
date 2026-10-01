// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ATSBaseTargetComponent.h"
#include "ATSTargetPointComponent.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/Controller.h>

// Sets default values for this component's properties
UATSBaseTargetComponent::UATSBaseTargetComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UATSBaseTargetComponent::SetTargetPoint_Implementation(UATSTargetPointComponent* targetPoint)
{
    CurrentTargetPoint = targetPoint;
}

bool UATSBaseTargetComponent::SetTargetPoint_Validate(UATSTargetPointComponent* targetPoint)
{
    return true;
}

void UATSBaseTargetComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UATSBaseTargetComponent, CurrentTarget);
    DOREPLIFETIME(UATSBaseTargetComponent, CurrentTargetPoint);
}

void UATSBaseTargetComponent::SetTarget_Implementation(AActor* target)
{
    if (target != CurrentTarget) {
        CurrentTarget = target;
        OnNewTarget.Broadcast(CurrentTarget);
    }
}

bool UATSBaseTargetComponent::SetTarget_Validate(AActor* target)
{
    return true;
}

bool UATSBaseTargetComponent::IsTargetInSight() const
{

    AController* contr = Cast<AController>(GetOwner());
    if (contr) {
        return contr->LineOfSightTo(CurrentTarget);
    }
    return false;
}

bool UATSBaseTargetComponent::IsPotentialTargetInSight(AActor* potentialTarget) const
{
    AController* contr = Cast<AController>(GetOwner());
    if (contr) {
        return contr->LineOfSightTo(potentialTarget);
    }
    return false;
}

void UATSBaseTargetComponent::OnRep_CurrentTarget()
{
    OnNewTarget.Broadcast(CurrentTarget);
    OnTargetChanged();
}

void UATSBaseTargetComponent::OnTargetChanged()
{
}

FVector UATSBaseTargetComponent::GetCurrentTargetPointLocation() const
{
    if (CurrentTarget) {
        if (CurrentTargetPoint) {
            return CurrentTargetPoint->GetComponentLocation();
        } else {
            return CurrentTarget->GetActorLocation();
        }
    }

    return FVector();
}
