// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CoreMinimal.h"

#include "ACFInputBufferNotifyState.generated.h"

/**
 *
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFInputBufferNotifyState : public UAnimNotifyState {
    GENERATED_BODY()

    void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override;

    void SetBufferEnabled(USkeletalMeshComponent* MeshComp, bool bEnabled);

    void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
};
