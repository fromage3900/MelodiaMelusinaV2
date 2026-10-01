// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFBowAnimInstance.h"
#include "Items/ACFItem.h"
#include "Items/ACFWeapon.h"
#include <Animation/AnimInstance.h>

#include "Components/ACFEquipmentComponent.h"
#include <Components/SceneComponent.h>
#include <GameFramework/Character.h>
#include "ItemActors/ACFWeaponActor.h"

UACFBowAnimInstance::UACFBowAnimInstance()
{
    bowState = EBowState::EIdle;
    InterpSpeed = 10.f;
    PullSocket = "Arrow";
}

void UACFBowAnimInstance::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);

    if (weaponOwner) {
        if (!itemOwner) {
            itemOwner =weaponOwner->GetItemOwner();
        }

        if (itemOwner && !mainMesh) {
            const UACFEquipmentComponent* ownerComp = itemOwner->FindComponentByClass<UACFEquipmentComponent>();
            if (ownerComp) {
                mainMesh = ownerComp->GetMainMesh();
            }
        }

        if (mainMesh) {

            SocketLocation = mainMesh->GetSocketLocation(PullSocket);
        }

        switch (bowState) {
        case EBowState::EIdle:
            Alpha = FMath::FInterpTo(Alpha, 0.f, DeltaSeconds, InterpSpeed);
            break;
        case EBowState::EPulling:
            Alpha = FMath::FInterpTo(Alpha, 1.f, DeltaSeconds, InterpSpeed);
            break;
        case EBowState::ERelease:
            Alpha = FMath::FInterpTo(Alpha, 0.f, DeltaSeconds, InterpSpeed);

            break;
        default:
            break;
        }
    }
    else {
        GatherOwner();
    }
}

void UACFBowAnimInstance::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();

    GatherOwner();

}

void UACFBowAnimInstance::GatherOwner()
{
	USkeletalMeshComponent* OwnerComponent = GetSkelMeshComponent();
	weaponOwner = Cast<AACFWeaponActor>(OwnerComponent->GetOwner());
}

AActor* UACFBowAnimInstance::GetItemOwner() const
{
    return itemOwner;
}

void UACFBowAnimInstance::SetBowState(EBowState val)
{
    bowState = val;
    OnBowStateChanged.Broadcast(bowState);
}

void UACFBowAnimInstance::ReleaseString()
{
    SetBowState(EBowState::ERelease);
}

void UACFBowAnimInstance::PullString()
{
    SetBowState(EBowState::EPulling);
}
