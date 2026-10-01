// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFAnimsetFragment.h"
#include "Animation/ACFAnimInstance.h"
#include "Animation/ACFAnimsetDataAsset.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Pawn.h"

void UACFAnimsetFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
    if (!pawnOwner || !AnimsetData)
    {
        return;
    }

    // Populate the layer look-up tables on the local AnimInstance.
    // ApplyFragmentsData() runs on both server and clients so every machine
    // gets its own tables filled — no replication needed for this step.
    // Active moveset/overlay selection continues to be driven by equipment
    // logic through UACFCharacterMovementComponent as normal.
    USkeletalMeshComponent* MeshComp = pawnOwner->FindComponentByClass<USkeletalMeshComponent>();
    if (!MeshComp)
    {
        return;
    }

    UACFAnimInstance* AnimInst = Cast<UACFAnimInstance>(MeshComp->GetAnimInstance());
    if (!AnimInst)
    {
        return;
    }

    AnimInst->ApplyAnimset(AnimsetData);
}
