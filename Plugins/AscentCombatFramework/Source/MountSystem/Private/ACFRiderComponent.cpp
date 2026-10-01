// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFRiderComponent.h"
#include "ACFAIController.h"
#include "ACFBaseAIController.h"
#include "ACFMountComponent.h"
#include "ACFMountPointComponent.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFGroupAIComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Net/UnrealNetwork.h"
#include <Components/CapsuleComponent.h>
#include <Components/SkeletalMeshComponent.h>
#include <GameFramework/Character.h>
#include <GameFramework/CharacterMovementComponent.h>
#include <GameFramework/PlayerController.h>
#include <TimerManager.h>
#include "Logging.h"


// Sets default values for this component's properties
UACFRiderComponent::UACFRiderComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
    // ...
}

// Called when the game starts
void UACFRiderComponent::BeginPlay()
{
    Super::BeginPlay();

    SetCharacterOwner(Cast<ACharacter>(GetOwner()));
}

void UACFRiderComponent::StartMount_Implementation(UACFMountableComponent* mount)
{
    if (!mount || !mount->CanBeMounted() || !GetCharacterOwner()) {
        UE_LOG(ACFLog, Warning, TEXT("Impossible to Mount!"));
        return;
    }
    if (bIsRiding) {
        StartDismount_Implementation(NAME_None);
    }
    Mount = mount;
    HandlePossession();
    Internal_Ride(true);
}

bool UACFRiderComponent::StartMount_Validate(UACFMountableComponent* mount)
{
    return true;
}

void UACFRiderComponent::OnRep_IsRiding()
{
    Internal_SetMountCollisionsEnabled(bIsRiding);
    OnRidingStateChanged.Broadcast(bIsRiding);
}

void UACFRiderComponent::StartDismount_Implementation(const FName& dismountPoint /*= NAME_None*/)
{
    if (!bIsRiding) {
        return;
    }
    FinishDismount(dismountPoint);
}

bool UACFRiderComponent::StartDismount_Validate(const FName& dismountPoint /*= NAME_None*/)
{
    return true;
}

void UACFRiderComponent::HandlePossession()
{
    if (!GetCharacterOwner()) {
        UE_LOG(ACFLog, Error, TEXT("Missing Owner on Riding Comp!'!"));
    }
    AController* contr = GetCharacterOwner()->GetController();
    APawn* mountedPawn = Mount->GetPawnOwner();
    if (contr && mountedPawn && Mount->NeedsPossession()) {

        AACFAIController* mountContr = Cast<AACFAIController>(mountedPawn->GetController());
        AACFCharacter* mountedChar = Cast<AACFCharacter>(mountedPawn);
        if (mountContr && mountedChar) {
            groupOwner = mountContr->GetGroup();

            if (groupOwner) {
                groupOwner->RemoveAgentFromGroup(mountedChar);
            }
        }
        mountedPawn->DetachFromControllerPendingDestroy();
        contr->UnPossess();
        contr->Possess(mountedPawn);
        GetCharacterOwner()->SpawnDefaultController();
        GetCharacterOwner()->bOnlyRelevantToOwner = false;
        AController* NewAI = GetCharacterOwner()->GetController();

        GetCharacterOwner()->SetOwner(NewAI);
        GetCharacterOwner()->ForceNetUpdate();
    }
}

void UACFRiderComponent::Internal_Ride(bool inIsRiding)
{
    bIsRiding = inIsRiding;
    Internal_SetMountCollisionsEnabled(bIsRiding);
    OnRidingStateChanged.Broadcast(bIsRiding);
    if (Mount) {
        if (bIsRiding) {
            Mount->SetRider(charOwner);
            Internal_AttachToMount();
        }
        Mount->SetMounted(bIsRiding);
    }
}

FGameplayTag UACFRiderComponent::GetMountTypeTag() const
{
    if (Mount) {
        return Mount->GetMountTag();
    }
    return FGameplayTag();
}

