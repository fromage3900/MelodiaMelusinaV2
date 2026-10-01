// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFRiderAnimInstance.h"
#include "ACFRiderComponent.h"
#include <Actors/ACFCharacter.h>
#include <Animation/ACFAnimInstance.h>

void UACFRiderAnimInstance::NativeBeginPlay()
{
    Super::NativeBeginPlay();
    SetReferences();
}

void UACFRiderAnimInstance::SetReferences()
{
    ACharacter* character = Cast<ACharacter>(TryGetPawnOwner());
    if (!RiderComp && character) {
        RiderComp = character->FindComponentByClass<UACFRiderComponent>();
    }
}

void UACFRiderAnimInstance::NativeThreadSafeUpdateAnimation(float DeltaTime)
{
    Super::NativeThreadSafeUpdateAnimation(DeltaTime);

    if (RiderComp) {
        bIsRiding = RiderComp->IsRiding();
        if (bIsRiding) {
            ACharacter* mount = Cast<ACharacter>(RiderComp->GetMount());
            if (mount && mount->GetMesh()) {
                UACFAnimInstance* animInstance = Cast<UACFAnimInstance>(mount->GetMesh()->GetAnimInstance());
                if (animInstance) {
                    MountSpeed = animInstance->GetNormalizedSpeed();
                    MountTurn = animInstance->GetTurnRate();
                }
            }
        }

    } else {
        SetReferences();
    }
}

