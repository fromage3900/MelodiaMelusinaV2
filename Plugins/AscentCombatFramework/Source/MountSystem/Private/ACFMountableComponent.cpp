// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFMountableComponent.h"
#include "ACFMountPointComponent.h"
#include "ACFRiderComponent.h"
#include "AIController.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/MeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/Character.h>

FName UACFMountableComponent::GetNearestMountPointTag(const FVector& location) const
{
    const UACFMountPointComponent* executionPoint = GetNearestMountPoint(location);
    if (executionPoint) {
        return executionPoint->GetPointTag();
    }

    return NAME_None;
}

class UACFMountPointComponent* UACFMountableComponent::GetNearestMountPoint(const FVector& location) const
{
    TArray<UACFMountPointComponent*> executionPoints;
    GetOwner()->GetComponents<UACFMountPointComponent>(executionPoints);

    UACFMountPointComponent* toBeReturned = nullptr;
    float minDistance = BIG_NUMBER;

    for (const auto& execPoint : executionPoints) {
        const FVector componentLoc = execPoint->GetComponentLocation();
        FVector distanceV = location - componentLoc;
        float distance;
        distanceV.ToDirectionAndLength(distanceV, distance);
        if (distance < minDistance) {
            toBeReturned = execPoint;
            minDistance = distance;
        }
    }

    return toBeReturned;
}

UACFMountableComponent::UACFMountableComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    // ...
}

// Called when the game starts
void UACFMountableComponent::BeginPlay()
{
    Super::BeginPlay();
    pawnOwner = Cast<APawn>(GetOwner());

    if (!pawnOwner) {
        UE_LOG(LogTemp, Error, TEXT("Mount must be pawn! - UACFMountComponent::BeginPlay"));
    }
}

void UACFMountableComponent::StartMount(ACharacter* inRider)
{
    if (!bIsMounted && inRider) {
        UACFRiderComponent* riderComp = inRider->FindComponentByClass<UACFRiderComponent>();
        if (riderComp) {
            riderComp->StartMount(this);
        }
    }
}

void UACFMountableComponent::StopMount_Implementation(FName dismountPoint /*= NAME_None*/)
{
    if (rider) {
        UACFRiderComponent* riderComp = rider->FindComponentByClass<UACFRiderComponent>();
        if (riderComp) {
            riderComp->StartDismount(dismountPoint);
        }
    }
}

void UACFMountableComponent::TriggerActionOnRider_Implementation(FGameplayTag ActionState, EActionPriority Priority /*= EActionPriority::ELow*/, bool bCanBeStored)
{
    if (!GetOwner()->HasAuthority()) {
        UE_LOG(LogTemp, Warning, TEXT("We are not on the server! - TriggerActionOnRider: %s"), *ActionState.ToString());
    }
    if (IsMounted() && GetRider()) {
        UACFAbilitySystemComponent* actionsComp = GetRider()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionsComp) {
            actionsComp->TriggerAction(ActionState, Priority, bCanBeStored);
        } else {
            UE_LOG(LogTemp, Warning, TEXT("Owner doesn't have actions comp! - UACFMountableComponent::TriggerActionOnRider"));
        }
    }
}

void UACFMountableComponent::ReleaseSustainedActionOnRider_Implementation(FGameplayTag actionTag)
{
    if (IsMounted() && GetRider()) {
        UACFAbilitySystemComponent* actionsComp = GetRider()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionsComp) {
            actionsComp->ReleaseSustainedAction(actionTag);
        } else {
            UE_LOG(LogTemp, Warning, TEXT("Owner doesn't have actions comp! - UACFMountableComponent::TriggerActionOnRider"));
        }
    }
}

FTransform UACFMountableComponent::GetMountPointTransform() const
{
    if (GetPawnOwner() && GetMountMesh()) {
        return GetMountMesh()->GetSocketTransform(MountPointSocket);
    }
    UE_LOG(LogTemp, Error, TEXT("Invalid Mount Point ! - UACFMountComponent::GetMountPointTransform"));
    return FTransform();
}

class UACFMountPointComponent* UACFMountableComponent::GetDismountPoint(const FName& dismountPoint /*= NAME_None*/) const
{
    TArray<UACFMountPointComponent*> executionPoints;
    const FName actualDismount = dismountPoint == NAME_None ? DefaultDismountPoint : dismountPoint;
    GetOwner()->GetComponents<UACFMountPointComponent>(executionPoints);
    for (const auto& execPoint : executionPoints) {
        if (execPoint->GetPointTag() == actualDismount) {
            return execPoint;
        }
    }
    return nullptr;
}

UMeshComponent* UACFMountableComponent::GetMountMesh() const
{
    if (mountMeshOverride) {
        return mountMeshOverride;
    }

    return pawnOwner->FindComponentByClass<UMeshComponent>();
}

FGameplayTag UACFMountableComponent::GetOwnerTeam() const
{
    const bool bImplements = GetPawnOwner()->GetClass()->ImplementsInterface(UACFEntityInterface::StaticClass());
    if (bImplements) {
        return IACFEntityInterface::Execute_GetEntityCombatTeam(GetPawnOwner());
    }
    return FGameplayTag();
}

void UACFMountableComponent::OnRep_IsMounted()
{
    OnMountedStateChanged.Broadcast(bIsMounted);
}

void UACFMountableComponent::SetMounted(bool inMounted)
{
    bIsMounted = inMounted;

    if (!bIsMounted) {
        rider = nullptr;
    }

    AAIController* aiContr = Cast<AAIController>(pawnOwner->GetController());
    if (aiContr) {
        UBehaviorTreeComponent* behavComp = aiContr->FindComponentByClass<UBehaviorTreeComponent>();

        if (inMounted) {

            if (behavComp) {
                behavComp->PauseLogic("Blocking Action");
                pawnOwner->DetachFromControllerPendingDestroy();
            }
        } else {
            if (behavComp) {
                behavComp->ResumeLogic("Blocking Action");
            }
        }
    }
    OnMountedStateChanged.Broadcast(inMounted);
}

void UACFMountableComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFMountableComponent, bIsMounted);
    DOREPLIFETIME(UACFMountableComponent, rider);
}