ACharacter* UACFRiderComponent::GetCharacterOwner() const
{
    if (charOwner)
    {
        return charOwner;
    }
    return Cast<ACharacter>(GetOwner());
}

void UACFRiderComponent::Internal_AttachToMount()
{
    if (!Mount) {
        StartDismount();
        return;
    }

    if (!GetCharacterOwner()) {
        UE_LOG(ACFLog, Error, TEXT("Missing Owner on Riding Comp!'!"));
    }
    // charOwner->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    //  charOwner->GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    GetCharacterOwner()->AttachToComponent(Mount->GetMountMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale,
        Mount->GetMountPoint());
    GetCharacterOwner()->GetCharacterMovement()->SetMovementMode(EMovementMode::MOVE_None);
}

void UACFRiderComponent::Internal_Mount()
{
    Internal_Ride(true);
}

void UACFRiderComponent::Internal_SetMountCollisionsEnabled(const bool bMounted)
{
   if (!GetCharacterOwner()) {
        UE_LOG(ACFLog, Error, TEXT("Missing Owner on Riding Comp!'!"));
    }

    if (bMounted) {
        //   charOwner->GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
        GetCharacterOwner()->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    } else {
        //   charOwner->GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        GetCharacterOwner()->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    }

    UAbilitySystemComponent* AbilitySystemComponent = GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
    if (AbilitySystemComponent) {
        AbilitySystemComponent->RefreshAbilityActorInfo();
    }
}

void UACFRiderComponent::OnRep_Mount()
{
    if (Mount) {
        Internal_AttachToMount();
    } else {
        Internal_DetachFromMount();
    }
}

void UACFRiderComponent::FinishDismount(const FName& dismountPoint /*= NAME_None*/)
{
    if (GetCharacterOwner() && bIsRiding && Mount) {
        Internal_DetachFromMount();
        const UACFMountPointComponent* pointComp = Mount->GetDismountPoint(dismountPoint);
        if (pointComp) {
            const FVector dismLocation = pointComp->GetComponentLocation();

            GetCharacterOwner()->SetActorLocation(dismLocation, true);
            const FRotator newRot(0.f, GetCharacterOwner()->GetActorRotation().Yaw, 0.f);
            GetCharacterOwner()->SetActorRotation(newRot);
        }

        APawn* pawnOwner = Mount->GetPawnOwner();
        if (pawnOwner) {
            AController* contr = pawnOwner->GetController();
            if (contr && Mount->NeedsPossession()) {
                GetCharacterOwner()->DetachFromControllerPendingDestroy();
                contr->Possess(GetCharacterOwner());
                pawnOwner->SpawnDefaultController();

                AACFAIController* mountContr = Cast<AACFAIController>(pawnOwner->GetController());
                AACFCharacter* mountedChar = Cast<AACFCharacter>(Mount->GetPawnOwner());

                if (groupOwner && mountedChar) {
                    groupOwner->AddExistingCharacterToGroup(mountedChar);
                    mountContr->SetLeadActorBK(GetCharacterOwner());
                }
                // QUICK FIX
                FRotator rot = contr->GetControlRotation();
                rot.Roll = 0.f;
                rot.Pitch = 0.f;
                contr->SetControlRotation(rot);
            }
        }
        Internal_Ride(false);
        Mount = nullptr;
    }
}

void UACFRiderComponent::Internal_DetachFromMount()
{
    GetCharacterOwner()->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
    GetCharacterOwner()->GetCharacterMovement()->SetMovementMode(EMovementMode::MOVE_Walking);
}

class APawn* UACFRiderComponent::GetMount() const
{
    if (Mount) {
        return Mount->GetMountOwner();
    }
    return nullptr;
}

void UACFRiderComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFRiderComponent, bIsRiding);
    DOREPLIFETIME(UACFRiderComponent, Mount);
}
